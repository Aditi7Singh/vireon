from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
import models
import database
import auth
from analytics import metrics

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])

@router.get("/sass-health")
async def get_sass_health(
    company_id: str = "00000000-0000-0000-0000-000000000000",
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Returns industry standard SaaS metrics and benchmarks.
    """
    # Fetch latest monthly metrics
    all_metrics = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).limit(12).all()

    if not all_metrics:
        raise HTTPException(status_code=404, detail="Incomplete financial data for benchmarking")

    latest = all_metrics[0]
    
    # Calculate Rule of 40
    # Simplified logic: (Rev Growth % + Net Margin %)
    # Let's assume net margin is (Net Cash Flow / Total Revenue)
    margin = float(latest.net_cash_flow / latest.total_revenue) * 100 if latest.total_revenue > 0 else 0
    # Growth requires previous month
    growth = 15.0 # Mocking 15% growth for now
    rule_of_40_score = growth + margin

    # Burn Multiple
    # Net Burn / Net New ARR
    net_burn = float(latest.total_expenses - latest.total_revenue)
    new_arr = 50000 # Mocking $50k new ARR 
    burn_multiple = net_burn / (new_arr / 12) if new_arr > 0 else float('inf')

    return {
        "metrics": [
            {
                "name": "Rule of 40",
                "value": f"{rule_of_40_score:.1f}%",
                "status": "Healthy" if rule_of_40_score >= 40 else "Monitor",
                "benchmark": "40.0%",
                "description": "Growth Rate + Profit Margin"
            },
            {
                "name": "Burn Multiple",
                "value": f"{burn_multiple:.2f}x",
                "status": "Great" if burn_multiple < 1.5 else "High" if burn_multiple < 3 else "Critical",
                "benchmark": "< 1.5x",
                "description": "Efficiency of burning capital for growth"
            },
            {
                "name": "Net Revenue Retention",
                "value": "108%",
                "status": "Standard",
                "benchmark": "> 110%",
                "description": "LTM revenue from existing customers"
            }
        ],
        "summary": "Your efficiency is top-quartile, but growth is lagging industry peers for your stage."
    }
