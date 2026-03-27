from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import auth
import database
import models
from tasks.alert_tasks import send_email


router = APIRouter(prefix="/invoices", tags=["invoice_lifecycle"])


class MarkPaidRequest(BaseModel):
    payment_amount: Optional[float] = None
    payment_date: Optional[date] = None


class WriteOffRequest(BaseModel):
    reason: str = "Manual write-off"


class ReminderRequest(BaseModel):
    message: Optional[str] = None


def _get_invoice_or_404(db: Session, invoice_id: UUID) -> models.Invoice:
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.get("/queue/{company_id}")
def get_collections_queue(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Return open receivables sorted by urgency for collections ops."""
    today = date.today()
    rows = (
        db.query(models.Invoice)
        .filter(
            models.Invoice.company_id == company_id,
            models.Invoice.type == "ACCOUNTS_RECEIVABLE",
            models.Invoice.amount_due > 0,
        )
        .order_by(models.Invoice.due_date.asc())
        .limit(200)
        .all()
    )

    queue = []
    for inv in rows:
        due = inv.due_date or inv.issue_date
        days_overdue = max((today - due).days, 0) if due else 0
        amount_due = float(inv.amount_due or 0)

        if days_overdue >= 90:
            priority = "critical"
        elif days_overdue >= 30:
            priority = "high"
        elif days_overdue > 0:
            priority = "medium"
        else:
            priority = "normal"

        queue.append(
            {
                "invoice_id": str(inv.id),
                "invoice_number": inv.invoice_number,
                "due_date": due.isoformat() if due else None,
                "days_overdue": days_overdue,
                "amount_due": amount_due,
                "priority": priority,
                "status": inv.status,
            }
        )

    return {
        "as_of": today.isoformat(),
        "count": len(queue),
        "queue": queue,
    }


@router.get("/dso/{company_id}")
def get_dso(
    company_id: UUID,
    lookback_days: int = 90,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Estimate Days Sales Outstanding using trailing period receivables and credit sales."""
    if lookback_days <= 0:
        raise HTTPException(status_code=400, detail="lookback_days must be positive")

    today = date.today()
    start = today - timedelta(days=lookback_days)

    open_ar = float(
        sum(
            float(x[0] or 0)
            for x in db.query(models.Invoice.amount_due)
            .filter(
                models.Invoice.company_id == company_id,
                models.Invoice.type == "ACCOUNTS_RECEIVABLE",
                models.Invoice.amount_due > 0,
            )
            .all()
        )
    )

    period_credit_sales = float(
        sum(
            float(x[0] or 0)
            for x in db.query(models.Invoice.total_amount)
            .filter(
                models.Invoice.company_id == company_id,
                models.Invoice.type == "ACCOUNTS_RECEIVABLE",
                models.Invoice.issue_date >= start,
                models.Invoice.issue_date <= today,
            )
            .all()
        )
    )

    average_daily_sales = period_credit_sales / lookback_days if lookback_days > 0 else 0.0
    dso = open_ar / average_daily_sales if average_daily_sales > 0 else 0.0

    return {
        "as_of": today.isoformat(),
        "lookback_days": lookback_days,
        "open_ar": round(open_ar, 2),
        "period_credit_sales": round(period_credit_sales, 2),
        "average_daily_sales": round(average_daily_sales, 2),
        "dso_days": round(dso, 2),
    }


@router.post("/{invoice_id}/mark-paid")
def mark_invoice_paid(
    invoice_id: UUID,
    payload: MarkPaidRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Post payment against invoice and transition status automatically."""
    invoice = _get_invoice_or_404(db, invoice_id)

    if invoice.type != "ACCOUNTS_RECEIVABLE":
        raise HTTPException(status_code=400, detail="Only AR invoices can be marked paid from this endpoint")

    amount_due = Decimal(str(invoice.amount_due or 0))
    if amount_due <= 0:
        return {"success": True, "message": "Invoice already settled", "status": invoice.status}

    payment_amount = Decimal(str(payload.payment_amount if payload.payment_amount is not None else float(amount_due)))
    if payment_amount <= 0:
        raise HTTPException(status_code=400, detail="payment_amount must be positive")

    amount_paid = Decimal(str(invoice.amount_paid or 0)) + payment_amount
    new_due = amount_due - payment_amount
    if new_due < 0:
        new_due = Decimal("0")

    invoice.amount_paid = amount_paid
    invoice.amount_due = new_due
    invoice.payment_date = payload.payment_date or date.today()
    invoice.status = "PAID" if new_due == 0 else "PARTIALLY_PAID"

    db.commit()
    return {
        "success": True,
        "invoice_id": str(invoice.id),
        "status": invoice.status,
        "amount_paid": float(invoice.amount_paid or 0),
        "amount_due": float(invoice.amount_due or 0),
    }


@router.post("/{invoice_id}/write-off")
def write_off_invoice(
    invoice_id: UUID,
    payload: WriteOffRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Write off remaining amount and close invoice as void/write-off."""
    invoice = _get_invoice_or_404(db, invoice_id)
    previous_due = float(invoice.amount_due or 0)

    invoice.amount_due = Decimal("0")
    invoice.status = "VOID"
    memo = (invoice.memo or "").strip()
    suffix = f"[WRITE_OFF {datetime.utcnow().isoformat()}] {payload.reason}"
    invoice.memo = f"{memo}\n{suffix}" if memo else suffix

    db.commit()
    return {
        "success": True,
        "invoice_id": str(invoice.id),
        "written_off_amount": previous_due,
        "status": invoice.status,
    }


@router.post("/{invoice_id}/remind")
def send_invoice_reminder(
    invoice_id: UUID,
    payload: ReminderRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Send customer reminder email for overdue/open receivable invoices."""
    invoice = _get_invoice_or_404(db, invoice_id)

    if invoice.type != "ACCOUNTS_RECEIVABLE":
        raise HTTPException(status_code=400, detail="Only AR invoices support reminder emails")

    if float(invoice.amount_due or 0) <= 0:
        return {"success": False, "message": "Invoice is already settled"}

    contact_email = None
    if invoice.contact_id:
        contact = db.query(models.Contact).filter(models.Contact.id == invoice.contact_id).first()
        contact_email = contact.email if contact else None

    if not contact_email:
        return {"success": False, "message": "No contact email configured for this invoice"}

    subject = f"Payment reminder: Invoice {invoice.invoice_number}"
    default_message = (
        f"This is a friendly reminder that invoice {invoice.invoice_number} has an outstanding balance "
        f"of {float(invoice.amount_due or 0):,.2f}."
    )
    if invoice.due_date:
        default_message += f" Due date: {invoice.due_date.isoformat()}."

    body = payload.message or default_message
    sent, error = send_email(contact_email, subject, body)

    return {
        "success": sent,
        "invoice_id": str(invoice.id),
        "recipient": contact_email,
        "message": error if not sent else "Reminder sent",
    }
