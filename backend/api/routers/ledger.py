from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, case
from sqlalchemy.orm import Session

import database
import models
import schemas
from services.ledger_service import create_ledger_entry, sync_existing_to_ledger

router = APIRouter(prefix="/ledger", tags=["ledger"])


@router.post("/entry", response_model=schemas.LedgerEntryRead)
def create_entry(payload: schemas.LedgerEntryCreate, db: Session = Depends(database.get_db)):
    return create_ledger_entry(db, payload.model_dump())


@router.get("/entries", response_model=list[schemas.LedgerEntryRead])
def list_entries(
    company_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[schemas.LedgerCategory] = None,
    product_tag: Optional[schemas.LedgerProductTag] = None,
    entry_type: Optional[schemas.LedgerEntryType] = None,
    db: Session = Depends(database.get_db),
):
    q = db.query(models.FinancialLedgerEntry).filter(models.FinancialLedgerEntry.company_id == company_id)
    if start_date:
        q = q.filter(models.FinancialLedgerEntry.transaction_date >= start_date)
    if end_date:
        q = q.filter(models.FinancialLedgerEntry.transaction_date <= end_date)
    if category:
        q = q.filter(models.FinancialLedgerEntry.category == category.value)
    if product_tag:
        q = q.filter(models.FinancialLedgerEntry.product_tag == product_tag.value)
    if entry_type:
        q = q.filter(models.FinancialLedgerEntry.entry_type == entry_type.value)
    return q.order_by(models.FinancialLedgerEntry.transaction_date.desc()).all()


@router.post("/sync")
def sync_ledger(company_id: UUID, db: Session = Depends(database.get_db)):
    return sync_existing_to_ledger(company_id, db)


@router.get("/summary")
def summary(company_id: UUID, db: Session = Depends(database.get_db)):
    rows = (
        db.query(
            func.date_trunc("month", models.FinancialLedgerEntry.transaction_date).label("month"),
            models.FinancialLedgerEntry.category,
            models.FinancialLedgerEntry.product_tag,
            func.sum(case((models.FinancialLedgerEntry.entry_type == "credit", models.FinancialLedgerEntry.amount_inr), else_=0)).label("credits"),
            func.sum(case((models.FinancialLedgerEntry.entry_type == "debit", models.FinancialLedgerEntry.amount_inr), else_=0)).label("debits"),
        )
        .filter(models.FinancialLedgerEntry.company_id == company_id)
        .group_by("month", models.FinancialLedgerEntry.category, models.FinancialLedgerEntry.product_tag)
        .order_by("month")
        .all()
    )
    data = []
    for r in rows:
        credits = float(r.credits or 0)
        debits = float(r.debits or 0)
        data.append(
            {
                "month": str(r.month.date()),
                "category": r.category.value if hasattr(r.category, "value") else str(r.category),
                "product_tag": r.product_tag.value if hasattr(r.product_tag, "value") else str(r.product_tag),
                "total_credits": credits,
                "total_debits": debits,
                "net_burn": debits - credits,
            }
        )
    return {"company_id": str(company_id), "summary": data}
