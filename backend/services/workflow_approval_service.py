from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

import models


class WorkflowApprovalService:
    def __init__(self, db: Session):
        self.db = db

    def create_workflow_template(self, company_id: UUID, name: str, steps: list[dict[str, Any]]) -> models.ApprovalWorkflow:
        workflow = models.ApprovalWorkflow(company_id=company_id, name=name, entity_type="finance_operation")
        self.db.add(workflow)
        self.db.flush()

        for idx, step in enumerate(steps, start=1):
            self.db.add(
                models.ApprovalStep(
                    workflow_id=workflow.id,
                    step_order=step.get("step_order", idx),
                    approver_role=step["approver_role"],
                    min_amount=Decimal(str(step.get("min_amount", 0))),
                    max_amount=Decimal(str(step["max_amount"])) if step.get("max_amount") is not None else None,
                    parallel_group=step.get("parallel_group"),
                    escalation_hours=step.get("escalation_hours"),
                    allow_delegation=bool(step.get("allow_delegation", True)),
                )
            )

        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def list_workflows(self, company_id: UUID) -> list[models.ApprovalWorkflow]:
        return (
            self.db.query(models.ApprovalWorkflow)
            .filter(models.ApprovalWorkflow.company_id == company_id)
            .order_by(models.ApprovalWorkflow.created_at.desc())
            .all()
        )

    def get_workflow_steps_for_amount(self, workflow_id: UUID, amount: float) -> list[models.ApprovalStep]:
        value = Decimal(str(amount))
        all_steps = (
            self.db.query(models.ApprovalStep)
            .filter(models.ApprovalStep.workflow_id == workflow_id)
            .order_by(models.ApprovalStep.step_order.asc())
            .all()
        )
        if not all_steps:
            return []

        applicable: list[models.ApprovalStep] = []
        for step in all_steps:
            min_ok = value >= Decimal(str(step.min_amount or 0))
            max_ok = step.max_amount is None or value <= Decimal(str(step.max_amount))
            if min_ok and max_ok:
                applicable.append(step)

        return applicable if applicable else all_steps

    def submit_request(
        self,
        workflow_id: UUID,
        company_id: UUID,
        amount: float,
        requested_by: str,
        reference_type: str = "finance_operation",
        reference_id: Optional[str] = None,
    ) -> models.ApprovalRequest:
        steps = self.get_workflow_steps_for_amount(workflow_id, amount)
        due_at = datetime.utcnow() + timedelta(hours=max([s.escalation_hours or 24 for s in steps] or [24]))

        req = models.ApprovalRequest(
            workflow_id=workflow_id,
            company_id=company_id,
            reference_type=reference_type,
            reference_id=reference_id,
            amount=Decimal(str(amount)),
            status="pending",
            current_step_order=min([s.step_order for s in steps] or [1]),
            requested_by=requested_by,
            due_at=due_at,
        )
        self.db.add(req)
        self.db.commit()
        self.db.refresh(req)
        return req

    def take_action(
        self,
        request_id: UUID,
        action: str,
        actor_id: str,
        actor_role: str,
        comments: Optional[str] = None,
        delegated_to: Optional[str] = None,
    ) -> dict[str, Any]:
        req = self.db.query(models.ApprovalRequest).filter(models.ApprovalRequest.id == request_id).first()
        if not req:
            return {"success": False, "message": "Approval request not found"}

        normalized_action = action.lower().strip()
        if normalized_action not in {"approve", "reject", "delegate"}:
            return {"success": False, "message": "Invalid action"}

        self.db.add(
            models.ApprovalAction(
                request_id=req.id,
                action=normalized_action,
                actor_id=actor_id,
                actor_role=actor_role,
                comments=comments,
                delegated_to=delegated_to,
            )
        )

        if normalized_action == "reject":
            req.status = "rejected"
        elif normalized_action == "delegate":
            req.status = "delegated"
        else:
            steps = self.get_workflow_steps_for_amount(req.workflow_id, float(req.amount or 0))
            max_step = max([s.step_order for s in steps] or [req.current_step_order])
            if req.current_step_order >= max_step:
                req.status = "approved"
            else:
                req.current_step_order += 1
                req.status = "pending"

        self.db.commit()
        return {
            "success": True,
            "request_id": str(req.id),
            "status": req.status,
            "current_step_order": req.current_step_order,
        }

    def get_pending_queue(self, company_id: UUID) -> list[dict[str, Any]]:
        rows = (
            self.db.query(models.ApprovalRequest)
            .filter(models.ApprovalRequest.company_id == company_id, models.ApprovalRequest.status.in_(["pending", "delegated"]))
            .order_by(models.ApprovalRequest.created_at.asc())
            .all()
        )
        return [
            {
                "request_id": str(row.id),
                "workflow_id": str(row.workflow_id),
                "amount": float(row.amount or 0),
                "status": row.status,
                "current_step_order": row.current_step_order,
                "due_at": row.due_at.isoformat() if row.due_at else None,
            }
            for row in rows
        ]
