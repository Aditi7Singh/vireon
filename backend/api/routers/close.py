from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import UUID

import auth
import database
import models
from services.close_service import CloseService

router = APIRouter(prefix="/close", tags=["close"])


class CloseRequest(BaseModel):
    company_id: UUID
    period: str


class LockPeriodRequest(BaseModel):
    company_id: UUID
    period: str
    user_id: UUID


class IntercompanyEliminationRequest(BaseModel):
    company_ids: list[UUID]
    period: str


@router.post("/validate")
def validate_close_readiness(
    payload: CloseRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return CloseService(db).validate_close_readiness(payload.company_id, payload.period)


@router.post("/accruals")
def calculate_accruals(
    payload: CloseRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return CloseService(db).calculate_accruals(payload.company_id, payload.period)


@router.post("/intercompany-elimination")
def run_intercompany_elimination(
    payload: IntercompanyEliminationRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return CloseService(db).run_intercompany_elimination(payload.company_ids, payload.period)


@router.post("/lock")
def lock_period(
    payload: LockPeriodRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return CloseService(db).lock_period(payload.company_id, payload.period, payload.user_id)


@router.get("/status/{company_id}")
def get_close_status(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return CloseService(db).get_close_status(company_id)
