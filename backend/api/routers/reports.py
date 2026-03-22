from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from uuid import UUID

import database
import auth
from services import reports_service

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/export/ledger/csv")
def export_ledger_csv(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Export all ledger entries to CSV."""
    csv_content = reports_service.generate_ledger_csv(db, str(company_id))
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=ledger_export_{company_id}.csv"}
    )

@router.get("/export/summary/pdf")
def export_summary_pdf(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Export a high-level financial summary to PDF (Mock)."""
    pdf_buffer = reports_service.generate_financial_summary_pdf(db, str(company_id))
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=financial_summary_{company_id}.pdf"}
    )
@router.get("/pl/multi-currency")
def get_multi_currency_pl(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Retrieve consolidated P&L report with multi-currency breakdown."""
    return reports_service.generate_multi_currency_pl(db, str(company_id))
