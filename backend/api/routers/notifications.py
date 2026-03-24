from __future__ import annotations

import os
from datetime import datetime
from uuid import UUID
from datetime import timedelta
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import database
import models
import schemas
from tasks.alert_tasks import send_alert_notifications

router = APIRouter(tags=["notifications"])

DEFAULT_ALERT_EMAIL = os.getenv("ALERT_FALLBACK_EMAIL", "sysswork@gmail.com")
TEST_NOTIFICATION_SYNC_DEFAULT = os.getenv("TEST_NOTIFICATION_SYNC", "true").lower() in {"1", "true", "yes"}


def _smtp_ready() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_USER") and os.getenv("SMTP_PASS"))


def _sanitize_contacts(contacts: Optional[dict]) -> dict:
    contacts = dict(contacts or {})
    contacts.pop("slack_webhook", None)
    contacts.pop("whatsapp", None)

    recipients = list(contacts.get("email_recipients") or [])
    if not recipients:
        recipients = [DEFAULT_ALERT_EMAIL]
    contacts["email_recipients"] = list(dict.fromkeys(recipients))
    
    # Preserve ceo and finance fields for email alert configuration
    if "ceo" not in contacts:
        contacts["ceo"] = None
    if "finance" not in contacts:
        contacts["finance"] = []
    
    return contacts


@router.get("/notifications/contacts/{company_id}")
def get_contacts(company_id: UUID, db: Session = Depends(database.get_db)):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return _sanitize_contacts(company.notification_contacts)


@router.put("/notifications/contacts/{company_id}")
def update_contacts(
    company_id: UUID,
    payload: schemas.NotificationContactsUpdate,
    db: Session = Depends(database.get_db),
):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    incoming = payload.model_dump(exclude_none=True)
    incoming.pop("slack_webhook", None)
    incoming.pop("whatsapp", None)
    company.notification_contacts = _sanitize_contacts({**(company.notification_contacts or {}), **incoming})
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
        alert = models.RunwayAlert(
            id=uuid.uuid4(),
            company_id=company_id,
            alert_level=models.RunwayAlertLevel.WARNING,
            runway_months=6.5,
            runway_date=(datetime.utcnow() + timedelta(days=195)).date(),
            alert_data={"source": "test_notification", "note": "Synthetic alert for notification testing"},
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

    smtp_ready = _smtp_ready()
    task_result = None
    if TEST_NOTIFICATION_SYNC_DEFAULT:
        task_result = send_alert_notifications(str(alert.id))
        mode = "sent_sync"
        message = (task_result or {}).get("message") or "Notification send attempted synchronously"
    else:
        try:
            send_alert_notifications.delay(str(alert.id))
            mode = "queued"
            message = "Notification task queued"
        except Exception:
            # Fall back to sync for local/dev setups where worker is unavailable.
            task_result = send_alert_notifications(str(alert.id))
            mode = "sent_sync_fallback"
            message = (task_result or {}).get("message") or "Queue unavailable; notification send attempted synchronously"

    success = bool(task_result.get("success")) if task_result is not None else True
    if not smtp_ready and "SMTP is not configured" not in message:
        message += "; SMTP is not configured (set SMTP_HOST, SMTP_USER, SMTP_PASS)"

    return {
        "success": success,
        "mode": mode,
        "message": message,
        "alert_id": str(alert.id),
        "smtp_ready": smtp_ready,
    }


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
