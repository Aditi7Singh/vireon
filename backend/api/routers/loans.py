from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

import models
import schemas
import database
import auth
from analytics.metrics import calculate_loan_payment_schedule, calculate_loan_metrics

router = APIRouter(prefix="/loans", tags=["loans"])


@router.get("", response_model=List[schemas.Loan])
def get_loans(
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Get all loans for the company."""
    company = db.query(models.Company).first()
    if not company:
        raise HTTPException(status_code=404, detail="No company found")
    
    loans = db.query(models.Loan).filter(models.Loan.company_id == company.id).all()
    return loans


@router.post("", response_model=schemas.Loan)
def create_loan(
    loan: schemas.LoanCreate,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Create a new loan."""
    company = db.query(models.Company).first()
    if not company:
        raise HTTPException(status_code=404, detail="No company found")
    
    # Calculate initial remaining balance
    remaining_balance = loan.principal_amount
    
    db_loan = models.Loan(
        company_id=company.id,
        loan_name=loan.loan_name,
        principal_amount=loan.principal_amount,
        interest_rate=loan.interest_rate,
        term_months=loan.term_months,
        start_date=loan.start_date,
        loan_type=loan.loan_type,
        lender=loan.lender,
        status=loan.status,
        remaining_balance=remaining_balance
    )
    
    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)
    return db_loan


@router.get("/{loan_id}/schedule")
def get_loan_schedule(
    loan_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Get payment schedule for a loan."""
    loan = db.query(models.Loan).filter(models.Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    schedule = calculate_loan_payment_schedule(
        float(loan.principal_amount),
        float(loan.interest_rate),
        loan.term_months
    )
    
    return {"loan_id": loan_id, "schedule": schedule}


@router.post("/{loan_id}/payments")
def add_loan_payment(
    loan_id: UUID,
    payment: schemas.LoanPaymentBase,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Add a payment to a loan."""
    loan = db.query(models.Loan).filter(models.Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    # Create payment record
    db_payment = models.LoanPayment(
        loan_id=loan_id,
        payment_date=payment.payment_date,
        payment_amount=payment.payment_amount,
        principal_paid=payment.principal_paid,
        interest_paid=payment.interest_paid,
        remaining_balance=payment.remaining_balance
    )
    
    # Update loan balance
    loan.remaining_balance = payment.remaining_balance
    if payment.remaining_balance <= 0:
        loan.status = "paid_off"
    
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment


@router.get("/metrics")
def get_loan_metrics(
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Get overall loan metrics for the company."""
    company = db.query(models.Company).first()
    if not company:
        raise HTTPException(status_code=404, detail="No company found")
    
    metrics = calculate_loan_metrics(db, str(company.id))
    return metrics