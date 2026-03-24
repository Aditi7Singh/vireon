from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from uuid import UUID
from pydantic import BaseModel

import models
import schemas
import database
import auth
from services import planning as planning_service

router = APIRouter(prefix="/planning", tags=["planning"])


class ScenarioSaveRequest(BaseModel):
    name: str
    scenario_type: str
    input_data: Dict
    result_data: Dict

@router.get("/budgets", response_model=List[schemas.Budget])
def get_budgets(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Budget).all()

@router.get("/budgets/{budget_id}/variance")
def get_budget_variance(
    budget_id: UUID, 
    department: str = None, 
    month: str = None, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    from datetime import datetime
    target_date = None
    if month:
        try:
            target_date = datetime.strptime(month, "%Y-%m").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")
            
    variance = planning_service.get_budget_variance(db, budget_id, target_month=target_date, department=department)
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


@router.get("/budgets/{budget_id}/variance/department")
def get_department_variance(budget_id: UUID, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Department-level budget variance analysis using GL entries."""
    result = planning_service.get_department_variance(db, budget_id)
    if not result:
        raise HTTPException(status_code=404, detail="Budget not found or no data")
    return result


@router.get("/budgets/{budget_id}/variance/flex")
def get_flex_budget_variance(budget_id: UUID, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Flex-budget variance: variable categories scaled by actual revenue ratio."""
    result = planning_service.get_flex_budget_variance(db, budget_id)
    if not result:
        raise HTTPException(status_code=404, detail="Budget not found or no data")
    return result


@router.get("/budgets/{budget_id}/alerts")
def get_budget_alerts(budget_id: UUID, threshold: float = 10.0, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Check which budget categories exceed the given threshold percentage."""
    return planning_service.check_budget_alerts(db, budget_id, threshold)


@router.post("/scenarios/save")
def save_scenario(
    payload: ScenarioSaveRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Save a scenario simulation for later comparison."""
    company = db.query(models.Company).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    snapshot = models.ScenarioSnapshot(
        company_id=company.id,
        name=payload.name,
        scenario_type=payload.scenario_type,
        input_data=payload.input_data,
        result_data=payload.result_data
    )
    db.add(snapshot)
    db.commit()
    return {"status": "success", "id": str(snapshot.id)}


@router.get("/scenarios/history")
def get_scenario_history(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Retrieve saved scenario simulations."""
    company = db.query(models.Company).first()
    if not company:
        return []
    
    return db.query(models.ScenarioSnapshot).filter(
        models.ScenarioSnapshot.company_id == company.id
    ).order_by(models.ScenarioSnapshot.created_at.desc()).all()

