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


@router.get("/margin/{company_id}")
def gross_margin(company_id: UUID, month: str, db: Session = Depends(database.get_db)):
    """Server-side gross margin calculated from GL accounts + expense COGS."""
    from services.margin_service import calculate_server_side_margin
    from datetime import datetime
    month_date = datetime.strptime(month, "%Y-%m").date()
    return calculate_server_side_margin(db, company_id, month_date)


@router.get("/margin/{company_id}/by-product")
def product_margin(company_id: UUID, month: str, db: Session = Depends(database.get_db)):
    """Per-product gross margin breakdown."""
    from services.margin_service import calculate_product_margin
    from datetime import datetime
    month_date = datetime.strptime(month, "%Y-%m").date()
    return calculate_product_margin(db, company_id, month_date)


@router.get("/margin/{company_id}/alerts")
def margin_alerts(company_id: UUID, month: str, threshold: float = 50.0, db: Session = Depends(database.get_db)):
    """Alerts when margin drops below threshold."""
    from services.margin_service import check_margin_alerts
    from datetime import datetime
    month_date = datetime.strptime(month, "%Y-%m").date()
    return check_margin_alerts(db, company_id, month_date, threshold)

