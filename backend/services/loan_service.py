"""
Loan Service
============
Logic for automated loan payment processing and ledger integration.
"""

from datetime import date
from decimal import Decimal
from typing import Dict, Any, List
from uuid import UUID
from sqlalchemy.orm import Session
import models
from analytics.metrics import calculate_loan_payment_schedule

def auto_post_due_payments(db: Session, company_id: UUID) -> Dict[str, Any]:
    """
    Check for active loans and post due payments to the General Ledger.
    """
    active_loans = db.query(models.Loan).filter(
        models.Loan.company_id == company_id,
        models.Loan.status == "active"
    ).all()
    
    today = date.today()
    payments_posted = 0
    total_amount = Decimal("0")
    
    for loan in active_loans:
        # Check if a payment is already recorded for this month
        last_payment = db.query(models.LoanPayment).filter(
            models.LoanPayment.loan_id == loan.id
        ).order_by(models.LoanPayment.payment_date.desc()).first()
        
        # If no payment this month, and we are past the start date
        if loan.start_date <= today:
            next_due_date = loan.start_date
            if last_payment:
                # Naive next due date estimation (one month after last payment)
                # In a real system, we'd use the amortization schedule dates
                from dateutil.relativedelta import relativedelta
                next_due_date = last_payment.payment_date + relativedelta(months=1)
            
            if next_due_date <= today:
                # Generate schedule to find exact amounts for the next installment
                # This is a bit expensive, but accurate
                schedule = calculate_loan_payment_schedule(
                    float(loan.principal_amount),
                    float(loan.interest_rate) / 100,
                    loan.term_months
                )
                
                # Find the installment based on payment count
                payment_count = db.query(models.LoanPayment).filter(models.LoanPayment.loan_id == loan.id).count()
                if payment_count < len(schedule):
                    installment = schedule[payment_count]
                    
                    # Create payment record
                    db_payment = models.LoanPayment(
                        loan_id=loan.id,
                        payment_date=next_due_date,
                        payment_amount=Decimal(str(installment["payment"])),
                        principal_paid=Decimal(str(installment["principal_paid"])),
                        interest_paid=Decimal(str(installment["interest_paid"])),
                        remaining_balance=Decimal(str(installment["remaining_balance"]))
                    )
                    db.add(db_payment)
                    db.flush() # Get ID
                    
                    # Update loan balance
                    loan.remaining_balance = db_payment.remaining_balance
                    if loan.remaining_balance <= 0:
                        loan.status = "paid_off"
                    
                    # Post to Ledger
                    _post_loan_to_ledger(db, loan, db_payment)
                    
                    payments_posted += 1
                    total_amount += db_payment.payment_amount
    
    db.commit()
    return {
        "status": "success",
        "payments_posted": payments_posted,
        "total_amount": float(total_amount)
    }

def _post_loan_to_ledger(db: Session, loan: models.Loan, payment: models.LoanPayment):
    """Internal helper to create GL entries for a loan payment."""
    # Principal Payment (Debit Liability)
    db.add(models.GeneralLedger(
        company_id=loan.company_id,
        account_code=models.GLAccountCode.LONG_TERM_DEBT,
        account_name="Loan Principal Payment",
        transaction_date=payment.payment_date,
        debit_amount=payment.principal_paid,
        credit_amount=0,
        description=f"Auto-post principal repayment - {loan.loan_name}",
        source_type="loan_auto",
        reference_id=str(payment.id)
    ))
    
    # Interest Payment (Debit Expense)
    db.add(models.GeneralLedger(
        company_id=loan.company_id,
        account_code=models.GLAccountCode.ACCRUED_EXPENSES,
        account_name="Loan Interest Expense",
        transaction_date=payment.payment_date,
        debit_amount=payment.interest_paid,
        credit_amount=0,
        description=f"Auto-post interest payment - {loan.loan_name}",
        source_type="loan_auto",
        reference_id=str(payment.id)
    ))
    
    # Cash Credit
    db.add(models.GeneralLedger(
        company_id=loan.company_id,
        account_code=models.GLAccountCode.CASH,
        account_name="Cash & Bank",
        transaction_date=payment.payment_date,
        debit_amount=0,
        credit_amount=payment.payment_amount,
        description=f"Auto-post loan outflow - {loan.loan_name}",
        source_type="loan_auto",
        reference_id=str(payment.id)
    ))
