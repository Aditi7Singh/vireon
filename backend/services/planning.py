from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import date, timedelta
import models
import numpy as np

def calculate_forecast(db: Session, company_id: Any, months_ahead: int = 6) -> List[Dict[str, Any]]:
    """Generates a linear regression based forecast for MRR and Cash."""
    metrics = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == company_id
    ).order_by(models.MonthlyMetric.metric_month.asc()).all()
    
    if len(metrics) < 3:
        return [] # Not enough data for a meaningful forecast
    
    # Simple linear trend for MRR
    revenues = [float(m.total_revenue) for m in metrics]
    x = np.arange(len(revenues))
    slope, intercept = np.polyfit(x, revenues, 1)
    
    forecasts = []
    last_date = metrics[-1].metric_month
    last_cash = float(metrics[-1].ending_cash)
    last_burn = float(metrics[-1].burn_rate)
    
    for i in range(1, months_ahead + 1):
        next_date = last_date + timedelta(days=30 * i)
        pred_revenue = intercept + slope * (len(revenues) + i - 1)
        
        # Simple cash projection: previous cash - current burn + (predicted revenue - current revenue)
        # In a real model, we'd predict expenses too
        pred_cash = last_cash - (last_burn * i)
        
        forecasts.append({
            "forecast_date": next_date,
            "mrr_predicted": max(0, pred_revenue),
            "cash_predicted": max(0, pred_cash),
            "confidence_lower": max(0, pred_cash * 0.9),
            "confidence_upper": pred_cash * 1.1
        })
    
    return forecasts

def get_budget_variance(db: Session, budget_id: Any) -> Dict[str, Any]:
    """Calculates budget vs actual variance for the current month."""
    budget = db.query(models.Budget).filter(models.Budget.id == budget_id).first()
    if not budget:
        return {}
    
    # Get actuals for the latest month
    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == budget.company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()
    
    if not latest_metric:
        return {}
    
    variances = []
    for line in budget.lines:
        # In a real app we'd map categories to GL accounts
        # Here we just use a mock comparison
        actual = float(latest_metric.total_expenses) / len(budget.lines) # Mock distribution
        variance = actual - float(line.monthly_amount)
        variances.append({
            "category": line.category,
            "budget": float(line.monthly_amount),
            "actual": actual,
            "variance": variance,
            "variance_pct": (variance / float(line.monthly_amount)) * 100 if line.monthly_amount else 0
        })
        
    return {
        "budget_name": budget.name,
        "month": latest_metric.metric_month,
        "variances": variances
    }
