from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List, Dict
from pydantic import BaseModel
from datetime import date
from pathlib import Path
import csv
import io

import models

import database
import auth
from services import reports_service

router = APIRouter(prefix="/reports", tags=["reports"])


class CustomReportRequest(BaseModel):
    company_id: UUID
    sections: List[str] = ["scorecard", "cash", "revenue", "expenses", "runway"]


class WarehouseExportRequest(BaseModel):
    company_id: UUID
    provider: str  # bigquery | snowflake
    dataset: str = "vireon"
    table: str = "financial_ledger_entries"

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


@router.get("/pl/consolidated-group")
def get_group_consolidated_pl(
    company_ids: Optional[str] = None,
    apply_eliminations: bool = Query(default=True),
    elimination_mode: str = Query(default="tag_or_keyword", pattern="^(tag_or_keyword|tag_only|keyword_only)$"),
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user),
):
    parsed_ids = None
    if company_ids:
        raw_ids = [cid.strip() for cid in company_ids.split(",") if cid.strip()]
        try:
            parsed_ids = [UUID(cid) for cid in raw_ids]
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid company_ids value: {exc}") from exc

    return reports_service.generate_group_consolidated_pl(
        db,
        parsed_ids,
        apply_eliminations=apply_eliminations,
        elimination_mode=elimination_mode,
    )


@router.post("/custom/build")
def build_custom_report(
    payload: CustomReportRequest,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user),
):
    """Build a composable report payload from selected sections."""
    latest_metric = (
        db.query(models.MonthlyMetric)
        .filter(models.MonthlyMetric.company_id == payload.company_id)
        .order_by(models.MonthlyMetric.metric_month.desc())
        .first()
    )

    section_data: Dict[str, object] = {}
    section_set = set(payload.sections)

    if "scorecard" in section_set:
        if latest_metric:
            revenue = float(latest_metric.total_revenue or 0)
            expenses = float(latest_metric.total_expenses or 0)
            section_data["scorecard"] = {
                "cash": float(latest_metric.ending_cash or 0),
                "revenue": revenue,
                "expenses": expenses,
                "net_burn": expenses - revenue,
                "runway_months": float(latest_metric.runway_months or 0),
            }
        else:
            section_data["scorecard"] = {}

    if "cash" in section_set:
        section_data["cash"] = {
            "ending_cash": float(latest_metric.ending_cash or 0) if latest_metric else 0.0,
            "as_of": latest_metric.metric_month.isoformat() if latest_metric else None,
        }

    if "revenue" in section_set:
        section_data["revenue"] = {
            "mrr": float(latest_metric.total_revenue or 0) if latest_metric else 0.0,
            "arr": float(latest_metric.total_revenue or 0) * 12 if latest_metric else 0.0,
        }

    if "expenses" in section_set:
        section_data["expenses"] = {
            "total": float(latest_metric.total_expenses or 0) if latest_metric else 0.0,
        }

    if "runway" in section_set:
        section_data["runway"] = {
            "months": float(latest_metric.runway_months or 0) if latest_metric else 0.0,
        }

    if "collections" in section_set:
        open_ar = sum(
            float(x[0] or 0)
            for x in db.query(models.Invoice.amount_due)
            .filter(
                models.Invoice.company_id == payload.company_id,
                models.Invoice.type == "ACCOUNTS_RECEIVABLE",
                models.Invoice.amount_due > 0,
            )
            .all()
        )
        open_ap = sum(
            float(x[0] or 0)
            for x in db.query(models.Invoice.amount_due)
            .filter(
                models.Invoice.company_id == payload.company_id,
                models.Invoice.type == "ACCOUNTS_PAYABLE",
                models.Invoice.amount_due > 0,
            )
            .all()
        )
        section_data["collections"] = {"open_ar": round(open_ar, 2), "open_ap": round(open_ap, 2)}

    return {
        "company_id": str(payload.company_id),
        "generated_at": date.today().isoformat(),
        "sections": payload.sections,
        "data": section_data,
    }


@router.post("/export/warehouse")
def export_to_warehouse(
    payload: WarehouseExportRequest,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user),
):
    """Export ledger rows to provider-compatible CSV payload for BigQuery/Snowflake ingestion."""
    provider = (payload.provider or "").strip().lower()
    if provider not in {"bigquery", "snowflake"}:
        raise HTTPException(status_code=400, detail="provider must be one of: bigquery, snowflake")

    rows = (
        db.query(models.FinancialLedgerEntry)
        .filter(models.FinancialLedgerEntry.company_id == payload.company_id)
        .order_by(models.FinancialLedgerEntry.transaction_date.asc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id",
        "company_id",
        "transaction_date",
        "amount",
        "currency",
        "amount_inr",
        "entry_type",
        "category",
        "description",
        "source",
        "created_at",
    ])
    for r in rows:
        writer.writerow([
            str(r.id),
            str(r.company_id),
            r.transaction_date.isoformat() if r.transaction_date else None,
            float(r.amount or 0),
            r.currency,
            float(r.amount_inr or 0),
            r.entry_type.value if hasattr(r.entry_type, "value") else str(r.entry_type),
            r.category.value if hasattr(r.category, "value") else str(r.category),
            r.description,
            r.source.value if hasattr(r.source, "value") else str(r.source),
            r.created_at.isoformat() if r.created_at else None,
        ])

    exports_dir = Path(__file__).resolve().parents[2] / "data" / "warehouse_exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    file_path = exports_dir / f"{provider}_{payload.dataset}_{payload.table}_{payload.company_id}.csv"
    file_path.write_text(output.getvalue(), encoding="utf-8")

    return {
        "success": True,
        "provider": provider,
        "dataset": payload.dataset,
        "table": payload.table,
        "rows_exported": len(rows),
        "file_path": str(file_path),
        "next_steps": [
            "Upload this CSV to your warehouse staging bucket.",
            "Run COPY/LOAD command into target table.",
            "Schedule this endpoint via Celery for periodic exports.",
        ],
    }
