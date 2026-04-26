from __future__ import annotations

from datetime import datetime

import models
from anomaly.celery_app import app as celery
from database import SessionLocal
from services.fx_service import run_revaluation


@celery.task
def run_monthly_fx_revaluation_all_companies():
    db = SessionLocal()
    try:
        month = datetime.utcnow().strftime("%Y-%m")
        companies = db.query(models.Company.id).all()
        created = 0
        for (company_id,) in companies:
            result = run_revaluation(db, company_id, month)
            created += int(result.get("snapshots_created", 0))
        return {"month": month, "companies": len(companies), "snapshots_created": created}
    finally:
        db.close()
