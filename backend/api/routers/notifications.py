import os
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import database
import models
import schemas
from tasks.alert_tasks import send_alert_notifications

router = APIRouter(tags=["notifications"])


@router.get("/notifications/contacts/{company_id}")
def get_contacts(company_id: UUID, db: Session = Depends(database.get_db)):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company.notification_contacts or {}


@router.put("/notifications/contacts/{company_id}")
def update_contacts(
    company_id: UUID,
    payload: schemas.NotificationContactsUpdate,
    db: Session = Depends(database.get_db),
):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company.notification_contacts = {**(company.notification_contacts or {}), **payload.model_dump(exclude_none=True)}
    db.commit()
    return {"success": True, "notification_contacts": company.notification_contacts}


@router.put("/notifications/thresholds/{company_id}")
def update_thresholds(
    company_id: UUID,
    payload: schemas.AlertThresholdsUpdate,
    db: Session = Depends(database.get_db),
):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company.alert_thresholds = payload.model_dump()
    db.commit()
    return {"success": True, "alert_thresholds": company.alert_thresholds}


@router.post("/alerts/test-notification/{company_id}")
def test_notification(company_id: UUID, db: Session = Depends(database.get_db)):
    env = os.getenv("ENV", "development").lower()
    if env in {"prod", "production"}:
        raise HTTPException(status_code=403, detail="Test notifications are disabled in production")

    alert = (
        db.query(models.RunwayAlert)
        .filter(models.RunwayAlert.company_id == company_id)
        .order_by(models.RunwayAlert.created_at.desc())
        .first()
    )
    if not alert:
        raise HTTPException(status_code=404, detail="No alert found for company")

    send_alert_notifications.delay(str(alert.id))
    return {"success": True, "message": "Notification task queued", "alert_id": str(alert.id)}


@router.get("/alerts/active/{company_id}")
def get_active_alerts(company_id: UUID, db: Session = Depends(database.get_db)):
    alerts = (
        db.query(models.RunwayAlert)
        .filter(models.RunwayAlert.company_id == company_id, models.RunwayAlert.acknowledged_at.is_(None))
        .order_by(models.RunwayAlert.created_at.desc())
        .all()
    )
    return [
        {
            "id": str(a.id),
            "alert_level": a.alert_level.value,
            "runway_months": float(a.runway_months),
            "runway_date": a.runway_date.isoformat(),
            "alert_data": a.alert_data,
            "sent_at": a.sent_at.isoformat() if a.sent_at else None,
        }
        for a in alerts
    ]
