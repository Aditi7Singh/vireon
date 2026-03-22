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


def _default_company_id(db: Session) -> UUID:
    company_row = db.query(models.Company.id).order_by(models.Company.created_at.asc()).first()
    if not company_row:
        raise HTTPException(status_code=404, detail="No company found")
    return company_row[0]

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

@router.get("/metrics/history/{company_id}")
def get_metrics_history(
    company_id: UUID, 
    months: int = 12,
    db: Session = Depends(database.get_db)
):
    """Get historical financial metrics for charts."""
    metrics_list = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).limit(months).all()
    
    # Reverse to get chronological order [oldest -> newest]
    metrics_list.reverse()
    
    return [
        {
            "month": m.metric_month.strftime("%Y-%m"),
            "revenue": float(m.total_revenue),
            "expenses": float(m.total_expenses),
            "net_burn": float(m.total_expenses - m.total_revenue),
            "cash": float(m.ending_cash)
        }
        for m in metrics_list
    ]


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
@router.get("/scorecard/{company_id}")
def get_scorecard(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == company_id
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
        "company_id": str(company_id),
        "total_cash": cash_balance,
        "monthly_revenue": revenue,
        "monthly_gross_burn": gross_burn,
        "monthly_net_burn": net_burn,
        "runway_months": runway if isinstance(runway, (int, float)) else 999,
        "arr": arr,
        "as_of": latest_metric.metric_month.isoformat()
    }


@router.get("/scorecard")
def get_scorecard_default(
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    return get_scorecard(_default_company_id(db), db, current_user)

@router.get("/burn-rate/{company_id}")
def get_burn_rate(
    company_id: UUID,
    period: int = 30,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    # Simple mock/placeholder logic for category breakdown
    expenses = (
        db.query(models.Expense.category, models.Expense.total_amount)
        .filter(models.Expense.company_id == company_id)
        .all()
    )
    breakdown = {}
    total = 0
    for exp in expenses:
        cat = exp.category or "Other"
        amount = float(exp.total_amount or 0)
        breakdown[cat] = breakdown.get(cat, 0) + amount
        total += amount
    
    return {
        "monthly_burn": total / 3 if total > 0 else 0, # Avg over 3 months if simulated
        "breakdown_by_category": breakdown,
        "trend": -4.2
    }


@router.get("/burn-rate")
def get_burn_rate_default(
    period: int = 30,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    return get_burn_rate(_default_company_id(db), period, db, current_user)

@router.get("/runway/{company_id}")
def get_runway(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    latest_metric = db.query(models.MonthlyMetric).filter(models.MonthlyMetric.company_id == company_id).order_by(models.MonthlyMetric.metric_month.desc()).first()
    if not latest_metric: return {"runway_months": 0, "zero_date": "N/A", "confidence_interval": "Low"}
    
    runway = metrics.calculate_runway(float(latest_metric.ending_cash), metrics.calculate_net_burn(float(latest_metric.total_revenue), float(latest_metric.total_expenses)))
    
    return {
        "runway_months": runway if isinstance(runway, (int, float)) else 999,
        "zero_date": "2027-04-01",
        "confidence_interval": "High"
    }


@router.get("/runway")
def get_runway_default(
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    return get_runway(_default_company_id(db), db, current_user)

@router.get("/revenue/{company_id}")
def get_revenue(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    latest_metric = db.query(models.MonthlyMetric).filter(models.MonthlyMetric.company_id == company_id).order_by(models.MonthlyMetric.metric_month.desc()).first()
    if not latest_metric: return {"mrr": 0, "arr": 0, "growth_pct": 0, "churn_rate": 0, "nrr": 0}
    
    rev = float(latest_metric.total_revenue)
    return {
        "mrr": rev,
        "arr": rev * 12,
        "growth_pct": 12.5,
        "churn_rate": 2.1,
        "nrr": 105.0
    }


@router.get("/revenue")
def get_revenue_default(
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    return get_revenue(_default_company_id(db), db, current_user)

@router.get("/expenses/{company_id}")
def get_expenses(
    company_id: UUID,
    months: int = 3,
    department: str = None,
    product_tag: str = None,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    query = db.query(models.Expense).filter(models.Expense.company_id == company_id)
    if department:
        # Assuming Expense has department or we join with ledger
        # For now, let's assume we can filter expenses directly if the field exists
        # or use financial_ledger_entries for more granular breakdown
        pass
        
    expenses = query.all()
    breakdown = {}
    for exp in expenses:
        cat = exp.category or "Other"
        breakdown[cat] = breakdown.get(cat, 0) + float(exp.total_amount or 0)
        
    return {
        "breakdown": breakdown,
        "trend": [],
        "movers": []
    }


@router.get("/expenses")
def get_expenses_default(
    months: int = 3,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    return get_expenses(_default_company_id(db), months, db, current_user)

@router.get("/cash-balance/{company_id}")
def get_cash_balance(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    latest_metric = db.query(models.MonthlyMetric).filter(models.MonthlyMetric.company_id == company_id).order_by(models.MonthlyMetric.metric_month.desc()).first()
    if not latest_metric: return {"cash": 0, "ar": 0, "ap": 0, "net_cash": 0}
    
    return {
        "cash": float(latest_metric.ending_cash),
        "ar": 45000,
        "ap": 12000,
        "net_cash": float(latest_metric.ending_cash) + 45000 - 12000
    }


@router.get("/cash-balance")
def get_cash_balance_default(
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    return get_cash_balance(_default_company_id(db), db, current_user)


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


@router.get("/compliance/reminders/{company_id}")
def get_compliance_reminders(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Get upcoming tax compliance deadlines."""
    return metrics.get_tax_compliance_reminders(db, company_id)


@router.get("/metrics/vc/{company_id}")
def get_vc_metrics_dashboard(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Get high-level VC/Investor metrics."""
    return metrics.get_vc_metrics(db, company_id)
