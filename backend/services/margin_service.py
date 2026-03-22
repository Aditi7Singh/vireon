from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
from datetime import date
import models
from decimal import Decimal

def calculate_server_side_margin(db: Session, company_id: Any, target_month: date = None) -> Dict[str, Any]:
    """
    Calculates Gross Margin for a given month.
    Margin = (Revenue - COGS) / Revenue
    """
    if not target_month:
        latest_metric = db.query(models.MonthlyMetric).filter(
            models.MonthlyMetric.company_id == company_id
        ).order_by(models.MonthlyMetric.metric_month.desc()).first()
        if not latest_metric:
            return {}
        target_month = latest_metric.metric_month

    month_start = target_month.replace(day=1)
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)

    # 1. Fetch Revenue from GL (Codes 4000-4999)
    revenue_total = db.query(
        func.sum(models.GeneralLedger.credit_amount - models.GeneralLedger.debit_amount)
    ).filter(
        models.GeneralLedger.company_id == company_id,
        models.GeneralLedger.transaction_date >= month_start,
        models.GeneralLedger.transaction_date < next_month,
        models.GeneralLedger.account_code.in_([
            models.GLAccountCode.PRODUCT_REVENUE,
            models.GLAccountCode.SERVICE_REVENUE,
            models.GLAccountCode.SUBSCRIPTION_REVENUE
        ])
    ).scalar() or 0.0

    # 2. Fetch COGS from GL
    cogs_total = db.query(
        func.sum(models.GeneralLedger.debit_amount - models.GeneralLedger.credit_amount)
    ).filter(
        models.GeneralLedger.company_id == company_id,
        models.GeneralLedger.transaction_date >= month_start,
        models.GeneralLedger.transaction_date < next_month,
        (models.GeneralLedger.account_name.ilike("%COGS%")) | 
        (models.GeneralLedger.account_name.ilike("%Cost of Goods Sold%"))
    ).scalar() or 0.0

    # Fallback: If GL is sparse, check Expense model with category tags
    if float(cogs_total) == 0:
        cogs_total = db.query(
            func.sum(models.Expense.total_amount)
        ).filter(
            models.Expense.company_id == company_id,
            models.Expense.transaction_date >= month_start,
            models.Expense.transaction_date < next_month,
            models.Expense.category.ilike("%COGS%")
        ).scalar() or 0.0

    revenue = float(revenue_total)
    cogs = float(cogs_total)
    gross_profit = revenue - cogs
    margin_pct = (gross_profit / revenue * 100) if revenue > 0 else 0.0

    return {
        "month": target_month.strftime("%Y-%m"),
        "revenue": revenue,
        "cogs": cogs,
        "gross_profit": gross_profit,
        "margin_percentage": round(margin_pct, 2),
        "status": "healthy" if margin_pct > 70 else "warning" if margin_pct > 40 else "critical"
    }

def calculate_product_margin(db: Session, company_id: Any, target_month: date = None) -> List[Dict[str, Any]]:
    """Breakdown of margins by product tag."""
    if not target_month:
        target_month = date.today()
    
    month_start = target_month.replace(day=1)
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)
        
    # Grouped revenue and cogs
    revenue_rows = db.query(
        models.GeneralLedger.product_tag,
        func.sum(models.GeneralLedger.credit_amount - models.GeneralLedger.debit_amount).label("rev")
    ).filter(
        models.GeneralLedger.company_id == company_id,
        models.GeneralLedger.transaction_date >= month_start,
        models.GeneralLedger.transaction_date < next_month,
        models.GeneralLedger.account_code.in_([
            models.GLAccountCode.PRODUCT_REVENUE,
            models.GLAccountCode.SERVICE_REVENUE,
            models.GLAccountCode.SUBSCRIPTION_REVENUE
        ])
    ).group_by(models.GeneralLedger.product_tag).all()
    
    cogs_rows = db.query(
        models.GeneralLedger.product_tag,
        func.sum(models.GeneralLedger.debit_amount - models.GeneralLedger.credit_amount).label("cost")
    ).filter(
        models.GeneralLedger.company_id == company_id,
        models.GeneralLedger.transaction_date >= month_start,
        models.GeneralLedger.transaction_date < next_month,
        (models.GeneralLedger.account_name.ilike("%COGS%")) | 
        (models.GeneralLedger.account_name.ilike("%Cost of Goods Sold%"))
    ).group_by(models.GeneralLedger.product_tag).all()
    
    rev_map = {str(r.product_tag.value if hasattr(r.product_tag, 'value') else r.product_tag): float(r.rev) for r in revenue_rows}
    cost_map = {str(r.product_tag.value if hasattr(r.product_tag, 'value') else r.product_tag): float(r.cost) for r in cogs_rows}
    
    all_tags = set(rev_map.keys()) | set(cost_map.keys())
    results = []
    for tag in sorted(all_tags):
        rev = rev_map.get(tag, 0.0)
        cost = cost_map.get(tag, 0.0)
        profit = rev - cost
        margin = (profit / rev * 100) if rev > 0 else 0.0
        results.append({
            "product_tag": tag,
            "revenue": rev,
            "cogs": cost,
            "gross_profit": profit,
            "margin_percentage": round(margin, 2)
        })
    return results

def check_margin_alerts(db: Session, company_id: Any, target_month: date = None, threshold: float = 50.0) -> List[Dict[str, Any]]:
    """Checks if overall or product-level margins are below threshold."""
    overall = calculate_server_side_margin(db, company_id, target_month)
    alerts = []
    if overall.get("margin_percentage", 0) < threshold:
        alerts.append({
            "type": "low_margin",
            "severity": "critical" if overall["margin_percentage"] < (threshold / 2) else "warning",
            "message": f"Overall gross margin ({overall['margin_percentage']}%) is below threshold ({threshold}%)",
            "data": overall
        })
    return alerts
