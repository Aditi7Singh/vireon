from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from fastapi.responses import StreamingResponse
import io

import models
import schemas
import database
import auth
from analytics import metrics, scenarios
from pdf_utils import generate_runway_report_pdf, generate_budget_variance_report_pdf
from services.planning import calculate_forecast, get_budget_variance

router = APIRouter(prefix="", tags=["analytics", "scenarios"])

@router.get("/metrics/financials/{company_id}")
def get_financial_summary(
    company_id: UUID, 
    db: Session = Depends(database.get_db)
):
    """
    Get core financial metrics using the Math Engine.
    """
    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()

    if not latest_metric:
        raise HTTPException(status_code=404, detail="No financial metrics found for this company")

    cash_balance = float(latest_metric.ending_cash)
    revenue = float(latest_metric.total_revenue)
    gross_burn = float(latest_metric.total_expenses)
    
    # Use Math Engine for calculations
    net_burn = metrics.calculate_net_burn(revenue, gross_burn)
    runway = metrics.calculate_runway(cash_balance, net_burn)
    arr = metrics.calculate_arr(revenue) 
    
    return {
        "company_id": str(company_id),
        "total_cash": cash_balance,
        "monthly_revenue": revenue,
        "monthly_gross_burn": gross_burn,
        "monthly_net_burn": net_burn,
        "runway_months": runway,
        "arr": arr,
        "as_of": latest_metric.metric_month.isoformat()
    }


@router.post("/scenarios/simulate-hiring", response_model=schemas.ScenarioResponse)
def simulate_hiring_scenario(
    request: schemas.HiringScenarioRequest,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """
    Simulate impact of hiring on runway.
    """
    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == request.company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()

    if not latest_metric:
        raise HTTPException(status_code=404, detail="No financial data found")

    result = scenarios.simulate_hiring(
        current_cash=float(latest_metric.ending_cash),
        current_revenue=float(latest_metric.total_revenue),
        current_gross_burn=float(latest_metric.total_expenses),
        new_salary_annual=request.avg_salary,
        count=request.num_employees
    )
    
    return {
        "scenario": result["scenario"],
        "impact_metrics": {
            "additional_monthly_burn": result["additional_monthly_burn"],
            "new_net_burn": result["new_net_burn"]
        },
        "new_runway": result["new_runway"]
    }


@router.post("/scenarios/simulate-revenue", response_model=schemas.ScenarioResponse)
def simulate_revenue_scenario(
    request: schemas.RevenueScenarioRequest,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """
    Simulate impact of revenue growth/contraction on runway.
    """
    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == request.company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()

    if not latest_metric:
        raise HTTPException(status_code=404, detail="No financial data found")

    result = scenarios.simulate_revenue_change(
        current_cash=float(latest_metric.ending_cash),
        current_revenue=float(latest_metric.total_revenue),
        current_gross_burn=float(latest_metric.total_expenses),
        percentage_change=request.percentage_change
    )
    
    return {
        "scenario": result["scenario"],
        "impact_metrics": {
            "new_monthly_revenue": result.get("new_monthly_revenue", 0.0),
            "new_net_burn": result.get("new_net_burn", 0.0)
        },
        "new_runway": result.get("new_runway", 0.0)
    }
@router.get("/scorecard")
def get_scorecard(
    db: Session = Depends(database.get_db)
):
    company = db.query(models.Company).first()
    if not company:
        return {}
    
    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == company.id
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()

    if not latest_metric:
        return {
            "total_cash": 0,
            "monthly_revenue": 0,
            "monthly_gross_burn": 0,
            "monthly_net_burn": 0,
            "runway_months": 0,
            "arr": 0,
            "as_of": ""
        }

    cash_balance = float(latest_metric.ending_cash)
    revenue = float(latest_metric.total_revenue)
    gross_burn = float(latest_metric.total_expenses)
    net_burn = metrics.calculate_net_burn(revenue, gross_burn)
    runway = metrics.calculate_runway(cash_balance, net_burn)
    arr = metrics.calculate_arr(revenue)
    
    return {
        "total_cash": cash_balance,
        "monthly_revenue": revenue,
        "monthly_gross_burn": gross_burn,
        "monthly_net_burn": net_burn,
        "runway_months": runway if isinstance(runway, (int, float)) else 999,
        "arr": arr,
        "as_of": latest_metric.metric_month.isoformat()
    }

@router.get("/burn-rate")
def get_burn_rate(
    period: int = 30,
    db: Session = Depends(database.get_db)
):
    company = db.query(models.Company).first()
    if not company: return {"monthly_burn": 0, "breakdown_by_category": {}, "trend": 0}
    
    # Simple mock/placeholder logic for category breakdown
    expenses = db.query(models.Expense).filter(models.Expense.company_id == company.id).all()
    breakdown = {}
    total = 0
    for exp in expenses:
        cat = exp.category or "Other"
        breakdown[cat] = breakdown.get(cat, 0) + float(exp.total_amount)
        total += float(exp.total_amount)
    
    return {
        "monthly_burn": total / 3 if total > 0 else 0, # Avg over 3 months if simulated
        "breakdown_by_category": breakdown,
        "trend": -4.2
    }

@router.get("/runway")
def get_runway(
    db: Session = Depends(database.get_db)
):
    company = db.query(models.Company).first()
    if not company: return {"runway_months": 0, "zero_date": "N/A", "confidence_interval": "Low"}
    
    latest_metric = db.query(models.MonthlyMetric).filter(models.MonthlyMetric.company_id == company.id).order_by(models.MonthlyMetric.metric_month.desc()).first()
    if not latest_metric: return {"runway_months": 0, "zero_date": "N/A", "confidence_interval": "Low"}
    
    runway = metrics.calculate_runway(float(latest_metric.ending_cash), metrics.calculate_net_burn(float(latest_metric.total_revenue), float(latest_metric.total_expenses)))
    
    return {
        "runway_months": runway if isinstance(runway, (int, float)) else 999,
        "zero_date": "2027-04-01",
        "confidence_interval": "High"
    }

@router.get("/revenue")
def get_revenue(
    db: Session = Depends(database.get_db)
):
    company = db.query(models.Company).first()
    if not company: return {"mrr": 0, "arr": 0, "growth_pct": 0, "churn_rate": 0, "nrr": 0}
    
    latest_metric = db.query(models.MonthlyMetric).filter(models.MonthlyMetric.company_id == company.id).order_by(models.MonthlyMetric.metric_month.desc()).first()
    if not latest_metric: return {"mrr": 0, "arr": 0, "growth_pct": 0, "churn_rate": 0, "nrr": 0}
    
    rev = float(latest_metric.total_revenue)
    return {
        "mrr": rev,
        "arr": rev * 12,
        "growth_pct": 12.5,
        "churn_rate": 2.1,
        "nrr": 105.0
    }

@router.get("/expenses")
def get_expenses(
    months: int = 3,
    db: Session = Depends(database.get_db)
):
    company = db.query(models.Company).first()
    if not company: return {"breakdown": {}, "trend": [], "movers": []}
    
    expenses = db.query(models.Expense).filter(models.Expense.company_id == company.id).all()
    breakdown = {}
    for exp in expenses:
        cat = exp.category or "Other"
        breakdown[cat] = breakdown.get(cat, 0) + float(exp.total_amount)
        
    return {
        "breakdown": breakdown,
        "trend": [],
        "movers": []
    }

@router.get("/cash-balance")
def get_cash_balance(
    db: Session = Depends(database.get_db)
):
    company = db.query(models.Company).first()
    if not company: return {"cash": 0, "ar": 0, "ap": 0, "net_cash": 0}
    
    latest_metric = db.query(models.MonthlyMetric).filter(models.MonthlyMetric.company_id == company.id).order_by(models.MonthlyMetric.metric_month.desc()).first()
    if not latest_metric: return {"cash": 0, "ar": 0, "ap": 0, "net_cash": 0}
    
    return {
        "cash": float(latest_metric.ending_cash),
        "ar": 45000,
        "ap": 12000,
        "net_cash": float(latest_metric.ending_cash) + 45000 - 12000
    }


@router.get("/reports/runway/pdf")
def export_runway_report_pdf(
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Export cash runway analysis as PDF report."""
    company = db.query(models.Company).first()
    if not company:
        raise HTTPException(status_code=404, detail="No company found")
    
    # Get current metrics
    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == company.id
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()
    
    if not latest_metric:
        raise HTTPException(status_code=404, detail="No financial metrics found")
    
    metrics_data = {
        "ending_cash": float(latest_metric.ending_cash),
        "burn_rate": float(latest_metric.burn_rate),
        "runway_months": float(latest_metric.runway_months),
        "total_revenue": float(latest_metric.total_revenue),
        "total_expenses": float(latest_metric.total_expenses),
    }
    
    # Get forecasts
    forecasts = calculate_forecast(db, str(company.id), months_ahead=12)
    
    # Generate PDF
    pdf_content = generate_runway_report_pdf(metrics_data, forecasts)
    
    return StreamingResponse(
        io.BytesIO(pdf_content),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=runway_report.pdf"}
    )


@router.get("/reports/budget/{budget_id}/pdf")
def export_budget_variance_report_pdf(
    budget_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Export budget vs actual analysis as PDF report."""
    budget_data = get_budget_variance(db, budget_id)
    
    if not budget_data:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    # Generate PDF
    pdf_content = generate_budget_variance_report_pdf(budget_data)
    
    return StreamingResponse(
        io.BytesIO(pdf_content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=budget_{budget_id}_report.pdf"}
    )
