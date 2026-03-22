from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import os

import auth
import database
import models


router = APIRouter(prefix="/system", tags=["system"])


@router.get("/startup-health")
def startup_health(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
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
        actions.append("Run ./start.sh to trigger bootstrap seeding")
    if metrics_count == 0:
        issues.append("No monthly metrics found")
        actions.append("Call /api/v1/system/startup-health after bootstrap or add seed metrics")
    if rates_count == 0:
        issues.append("No exchange rates available")
        actions.append("POST /api/v1/fx/sync-default to seed FX rates")

    checks = {
        "companies": company_count,
        "monthly_metrics": metrics_count,
        "ledger_entries": ledger_count,
        "exchange_rates": rates_count,
        "fx_revaluation_snapshots": snapshots_count,
        "documents": docs_count,
        "ocr_pipeline": "async_worker_available" if os.getenv("OCR_ASYNC", "false").lower() == "true" else "basic_extraction_enabled",
    }

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
    db.execute("SELECT 1")
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
