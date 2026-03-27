from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import database
import schemas
from services.forecasting_service import (
    calculate_dynamic_runway,
    calculate_hiring_impact,
    prepare_monthly_timeseries,
    fit_sarima_model,
    save_forecast_to_db,
    calculate_ensemble_runway,
    monitor_forecast_accuracy,
)

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("/runway/{company_id}")
def get_runway(company_id: UUID, db: Session = Depends(database.get_db)):
    return calculate_dynamic_runway(company_id, db)


@router.post("/hiring-impact")
def get_hiring_impact(payload: schemas.HiringImpactRequest, db: Session = Depends(database.get_db)):
    return calculate_hiring_impact(
        payload.company_id, 
        db, 
        payload.annual_ctc_inr, 
        payload.join_month,
        equipment_cost=payload.equipment_cost,
        onboarding_cost=payload.onboarding_cost,
        benefits_multiplier=payload.benefits_multiplier
    )


@router.get("/product/{company_id}/{product_tag}")
def product_runway(company_id: UUID, product_tag: str, db: Session = Depends(database.get_db)):
    burn_df = prepare_monthly_timeseries(company_id, db, entry_type="debit", product_tag=product_tag)
    revenue_df = prepare_monthly_timeseries(company_id, db, entry_type="credit", product_tag=product_tag)
    return {
        "company_id": str(company_id),
        "product_tag": product_tag,
        "burn_forecast": fit_sarima_model(burn_df)["forecast_df"].to_dict(orient="records"),
        "revenue_forecast": fit_sarima_model(revenue_df)["forecast_df"].to_dict(orient="records"),
    }


@router.post("/refresh/{company_id}")
def refresh_forecast(company_id: UUID, db: Session = Depends(database.get_db)):
    forecast = calculate_dynamic_runway(company_id, db)
    save_forecast_to_db(company_id, forecast, db)
    return {"success": True, "message": "Forecast refreshed", "company_id": str(company_id)}


@router.get("/ensemble/{company_id}")
def ensemble_runway(company_id: UUID, db: Session = Depends(database.get_db)):
    return calculate_ensemble_runway(company_id, db)


@router.get("/monitor/{company_id}")
def forecast_monitor(company_id: UUID, lookback_months: int = 6, db: Session = Depends(database.get_db)):
    return monitor_forecast_accuracy(company_id, db, lookback_months=lookback_months)


@router.post("/retrain/{company_id}")
def retrain_forecast(company_id: UUID, db: Session = Depends(database.get_db)):
    forecast = calculate_ensemble_runway(company_id, db)
    save_forecast_to_db(company_id, forecast, db)
    monitor = monitor_forecast_accuracy(company_id, db, lookback_months=6)
    return {
        "success": True,
        "company_id": str(company_id),
        "message": "Ensemble forecast retrained and persisted",
        "monitoring": monitor,
    }
