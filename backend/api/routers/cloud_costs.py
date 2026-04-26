from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import List, Dict, Any
import schemas
import database
import auth
import models
from datetime import datetime, date, timedelta

router = APIRouter(prefix="/cloud-costs", tags=["cloud_costs"])

@router.get("/summary", response_model=Dict[str, Any])
def get_cloud_summary(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Get summarized cloud costs for a company."""
    # Find all accounts for the company
    accounts = db.query(models.CloudAccount).filter(models.CloudAccount.company_id == company_id).all()
    account_ids = [acc.id for acc in accounts]
    
    # Calculate costs for the last 30 days
    thirty_days_ago = date.today() - timedelta(days=30)
    
    total_spend_30d = db.query(func.sum(models.CloudCostDetail.amount)).filter(
        models.CloudCostDetail.account_id.in_(account_ids),
        models.CloudCostDetail.usage_date >= thirty_days_ago
    ).scalar() or 0.0
    
    service_breakdown = db.query(
        models.CloudCostDetail.service_name, 
        func.sum(models.CloudCostDetail.amount).label("total")
    ).filter(
        models.CloudCostDetail.account_id.in_(account_ids),
        models.CloudCostDetail.usage_date >= thirty_days_ago
    ).group_by(models.CloudCostDetail.service_name).all()
    
    return {
        "total_spend_30d": float(total_spend_30d),
        "service_breakdown": {row.service_name: float(row.total) for row in service_breakdown},
        "accounts_connected": len(accounts),
        "as_of": date.today().isoformat()
    }

@router.get("/recommendations")
def get_cloud_recommendations(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Return data-driven cloud optimization recommendations for the last 30 days."""
    thirty_days_ago = date.today() - timedelta(days=30)
    accounts = db.query(models.CloudAccount).filter(models.CloudAccount.company_id == company_id).all()
    account_ids = [acc.id for acc in accounts]
    if not account_ids:
        return {
            "as_of": date.today().isoformat(),
            "recommendations": [],
            "total_potential_monthly_saving": 0.0,
            "message": "No cloud accounts connected yet.",
        }

    rows = db.query(
        models.CloudCostDetail.service_name,
        models.CloudCostDetail.region,
        func.sum(models.CloudCostDetail.amount).label("total"),
    ).filter(
        models.CloudCostDetail.account_id.in_(account_ids),
        models.CloudCostDetail.usage_date >= thirty_days_ago,
    ).group_by(
        models.CloudCostDetail.service_name,
        models.CloudCostDetail.region,
    ).all()

    if not rows:
        return {
            "as_of": date.today().isoformat(),
            "recommendations": [],
            "total_potential_monthly_saving": 0.0,
            "message": "No cloud usage data in the last 30 days.",
        }

    service_totals: Dict[str, float] = {}
    regional_totals: Dict[str, float] = {}
    total_spend = 0.0
    for r in rows:
        amount = float(r.total or 0)
        service = r.service_name or "Unknown"
        region = r.region or "global"
        service_totals[service] = service_totals.get(service, 0.0) + amount
        regional_totals[region] = regional_totals.get(region, 0.0) + amount
        total_spend += amount

    recommendations = []

    # Rule 1: Service concentration can usually be optimized with rightsizing/commitment plans.
    top_service, top_service_cost = max(service_totals.items(), key=lambda x: x[1])
    if total_spend > 0 and (top_service_cost / total_spend) >= 0.4:
        recommendations.append(
            {
                "service": top_service,
                "type": "Rightsizing / Commitment Plan",
                "description": f"{top_service} contributes {(top_service_cost / total_spend) * 100:.1f}% of cloud spend. Review reserved capacity and idle resources.",
                "potential_monthly_saving": round(top_service_cost * 0.12, 2),
                "priority": "HIGH",
            }
        )

    # Rule 2: Too many regions often indicates replication inefficiency.
    if len(regional_totals) >= 4:
        recommendations.append(
            {
                "service": "multi-service",
                "type": "Region Consolidation",
                "description": f"Workloads are spread across {len(regional_totals)} regions. Consolidate non-critical workloads to reduce data transfer and operational overhead.",
                "potential_monthly_saving": round(total_spend * 0.06, 2),
                "priority": "MEDIUM",
            }
        )

    # Rule 3: Low-spend disconnected accounts can be decommissioned.
    low_spend_accounts = []
    for account in accounts:
        account_spend = db.query(func.sum(models.CloudCostDetail.amount)).filter(
            models.CloudCostDetail.account_id == account.id,
            models.CloudCostDetail.usage_date >= thirty_days_ago,
        ).scalar() or 0.0
        if float(account_spend) < 25:
            low_spend_accounts.append(account)
    if low_spend_accounts:
        recommendations.append(
            {
                "service": "account-governance",
                "type": "Account Cleanup",
                "description": f"{len(low_spend_accounts)} account(s) show minimal usage. Validate ownership and close unused accounts.",
                "potential_monthly_saving": round(len(low_spend_accounts) * 10.0, 2),
                "priority": "LOW",
            }
        )

    total_potential = round(sum(float(r["potential_monthly_saving"]) for r in recommendations), 2)
    return {
        "as_of": date.today().isoformat(),
        "recommendations": recommendations,
        "total_potential_monthly_saving": total_potential,
        "observed_30d_spend": round(total_spend, 2),
    }
