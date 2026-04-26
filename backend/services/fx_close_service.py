from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

import models


def preview_fx_close(db: Session, company_id: UUID, month: str) -> dict:
    snapshots = (
        db.query(models.FxRevaluationSnapshot)
        .filter(
            models.FxRevaluationSnapshot.company_id == company_id,
            models.FxRevaluationSnapshot.snapshot_month == month,
        )
        .order_by(models.FxRevaluationSnapshot.base_currency.asc())
        .all()
    )

    rows = []
    total = Decimal("0")
    for snap in snapshots:
        gain_loss = Decimal(str(snap.gain_loss_inr or 0))
        total += gain_loss
        rows.append(
            {
                "snapshot_id": str(snap.id),
                "currency": snap.base_currency,
                "exposure": float(snap.exposure_amount or 0),
                "gain_loss_inr": float(gain_loss),
                "status": "gain" if gain_loss > 0 else "loss" if gain_loss < 0 else "flat",
            }
        )

    return {
        "company_id": str(company_id),
        "month": month,
        "snapshot_count": len(rows),
        "total_gain_loss_inr": float(total),
        "entries": rows,
    }


def post_fx_close_entries(db: Session, company_id: UUID, month: str, posted_by: str = "system") -> dict:
    existing = (
        db.query(models.FxCloseBatch)
        .filter(
            models.FxCloseBatch.company_id == company_id,
            models.FxCloseBatch.close_month == month,
            models.FxCloseBatch.status.in_(["posted", "approved"]),
        )
        .order_by(models.FxCloseBatch.created_at.desc())
        .first()
    )
    if existing:
        return {
            "success": False,
            "message": "FX close already posted for this month",
            "batch_id": str(existing.id),
            "status": existing.status,
        }

    preview = preview_fx_close(db, company_id, month)
    batch = models.FxCloseBatch(
        company_id=company_id,
        close_month=month,
        status="posted",
        total_gain_loss_inr=Decimal(str(preview["total_gain_loss_inr"])),
        posted_by=posted_by,
        posted_at=datetime.utcnow(),
        notes=f"Auto-posted from {preview['snapshot_count']} FX revaluation snapshots",
    )
    db.add(batch)
    db.flush()

    created_entries = 0
    snapshots = (
        db.query(models.FxRevaluationSnapshot)
        .filter(
            models.FxRevaluationSnapshot.company_id == company_id,
            models.FxRevaluationSnapshot.snapshot_month == month,
        )
        .all()
    )

    for snap in snapshots:
        gain_loss = Decimal(str(snap.gain_loss_inr or 0))
        if gain_loss == 0:
            continue

        # Balance sheet adjustment entry.
        db.add(
            models.GeneralLedger(
                company_id=company_id,
                account_code=models.GLAccountCode.ACCRUED_EXPENSES,
                account_name=f"FX Close Adjustment ({snap.base_currency})",
                transaction_date=datetime.utcnow().date(),
                debit_amount=gain_loss if gain_loss > 0 else 0,
                credit_amount=abs(gain_loss) if gain_loss < 0 else 0,
                description=f"FX close adjustment for {snap.base_currency} exposure in {month}",
                source_type="fx_close",
                reference_id=f"{batch.id}:{snap.id}:adjustment",
            )
        )

        # P&L unrealized FX impact entry.
        db.add(
            models.GeneralLedger(
                company_id=company_id,
                account_code=models.GLAccountCode.REVALUATION_GAIN_LOSS_UNREALIZED,
                account_name="Unrealized FX Gain/Loss",
                transaction_date=datetime.utcnow().date(),
                debit_amount=abs(gain_loss) if gain_loss < 0 else 0,
                credit_amount=gain_loss if gain_loss > 0 else 0,
                description=f"FX close P&L posting for {snap.base_currency} in {month}",
                source_type="fx_close",
                reference_id=f"{batch.id}:{snap.id}:pnl",
            )
        )
        created_entries += 2

    db.commit()
    db.refresh(batch)

    return {
        "success": True,
        "batch_id": str(batch.id),
        "status": batch.status,
        "month": month,
        "journal_entries_created": created_entries,
        "total_gain_loss_inr": float(batch.total_gain_loss_inr or 0),
    }


def approve_fx_close_batch(db: Session, batch_id: UUID, approved_by: str = "finance") -> dict:
    batch = db.query(models.FxCloseBatch).filter(models.FxCloseBatch.id == batch_id).first()
    if not batch:
        return {"success": False, "message": "Batch not found"}

    if batch.status == "approved":
        return {
            "success": True,
            "message": "Batch already approved",
            "batch_id": str(batch.id),
            "approved_at": batch.approved_at.isoformat() if batch.approved_at else None,
        }

    batch.status = "approved"
    batch.approved_by = approved_by
    batch.approved_at = datetime.utcnow()
    db.commit()

    return {
        "success": True,
        "message": "Batch approved",
        "batch_id": str(batch.id),
        "status": batch.status,
        "approved_by": approved_by,
        "approved_at": batch.approved_at.isoformat() if batch.approved_at else None,
    }
