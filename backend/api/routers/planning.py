from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from uuid import UUID

import models
import schemas
import database
import auth
from services import planning as planning_service

router = APIRouter(prefix="/planning", tags=["planning"])

@router.get("/budgets", response_model=List[schemas.Budget])
def get_budgets(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Budget).all()

@router.get("/budgets/{budget_id}/variance")
def get_budget_variance(budget_id: UUID, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    variance = planning_service.get_budget_variance(db, budget_id)
    if not variance:
        raise HTTPException(status_code=404, detail="Budget not found or no data available")
    return variance

@router.get("/forecasts", response_model=List[schemas.Forecast])
def get_forecasts(company_id: UUID, months: int = 6, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    forecasts = planning_service.calculate_forecast(db, company_id, months)
    return forecasts

@router.post("/forecasts/generate")
def generate_forecasts(company_id: UUID, months: int = 6, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Generates and saves forecasts to the database."""
    forecasts_data = planning_service.calculate_forecast(db, company_id, months)
    
    # Save to DB
    for f in forecasts_data:
        db_forecast = models.Forecast(
            company_id=company_id,
            forecast_date=f["forecast_date"],
            mrr_predicted=f["mrr_predicted"],
            cash_predicted=f["cash_predicted"],
            confidence_lower=f["confidence_lower"],
            confidence_upper=f["confidence_upper"]
        )
        db.add(db_forecast)
    
    db.commit()
    return {"status": "success", "count": len(forecasts_data)}
