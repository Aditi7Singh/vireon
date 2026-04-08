"""
Bank Reconciliation Router
Auto-match bank transactions with GL entries
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
import uuid
from difflib import SequenceMatcher

import database
import models
from auth import get_current_user

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])


@router.post("/", response_model=dict)
def create_reconciliation(
    company_id: uuid.UUID,
    account_id: uuid.UUID,
    period_start: date,
    period_end: date,
    statement_balance: Decimal,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new bank reconciliation"""
    # Calculate book balance
    book_balance = calculate_book_balance(db, account_id, period_start, period_end)
    variance = statement_balance - book_balance
    
    recon = models.BankReconciliation(
        company_id=company_id,
        account_id=account_id,
        period_start=period_start,
        period_end=period_end,
        statement_balance=statement_balance,
        book_balance=book_balance,
        variance=variance,
        status=models.ReconciliationStatus.PENDING
    )
    db.add(recon)
    db.commit()
    db.refresh(recon)
    
    # Auto-match transactions
    auto_match_transactions(db, recon.id, account_id, period_start, period_end)
    
    return {
        "reconciliation_id": str(recon.id),
        "statement_balance": float(statement_balance),
        "book_balance": float(book_balance),
        "variance": float(variance),
        "status": recon.status.value
    }


@router.get("/{reconciliation_id}", response_model=dict)
def get_reconciliation(
    reconciliation_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get reconciliation details"""
    recon = db.query(models.BankReconciliation).filter(
        models.BankReconciliation.id == reconciliation_id
    ).first()
    
    if not recon:
        raise HTTPException(status_code=404, detail="Reconciliation not found")
    
    # Get matched and unmatched counts
    matched_count = db.query(models.BankTransactionMatch).filter(
        and_(
            models.BankTransactionMatch.reconciliation_id == reconciliation_id,
            models.BankTransactionMatch.ledger_entry_id.isnot(None)
        )
    ).count()
    
    unmatched_count = db.query(models.BankTransactionMatch).filter(
        and_(
            models.BankTransactionMatch.reconciliation_id == reconciliation_id,
            models.BankTransactionMatch.ledger_entry_id.is_(None)
        )
    ).count()
    
    return {
        "id": str(recon.id),
        "company_id": str(recon.company_id),
        "account_id": str(recon.account_id),
        "period_start": recon.period_start.isoformat(),
        "period_end": recon.period_end.isoformat(),
        "statement_balance": float(recon.statement_balance),
        "book_balance": float(recon.book_balance),
        "variance": float(recon.variance),
        "status": recon.status.value,
        "matched_count": matched_count,
        "unmatched_count": unmatched_count,
        "approved_by": recon.approved_by,
        "approved_at": recon.approved_at.isoformat() if recon.approved_at else None
    }


@router.get("/{reconciliation_id}/unmatched", response_model=List[dict])
def get_unmatched_transactions(
    reconciliation_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get unmatched transactions for manual review"""
    unmatched = db.query(models.BankTransactionMatch).filter(
        and_(
            models.BankTransactionMatch.reconciliation_id == reconciliation_id,
            models.BankTransactionMatch.ledger_entry_id.is_(None)
        )
    ).all()
    
    result = []
    for match in unmatched:
        result.append({
            "match_id": str(match.id),
            "bank_transaction_id": match.bank_transaction_id,
            "suggested_matches": find_suggested_matches(db, match.bank_transaction_id)
        })
    
    return result


@router.post("/{reconciliation_id}/match", response_model=dict)
def manual_match_transaction(
    reconciliation_id: uuid.UUID,
    match_id: uuid.UUID,
    ledger_entry_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Manually match a bank transaction with GL entry"""
    match = db.query(models.BankTransactionMatch).filter(
        models.BankTransactionMatch.id == match_id
    ).first()
    
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    match.ledger_entry_id = ledger_entry_id
    match.match_type = "manual"
    match.match_confidence = Decimal("100.00")
    match.matched_by = current_user.username
    match.matched_at = datetime.utcnow()
    
    db.commit()
    
    # Update reconciliation counts
    update_reconciliation_counts(db, reconciliation_id)
    
    return {"message": "Transaction matched successfully"}


@router.post("/{reconciliation_id}/approve", response_model=dict)
def approve_reconciliation(
    reconciliation_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Approve and lock reconciliation"""
    recon = db.query(models.BankReconciliation).filter(
        models.BankReconciliation.id == reconciliation_id
    ).first()
    
    if not recon:
        raise HTTPException(status_code=404, detail="Reconciliation not found")
    
    # Check if all transactions are matched or explained
    unmatched_count = db.query(models.BankTransactionMatch).filter(
        and_(
            models.BankTransactionMatch.reconciliation_id == reconciliation_id,
            models.BankTransactionMatch.ledger_entry_id.is_(None)
        )
    ).count()
    
    if unmatched_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve: {unmatched_count} unmatched transactions remain"
        )
    
    recon.status = models.ReconciliationStatus.APPROVED
    recon.approved_by = current_user.username
    recon.approved_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Reconciliation approved and locked",
        "reconciliation_id": str(reconciliation_id)
    }


@router.get("/{company_id}/list", response_model=List[dict])
def list_reconciliations(
    company_id: uuid.UUID,
    status: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List reconciliations for a company"""
    query = db.query(models.BankReconciliation).filter(
        models.BankReconciliation.company_id == company_id
    )
    
    if status:
        query = query.filter(models.BankReconciliation.status == status)
    
    recons = query.order_by(models.BankReconciliation.period_end.desc()).all()
    
    result = []
    for recon in recons:
        result.append({
            "id": str(recon.id),
            "account_id": str(recon.account_id),
            "period_start": recon.period_start.isoformat(),
            "period_end": recon.period_end.isoformat(),
            "statement_balance": float(recon.statement_balance),
            "variance": float(recon.variance),
            "status": recon.status.value,
            "matched_count": recon.matched_count,
            "unmatched_count": recon.unmatched_count
        })
    
    return result


# Helper functions

def calculate_book_balance(
    db: Session,
    account_id: uuid.UUID,
    period_start: date,
    period_end: date
) -> Decimal:
    """Calculate book balance from GL entries"""
    result = db.query(func.sum(models.FinancialLedgerEntry.amount_inr)).filter(
        and_(
            models.FinancialLedgerEntry.reference_id == str(account_id),
            models.FinancialLedgerEntry.transaction_date >= period_start,
            models.FinancialLedgerEntry.transaction_date <= period_end
        )
    ).scalar()
    
    return result or Decimal("0.00")


def auto_match_transactions(
    db: Session,
    reconciliation_id: uuid.UUID,
    account_id: uuid.UUID,
    period_start: date,
    period_end: date
):
    """Auto-match transactions using fuzzy logic"""
    # Get GL entries for period
    gl_entries = db.query(models.FinancialLedgerEntry).filter(
        and_(
            models.FinancialLedgerEntry.reference_id == str(account_id),
            models.FinancialLedgerEntry.transaction_date >= period_start,
            models.FinancialLedgerEntry.transaction_date <= period_end
        )
    ).all()
    
    # In production, you would get bank transactions from Plaid or statement import
    # For now, create placeholder matches for GL entries
    for entry in gl_entries:
        match = models.BankTransactionMatch(
            reconciliation_id=reconciliation_id,
            bank_transaction_id=str(entry.id),  # Placeholder
            ledger_entry_id=entry.id,
            match_confidence=Decimal("95.00"),
            match_type="exact",
            matched_by="system"
        )
        db.add(match)
    
    db.commit()
    update_reconciliation_counts(db, reconciliation_id)


def find_suggested_matches(db: Session, bank_transaction_id: str) -> List[dict]:
    """Find suggested GL entries for a bank transaction"""
    # In production, implement fuzzy matching logic
    # Match on amount, date range, description similarity
    # Return top 5 suggestions with confidence scores
    return []


def update_reconciliation_counts(db: Session, reconciliation_id: uuid.UUID):
    """Update matched/unmatched counts on reconciliation"""
    recon = db.query(models.BankReconciliation).filter(
        models.BankReconciliation.id == reconciliation_id
    ).first()
    
    if recon:
        recon.matched_count = db.query(models.BankTransactionMatch).filter(
            and_(
                models.BankTransactionMatch.reconciliation_id == reconciliation_id,
                models.BankTransactionMatch.ledger_entry_id.isnot(None)
            )
        ).count()
        
        recon.unmatched_count = db.query(models.BankTransactionMatch).filter(
            and_(
                models.BankTransactionMatch.reconciliation_id == reconciliation_id,
                models.BankTransactionMatch.ledger_entry_id.is_(None)
            )
        ).count()
        
        db.commit()
