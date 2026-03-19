from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import date, timedelta
import models
import numpy as np
from sqlalchemy import func, extract

def calculate_forecast(db: Session, company_id: Any, months_ahead: int = 6) -> List[Dict[str, Any]]:
    """Generates an improved forecast using exponential smoothing for MRR and Cash."""
    metrics = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == company_id
    ).order_by(models.MonthlyMetric.metric_month.asc()).all()
    
    if len(metrics) < 3:
        return [] # Not enough data for a meaningful forecast
    
    # Use exponential smoothing for revenue forecasting
    revenues = [float(m.total_revenue) for m in metrics]
    alpha = 0.3  # Smoothing factor
    
    # Calculate smoothed values
    smoothed = [revenues[0]]
    for i in range(1, len(revenues)):
        smoothed.append(alpha * revenues[i] + (1 - alpha) * smoothed[-1])
    
    # Forecast using trend from smoothed data
    if len(smoothed) >= 2:
        trend = smoothed[-1] - smoothed[-2]
    else:
        trend = 0
    
    forecasts = []
    last_date = metrics[-1].metric_month
    last_cash = float(metrics[-1].ending_cash)
    last_burn = float(metrics[-1].burn_rate)
    
    current_revenue = smoothed[-1]
    
    for i in range(1, months_ahead + 1):
        next_date = last_date + timedelta(days=30 * i)
        pred_revenue = current_revenue + trend * i
        
        # Improved cash projection: account for revenue growth
        revenue_growth = (pred_revenue - float(metrics[-1].total_revenue)) / max(1, float(metrics[-1].total_revenue))
        adjusted_burn = last_burn * (1 - revenue_growth * 0.5)  # Assume some burn reduction with growth
        pred_cash = last_cash - (adjusted_burn * i) + (pred_revenue - float(metrics[-1].total_revenue)) * i
        
        forecasts.append({
            "forecast_date": next_date,
            "mrr_predicted": max(0, pred_revenue),
            "cash_predicted": max(0, pred_cash),
            "confidence_lower": max(0, pred_cash * 0.8),
            "confidence_upper": pred_cash * 1.2
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
    
    # Get actual expenses by category for the month
    month_start = latest_metric.metric_month.replace(day=1)
    next_month = month_start.replace(month=month_start.month % 12 + 1, year=month_start.year + (month_start.month // 12))
    month_end = next_month - timedelta(days=1)
    
    actual_expenses = db.query(
        models.Expense.category,
        func.sum(models.Expense.total_amount).label('total')
    ).filter(
        models.Expense.company_id == budget.company_id,
        models.Expense.transaction_date >= month_start,
        models.Expense.transaction_date <= month_end
    ).group_by(models.Expense.category).all()
    
    # Convert to dict
    actual_by_category = {row.category: float(row.total) for row in actual_expenses}
    
    variances = []
    for line in budget.lines:
        actual = actual_by_category.get(line.category, 0.0)
        budget_amount = float(line.monthly_amount)
        variance = actual - budget_amount
        variances.append({
            "category": line.category,
            "budget": budget_amount,
            "actual": actual,
            "variance": variance,
            "variance_pct": (variance / budget_amount) * 100 if budget_amount else 0
        })
        
    return {
        "budget_name": budget.name,
        "month": latest_metric.metric_month,
        "variances": variances
    }
