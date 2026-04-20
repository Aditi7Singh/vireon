from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

import auth
import database
import models

router = APIRouter(prefix="/invoices-list", tags=["invoices_api"])


class InvoiceCreate(BaseModel):
    invoice_number: Optional[str] = None
    contact_id: Optional[UUID] = None
    issue_date: date
    due_date: date
    type: str  # ACCOUNTS_RECEIVABLE | ACCOUNTS_PAYABLE
    sub_total: float
    tax_amount: float = 0.0
    currency: str = "USD"
    memo: Optional[str] = None


class InvoiceStatusUpdate(BaseModel):
    status: str
    payment_amount: Optional[float] = None
    payment_date: Optional[date] = None


def _serialize(inv: models.Invoice, contact_name: Optional[str] = None) -> dict:
    return {
        "id": str(inv.id),
        "invoice_number": inv.invoice_number,
        "contact_id": str(inv.contact_id) if inv.contact_id else None,
        "contact_name": contact_name,
        "issue_date": inv.issue_date.isoformat() if inv.issue_date else None,
        "due_date": inv.due_date.isoformat() if inv.due_date else None,
        "payment_date": inv.payment_date.isoformat() if inv.payment_date else None,
        "status": inv.status,
        "type": inv.type,
        "sub_total": float(inv.sub_total or 0),
        "tax_amount": float(inv.tax_amount or 0),
        "total_amount": float(inv.total_amount or 0),
        "amount_paid": float(inv.amount_paid or 0),
        "amount_due": float(inv.amount_due or 0),
        "currency": inv.currency,
        "memo": inv.memo,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
    }


def _get_contact_names(db: Session, invoices: list[models.Invoice]) -> dict[str, str]:
    contact_ids = {inv.contact_id for inv in invoices if inv.contact_id}
    if not contact_ids:
        return {}
    contacts = db.query(models.Contact).filter(models.Contact.id.in_(contact_ids)).all()
    return {str(c.id): c.name for c in contacts}


@router.get("")
def list_invoices(
    company_id: UUID,
    type: Optional[str] = Query(None, description="ACCOUNTS_RECEIVABLE or ACCOUNTS_PAYABLE"),
    status: Optional[str] = Query(None),
    contact_id: Optional[UUID] = Query(None),
    limit: int = Query(200, le=1000),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    q = db.query(models.Invoice).filter(models.Invoice.company_id == company_id)
    if type:
        q = q.filter(models.Invoice.type == type)
    if status:
        q = q.filter(models.Invoice.status == status)
    if contact_id:
        q = q.filter(models.Invoice.contact_id == contact_id)
    invoices = q.order_by(models.Invoice.issue_date.desc()).limit(limit).all()
    names = _get_contact_names(db, invoices)

    # AR aging buckets
    today = date.today()
    aging = {"current": 0.0, "1_30": 0.0, "31_60": 0.0, "61_90": 0.0, "over_90": 0.0}
    for inv in invoices:
        if inv.amount_due and float(inv.amount_due) > 0 and inv.due_date:
            days = (today - inv.due_date).days
            amt = float(inv.amount_due)
            if days <= 0:
                aging["current"] += amt
            elif days <= 30:
                aging["1_30"] += amt
            elif days <= 60:
                aging["31_60"] += amt
            elif days <= 90:
                aging["61_90"] += amt
            else:
                aging["over_90"] += amt

    return {
        "count": len(invoices),
        "invoices": [_serialize(inv, names.get(str(inv.contact_id))) for inv in invoices],
        "aging": {k: round(v, 2) for k, v in aging.items()},
        "total_outstanding": round(sum(aging.values()), 2),
    }


@router.get("/{invoice_id}")
def get_invoice(
    invoice_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    inv = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    name = None
    if inv.contact_id:
        c = db.query(models.Contact).filter(models.Contact.id == inv.contact_id).first()
        name = c.name if c else None
    return _serialize(inv, name)


@router.post("", status_code=201)
def create_invoice(
    company_id: UUID,
    payload: InvoiceCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    total = Decimal(str(payload.sub_total)) + Decimal(str(payload.tax_amount))
    inv_num = payload.invoice_number or f"INV-{uuid4().hex[:8].upper()}"

    inv = models.Invoice(
        id=uuid4(),
        company_id=company_id,
        remote_id=f"manual-{uuid4()}",
        invoice_number=inv_num,
        contact_id=payload.contact_id,
        issue_date=payload.issue_date,
        due_date=payload.due_date,
        status="DRAFT",
        type=payload.type,
        sub_total=Decimal(str(payload.sub_total)),
        tax_amount=Decimal(str(payload.tax_amount)),
        total_amount=total,
        amount_paid=Decimal("0"),
        amount_due=total,
        currency=payload.currency,
        memo=payload.memo,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return _serialize(inv)


@router.patch("/{invoice_id}/status")
def update_invoice_status(
    invoice_id: UUID,
    payload: InvoiceStatusUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    inv = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    inv.status = payload.status
    if payload.payment_amount is not None:
        paid = Decimal(str(inv.amount_paid or 0)) + Decimal(str(payload.payment_amount))
        inv.amount_paid = paid
        inv.amount_due = max(Decimal(str(inv.total_amount or 0)) - paid, Decimal("0"))
        inv.payment_date = payload.payment_date or date.today()
        if inv.amount_due == 0:
            inv.status = "PAID"
        else:
            inv.status = "PARTIALLY_PAID"

    inv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(inv)
    return _serialize(inv)


@router.delete("/{invoice_id}", status_code=204)
def void_invoice(
    invoice_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    inv = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    inv.status = "VOID"
    inv.updated_at = datetime.utcnow()
    db.commit()
