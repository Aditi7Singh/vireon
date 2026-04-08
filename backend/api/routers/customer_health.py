"""
Customer Health Scoring Router
Customer health scoring and churn prediction for SaaS companies
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from typing import List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid

import database
import models
from auth import get_current_user

router = APIRouter(prefix="/customer-health", tags=["customer-health"])


@router.post("/calculate", response_model=dict)
def calculate_customer_health_scores(
    company_id: uuid.UUID,
    customer_ids: Optional[List[uuid.UUID]] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Calculate health scores for customers"""
    
    # Get customers to analyze
    query = db.query(models.Contact).filter(
        and_(
            models.Contact.company_id == company_id,
            models.Contact.type == "CUSTOMER"
        )
    )
    
    if customer_ids:
        query = query.filter(models.Contact.id.in_(customer_ids))
    
    customers = query.all()
    
    scores_created = 0
    for customer in customers:
        # Calculate health components
        payment_score = calculate_payment_behavior_score(db, customer.id)
        revenue_score = calculate_revenue_trend_score(db, customer.id)
        churn_prob = predict_churn_probability(db, customer.id, payment_score, revenue_score)
        
        # Overall health score (weighted average)
        overall_score = (payment_score * Decimal("0.4")) + (revenue_score * Decimal("0.6"))
        
        # Determine status
        if overall_score >= 70:
            status = models.CustomerHealthStatus.HEALTHY
        elif overall_score >= 40:
            status = models.CustomerHealthStatus.AT_RISK
        else:
            status = models.CustomerHealthStatus.CHURNED
        
        # Get additional metrics
        metrics = get_customer_metrics(db, customer.id)
        
        # Create or update health score
        existing = db.query(models.CustomerHealthScore).filter(
            and_(
                models.CustomerHealthScore.company_id == company_id,
                models.CustomerHealthScore.customer_id == customer.id
            )
        ).order_by(models.CustomerHealthScore.calculated_at.desc()).first()
        
        health_score = models.CustomerHealthScore(
            company_id=company_id,
            customer_id=customer.id,
            score=overall_score,
            status=status,
            payment_behavior_score=payment_score,
            revenue_trend_score=revenue_score,
            churn_probability=churn_prob,
            arr_at_risk=metrics["arr_at_risk"],
            late_payment_count=metrics["late_payment_count"],
            dispute_count=metrics["dispute_count"],
            revenue_growth_rate=metrics["revenue_growth_rate"],
            last_payment_date=metrics["last_payment_date"]
        )
        
        db.add(health_score)
        scores_created += 1
    
    db.commit()
    
    return {
        "message": f"Calculated health scores for {scores_created} customers",
        "scores_created": scores_created,
        "calculation_date": datetime.utcnow().isoformat()
    }


@router.get("/", response_model=List[dict])
def list_customer_health_scores(
    company_id: uuid.UUID,
    status: Optional[str] = None,
    min_churn_probability: Optional[float] = None,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List customer health scores with filters"""
    
    # Get latest score for each customer
    subquery = db.query(
        models.CustomerHealthScore.customer_id,
        func.max(models.CustomerHealthScore.calculated_at).label("max_date")
    ).filter(
        models.CustomerHealthScore.company_id == company_id
    ).group_by(models.CustomerHealthScore.customer_id).subquery()
    
    query = db.query(models.CustomerHealthScore).join(
        subquery,
        and_(
            models.CustomerHealthScore.customer_id == subquery.c.customer_id,
            models.CustomerHealthScore.calculated_at == subquery.c.max_date
        )
    )
    
    if status:
        query = query.filter(models.CustomerHealthScore.status == status)
    
    if min_churn_probability is not None:
        query = query.filter(
            models.CustomerHealthScore.churn_probability >= min_churn_probability
        )
    
    scores = query.order_by(models.CustomerHealthScore.churn_probability.desc()).limit(limit).all()
    
    result = []
    for score in scores:
        # Get customer details
        customer = db.query(models.Contact).filter(models.Contact.id == score.customer_id).first()
        
        result.append({
            "customer_id": str(score.customer_id),
            "customer_name": customer.name if customer else "Unknown",
            "score": float(score.score),
            "status": score.status.value,
            "churn_probability": float(score.churn_probability) if score.churn_probability else 0,
            "arr_at_risk": float(score.arr_at_risk) if score.arr_at_risk else 0,
            "payment_behavior_score": float(score.payment_behavior_score) if score.payment_behavior_score else 0,
            "revenue_trend_score": float(score.revenue_trend_score) if score.revenue_trend_score else 0,
            "late_payment_count": score.late_payment_count,
            "calculated_at": score.calculated_at.isoformat()
        })
    
    return result


@router.get("/{customer_id}", response_model=dict)
def get_customer_health_detail(
    customer_id: uuid.UUID,
    company_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get detailed health information for a customer"""
    
    # Get latest health score
    score = db.query(models.CustomerHealthScore).filter(
        and_(
            models.CustomerHealthScore.company_id == company_id,
            models.CustomerHealthScore.customer_id == customer_id
        )
    ).order_by(models.CustomerHealthScore.calculated_at.desc()).first()
    
    if not score:
        raise HTTPException(status_code=404, detail="Customer health score not found")
    
    # Get customer details
    customer = db.query(models.Contact).filter(models.Contact.id == customer_id).first()
    
    # Get historical scores
    historical_scores = db.query(models.CustomerHealthScore).filter(
        and_(
            models.CustomerHealthScore.company_id == company_id,
            models.CustomerHealthScore.customer_id == customer_id
        )
    ).order_by(models.CustomerHealthScore.calculated_at.desc()).limit(12).all()
    
    # Get recent invoices
    recent_invoices = db.query(models.Invoice).filter(
        models.Invoice.contact_id == customer_id
    ).order_by(models.Invoice.issue_date.desc()).limit(10).all()
    
    return {
        "customer": {
            "id": str(customer.id) if customer else None,
            "name": customer.name if customer else "Unknown",
            "email": customer.email if customer else None
        },
        "current_health": {
            "score": float(score.score),
            "status": score.status.value,
            "churn_probability": float(score.churn_probability) if score.churn_probability else 0,
            "arr_at_risk": float(score.arr_at_risk) if score.arr_at_risk else 0,
            "payment_behavior_score": float(score.payment_behavior_score) if score.payment_behavior_score else 0,
            "revenue_trend_score": float(score.revenue_trend_score) if score.revenue_trend_score else 0,
            "calculated_at": score.calculated_at.isoformat()
        },
        "metrics": {
            "late_payment_count": score.late_payment_count,
            "dispute_count": score.dispute_count,
            "revenue_growth_rate": float(score.revenue_growth_rate) if score.revenue_growth_rate else 0,
            "last_payment_date": score.last_payment_date.isoformat() if score.last_payment_date else None
        },
        "historical_trend": [
            {
                "date": s.calculated_at.isoformat(),
                "score": float(s.score),
                "churn_probability": float(s.churn_probability) if s.churn_probability else 0
            }
            for s in historical_scores
        ],
        "recent_invoices": [
            {
                "invoice_number": inv.invoice_number,
                "issue_date": inv.issue_date.isoformat(),
                "due_date": inv.due_date.isoformat(),
                "total_amount": float(inv.total_amount),
                "status": inv.status,
                "days_overdue": (date.today() - inv.due_date).days if inv.due_date < date.today() and inv.status == "OPEN" else 0
            }
            for inv in recent_invoices
        ]
    }


@router.get("/at-risk/summary", response_model=dict)
def get_at_risk_summary(
    company_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get summary of at-risk customers"""
    
    # Get latest scores for all customers
    subquery = db.query(
        models.CustomerHealthScore.customer_id,
        func.max(models.CustomerHealthScore.calculated_at).label("max_date")
    ).filter(
        models.CustomerHealthScore.company_id == company_id
    ).group_by(models.CustomerHealthScore.customer_id).subquery()
    
    latest_scores = db.query(models.CustomerHealthScore).join(
        subquery,
        and_(
            models.CustomerHealthScore.customer_id == subquery.c.customer_id,
            models.CustomerHealthScore.calculated_at == subquery.c.max_date
        )
    ).all()
    
    # Calculate summary
    total_customers = len(latest_scores)
    healthy = sum(1 for s in latest_scores if s.status == models.CustomerHealthStatus.HEALTHY)
    at_risk = sum(1 for s in latest_scores if s.status == models.CustomerHealthStatus.AT_RISK)
    churned = sum(1 for s in latest_scores if s.status == models.CustomerHealthStatus.CHURNED)
    
    total_arr_at_risk = sum(float(s.arr_at_risk or 0) for s in latest_scores if s.status == models.CustomerHealthStatus.AT_RISK)
    
    high_churn_risk = [
        {
            "customer_id": str(s.customer_id),
            "score": float(s.score),
            "churn_probability": float(s.churn_probability or 0),
            "arr_at_risk": float(s.arr_at_risk or 0)
        }
        for s in latest_scores
        if s.churn_probability and s.churn_probability > 50
    ]
    
    return {
        "summary": {
            "total_customers": total_customers,
            "healthy": healthy,
            "at_risk": at_risk,
            "churned": churned,
            "health_percentage": (healthy / total_customers * 100) if total_customers > 0 else 0
        },
        "financial_impact": {
            "total_arr_at_risk": total_arr_at_risk,
            "high_risk_customers": len(high_churn_risk)
        },
        "high_churn_risk_customers": sorted(high_churn_risk, key=lambda x: x["churn_probability"], reverse=True)[:10]
    }


@router.post("/{customer_id}/intervention", response_model=dict)
def record_intervention(
    customer_id: uuid.UUID,
    company_id: uuid.UUID,
    intervention_type: str,
    notes: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Record customer intervention action"""
    
    # In production, you'd have an interventions table
    # For now, add a comment to the customer
    comment = models.TransactionComment(
        company_id=company_id,
        entity_type="customer",
        entity_id=customer_id,
        comment_text=f"[INTERVENTION - {intervention_type}] {notes}",
        created_by=current_user.username
    )
    
    db.add(comment)
    db.commit()
    
    return {
        "message": "Intervention recorded",
        "customer_id": str(customer_id),
        "intervention_type": intervention_type,
        "recorded_at": datetime.utcnow().isoformat()
    }


# Helper functions

def calculate_payment_behavior_score(db: Session, customer_id: uuid.UUID) -> Decimal:
    """Calculate payment behavior score (0-100)"""
    
    # Get invoices for last 12 months
    twelve_months_ago = date.today() - timedelta(days=365)
    invoices = db.query(models.Invoice).filter(
        and_(
            models.Invoice.contact_id == customer_id,
            models.Invoice.issue_date >= twelve_months_ago
        )
    ).all()
    
    if not invoices:
        return Decimal("50.0")  # Neutral score for new customers
    
    score = Decimal("100.0")
    
    # Penalize late payments
    late_count = sum(1 for inv in invoices if inv.payment_date and inv.payment_date > inv.due_date)
    score -= Decimal(str(late_count * 5))  # -5 points per late payment
    
    # Penalize open/overdue invoices
    overdue_count = sum(1 for inv in invoices if inv.status in ["OPEN", "OVERDUE"] and inv.due_date < date.today())
    score -= Decimal(str(overdue_count * 10))  # -10 points per overdue invoice
    
    # Penalize partial payments
    partial_count = sum(1 for inv in invoices if inv.status == "PARTIALLY_PAID")
    score -= Decimal(str(partial_count * 7))  # -7 points per partial payment
    
    return max(Decimal("0.0"), min(score, Decimal("100.0")))


def calculate_revenue_trend_score(db: Session, customer_id: uuid.UUID) -> Decimal:
    """Calculate revenue trend score (0-100)"""
    
    # Get paid invoices for last 12 months
    twelve_months_ago = date.today() - timedelta(days=365)
    six_months_ago = date.today() - timedelta(days=180)
    
    recent_revenue = db.query(func.sum(models.Invoice.total_amount)).filter(
        and_(
            models.Invoice.contact_id == customer_id,
            models.Invoice.issue_date >= six_months_ago,
            models.Invoice.status == "PAID"
        )
    ).scalar() or Decimal("0.0")
    
    older_revenue = db.query(func.sum(models.Invoice.total_amount)).filter(
        and_(
            models.Invoice.contact_id == customer_id,
            models.Invoice.issue_date >= twelve_months_ago,
            models.Invoice.issue_date < six_months_ago,
            models.Invoice.status == "PAID"
        )
    ).scalar() or Decimal("0.0")
    
    if older_revenue == 0:
        return Decimal("70.0")  # Neutral for new customers
    
    # Calculate growth rate
    growth_rate = ((recent_revenue - older_revenue) / older_revenue) * 100
    
    # Convert to score (0-100)
    if growth_rate >= 20:
        return Decimal("100.0")
    elif growth_rate >= 0:
        return Decimal("80.0")
    elif growth_rate >= -20:
        return Decimal("50.0")
    elif growth_rate >= -50:
        return Decimal("20.0")
    else:
        return Decimal("0.0")


def predict_churn_probability(
    db: Session,
    customer_id: uuid.UUID,
    payment_score: Decimal,
    revenue_score: Decimal
) -> Decimal:
    """Predict churn probability (0-100)"""
    
    # Simple model: inverse of health scores
    health_score = (payment_score * Decimal("0.4")) + (revenue_score * Decimal("0.6"))
    churn_prob = Decimal("100.0") - health_score
    
    # Adjust based on recent activity
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_activity = db.query(models.Invoice).filter(
        and_(
            models.Invoice.contact_id == customer_id,
            models.Invoice.issue_date >= thirty_days_ago
        )
    ).count()
    
    if recent_activity == 0:
        churn_prob += Decimal("20.0")  # No recent activity increases risk
    
    return min(churn_prob, Decimal("100.0"))


def get_customer_metrics(db: Session, customer_id: uuid.UUID) -> dict:
    """Get additional customer metrics"""
    
    # Calculate ARR
    twelve_months_ago = date.today() - timedelta(days=365)
    annual_revenue = db.query(func.sum(models.Invoice.total_amount)).filter(
        and_(
            models.Invoice.contact_id == customer_id,
            models.Invoice.issue_date >= twelve_months_ago,
            models.Invoice.status.in_(["PAID", "PARTIALLY_PAID"])
        )
    ).scalar() or Decimal("0.0")
    
    # Late payment count
    late_payment_count = db.query(models.Invoice).filter(
        and_(
            models.Invoice.contact_id == customer_id,
            models.Invoice.payment_date > models.Invoice.due_date
        )
    ).count()
    
    # Last payment date
    last_payment = db.query(models.Invoice).filter(
        and_(
            models.Invoice.contact_id == customer_id,
            models.Invoice.status == "PAID"
        )
    ).order_by(models.Invoice.payment_date.desc()).first()
    
    # Revenue growth rate
    six_months_ago = date.today() - timedelta(days=180)
    recent_revenue = db.query(func.sum(models.Invoice.total_amount)).filter(
        and_(
            models.Invoice.contact_id == customer_id,
            models.Invoice.issue_date >= six_months_ago,
            models.Invoice.status == "PAID"
        )
    ).scalar() or Decimal("0.0")
    
    older_revenue = db.query(func.sum(models.Invoice.total_amount)).filter(
        and_(
            models.Invoice.contact_id == customer_id,
            models.Invoice.issue_date >= twelve_months_ago,
            models.Invoice.issue_date < six_months_ago,
            models.Invoice.status == "PAID"
        )
    ).scalar() or Decimal("0.0")
    
    growth_rate = Decimal("0.0")
    if older_revenue > 0:
        growth_rate = ((recent_revenue - older_revenue) / older_revenue) * 100
    
    return {
        "arr_at_risk": annual_revenue,
        "late_payment_count": late_payment_count,
        "dispute_count": 0,  # Placeholder - needs dispute tracking
        "revenue_growth_rate": growth_rate,
        "last_payment_date": last_payment.payment_date if last_payment else None
    }
