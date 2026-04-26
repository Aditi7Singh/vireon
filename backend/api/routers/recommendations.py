import os
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import database
import models
from services.recommendations_service import generate_recommendations, generate_impact_alert

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/generate/{company_id}")
def generate(company_id: UUID, db: Session = Depends(database.get_db)):
    return generate_recommendations(company_id, db)


@router.get("/latest/{company_id}")
def latest(company_id: UUID, db: Session = Depends(database.get_db)):
    report = (
        db.query(models.RecommendationReport)
        .filter(models.RecommendationReport.company_id == company_id)
        .order_by(models.RecommendationReport.generated_at.desc())
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="No report found")
    return {
        "id": str(report.id),
        "generated_at": report.generated_at.isoformat(),
        "month": report.month,
        "recommendations": report.recommendations,
        "runway_at_generation": float(report.runway_at_generation or 0),
    }


@router.get("/history/{company_id}")
def history(company_id: UUID, db: Session = Depends(database.get_db)):
    reports = (
        db.query(models.RecommendationReport)
        .filter(models.RecommendationReport.company_id == company_id)
        .order_by(models.RecommendationReport.generated_at.desc())
        .all()
    )
    return [
        {
            "id": str(r.id),
            "generated_at": r.generated_at.isoformat(),
            "month": r.month,
            "status": r.status.value,
        }
        for r in reports
    ]


@router.post("/check-alerts/{company_id}")
def check_alerts(company_id: UUID, db: Session = Depends(database.get_db)):
    result = generate_impact_alert(company_id, db)
    return result or {"created": False, "message": "Runway is healthy; no alert created."}


@router.get("/alerts/active/{company_id}")
def active_alerts(company_id: UUID, db: Session = Depends(database.get_db)):
    alerts = (
        db.query(models.RunwayAlert)
        .filter(models.RunwayAlert.company_id == company_id, models.RunwayAlert.acknowledged_at.is_(None))
        .order_by(models.RunwayAlert.created_at.desc())
        .all()
    )
    return [
        {
            "id": str(a.id),
            "level": a.alert_level.value,
            "runway_months": float(a.runway_months),
            "runway_date": a.runway_date.isoformat(),
            "alert_data": a.alert_data,
        }
        for a in alerts
    ]


@router.patch("/alerts/{alert_id}/acknowledge")
def acknowledge(alert_id: UUID, acknowledged_by: str = "finance", db: Session = Depends(database.get_db)):
    alert = db.query(models.RunwayAlert).filter(models.RunwayAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.acknowledged_at = datetime.utcnow()
    alert.acknowledged_by = acknowledged_by
    db.commit()
    return {"success": True, "alert_id": str(alert.id)}
