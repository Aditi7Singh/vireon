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


class BudgetCreateRequest(BaseModel):
    company_id: UUID
    period: str
    budgets: Dict


class BudgetApprovalRequest(BaseModel):
    approver_id: UUID


class BudgetReallocateRequest(BaseModel):
    from_category: str
    to_category: str
    amount: float

@router.get("/budgets", response_model=List[schemas.Budget])
def get_budgets(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Budget).all()


@router.post("/budgets")
def create_budget(
    payload: BudgetCreateRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    budget = planning_service.create_budget(db, payload.company_id, payload.period, payload.budgets)
    return {
        "id": str(budget.id),
        "company_id": str(budget.company_id),
        "name": budget.name,
        "status": budget.status,
    }


@router.get("/budgets/{budget_id}")
def get_budget(
    budget_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    budget = db.query(models.Budget).filter(models.Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget


@router.put("/budgets/{budget_id}")
def update_budget(
    budget_id: UUID,
    payload: BudgetCreateRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    budget = db.query(models.Budget).filter(models.Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    existing_lines = db.query(models.BudgetLine).filter(models.BudgetLine.budget_id == budget.id).all()
    for line in existing_lines:
        db.delete(line)
    db.flush()
    for category, amount in payload.budgets.items():
        db.add(models.BudgetLine(budget_id=budget.id, category=str(category), monthly_amount=float(amount)))
    budget.name = f"Budget {payload.period}"
    budget.fiscal_year = int(payload.period.split("-")[0]) if "-" in payload.period else budget.fiscal_year
    db.commit()
    return {"success": True, "budget_id": str(budget.id)}


@router.delete("/budgets/{budget_id}")
def delete_budget(
    budget_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    budget = db.query(models.Budget).filter(models.Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    db.delete(budget)
    db.commit()
    return {"success": True, "budget_id": str(budget_id)}


@router.post("/budgets/{budget_id}/submit")
def submit_budget_for_approval(
    budget_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    result = planning_service.submit_for_approval(db, budget_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message", "Failed to submit budget"))
    return result


@router.post("/budgets/{budget_id}/approve")
def approve_budget(
    budget_id: UUID,
    payload: BudgetApprovalRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    result = planning_service.approve_budget(db, budget_id, payload.approver_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message", "Failed to approve budget"))
    return result


@router.get("/budgets/utilization/{company_id}")
def track_budget_utilization(
    company_id: UUID,
    period: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    result = planning_service.track_budget_utilization(db, company_id, period)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message", "No budget utilization data"))
    return result


@router.post("/budgets/{budget_id}/reallocate")
def reallocate_budget(
    budget_id: UUID,
    payload: BudgetReallocateRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    result = planning_service.reallocate_budget(
        db,
        budget_id,
        payload.from_category,
        payload.to_category,
        payload.amount,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Budget reallocation failed"))
    return result

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

