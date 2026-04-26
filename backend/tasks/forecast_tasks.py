from __future__ import annotations

from database import SessionLocal
import models
from anomaly.celery_app import app as celery
from services.forecasting_service import calculate_ensemble_runway, save_forecast_to_db


@celery.task
def retrain_forecasts_all_companies():
    db = SessionLocal()
    try:
        companies = db.query(models.Company).all()
        retrained = 0
        for company in companies:
            forecast = calculate_ensemble_runway(company.id, db)
            save_forecast_to_db(company.id, forecast, db)
            retrained += 1
        return {"companies": len(companies), "retrained": retrained}
    finally:
        db.close()
