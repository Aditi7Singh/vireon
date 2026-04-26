from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from typing import Any, Dict, Optional, Union
from uuid import UUID

from sqlalchemy.orm import Session

import models


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _hash_event(payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def log_entity_change(
        self,
        entity_type: str,
        entity_id: UUID,
        old: Optional[Dict[str, Any]],
        new: Optional[Dict[str, Any]],
        user_id: Union[UUID, str],
        company_id: Optional[UUID] = None,
        event_type: str = "entity_change",
    ) -> models.AuditEvent:
        payload = {
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "old": old or {},
            "new": new or {},
            "user_id": str(user_id),
            "timestamp": datetime.utcnow().isoformat(),
        }
        event = models.AuditEvent(
            company_id=company_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=str(entity_id),
            old_value=old or {},
            new_value=new or {},
            user_id=str(user_id),
            timestamp=datetime.utcnow(),
            immutable_hash=self._hash_event(payload),
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def query_audit_trail(
        self,
        entity_type: str,
        entity_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[models.AuditEvent]:
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        return (
            self.db.query(models.AuditEvent)
            .filter(
                models.AuditEvent.entity_type == entity_type,
                models.AuditEvent.entity_id == str(entity_id),
                models.AuditEvent.timestamp >= start_dt,
                models.AuditEvent.timestamp <= end_dt,
            )
            .order_by(models.AuditEvent.timestamp.desc())
            .all()
        )

    def generate_audit_report(self, company_id: UUID, period: str, audit_type: str) -> dict[str, Any]:
        year, month = [int(part) for part in period.split("-")]
        start_dt = datetime(year, month, 1)
        if month == 12:
            end_dt = datetime(year + 1, 1, 1)
        else:
            end_dt = datetime(year, month + 1, 1)

        q = self.db.query(models.AuditEvent).filter(
            models.AuditEvent.company_id == company_id,
            models.AuditEvent.timestamp >= start_dt,
            models.AuditEvent.timestamp < end_dt,
        )
        if audit_type and audit_type != "all":
            q = q.filter(models.AuditEvent.event_type == audit_type)

        rows = q.order_by(models.AuditEvent.timestamp.desc()).all()
        by_type: dict[str, int] = {}
        by_entity: dict[str, int] = {}
        for row in rows:
            by_type[row.event_type] = by_type.get(row.event_type, 0) + 1
            by_entity[row.entity_type] = by_entity.get(row.entity_type, 0) + 1

        return {
            "company_id": str(company_id),
            "period": period,
            "audit_type": audit_type,
            "event_count": len(rows),
            "by_type": by_type,
            "by_entity": by_entity,
            "events": [
                {
                    "id": str(row.id),
                    "event_type": row.event_type,
                    "entity_type": row.entity_type,
                    "entity_id": row.entity_id,
                    "user_id": row.user_id,
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                }
                for row in rows[:200]
            ],
        }
