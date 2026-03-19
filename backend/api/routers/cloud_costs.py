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
    """Get Cloud Optimization Recommendations (Stub)."""
    # Logic for ROI-ranked optimizations (Reserved Instances, Idle Resources)
    return [
        {
            "service": "EC2",
            "type": "Idle Resource",
            "description": "Terminate 2 idle t3.large instances in us-east-1",
            "potential_monthly_saving": 120.0,
            "priority": "HIGH"
        },
        {
            "service": "S3",
            "type": "Lifecycle Policy",
            "description": "Move 5TB of data to Glacier (Archive)",
            "potential_monthly_saving": 85.0,
            "priority": "MEDIUM"
        }
    ]
