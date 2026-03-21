from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, case
from sqlalchemy.orm import Session

import models


def _month_bounds(month: str):
    start = datetime.strptime(month, "%Y-%m").date().replace(day=1)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def _latest_rate(db: Session, base_currency: str, as_of_month: str):
    start, _ = _month_bounds(as_of_month)
    return (
        db.query(models.ExchangeRate)
        .filter(
            models.ExchangeRate.base_currency == base_currency,
            models.ExchangeRate.target_currency == "INR",
            models.ExchangeRate.status == "active",
            models.ExchangeRate.effective_date <= start,
        )
        .order_by(models.ExchangeRate.effective_date.desc())
        .first()
    )


def _previous_month(month: str) -> str:
    dt = datetime.strptime(month, "%Y-%m")
    if dt.month == 1:
        return f"{dt.year - 1}-12"
    return f"{dt.year}-{dt.month - 1:02d}"


def run_revaluation(db: Session, company_id: UUID, month: str) -> dict:
    start, end = _month_bounds(month)

    rows = (
        db.query(
            models.FinancialLedgerEntry.currency,
            func.sum(
                case(
                    (models.FinancialLedgerEntry.entry_type == models.LedgerEntryType.CREDIT, -models.FinancialLedgerEntry.amount),
                    else_=models.FinancialLedgerEntry.amount,
                )
            ).label("exposure"),
        )
        .filter(
            models.FinancialLedgerEntry.company_id == company_id,
            models.FinancialLedgerEntry.transaction_date >= start,
            models.FinancialLedgerEntry.transaction_date < end,
            models.FinancialLedgerEntry.currency != "INR",
        )
        .group_by(models.FinancialLedgerEntry.currency)
        .all()
    )

    db.query(models.FxRevaluationSnapshot).filter(
        models.FxRevaluationSnapshot.company_id == company_id,
        models.FxRevaluationSnapshot.snapshot_month == month,
    ).delete()

    snapshots = []
    prev_month = _previous_month(month)
    for r in rows:
        base_currency = (r.currency or "INR").upper()
        exposure = Decimal(str(r.exposure or 0))

        current_rate_row = _latest_rate(db, base_currency, month)
        previous_rate_row = _latest_rate(db, base_currency, prev_month)
        current_rate = Decimal(str(current_rate_row.exchange_rate)) if current_rate_row else Decimal("1")
        previous_rate = Decimal(str(previous_rate_row.exchange_rate)) if previous_rate_row else current_rate

        revalued_amount_inr = exposure * current_rate
        gain_loss = exposure * (current_rate - previous_rate)

        snap = models.FxRevaluationSnapshot(
            company_id=company_id,
            snapshot_month=month,
            base_currency=base_currency,
            exposure_amount=exposure,
            previous_rate=previous_rate,
            current_rate=current_rate,
            revalued_amount_inr=revalued_amount_inr,
            gain_loss_inr=gain_loss,
        )
        db.add(snap)
        snapshots.append(snap)

    db.commit()

    return {
        "company_id": str(company_id),
        "month": month,
        "snapshots_created": len(snapshots),
        "total_gain_loss_inr": float(sum(Decimal(str(s.gain_loss_inr or 0)) for s in snapshots)),
    }
