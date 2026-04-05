from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import UUID

import auth
import database
import models
from services.consolidation_service import ConsolidationService

router = APIRouter(prefix="/consolidation", tags=["consolidation"])


class AddSubsidiaryRequest(BaseModel):
    parent_id: UUID
    subsidiary_id: UUID


class ConsolidationRequest(BaseModel):
    company_ids: list[UUID]
    period: str


class CurrencyTranslationRequest(BaseModel):
    amounts: dict[str, float]
    target_currency: str


@router.post("/hierarchy/subsidiary")
def add_subsidiary(
    payload: AddSubsidiaryRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return ConsolidationService(db).add_subsidiary(payload.parent_id, payload.subsidiary_id)


@router.post("/intercompany/match")
def match_intercompany_transactions(
    payload: ConsolidationRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return ConsolidationService(db).match_intercompany_transactions(payload.company_ids, payload.period)


@router.post("/currency/translate")
def translate_to_base_currency(
    payload: CurrencyTranslationRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return ConsolidationService(db).translate_to_base_currency(payload.amounts, payload.target_currency)


@router.post("/balance-sheet")
def consolidated_balance_sheet(
    payload: ConsolidationRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return ConsolidationService(db).generate_consolidated_balance_sheet(payload.company_ids, payload.period)


@router.post("/pnl")
def consolidated_pnl(
    payload: ConsolidationRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return ConsolidationService(db).generate_consolidated_pnl(payload.company_ids, payload.period)


@router.post("/snapshot")
def snapshot_consolidation(
    payload: ConsolidationRequest,
    target_currency: str = "INR",
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return ConsolidationService(db).snapshot_consolidation(payload.company_ids, payload.period, target_currency)
