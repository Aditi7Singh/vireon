from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date

import database
from services.tax_service import (
    get_active_tax_rules,
    calculate_tax_for_invoice,
    calculate_tax_for_payroll,
    calculate_quarterly_tax_summary,
)

router = APIRouter(prefix="/tax", tags=["tax"])


@router.get("/rules/{company_id}")
def list_tax_rules(company_id: UUID, db: Session = Depends(database.get_db)):
    """List all active tax rules for a company."""
    rules = get_active_tax_rules(db, company_id)
    return [
        {
            "id": str(r.id),
            "tax_name": r.tax_name,
            "rate": float(r.rate),
            "threshold_amount": float(r.threshold_amount) if r.threshold_amount else None,
            "description": r.description,
            "is_active": r.is_active,
        }
        for r in rules
    ]


@router.get("/calculate/invoice")
def tax_for_invoice(
    company_id: UUID,
    invoice_base_amount: float,
    is_service: bool = True,
    db: Session = Depends(database.get_db),
):
    """Calculate GST + TDS for an invoice amount using active TaxRules."""
    return calculate_tax_for_invoice(db, company_id, invoice_base_amount, is_service)


@router.get("/calculate/payroll")
def tax_for_payroll(
    company_id: UUID,
    gross_monthly: float,
    db: Session = Depends(database.get_db),
):
    """Calculate PF, ESI, PT deductions for a given gross salary."""
    return calculate_tax_for_payroll(db, company_id, gross_monthly)


@router.get("/quarterly-summary")
def quarterly_tax_summary(
    company_id: UUID,
    year: int,
    quarter: int,
    db: Session = Depends(database.get_db),
):
    """Get quarterly tax liability summary (GST + TDS aggregated)."""
    return calculate_quarterly_tax_summary(db, company_id, year, quarter)


@router.post("/quarterly-liability")
def create_liability(
    company_id: UUID,
    year: int,
    quarter: int,
    db: Session = Depends(database.get_db),
):
    """Compute and persist the quarterly tax liability."""
    from services.tax_service import create_quarterly_liability
    return create_quarterly_liability(db, company_id, year, quarter)


@router.get("/payment-schedule/{company_id}")
def payment_schedule(
    company_id: UUID,
    db: Session = Depends(database.get_db),
):
    """Get upcoming tax payment schedule."""
    from services.tax_service import get_payment_schedule
    return get_payment_schedule(db, company_id)


@router.post("/reconcile-payment")
def reconcile_payment(
    liability_id: UUID,
    amount: float,
    reference: str,
    db: Session = Depends(database.get_db),
):
    """Mark a tax payment as completed."""
    from services.tax_service import reconcile_tax_payment
    return reconcile_tax_payment(db, liability_id, amount, reference)
