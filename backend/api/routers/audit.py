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
