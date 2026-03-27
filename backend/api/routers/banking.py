from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
import schemas
import database
import auth
import models
from services.vendor_services import detect_saas_vendors, get_saas_benchmarks
from services import plaid_service
from decimal import Decimal
from datetime import date, datetime, timedelta
import uuid

from pydantic import BaseModel


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


class PlaidLinkTokenRequest(BaseModel):
    company_id: UUID
    user_id: Optional[str] = None


class PlaidPublicTokenRequest(BaseModel):
    public_token: str


class PlaidSyncRequest(BaseModel):
    company_id: UUID
    access_token: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None


@router.post("/plaid/link-token")
def create_plaid_link_token(
    payload: PlaidLinkTokenRequest,
    current_user: models.User = Depends(auth.get_current_user),
):
    try:
        result = plaid_service.create_link_token(str(payload.company_id), payload.user_id)
        return {
            "success": True,
            "link_token": result.get("link_token"),
            "expiration": result.get("expiration"),
            "request_id": result.get("request_id"),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Plaid link token creation failed: {exc}")


@router.post("/plaid/exchange-public-token")
def exchange_plaid_public_token(
    payload: PlaidPublicTokenRequest,
    current_user: models.User = Depends(auth.get_current_user),
):
    try:
        result = plaid_service.exchange_public_token(payload.public_token)
        return {
            "success": True,
            "access_token": result.get("access_token"),
            "item_id": result.get("item_id"),
            "request_id": result.get("request_id"),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Plaid token exchange failed: {exc}")


@router.post("/plaid/sync-transactions")
def sync_plaid_transactions(
    payload: PlaidSyncRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    try:
        accounts = plaid_service.get_accounts(payload.access_token)

        start = payload.start_date or (date.today() - timedelta(days=90))
        end = payload.end_date or date.today()
        transactions = plaid_service.get_transactions(payload.access_token, start, end)

        feed_by_account_id = {}
        for acc in accounts:
            account_id = acc.get("account_id")
            if not account_id:
                continue

            account_name = acc.get("name") or acc.get("official_name") or "Plaid Account"
            last4 = acc.get("mask") or ""
            subtype = (acc.get("subtype") or "checking")[:50]
            currency = acc.get("balances", {}).get("iso_currency_code") or "USD"

            feed = (
                db.query(models.BankFeed)
                .filter(
                    models.BankFeed.company_id == payload.company_id,
                    models.BankFeed.bank_name == "Plaid",
                    models.BankFeed.account_name == account_name,
                    models.BankFeed.account_number_last4 == (last4[-4:] if last4 else None),
                )
                .first()
            )
            if not feed:
                feed = models.BankFeed(
                    id=uuid.uuid4(),
                    company_id=payload.company_id,
                    bank_name="Plaid",
                    account_name=account_name,
                    account_type=subtype,
                    account_number_last4=(last4[-4:] if last4 else None),
                    currency=currency,
                    status="active",
                )
                db.add(feed)
                db.flush()

            feed_by_account_id[account_id] = feed

        inserted = 0
        skipped = 0
        for txn in transactions:
            account_id = txn.get("account_id")
            feed = feed_by_account_id.get(account_id)
            if not feed:
                skipped += 1
                continue

            # Basic duplicate prevention.
            txn_date = datetime.strptime(txn.get("date"), "%Y-%m-%d").date() if txn.get("date") else None
            description = txn.get("name") or txn.get("merchant_name") or "Plaid transaction"
            merchant = txn.get("merchant_name") or txn.get("name") or "unknown"
            amount = Decimal(str(txn.get("amount", 0)))

            existing = (
                db.query(models.BankingTransaction)
                .filter(
                    models.BankingTransaction.feed_id == feed.id,
                    models.BankingTransaction.transaction_date == txn_date,
                    models.BankingTransaction.description == description,
                    models.BankingTransaction.amount == amount,
                )
                .first()
            )
            if existing:
                skipped += 1
                continue

            db.add(
                models.BankingTransaction(
                    id=uuid.uuid4(),
                    feed_id=feed.id,
                    transaction_date=txn_date,
                    amount=amount,
                    description=description,
                    merchant_name=merchant,
                    category=_infer_category(description, merchant),
                    is_saas=_is_saas_like(description, merchant),
                )
            )
            inserted += 1

        for feed in feed_by_account_id.values():
            feed.last_synced_at = datetime.utcnow()

        db.commit()
        return {
            "success": True,
            "accounts_discovered": len(feed_by_account_id),
            "transactions_fetched": len(transactions),
            "transactions_inserted": inserted,
            "transactions_skipped": skipped,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Plaid sync failed: {exc}")

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
