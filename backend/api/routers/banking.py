from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
import schemas
import database
import auth
import models
from services.vendor_services import detect_saas_vendors, get_saas_benchmarks
from datetime import datetime

router = APIRouter(prefix="/banking", tags=["banking"])

@router.get("/saas-detected")
def get_saas_detection(company_id: UUID, db: Session = Depends(database.get_db)):
    """Detect SaaS vendors from banking transactions."""
    return detect_saas_vendors(db, company_id)

@router.get("/saas-benchmarks")
def get_benchmarks(stage: str = "seed"):
    """Get industry SaaS benchmarks for a given company stage."""
    return get_saas_benchmarks(stage)

@router.get("/feeds", response_model=List[schemas.BankFeed])
def get_bank_feeds(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Get all connected bank feeds for a company."""
    return db.query(models.BankFeed).filter(models.BankFeed.company_id == company_id).all()

@router.get("/transactions", response_model=List[schemas.BankingTransaction])
def get_banking_transactions(
    feed_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Get transactions for a specific bank feed."""
    return db.query(models.BankingTransaction).filter(models.BankingTransaction.feed_id == feed_id).order_by(models.BankingTransaction.transaction_date.desc()).all()

@router.post("/sync/{feed_id}")
def sync_bank_feed(
    feed_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Trigger a manual sync for a bank feed (Stub for Plaid)."""
    feed = db.query(models.BankFeed).filter(models.BankFeed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Bank feed not found")
    
    feed.last_synced_at = datetime.utcnow()
    db.commit()
    return {"message": "Sync triggered successfully", "last_synced_at": feed.last_synced_at}
@router.get("/consolidated-pl/{company_id}")
def get_consolidated_pl(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """
    Returns a consolidated P&L across all bank feeds, 
    aggregating by category and providing totals in INR.
    """
    from sqlalchemy import func
    
    # Simple aggregation of banking transactions by category
    # Note: Real P&L should also include Ledger entries, but this 
    # provides the "Banking-view" of P&L.
    results = db.query(
        models.BankingTransaction.category,
        func.sum(models.BankingTransaction.amount).label("total_amount")
    ).join(models.BankFeed).filter(
        models.BankFeed.company_id == company_id
    ).group_by(models.BankingTransaction.category).all()
    
    return [
        {
            "category": r.category,
            "amount_inr": float(r.total_amount),
            "source": "banking_aggregate"
        }
        for r in results
    ]
