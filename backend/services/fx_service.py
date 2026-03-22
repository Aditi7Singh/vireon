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

        # --- Ledger Integration ---
        if gain_loss != 0:
            # Entry 1: Adjust the balance sheet (Asset/Liability adjustment)
            # For simplicity, we use ACCRUED_EXPENSES as the contra account for revaluation
            adjustment_entry = models.GeneralLedger(
                company_id=company_id,
                account_code=models.GLAccountCode.ACCRUED_EXPENSES,
                account_name=f"FX Revaluation Adjustment ({base_currency})",
                transaction_date=datetime.utcnow().date(),
                debit_amount=gain_loss if gain_loss > 0 else 0,
                credit_amount=abs(gain_loss) if gain_loss < 0 else 0,
                description=f"Unrealized FX adjustment for {base_currency} exposure in {month}",
                source_type="fx_revaluation",
                reference_id=str(snap.id)
            )
            db.add(adjustment_entry)

            # Entry 2: Record the unrealized gain/loss in the P&L
            pnl_entry = models.GeneralLedger(
                company_id=company_id,
                account_code=models.GLAccountCode.REVALUATION_GAIN_LOSS_UNREALIZED,
                account_name="Unrealized FX Gain/Loss",
                transaction_date=datetime.utcnow().date(),
                debit_amount=abs(gain_loss) if gain_loss < 0 else 0, # Loss is debit
                credit_amount=gain_loss if gain_loss > 0 else 0,    # Gain is credit
                description=f"Unrealized FX gain/loss on {base_currency} for {month}",
                source_type="fx_revaluation",
                reference_id=str(snap.id)
            )
            db.add(pnl_entry)

    db.commit()

    return {
        "company_id": str(company_id),
        "month": month,
        "snapshots_created": len(snapshots),
        "total_gain_loss_inr": float(sum(Decimal(str(s.gain_loss_inr or 0)) for s in snapshots)),
    }


def get_multicurrency_pl(db: Session, company_id: UUID, month: str) -> dict:
    """
    Consolidate P&L across all currencies into base currency (INR).
    """
    start, end = _month_bounds(month)
    
    entries = db.query(
        models.FinancialLedgerEntry.currency,
        models.FinancialLedgerEntry.entry_type,
        func.sum(models.FinancialLedgerEntry.amount).label("amount"),
        func.sum(models.FinancialLedgerEntry.amount_inr).label("amount_inr")
    ).filter(
        models.FinancialLedgerEntry.company_id == company_id,
        models.FinancialLedgerEntry.transaction_date >= start,
        models.FinancialLedgerEntry.transaction_date < end
    ).group_by(
        models.FinancialLedgerEntry.currency,
        models.FinancialLedgerEntry.entry_type
    ).all()
    
    currency_data = {}
    total_revenue_inr = Decimal("0")
    total_expense_inr = Decimal("0")
    
    for e in entries:
        curr = e.currency or "INR"
        if curr not in currency_data:
            currency_data[curr] = {"credits": 0.0, "debits": 0.0}
            
        amt = float(e.amount or 0)
        amt_inr = Decimal(str(e.amount_inr or 0))
        
        if e.entry_type == models.LedgerEntryType.CREDIT:
            currency_data[curr]["credits"] += amt
            total_revenue_inr += amt_inr
        else:
            currency_data[curr]["debits"] += amt
            total_expense_inr += amt_inr
            
    return {
        "month": month,
        "currency_breakdown": currency_data,
        "consolidated_revenue_inr": float(total_revenue_inr),
        "consolidated_expense_inr": float(total_expense_inr),
        "net_profit_inr": float(total_revenue_inr - total_expense_inr)
    }


def get_fx_adjusted_runway(db: Session, company_id: UUID) -> dict:
    """
    Calculate runway factoring in FX exposure and revaluation results.
    """
    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()
    
    if not latest_metric:
        return {"error": "No data available"}
        
    cash = float(latest_metric.ending_cash or 0)
    burn = float(latest_metric.burn_rate or 1)
    
    # Get recent revaluation effects
    revals = db.query(models.FxRevaluationSnapshot).filter(
        models.FxRevaluationSnapshot.company_id == company_id
    ).order_by(models.FxRevaluationSnapshot.snapshot_month.desc()).limit(3).all()
    
    avg_fx_gain_loss = sum(float(r.gain_loss_inr or 0) for r in revals) / len(revals) if revals else 0.0
    
    # Adjusted burn includes FX volatility buffer
    adjusted_burn = burn - avg_fx_gain_loss 
    runway = cash / max(adjusted_burn, 1)
    
    return {
        "cash_balance": cash,
        "base_burn_rate": burn,
        "avg_fx_volatility_impact": avg_fx_gain_loss,
        "fx_adjusted_burn": adjusted_burn,
        "runway_months": round(runway, 1)
    }

