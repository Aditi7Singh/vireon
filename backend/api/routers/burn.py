from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import database
from services import burn_service

router = APIRouter(prefix="/burn", tags=["burn"])


@router.get("/summary/{company_id}")
def burn_summary(company_id: UUID, month: str, db: Session = Depends(database.get_db)):
    return burn_service.get_net_burn(company_id, db, month)


@router.get("/multiple/{company_id}")
def burn_multiple(company_id: UUID, month: str, db: Session = Depends(database.get_db)):
    return burn_service.get_burn_multiple(company_id, db, month)


@router.get("/products/{company_id}")
def product_pl(company_id: UUID, month: str, db: Session = Depends(database.get_db)):
    return burn_service.get_product_pl(company_id, db, month)


@router.get("/expenses/{company_id}")
def expense_breakdown(company_id: UUID, month: str, db: Session = Depends(database.get_db)):
    return burn_service.get_expense_breakdown(company_id, db, month)


@router.get("/headcount/{company_id}")
def headcount(company_id: UUID, db: Session = Depends(database.get_db)):
    return burn_service.get_headcount_costs(company_id, db)


@router.get("/dashboard/{company_id}")
def dashboard(company_id: UUID, month: str, db: Session = Depends(database.get_db)):
    return {
        "summary": burn_service.get_net_burn(company_id, db, month),
        "multiple": burn_service.get_burn_multiple(company_id, db, month),
        "products": burn_service.get_product_pl(company_id, db, month),
        "expenses": burn_service.get_expense_breakdown(company_id, db, month),
        "headcount": burn_service.get_headcount_costs(company_id, db),
    }
