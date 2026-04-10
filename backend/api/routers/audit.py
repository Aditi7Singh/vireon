from __future__ import annotations

from datetime import date
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from uuid import UUID

import auth
import database
import models
from services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditLogRequest(BaseModel):
    company_id: Optional[UUID] = None
    event_type: str = "entity_change"
    entity_type: str
    entity_id: UUID
    old_value: dict = {}
    new_value: dict = {}
    user_id: UUID


@router.post("/events")
def log_event(
    payload: AuditLogRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    event = AuditService(db).log_entity_change(
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        old=payload.old_value,
        new=payload.new_value,
        user_id=payload.user_id,
        company_id=payload.company_id,
        event_type=payload.event_type,
    )
    return {"id": str(event.id), "hash": event.immutable_hash}


@router.get("/trail/{entity_type}/{entity_id}")
def query_audit_trail(
    entity_type: str,
    entity_id: UUID,
    start_date: date,
    end_date: date,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    rows = AuditService(db).query_audit_trail(entity_type, entity_id, start_date, end_date)
    return [
        {
            "id": str(row.id),
            "event_type": row.event_type,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "user_id": row.user_id,
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            "hash": row.immutable_hash,
        }
        for row in rows
    ]


@router.get("/report/{company_id}")
def generate_audit_report(
    company_id: UUID,
    period: str,
    audit_type: str = "all",
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return AuditService(db).generate_audit_report(company_id, period, audit_type)


@router.get("/tamper-check/{company_id}")
def run_tamper_detection(
    company_id: UUID,
    limit: int = 500,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    SOC 2 tamper detection: re-hash stored audit events and compare with
    the stored immutable_hash. Flags any event where the hash doesn't match
    (indicating a record was modified after logging).

    Returns:
        {
          total_checked, tampered_count, clean_count,
          tampered_events: [{id, entity_type, timestamp, stored_hash, computed_hash}],
          soc2_status: "PASS" | "FAIL",
        }
    """
    import hashlib, json as _json
    from datetime import datetime as _dt

    events = (
        db.query(models.AuditEvent)
        .filter(models.AuditEvent.company_id == company_id)
        .order_by(models.AuditEvent.timestamp.desc())
        .limit(limit)
        .all()
    )

    tampered = []
    clean = 0

    for ev in events:
        payload = {
            "event_type": ev.event_type,
            "entity_type": ev.entity_type,
            "entity_id": str(ev.entity_id),
            "old": ev.old_value or {},
            "new": ev.new_value or {},
            "user_id": str(ev.user_id),
            "timestamp": ev.timestamp.isoformat() if ev.timestamp else "",
        }
        computed = hashlib.sha256(
            _json.dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest()

        if computed != ev.immutable_hash:
            tampered.append({
                "id": str(ev.id),
                "entity_type": ev.entity_type,
                "entity_id": str(ev.entity_id),
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                "stored_hash": ev.immutable_hash,
                "computed_hash": computed,
            })
        else:
            clean += 1

    return {
        "company_id": str(company_id),
        "total_checked": len(events),
        "clean_count": clean,
        "tampered_count": len(tampered),
        "tampered_events": tampered,
        "soc2_status": "PASS" if not tampered else "FAIL",
        "checked_at": __import__("datetime").datetime.utcnow().isoformat(),
        "summary": (
            f"All {clean} audit records verified intact — no tampering detected."
            if not tampered else
            f"WARNING: {len(tampered)} record(s) have been modified after logging. "
            f"SOC 2 compliance is at risk."
        ),
    }
