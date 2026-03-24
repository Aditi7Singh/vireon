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


def _normalize_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _infer_category(description: str, merchant_name: str) -> str:
    text = f"{description or ''} {merchant_name or ''}".lower()
    if any(k in text for k in ["aws", "azure", "gcp", "cloud", "hosting"]):
        return "Cloud Infrastructure"
    if any(k in text for k in ["saas", "subscription", "zoom", "slack", "notion", "github", "figma"]):
        return "Software"
    if any(k in text for k in ["ads", "google ads", "meta ads", "linkedin", "marketing"]):
        return "Marketing"
    if any(k in text for k in ["flight", "hotel", "uber", "travel"]):
        return "Travel"
    if any(k in text for k in ["rent", "office", "cowork", "workspace"]):
        return "Office"
    return "General"


def _is_saas_like(description: str, merchant_name: str) -> bool:
    text = f"{description or ''} {merchant_name or ''}".lower()
    return any(k in text for k in ["saas", "subscription", "monthly", "annual", "license", "zoom", "slack", "github", "figma", "notion"])

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
    """Run local sync enrichment: categorization + SaaS flagging + duplicate detection."""
    feed = db.query(models.BankFeed).filter(models.BankFeed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Bank feed not found")

    txns = db.query(models.BankingTransaction).filter(models.BankingTransaction.feed_id == feed_id).order_by(
        models.BankingTransaction.transaction_date.desc()
    ).all()

    enriched_count = 0
    duplicate_candidates = []
    seen = {}

    for t in txns:
        original_category = t.category
        original_saas = bool(t.is_saas)

        if not t.category:
            t.category = _infer_category(t.description, t.merchant_name)
        if not t.is_saas:
            t.is_saas = _is_saas_like(t.description, t.merchant_name)

        if t.category != original_category or bool(t.is_saas) != original_saas:
            enriched_count += 1

        # Duplicate heuristic: same merchant/description + same amount + same date.
        key = (
            _normalize_text(t.merchant_name or t.description or "unknown"),
            float(t.amount or 0),
            t.transaction_date.isoformat() if t.transaction_date else "",
        )
        if key in seen:
            duplicate_candidates.append({
                "existing_transaction_id": str(seen[key]),
                "duplicate_transaction_id": str(t.id),
                "merchant_or_description": t.merchant_name or t.description,
                "amount": float(t.amount or 0),
                "transaction_date": t.transaction_date.isoformat() if t.transaction_date else None,
            })
        else:
            seen[key] = t.id

    feed.last_synced_at = datetime.utcnow()
    db.commit()
    return {
        "message": "Sync completed",
        "last_synced_at": feed.last_synced_at,
        "transactions_scanned": len(txns),
        "transactions_enriched": enriched_count,
        "duplicate_candidates_count": len(duplicate_candidates),
        "duplicate_candidates": duplicate_candidates[:20],
    }
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
