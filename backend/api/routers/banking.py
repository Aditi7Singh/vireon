from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
import schemas
import database
import auth
import models
from datetime import datetime

router = APIRouter(prefix="/banking", tags=["banking"])

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
