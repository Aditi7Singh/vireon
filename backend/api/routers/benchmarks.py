from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from uuid import UUID
import models
import database
import auth
from analytics import metrics

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])

@router.get("/sass-health")
async def get_sass_health(
    company_id: Optional[UUID] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Returns industry standard SaaS metrics and benchmarks.
    Rule of 40: Combines growth rate (%) + net margin (%) - industry benchmark is 40+
    Burn Multiple: Net burn / new ARR - goal is <1.5x
    NRR: Net Revenue Retention - goal is >110%
    """
    if company_id is None:
        company_row = db.query(models.Company.id).order_by(models.Company.created_at.asc()).first()
        if not company_row:
            raise HTTPException(status_code=404, detail="No company found")
        company_id = company_row[0]

    # Fetch latest 12 months of metrics
    all_metrics = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).limit(12).all()

    if not all_metrics or len(all_metrics) == 0:
        return {
            "metrics": [
                {
                    "name": "Rule of 40",
                    "value": "—",
                    "status": "Pending Data",
                    "benchmark": "40.0%",
                    "description": "Growth Rate + Profit Margin",
                    "narrative": "No historical data available. Start tracking monthly metrics."
                },
                {
                    "name": "Burn Multiple",
                    "value": "—",
                    "status": "Pending Data",
                    "benchmark": "< 1.5x",
                    "description": "Efficiency of burning capital for growth",
                    "narrative": "No data for calculation."
                },
                {
                    "name": "Net Revenue Retention",
                    "value": "—",
                    "status": "Pending Data",
                    "benchmark": "> 110%",
                    "description": "LTM revenue from existing customers",
                    "narrative": "Track existing customer revenue month-over-month."
                }
            ],
            "summary": "Benchmark card is ready. Add monthly metrics to see live SaaS health scoring."
        }

    latest = all_metrics[0]
    
    # 1. RULE OF 40 CALCULATION
    # Formula: Growth Rate % + Net Margin %
    # Growth rate: Compare current month revenue to 12 months ago
    revenue_now = float(latest.total_revenue or 0)
    revenue_12m_ago = float(all_metrics[-1].total_revenue or 0) if len(all_metrics) >= 12 else revenue_now
    
    if revenue_12m_ago > 0:
        yoy_growth = ((revenue_now - revenue_12m_ago) / revenue_12m_ago) * 100
    else:
        yoy_growth = 0
    
    # Net Margin: (Revenue - Expenses) / Revenue * 100
    total_expenses = float(latest.total_expenses or 0)
    net_income = revenue_now - total_expenses
    net_margin = (net_income / revenue_now * 100) if revenue_now > 0 else 0
    
    rule_of_40_score = yoy_growth + net_margin
    rule_of_40_status = "Excellent" if rule_of_40_score >= 60 else "Healthy" if rule_of_40_score >= 40 else "Monitor" if rule_of_40_score >= 20 else "Critical"
    
    # 2. BURN MULTIPLE CALCULATION
    # Formula: Monthly Net Burn / Monthly New ARR
    # Net Burn = Expenses - Revenue (always positive when company is losing money)
    monthly_burn = max(0, total_expenses - revenue_now)
    
    # Estimate new ARR from this month's revenue (simplified)
    # In a real system, this would come from new_customer_revenue
    estimated_new_arr = max(1, revenue_now * 0.3)  # Assume 30% of revenue is bookings/new ARR
    monthly_new_arr = estimated_new_arr / 12
    
    if monthly_new_arr > 0:
        burn_multiple = monthly_burn / monthly_new_arr
    else:
        burn_multiple = float('inf') if monthly_burn > 0 else 0
    
    burn_multiple_status = "Excellent" if burn_multiple < 0.5 else "Great" if burn_multiple < 1.5 else "High" if burn_multiple < 3 else "Critical"
    
    # Cap display at 99.99x to avoid extreme values
    burn_multiple_display = min(burn_multiple, 99.99)
    
    # 3. NET REVENUE RETENTION (NRR)
    # Formula: (Existing Customer Revenue This Month / Existing Customer Revenue Last Month) * 100
    # Simplified: Calculate from historical revenue trend
    if len(all_metrics) >= 2:
        prev_month_revenue = float(all_metrics[1].total_revenue or 0)
        if prev_month_revenue > 0:
            # Estimate NRR from revenue growth (this is simplified)
            # In a full implementation, track existing vs new customer revenue separately
            nrr = (revenue_now / prev_month_revenue) * 100
        else:
            nrr = 100
    else:
        nrr = 100
    
    nrr_status = "Excellent" if nrr >= 130 else "Great" if nrr >= 110 else "Good" if nrr >= 100 else "Warning"
    
    return {
        "metrics": [
            {
                "name": "Rule of 40",
                "value": f"{rule_of_40_score:.1f}%",
                "status": rule_of_40_status,
                "benchmark": "40.0%",
                "description": "Growth Rate + Profit Margin",
                "narrative": f"Your score is {rule_of_40_score:.0f}%, combining {yoy_growth:.0f}% YoY growth with {net_margin:.0f}% net margin."
            },
            {
                "name": "Burn Multiple",
                "value": f"{burn_multiple_display:.2f}x",
                "status": burn_multiple_status,
                "benchmark": "< 1.5x",
                "description": "Efficiency of burning capital for growth",
                "narrative": f"You're burning ₹{monthly_burn:,.0f}/month to generate ₹{monthly_new_arr*12:,.0f} ARR (ratio: {burn_multiple_display:.2f}x)."
            },
            {
                "name": "Net Revenue Retention",
                "value": f"{nrr:.0f}%",
                "status": nrr_status,
                "benchmark": "> 110%",
                "description": "LTM revenue from existing customers",
                "narrative": f"Month-over-month retention trending at {nrr:.0f}%. Target is >110% for SaaS efficiency."
            }
        ],
        "summary": f"Your SaaS efficiency score (Rule of 40) is {rule_of_40_score:.0f}%. With {burn_multiple_display:.2f}x burn multiple and {nrr:.0f}% NRR, you're {'on track' if rule_of_40_score >= 40 else 'below target'}."
    }
