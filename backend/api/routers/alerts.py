from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

import models
import schemas
import database
import auth
from anomaly_detection import detect_expense_anomalies, detect_revenue_anomalies, detect_duplicate_invoices

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("", response_model=schemas.AlertsResponse)
def get_alerts(
    severity: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(database.get_db)
):
    # For now, get the first company for simplicity
    company = db.query(models.Company).first()
    if not company:
        return {
            "alerts": [],
            "total": 0,
            "critical_count": 0,
            "warning_count": 0,
            "last_scan_at": ""
        }

    query = db.query(models.Anomaly).filter(models.Anomaly.company_id == company.id)
    
    if severity:
        query = query.filter(models.Anomaly.severity == severity)
    
    total = query.count()
    critical_count = query.filter(models.Anomaly.severity == "critical").count()
    warning_count = query.filter(models.Anomaly.severity == "warning").count()
    
    anomalies = query.order_by(models.Anomaly.anomaly_date.desc()).limit(limit).all()
    
    # Map models.Anomaly to schemas.Alert
    alerts = []
    for a in anomalies:
        alerts.append({
            "id": str(a.id),
            "severity": a.severity or "info",
            "alert_type": a.type or "anomaly",
            "category": "Expense", # Default to expense for now
            "description": a.description,
            "amount": float(a.actual_value or 0),
            "baseline": float(a.expected_value or 0),
            "delta_pct": float(((a.actual_value / a.expected_value) - 1) * 100) if a.expected_value and a.expected_value != 0 else 0,
            "runway_impact": 0.5, # Placeholder
            "suggested_owner": "Finance Team",
            "created_at": a.created_at.isoformat(),
            "status": "active"
        })
        
    return {
        "alerts": alerts,
        "total": total,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "last_scan_at": anomalies[0].created_at.isoformat() if anomalies else ""
    }

@router.patch("/{alert_id}/dismiss")
def dismiss_alert(
    alert_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    anomaly = db.query(models.Anomaly).filter(models.Anomaly.id == alert_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    anomaly.status = "dismissed"
    db.commit()
    return {"status": "success"}

@router.post("/scan-now")
def trigger_scan(
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    company = db.query(models.Company).first()
    if not company:
        raise HTTPException(status_code=404, detail="No company found to scan")
    
    detect_expense_anomalies(db, company_id=company.id)
    detect_revenue_anomalies(db, company_id=company.id)
    detect_duplicate_invoices(db, company_id=company.id)
    return {"task_id": "immediate_scan_task"}
