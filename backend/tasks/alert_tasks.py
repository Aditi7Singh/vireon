from __future__ import annotations

import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

import models
from anomaly.celery_app import app as celery
from database import SessionLocal
from services.recommendations_service import generate_impact_alert


DEFAULT_ALERT_EMAIL = os.getenv("ALERT_FALLBACK_EMAIL", "sysswork@gmail.com")


def _collect_recipients(contacts: dict) -> List[str]:
    recipients: List[str] = []

    recipients.extend(contacts.get("email_recipients", []))

    # Backward compatibility for existing stored contact shapes.
    if contacts.get("ceo"):
        recipients.append(contacts["ceo"])
    recipients.extend(contacts.get("founders", []))
    recipients.extend(contacts.get("finance", []))
    if contacts.get("cto"):
        recipients.append(contacts["cto"])

    if not recipients:
        recipients.append(DEFAULT_ALERT_EMAIL)

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(recipients))


@celery.task
def check_runway_alerts_all_companies():
    """Runs daily. For each active company, checks runway and creates alert if needed."""
    db: Session = SessionLocal()
    try:
        companies = db.query(models.Company).all()
        created = 0
        for company in companies:
            result = generate_impact_alert(company.id, db)
            if result and result.get("alert_id"):
                created += 1
                send_alert_notifications.delay(result["alert_id"])
        return {"checked": len(companies), "alerts_created": created}
    finally:
        db.close()


@celery.task
def send_alert_notifications(alert_id: str):
    """Sends email-only notification for a runway alert."""
    db: Session = SessionLocal()
    try:
        alert = db.query(models.RunwayAlert).filter(models.RunwayAlert.id == UUID(alert_id)).first()
        if not alert:
            return {"success": False, "message": "Alert not found"}

        company = db.query(models.Company).filter(models.Company.id == alert.company_id).first()
        contacts = company.notification_contacts or {}

        payload = {
            "level": alert.alert_level.value,
            "runway_months": float(alert.runway_months),
            "runway_date": alert.runway_date.isoformat(),
            "top_burn_drivers": (alert.alert_data or {}).get("top_3_burn_drivers", []),
            "recommended_actions": (alert.alert_data or {}).get("suggested_immediate_actions", []),
        }

        recipients = _collect_recipients(contacts)

        subject = f"[VIREON] Runway Alert - {payload['level'].upper()}: {payload['runway_months']:.1f} months remaining"
        body = (
            f"Current runway: {payload['runway_months']:.1f} months\n"
            f"Estimated runway date: {payload['runway_date']}\n\n"
            "Top burn drivers:\n"
            + "\n".join([f"- {x}" for x in payload["top_burn_drivers"][:3]])
            + "\n\nRecommended immediate actions:\n"
            + "\n".join([f"- {x}" for x in payload["recommended_actions"][:3]])
        )

        sent, error_message = _send_email(recipients, subject, body)
        if not sent:
            return {
                "success": False,
                "alert_id": alert_id,
                "recipients": recipients,
                "message": error_message or "Email send failed",
            }

        alert.sent_at = datetime.utcnow()
        db.commit()
        return {"success": True, "alert_id": alert_id, "recipients": recipients}
    finally:
        db.close()


def _send_email(recipients: List[str], subject: str, body: str) -> Tuple[bool, Optional[str]]:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    sender = os.getenv("SMTP_FROM", user or "no-reply@vireon.ai")

    if not host or not user or not password:
        return False, "SMTP is not configured (set SMTP_HOST, SMTP_USER, SMTP_PASS)"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(sender, recipients, msg.as_string())
        return True, None
    except Exception as exc:
        return False, f"SMTP send failed: {exc}"


def send_email(recipient: str, subject: str, body: str) -> Tuple[bool, Optional[str]]:
    """Public helper for single-recipient email sends from API routes."""
    if not recipient or "@" not in recipient:
        return False, "Invalid email recipient"
    return _send_email([recipient], subject, body)
