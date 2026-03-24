from __future__ import annotations

from datetime import date, datetime, timedelta
from enum import Enum
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import database
import models
import schemas
from services.ledger_service import create_ledger_entry

router = APIRouter(prefix="/inputs", tags=["inputs"])


class TechCostType(str, Enum):
    aws_compute = "aws_compute"
    aws_storage = "aws_storage"
    aws_other = "aws_other"
    software_license = "software_license"
    saas_tool = "saas_tool"
    infra_other = "infra_other"


class MarketingCostType(str, Enum):
    press_release = "press_release"
    podcast = "podcast"
    event = "event"
    ads = "ads"
    content = "content"
    agency = "agency"
    other = "other"


class OfficeExpenseType(str, Enum):
    rent = "rent"
    utilities = "utilities"
    internet = "internet"
    furniture = "furniture"
    equipment = "equipment"
    misc = "misc"


class OfficeInputTag(str, Enum):
    bengaluru = "bengaluru"
    gangavathi = "gangavathi"


class Department(str, Enum):
    engineering = "engineering"
    marketing = "marketing"
    operations = "operations"
    sales = "sales"
    design = "design"


class TechCostInput(BaseModel):
    company_id: UUID
    cost_type: TechCostType
    product_tag: schemas.LedgerProductTag
    amount_inr: float = Field(gt=0)
    billing_period: str
    vendor_name: str
    description: str
    is_recurring: bool = False


class MarketingCostInput(BaseModel):
    company_id: UUID
    cost_type: MarketingCostType
    product_tag: schemas.LedgerProductTag
    amount_inr: float = Field(gt=0)
    event_date: date
    vendor_name: str
    description: str
    expected_reach: Optional[int] = None


class OfficeExpenseInput(BaseModel):
    company_id: UUID
    expense_type: OfficeExpenseType
    office_tag: OfficeInputTag
    amount_inr: float = Field(gt=0)
    expense_date: date
    description: str
    is_recurring: bool = False


class HiringCostInput(BaseModel):
    company_id: UUID
    role_title: str
    department: Department
    product_tag: schemas.LedgerProductTag
    annual_ctc_inr: float = Field(gt=0)
    expected_join_date: date
    is_confirmed: bool
    description: str


def _require_role(actual: Optional[str], allowed: List[str]):
    role = (actual or "").lower()
    if role not in allowed:
        raise HTTPException(status_code=403, detail=f"Role {role or 'unknown'} cannot access this endpoint")


@router.post("/tech-cost", response_model=schemas.StandardWriteResponse)
def create_tech_cost(
    payload: TechCostInput,
    db: Session = Depends(database.get_db),
    x_user_role: Optional[str] = Header(None),
):
    _require_role(x_user_role, ["cto", "ceo"])
    entry = create_ledger_entry(
        db,
        {
            "company_id": payload.company_id,
            "transaction_date": datetime.strptime(payload.billing_period + "-01", "%Y-%m-%d").date(),
            "amount": payload.amount_inr,
            "currency": "INR",
            "amount_inr": payload.amount_inr,
            "entry_type": models.LedgerEntryType.DEBIT,
            "category": models.LedgerCategory.TECH_COST,
            "product_tag": payload.product_tag.value,
            "source": models.LedgerSource.MANUAL_CTO,
            "description": payload.description,
            "entered_by_role": models.LedgerEnteredByRole.CTO,
            "is_recurring": payload.is_recurring,
            "tags": {"cost_type": payload.cost_type.value, "vendor_name": payload.vendor_name, "billing_period": payload.billing_period},
        },
    )
    return {"success": True, "ledger_entry_id": str(entry.id), "message": "Tech cost entry created"}


@router.post("/marketing-cost", response_model=schemas.StandardWriteResponse)
def create_marketing_cost(
    payload: MarketingCostInput,
    db: Session = Depends(database.get_db),
    x_user_role: Optional[str] = Header(None),
):
    _require_role(x_user_role, ["marketing", "ceo"])
    entry = create_ledger_entry(
        db,
        {
            "company_id": payload.company_id,
            "transaction_date": payload.event_date,
            "amount": payload.amount_inr,
            "currency": "INR",
            "amount_inr": payload.amount_inr,
            "entry_type": models.LedgerEntryType.DEBIT,
            "category": models.LedgerCategory.MARKETING,
            "product_tag": payload.product_tag.value,
            "source": models.LedgerSource.MANUAL_MARKETING,
            "description": payload.description,
            "entered_by_role": models.LedgerEnteredByRole.MARKETING,
            "tags": {
                "cost_type": payload.cost_type.value,
                "vendor_name": payload.vendor_name,
                "expected_reach": payload.expected_reach,
            },
        },
    )
    return {"success": True, "ledger_entry_id": str(entry.id), "message": "Marketing cost entry created"}


@router.post("/office-expense", response_model=schemas.StandardWriteResponse)
def create_office_expense(
    payload: OfficeExpenseInput,
    db: Session = Depends(database.get_db),
    x_user_role: Optional[str] = Header(None),
):
    _require_role(x_user_role, ["finance", "ceo"])
    entry = create_ledger_entry(
        db,
        {
            "company_id": payload.company_id,
            "transaction_date": payload.expense_date,
            "amount": payload.amount_inr,
            "currency": "INR",
            "amount_inr": payload.amount_inr,
            "entry_type": models.LedgerEntryType.DEBIT,
            "category": models.LedgerCategory.OFFICE_EXPENSE,
            "office_tag": payload.office_tag.value,
            "source": models.LedgerSource.MANUAL_FINANCE,
            "description": payload.description,
            "entered_by_role": models.LedgerEnteredByRole.FINANCE,
            "is_recurring": payload.is_recurring,
            "tags": {"expense_type": payload.expense_type.value},
        },
    )
    return {"success": True, "ledger_entry_id": str(entry.id), "message": "Office expense entry created"}


@router.post("/hiring-cost", response_model=schemas.StandardWriteResponse)
def create_hiring_cost(
    payload: HiringCostInput,
    db: Session = Depends(database.get_db),
    x_user_role: Optional[str] = Header(None),
):
    _require_role(x_user_role, ["finance", "ceo"])
    monthly_cost = payload.annual_ctc_inr / 12
    entry = create_ledger_entry(
        db,
        {
            "company_id": payload.company_id,
            "transaction_date": payload.expected_join_date,
            "amount": monthly_cost,
            "currency": "INR",
            "amount_inr": monthly_cost,
            "entry_type": models.LedgerEntryType.DEBIT,
            "category": models.LedgerCategory.HIRING,
            "product_tag": payload.product_tag.value,
            "source": models.LedgerSource.MANUAL_FINANCE,
            "description": payload.description,
            "entered_by_role": models.LedgerEnteredByRole.FINANCE,
            "tags": {
                "role_title": payload.role_title,
                "department": payload.department.value,
                "annual_ctc_inr": payload.annual_ctc_inr,
                "monthly_cost": monthly_cost,
                "expected_join_date": payload.expected_join_date.isoformat(),
                "is_confirmed": payload.is_confirmed,
            },
        },
    )
    return {"success": True, "ledger_entry_id": str(entry.id), "message": "Hiring cost entry created"}


@router.get("/pending-review")
def pending_review(company_id: UUID, db: Session = Depends(database.get_db), x_user_role: Optional[str] = Header(None)):
    _require_role(x_user_role, ["finance", "ceo"])
    since = date.today() - timedelta(days=7)
    rows = (
        db.query(models.FinancialLedgerEntry)
        .filter(
            models.FinancialLedgerEntry.company_id == company_id,
            models.FinancialLedgerEntry.transaction_date >= since,
            models.FinancialLedgerEntry.source.in_(
                [
                    models.LedgerSource.MANUAL_CTO,
                    models.LedgerSource.MANUAL_MARKETING,
                    models.LedgerSource.MANUAL_FINANCE,
                ]
            ),
        )
        .order_by(models.FinancialLedgerEntry.created_at.desc())
        .all()
    )

    grouped: dict[str, list[dict]] = {}
    for r in rows:
        role = r.entered_by_role.value
        grouped.setdefault(role, []).append(
            {
                "id": str(r.id),
                "date": r.transaction_date.isoformat(),
                "category": r.category.value,
                "amount_inr": float(r.amount_inr),
                "description": r.description,
                "tags": r.tags or {},
            }
        )
    return {"company_id": str(company_id), "pending_review": grouped}
