from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from uuid import UUID

import auth
import database
import models
from services.workflow_approval_service import WorkflowApprovalService

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalStepInput(BaseModel):
    step_order: int
    approver_role: str
    min_amount: float = 0
    max_amount: Optional[float] = None
    parallel_group: Optional[str] = None
    escalation_hours: Optional[int] = None
    allow_delegation: bool = True


class WorkflowCreateRequest(BaseModel):
    company_id: UUID
    name: str
    steps: list[ApprovalStepInput]


class ApprovalSubmitRequest(BaseModel):
    workflow_id: UUID
    company_id: UUID
    amount: float
    requested_by: str
    reference_type: str = "finance_operation"
    reference_id: Optional[str] = None


class ApprovalActionRequest(BaseModel):
    action: str
    actor_id: str
    actor_role: str
    comments: Optional[str] = None
    delegated_to: Optional[str] = None


@router.post("/workflows")
def create_workflow(
    payload: WorkflowCreateRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    service = WorkflowApprovalService(db)
    workflow = service.create_workflow_template(
        payload.company_id,
        payload.name,
        [step.model_dump() for step in payload.steps],
    )
    return {"id": str(workflow.id), "name": workflow.name, "company_id": str(workflow.company_id)}


@router.get("/workflows/{company_id}")
def list_workflows(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    service = WorkflowApprovalService(db)
    rows = service.list_workflows(company_id)
    return [
        {
            "id": str(row.id),
            "name": row.name,
            "entity_type": row.entity_type,
            "is_active": row.is_active,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


@router.post("/requests")
def submit_request(
    payload: ApprovalSubmitRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    req = WorkflowApprovalService(db).submit_request(
        workflow_id=payload.workflow_id,
        company_id=payload.company_id,
        amount=payload.amount,
        requested_by=payload.requested_by,
        reference_type=payload.reference_type,
        reference_id=payload.reference_id,
    )
    return {"request_id": str(req.id), "status": req.status, "current_step_order": req.current_step_order}


@router.post("/requests/{request_id}/action")
def take_action(
    request_id: UUID,
    payload: ApprovalActionRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return WorkflowApprovalService(db).take_action(
        request_id=request_id,
        action=payload.action,
        actor_id=payload.actor_id,
        actor_role=payload.actor_role,
        comments=payload.comments,
        delegated_to=payload.delegated_to,
    )


@router.get("/queue/{company_id}")
def get_pending_queue(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return WorkflowApprovalService(db).get_pending_queue(company_id)
