from __future__ import annotations
import logging
from datetime import datetime
from uuid import UUID

import models
from anomaly.celery_app import app as celery
from database import SessionLocal
from services.erpnext_service import ERPNextService
from services.merge_service import MergeService

logger = logging.getLogger(__name__)

@celery.task
def erpnext_sync_task(company_id_str: str, incremental: bool = True):
    db = SessionLocal()
    try:
        company_id = UUID(company_id_str)
        service = ERPNextService(db, company_id)
        # Use run_async if needed, but for celery simplicity here:
        import asyncio
        result = asyncio.run(service.sync_all(incremental=incremental))
        return result
    except Exception as e:
        logger.error(f"Scheduled ERPNext Sync Failed for {company_id_str}: {e}")
        return {"error": str(e)}
    finally:
        db.close()

@celery.task
def merge_sync_task(company_id_str: str):
    db = SessionLocal()
    try:
        company_id = UUID(company_id_str)
        service = MergeService(db, company_id)
        result = service.sync_all()
        return result
    except Exception as e:
        logger.error(f"Scheduled Merge Sync Failed for {company_id_str}: {e}")
        return {"error": str(e)}
    finally:
        db.close()

@celery.task
def trigger_all_company_syncs():
    """Daily task to trigger sync for all active companies."""
    db = SessionLocal()
    try:
        companies = db.query(models.Company.id).all()
        for (company_id,) in companies:
            erpnext_sync_task.delay(str(company_id))
            merge_sync_task.delay(str(company_id))
        return {"companies_triggered": len(companies)}
    finally:
        db.close()
