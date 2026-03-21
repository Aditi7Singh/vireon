from datetime import date
from decimal import Decimal
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import auth
import database
import models
from services.fx_service import run_revaluation


router = APIRouter(prefix="/fx", tags=["fx"])


class ConvertRequest(BaseModel):
    amount: float
    base_currency: str
    target_currency: str = "INR"


@router.post("/sync-default")
def sync_default_rates(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    today = date.today()
    default_rates = {
        "USD": Decimal("83.000000"),
        "EUR": Decimal("90.000000"),
        "GBP": Decimal("105.000000"),
        "INR": Decimal("1.000000"),
    }

    upserted = 0
    for base_currency, rate in default_rates.items():
        existing = (
            db.query(models.ExchangeRate)
            .filter(
                models.ExchangeRate.base_currency == base_currency,
                models.ExchangeRate.target_currency == "INR",
                models.ExchangeRate.effective_date == today,
            )
            .first()
        )
        if existing:
            existing.exchange_rate = rate
            existing.status = "active"
        else:
            db.add(
                models.ExchangeRate(
                    id=uuid.uuid4(),
                    base_currency=base_currency,
                    target_currency="INR",
                    exchange_rate=rate,
                    effective_date=today,
                    status="active",
                )
            )
        upserted += 1
    db.commit()

    return {"synced": upserted, "effective_date": today.isoformat()}


@router.post("/convert")
def convert_currency(
    payload: ConvertRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    base = payload.base_currency.upper()
    target = payload.target_currency.upper()
    if base == target:
        return {"amount": payload.amount, "converted_amount": payload.amount, "rate": 1.0, "currency": target}

    rate_row = (
        db.query(models.ExchangeRate)
        .filter(
            models.ExchangeRate.base_currency == base,
            models.ExchangeRate.target_currency == target,
            models.ExchangeRate.status == "active",
        )
        .order_by(models.ExchangeRate.effective_date.desc())
        .first()
    )

    if not rate_row:
        raise HTTPException(status_code=404, detail=f"No exchange rate for {base}->{target}")

    converted = Decimal(str(payload.amount)) * Decimal(str(rate_row.exchange_rate))
    return {
        "amount": payload.amount,
        "converted_amount": float(converted),
        "rate": float(rate_row.exchange_rate),
        "currency": target,
        "effective_date": rate_row.effective_date.isoformat(),
    }


@router.post("/revalue/{company_id}")
def revalue_company_fx(
    company_id: UUID,
    month: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return run_revaluation(db, company_id, month)


@router.get("/snapshots/{company_id}")
def get_revaluation_snapshots(
    company_id: UUID,
    month: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    rows = (
        db.query(models.FxRevaluationSnapshot)
        .filter(
            models.FxRevaluationSnapshot.company_id == company_id,
            models.FxRevaluationSnapshot.snapshot_month == month,
        )
        .order_by(models.FxRevaluationSnapshot.base_currency.asc())
        .all()
    )
    return {
        "company_id": str(company_id),
        "month": month,
        "snapshots": [
            {
                "base_currency": r.base_currency,
                "exposure_amount": float(r.exposure_amount or 0),
                "previous_rate": float(r.previous_rate or 0),
                "current_rate": float(r.current_rate or 0),
                "revalued_amount_inr": float(r.revalued_amount_inr or 0),
                "gain_loss_inr": float(r.gain_loss_inr or 0),
            }
            for r in rows
        ],
    }
