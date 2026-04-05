from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import date, timedelta
from uuid import UUID
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

def get_budget_variance(db: Session, budget_id: Any, target_month: date = None, department: str = None) -> Dict[str, Any]:
    """
    Calculates budget vs actual variance. 
    Prioritizes GeneralLedger for actuals if available, otherwise falls back to Expense model.
    """
    budget = db.query(models.Budget).filter(models.Budget.id == budget_id).first()
    if not budget:
        return {}
    
    # Determine target month (default to latest metric month)
    if not target_month:
        latest_metric = db.query(models.MonthlyMetric).filter(
            models.MonthlyMetric.company_id == budget.company_id
        ).order_by(models.MonthlyMetric.metric_month.desc()).first()
        if not latest_metric:
            return {}
        target_month = latest_metric.metric_month
    
    month_start = target_month.replace(day=1)
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)
    
    # 1. Get Actuals from GeneralLedger (more accurate)
    gl_query = db.query(
        models.GeneralLedger.account_name,
        models.GeneralLedger.department,
        func.sum(models.GeneralLedger.debit_amount - models.GeneralLedger.credit_amount).label("net_amount")
    ).filter(
        models.GeneralLedger.company_id == budget.company_id,
        models.GeneralLedger.transaction_date >= month_start,
        models.GeneralLedger.transaction_date < next_month
    )
    
    if department:
        gl_query = gl_query.filter(models.GeneralLedger.department == department)
        
    gl_actuals = gl_query.group_by(models.GeneralLedger.account_name, models.GeneralLedger.department).all()
    
    # Map GL entries to budget categories (Heuristic mapping)
    actual_by_category = {}
    for row in gl_actuals:
        # Simplification: Use department/account name to map to budget categories
        # In a real app, this would use a mapping table
        cat = str(row.department.value if hasattr(row.department, 'value') else row.department).lower()
        actual_by_category[cat] = actual_by_category.get(cat, 0.0) + float(row.net_amount or 0)

    # 2. Fallback to Expense model if GL is empty
    if not actual_by_category:
        exp_query = db.query(
            models.Expense.category,
            func.sum(models.Expense.total_amount).label('total')
        ).filter(
            models.Expense.company_id == budget.company_id,
            models.Expense.transaction_date >= month_start,
            models.Expense.transaction_date < next_month
        )
        if department:
            exp_query = exp_query.filter(models.Expense.department == department)
            
        expense_actuals = exp_query.group_by(models.Expense.category).all()
        actual_by_category = {row.category: float(row.total) for row in expense_actuals}

    variances = []
    processed_categories = set()
    
    # Compare Budgeted Lines
    for line in budget.lines:
        processed_categories.add(line.category)
        actual = actual_by_category.get(line.category, 0.0)
        budget_amount = float(line.monthly_amount)
        variance = actual - budget_amount
        variances.append({
            "category": line.category,
            "budget": budget_amount,
            "actual": actual,
            "variance": variance,
            "variance_pct": (variance / budget_amount) * 100 if budget_amount else 0,
            "is_zero_based": False
        })
        
    # Handle Zero-Based Budgeting: Actuals and categories NOT in the budget
    for category, actual in actual_by_category.items():
        if category not in processed_categories and actual != 0:
            variances.append({
                "category": category,
                "budget": 0.0,
                "actual": actual,
                "variance": actual,
                "variance_pct": 100.0, # 100% variance if budget was 0
                "is_zero_based": True
            })
            
    return {
        "budget_name": budget.name,
        "month": target_month,
        "department_filter": department,
        "variances": sorted(variances, key=lambda x: abs(x["variance"]), reverse=True)
    }


def get_department_variance(db: Session, budget_id: Any, target_month: date = None) -> Dict[str, Any]:
    """
    Department-level variance analysis using GeneralLedger entries.
    
    Groups actuals by department enum and compares to budget allocations.
    """
    budget = db.query(models.Budget).filter(models.Budget.id == budget_id).first()
    if not budget:
        return {}

    # Determine month
    if not target_month:
        latest_metric = db.query(models.MonthlyMetric).filter(
            models.MonthlyMetric.company_id == budget.company_id
        ).order_by(models.MonthlyMetric.metric_month.desc()).first()
        if not latest_metric:
            return {}
        target_month = latest_metric.metric_month

    month_start = target_month.replace(day=1)
    next_month = month_start.replace(month=month_start.month % 12 + 1,
                                     year=month_start.year + (month_start.month // 12))

    # GL department breakdown
    dept_actuals = db.query(
        models.GeneralLedger.department,
        func.sum(models.GeneralLedger.debit_amount).label("total_debit"),
        func.sum(models.GeneralLedger.credit_amount).label("total_credit"),
    ).filter(
        models.GeneralLedger.company_id == budget.company_id,
        models.GeneralLedger.transaction_date >= month_start,
        models.GeneralLedger.transaction_date < next_month,
        models.GeneralLedger.department.isnot(None),
    ).group_by(models.GeneralLedger.department).all()

    dept_map = {}
    for row in dept_actuals:
        dept_name = row.department.value if hasattr(row.department, "value") else str(row.department)
        dept_map[dept_name] = float(row.total_debit or 0) - float(row.total_credit or 0)

    # Map budget lines to departments (approximate: match category → department)
    category_to_dept = {
        "payroll": "people", "hiring": "people",
        "tech_cost": "engineering", "marketing": "marketing",
        "office_expense": "operations", "misc": "finance",
    }
    dept_budgets = {}
    for line in budget.lines:
        dept = category_to_dept.get(line.category, "operations")
        dept_budgets[dept] = dept_budgets.get(dept, 0) + float(line.monthly_amount)

    # Build variance for each department
    all_depts = set(list(dept_map.keys()) + list(dept_budgets.keys()))
    variances = []
    for dept in sorted(all_depts):
        actual = dept_map.get(dept, 0.0)
        budgeted = dept_budgets.get(dept, 0.0)
        variance = actual - budgeted
        variances.append({
            "department": dept,
            "budget": budgeted,
            "actual": actual,
            "variance": round(variance, 2),
            "variance_pct": round((variance / budgeted) * 100, 2) if budgeted else 0,
        })

    return {
        "budget_name": budget.name,
        "month": target_month,
        "department_variances": variances,
        "total_budget": sum(v["budget"] for v in variances),
        "total_actual": sum(v["actual"] for v in variances),
    }


def get_flex_budget_variance(db: Session, budget_id: Any) -> Dict[str, Any]:
    """
    Flex-budget variance: scales revenue-dependent budget lines by actual revenue ratio.
    
    Revenue-dependent categories: marketing, hiring, misc
    Fixed categories: payroll, tech_cost, office_expense
    """
    budget = db.query(models.Budget).filter(models.Budget.id == budget_id).first()
    if not budget:
        return {}

    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == budget.company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()
    if not latest_metric:
        return {}

    # Calculate revenue ratio
    budgeted_revenue = sum(float(l.monthly_amount) for l in budget.lines
                          if l.category in ("revenue",))
    actual_revenue = float(latest_metric.total_revenue or 0)
    revenue_ratio = (actual_revenue / budgeted_revenue) if budgeted_revenue > 0 else 1.0

    # Categories that scale with revenue
    variable_categories = {"marketing", "hiring", "misc"}

    month_start = latest_metric.metric_month.replace(day=1)
    next_month = month_start.replace(month=month_start.month % 12 + 1,
                                     year=month_start.year + (month_start.month // 12))

    actual_expenses = db.query(
        models.Expense.category,
        func.sum(models.Expense.total_amount).label("total")
    ).filter(
        models.Expense.company_id == budget.company_id,
        models.Expense.transaction_date >= month_start,
        models.Expense.transaction_date < next_month,
    ).group_by(models.Expense.category).all()
    actual_by_cat = {row.category: float(row.total) for row in actual_expenses}

    variances = []
    for line in budget.lines:
        original_budget = float(line.monthly_amount)
        if line.category in variable_categories:
            flex_budget = original_budget * revenue_ratio
        else:
            flex_budget = original_budget

        actual = actual_by_cat.get(line.category, 0.0)
        variance = actual - flex_budget

        variances.append({
            "category": line.category,
            "original_budget": original_budget,
            "flex_budget": round(flex_budget, 2),
            "actual": actual,
            "variance": round(variance, 2),
            "variance_pct": round((variance / flex_budget) * 100, 2) if flex_budget else 0,
            "is_variable": line.category in variable_categories,
        })

    return {
        "budget_name": budget.name,
        "month": latest_metric.metric_month,
        "revenue_ratio": round(revenue_ratio, 4),
        "flex_variances": variances,
    }


def check_budget_alerts(db: Session, budget_id: Any, threshold_pct: float = 10.0) -> List[Dict[str, Any]]:
    """
    Check which budget categories are over threshold and return alert-formatted results.
    
    Args:
        threshold_pct: Percentage over budget before alerting (default 10%)
    
    Returns:
        List of alert dicts compatible with the RunwayAlert system.
    """
    variance_data = get_budget_variance(db, budget_id)
    if not variance_data:
        return []

    alerts = []
    for v in variance_data.get("variances", []):
        if v["variance_pct"] > threshold_pct:
            alerts.append({
                "alert_type": "budget_overrun",
                "severity": "critical" if v["variance_pct"] > 25 else "warning",
                "category": v["category"],
                "budget": v["budget"],
                "actual": v["actual"],
                "variance": v["variance"],
                "variance_pct": round(v["variance_pct"], 2),
                "message": f"{v['category']} is {v['variance_pct']:.1f}% over budget "
                           f"(₹{v['actual']:,.0f} vs ₹{v['budget']:,.0f})",
            })

    return alerts


def create_budget(db: Session, company_id: UUID, period: str, budgets: dict) -> models.Budget:
    """
    Create a budget and lines from category/department payload.

    Expected payload patterns:
    - {"marketing": 12000, "payroll": 50000}
    - {"engineering": {"payroll": 30000, "tools": 5000}}
    """
    fiscal_year = int(period.split("-")[0]) if "-" in period else date.today().year
    budget_name = f"Budget {period}"
    budget = models.Budget(
        company_id=company_id,
        name=budget_name,
        fiscal_year=fiscal_year,
        status="draft",
    )
    db.add(budget)
    db.flush()

    for key, value in budgets.items():
        if isinstance(value, dict):
            department = str(key)
            for category, amount in value.items():
                db.add(
                    models.BudgetLine(
                        budget_id=budget.id,
                        category=f"{department}:{category}",
                        monthly_amount=float(amount or 0),
                    )
                )
        else:
            db.add(
                models.BudgetLine(
                    budget_id=budget.id,
                    category=str(key),
                    monthly_amount=float(value or 0),
                )
            )

    db.commit()
    db.refresh(budget)
    return budget


def submit_for_approval(db: Session, budget_id: UUID) -> dict:
    budget = db.query(models.Budget).filter(models.Budget.id == budget_id).first()
    if not budget:
        return {"success": False, "message": "Budget not found"}

    budget.status = "pending_approval"
    db.commit()
    return {"success": True, "budget_id": str(budget.id), "status": budget.status}


def approve_budget(db: Session, budget_id: UUID, approver_id: UUID) -> dict:
    budget = db.query(models.Budget).filter(models.Budget.id == budget_id).first()
    if not budget:
        return {"success": False, "message": "Budget not found"}

    old_status = budget.status
    budget.status = "approved"
    db.commit()

    return {
        "success": True,
        "budget_id": str(budget.id),
        "old_status": old_status,
        "new_status": budget.status,
        "approved_by": str(approver_id),
    }


def track_budget_utilization(db: Session, company_id: UUID, period: str) -> dict:
    budget = (
        db.query(models.Budget)
        .filter(models.Budget.company_id == company_id)
        .order_by(models.Budget.created_at.desc())
        .first()
    )
    if not budget:
        return {"success": False, "message": "Budget not found"}

    target_month = date.fromisoformat(f"{period}-01") if len(period) == 7 else date.fromisoformat(period)
    variance = get_budget_variance(db, budget.id, target_month=target_month)
    if not variance:
        return {"success": False, "message": "No variance data"}

    total_budget = sum(float(v.get("budget", 0)) for v in variance.get("variances", []))
    total_actual = sum(float(v.get("actual", 0)) for v in variance.get("variances", []))
    utilization_pct = (total_actual / total_budget) * 100 if total_budget > 0 else 0

    return {
        "success": True,
        "company_id": str(company_id),
        "period": period,
        "budget_id": str(budget.id),
        "budget_total": round(total_budget, 2),
        "actual_total": round(total_actual, 2),
        "utilization_pct": round(utilization_pct, 2),
        "category_breakdown": variance.get("variances", []),
    }


def reallocate_budget(
    db: Session,
    budget_id: UUID,
    from_category: str,
    to_category: str,
    amount: float,
) -> dict:
    budget = db.query(models.Budget).filter(models.Budget.id == budget_id).first()
    if not budget:
        return {"success": False, "message": "Budget not found"}

    from_line = (
        db.query(models.BudgetLine)
        .filter(models.BudgetLine.budget_id == budget_id, models.BudgetLine.category == from_category)
        .first()
    )
    to_line = (
        db.query(models.BudgetLine)
        .filter(models.BudgetLine.budget_id == budget_id, models.BudgetLine.category == to_category)
        .first()
    )
    if not from_line:
        return {"success": False, "message": "Source category not found"}
    if float(from_line.monthly_amount or 0) < amount:
        return {"success": False, "message": "Insufficient budget in source category"}
    if not to_line:
        to_line = models.BudgetLine(budget_id=budget_id, category=to_category, monthly_amount=0)
        db.add(to_line)

    from_before = float(from_line.monthly_amount or 0)
    to_before = float(to_line.monthly_amount or 0)
    from_line.monthly_amount = from_before - amount
    to_line.monthly_amount = to_before + amount
    db.commit()

    return {
        "success": True,
        "budget_id": str(budget.id),
        "from_category": from_category,
        "to_category": to_category,
        "reallocated_amount": float(amount),
        "from_before": round(from_before, 2),
        "from_after": round(float(from_line.monthly_amount or 0), 2),
        "to_before": round(to_before, 2),
        "to_after": round(float(to_line.monthly_amount or 0), 2),
    }

