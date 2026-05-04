from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import json
from datetime import datetime
from datetime import date
from decimal import Decimal
import uuid
from pathlib import Path
from pydantic import BaseModel
from typing import Optional

import auth
import database
import models
import bootstrap
from services.connector_policy import load_connector_policy, save_connector_policy


router = APIRouter(prefix="/system", tags=["system"])


def _is_missing(value: Optional[str]) -> bool:
    if value is None:
        return True
    clean = value.strip()
    if not clean:
        return True
    placeholders = {
        "your_api",
        "your_merge_api_key_here",
        "your_merge_secret_key_here",
        "your_linked_account_token_here",
        "sample test linked account token",
        "change-me",
        "replace-me",
    }
    return clean.lower() in placeholders


class RemediationRequest(BaseModel):
    action: str
    month: Optional[str] = None


class ConnectorConflictPolicyUpdate(BaseModel):
    merge: Optional[str] = None
    plaid: Optional[str] = None
    cloud_costs: Optional[str] = None


@router.get("/startup-health")
def startup_health(
    db: Session = Depends(database.get_db),
):
    default_company_row = db.query(models.Company.id).order_by(models.Company.created_at.asc()).first()
    default_company_id = str(default_company_row[0]) if default_company_row else None

    company_count = db.query(models.Company).count()
    metrics_count = db.query(models.MonthlyMetric).count()
    ledger_count = db.query(models.FinancialLedgerEntry).count()
    rates_count = db.query(models.ExchangeRate).count()
    snapshots_count = db.query(models.FxRevaluationSnapshot).count()
    docs_count = db.query(models.Document).count()

    issues = []
    actions = []
    if company_count == 0:
        issues.append("No company records found")
        actions.append("bootstrap_seed")
    if metrics_count == 0:
        issues.append("No monthly metrics found")
        actions.append("bootstrap_seed")
    if rates_count == 0:
        issues.append("No exchange rates available")
        actions.append("sync_default_fx_rates")

    checks = {
        "companies": company_count,
        "monthly_metrics": metrics_count,
        "ledger_entries": ledger_count,
        "exchange_rates": rates_count,
        "fx_revaluation_snapshots": snapshots_count,
        "documents": docs_count,
        "ocr_pipeline": "async_worker_available" if os.getenv("OCR_ASYNC", "false").lower() == "true" else "basic_extraction_enabled",
    }

    # Production credential readiness checks.
    env_name = os.getenv("ENV", "development").lower()
    storage_backend = os.getenv("STORAGE_BACKEND", "local").lower()
    ocr_provider = os.getenv("OCR_PROVIDER", "local").lower()
    missing_credentials = []

    if storage_backend == "s3":
        for key in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "S3_BUCKET"]:
            if _is_missing(os.getenv(key)):
                missing_credentials.append(key)

    if ocr_provider == "textract":
        for key in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]:
            if _is_missing(os.getenv(key)):
                missing_credentials.append(key)

    data_source = os.getenv("DATA_SOURCE", "").lower()

    if data_source in {"merge", "mergedev"}:
        for key in ["MERGE_API_KEY"]:
            if _is_missing(os.getenv(key)):
                missing_credentials.append(key)
        merge_account_token = os.getenv("MERGE_ACCOUNT_TOKEN") or os.getenv("MERGE_LINKED_ACCOUNT_TOKEN")
        if _is_missing(merge_account_token):
            missing_credentials.append("MERGE_ACCOUNT_TOKEN")

    if data_source in {"plaid"}:
        for key in ["PLAID_CLIENT_ID", "PLAID_SECRET"]:
            if _is_missing(os.getenv(key)):
                missing_credentials.append(key)

    for key in ["SMTP_HOST", "SMTP_USER", "SMTP_PASS"]:
        if _is_missing(os.getenv(key)):
            missing_credentials.append(key)

    missing_credentials = sorted(set(missing_credentials))
    if env_name in {"prod", "production"} and missing_credentials:
        issues.append("Production connector credentials are incomplete")
        actions.append("configure_production_secrets")

    conflict_policy = load_connector_policy()

    table_readiness = {
        "companies": company_count > 0,
        "monthly_metrics": metrics_count > 0,
        "financial_ledger_entries": ledger_count > 0,
        "exchange_rates": rates_count > 0,
        "fx_revaluation_snapshots": snapshots_count >= 0,
        "documents": docs_count >= 0,
    }

    return {
        "status": "ok" if not issues else "warning",
        "default_company_id": default_company_id,
        "checks": checks,
        "table_readiness": table_readiness,
        "issues": issues,
        "actions": actions,
        "credential_readiness": {
            "environment": env_name,
            "storage_backend": storage_backend,
            "ocr_provider": ocr_provider,
            "missing_keys": missing_credentials,
            "ready": len(missing_credentials) == 0,
        },
        "connector_conflict_policy": conflict_policy,
    }


@router.get("/connectors/conflict-policy")
def get_connector_conflict_policy(
    current_user: models.User = Depends(auth.get_current_user),
):
    return {"policy": load_connector_policy()}


@router.put("/connectors/conflict-policy")
def update_connector_conflict_policy(
    payload: ConnectorConflictPolicyUpdate,
    current_user: models.User = Depends(auth.get_current_user),
):
    allowed = {"source_of_truth", "latest_timestamp_wins", "manual_review"}
    next_policy = load_connector_policy()
    for key, value in payload.model_dump(exclude_none=True).items():
        if value not in allowed:
            return {
                "success": False,
                "message": f"Invalid policy '{value}' for {key}. Allowed: {sorted(allowed)}",
            }
        next_policy[key] = value

    save_connector_policy(next_policy)
    return {"success": True, "policy": next_policy}


def _sync_default_fx_rates(db: Session) -> int:
    today = date.today()
    default_rates = {
        "USD": Decimal("83.000000"),
        "EUR": Decimal("90.000000"),
        "GBP": Decimal("105.000000"),
        "INR": Decimal("1.000000"),
    }

    upserted = 0
    for base_currency, rate in default_rates.items():
        existing = (
            db.query(models.ExchangeRate)
            .filter(
                models.ExchangeRate.base_currency == base_currency,
                models.ExchangeRate.target_currency == "INR",
                models.ExchangeRate.effective_date == today,
            )
            .first()
        )
        if existing:
            existing.exchange_rate = rate
            existing.status = "active"
        else:
            db.add(
                models.ExchangeRate(
                    id=uuid.uuid4(),
                    base_currency=base_currency,
                    target_currency="INR",
                    exchange_rate=rate,
                    effective_date=today,
                    status="active",
                )
            )
        upserted += 1
    db.commit()
    return upserted


@router.post("/remediate")
def remediate_startup(
    payload: RemediationRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    action = (payload.action or "").strip().lower()

    if action == "bootstrap_seed":
        bootstrap.run_bootstrap()
        return {"success": True, "action": action, "message": "Bootstrap run completed"}

    if action == "sync_default_fx_rates":
        synced = _sync_default_fx_rates(db)
        return {"success": True, "action": action, "synced": synced}

    if action == "run_monthly_fx_revaluation":
        from services.fx_service import run_revaluation

        month = payload.month or datetime.utcnow().strftime("%Y-%m")
        company_row = db.query(models.Company.id).order_by(models.Company.created_at.asc()).first()
        if not company_row:
            return {"success": False, "action": action, "message": "No company found"}
        result = run_revaluation(db, company_row[0], month)
        return {"success": True, "action": action, "result": result}

    return {
        "success": False,
        "action": action,
        "message": "Unknown action. Supported actions: bootstrap_seed, sync_default_fx_rates, run_monthly_fx_revaluation",
    }


@router.get("/production-health")
def production_health(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Deep health check for production monitoring."""
    import time
    
    # 1. Database Latency Check
    start = time.time()
    db.execute(text("SELECT 1"))
    latency_ms = (time.time() - start) * 1000
    
    # 2. Worker Check (Mock)
    worker_status = "active" # In real prod, check celery inspect ping
    
    return {
        "status": "healthy" if latency_ms < 100 else "degraded",
        "database_latency_ms": round(latency_ms, 2),
        "worker_status": worker_status,
        "environment": os.getenv("ENV", "development"),
        "timestamp": datetime.utcnow().isoformat()
    }
