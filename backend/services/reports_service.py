from __future__ import annotations

import pandas as pd
from typing import List, Dict, Any, Optional
from io import StringIO, BytesIO
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
import models


def _is_intercompany_entry(entry: models.FinancialLedgerEntry, elimination_mode: str) -> bool:
    """Detect intercompany entries using tags and/or description keyword hints."""
    tags = entry.tags or {}
    has_tag_marker = bool(tags.get("intercompany") or tags.get("intercompany_counterparty_company_id"))
    has_keyword_marker = "intercompany" in (entry.description or "").lower()

    mode = (elimination_mode or "tag_or_keyword").lower()
    if mode == "tag_only":
        return has_tag_marker
    if mode == "keyword_only":
        return has_keyword_marker
    return has_tag_marker or has_keyword_marker

def generate_ledger_csv(db: Session, company_id: str) -> str:
    """Generate a CSV string for all ledger entries."""
    if isinstance(company_id, str):
        company_id = uuid.UUID(company_id)

    entries = db.query(models.FinancialLedgerEntry).filter(
        models.FinancialLedgerEntry.company_id == company_id
    ).order_by(models.FinancialLedgerEntry.transaction_date.desc()).all()
    
    data = []
    for e in entries:
        data.append({
            "Date": e.transaction_date,
            "Description": e.description,
            "Amount": float(e.amount),
            "Currency": e.currency,
            "Category": e.category.value if hasattr(e.category, "value") else str(e.category),
            "Department": e.department or "N/A",
            "Product": e.product_tag.value if hasattr(e.product_tag, "value") else str(e.product_tag),
            "Type": e.entry_type.value if hasattr(e.entry_type, "value") else str(e.entry_type),
            "Office": e.office_tag.value if hasattr(e.office_tag, "value") else str(e.office_tag)
        })
    
    df = pd.DataFrame(data)
    output = StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()

def generate_financial_summary_pdf(db: Session, company_id: str) -> BytesIO:
    """Generate a compact PDF summary using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    if isinstance(company_id, str):
        company_id = uuid.UUID(company_id)

    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    latest = (
        db.query(models.MonthlyMetric)
        .filter(models.MonthlyMetric.company_id == company_id)
        .order_by(models.MonthlyMetric.metric_month.desc())
        .first()
    )

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 48

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, y, "Vireon Financial Summary")
    y -= 22
    pdf.setFont("Helvetica", 10)
    pdf.drawString(40, y, f"Generated at: {pd.Timestamp.now('UTC').isoformat()}")
    y -= 16
    pdf.drawString(40, y, f"Company: {company.name if company else company_id}")
    y -= 24

    if latest:
        lines = [
            f"Metric Month: {latest.metric_month.isoformat()}",
            f"Revenue: INR {float(latest.total_revenue or 0):,.2f}",
            f"Expenses: INR {float(latest.total_expenses or 0):,.2f}",
            f"Burn Rate: INR {float(latest.burn_rate or 0):,.2f}",
            f"Ending Cash: INR {float(latest.ending_cash or 0):,.2f}",
            f"Runway Months: {float(latest.runway_months or 0):.1f}",
        ]
    else:
        lines = ["No monthly metrics found for this company."]

    for line in lines:
        pdf.drawString(40, y, line)
        y -= 16

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer
def generate_multi_currency_pl(db: Session, company_id: str) -> List[Dict[str, Any]]:
    """
    Consolidated P&L report aggregating all ledger entries.
    Shows totals in INR while tracking source currencies.
    """
    import uuid
    if isinstance(company_id, str):
        company_id = uuid.UUID(company_id)
    from sqlalchemy import func
    
    # Aggregate by Category and Currency
    results = db.query(
        models.FinancialLedgerEntry.category,
        models.FinancialLedgerEntry.currency,
        func.sum(models.FinancialLedgerEntry.amount).label("amount_original"),
        func.sum(models.FinancialLedgerEntry.amount_inr).label("amount_inr")
    ).filter(
        models.FinancialLedgerEntry.company_id == company_id
    ).group_by(
        models.FinancialLedgerEntry.category,
        models.FinancialLedgerEntry.currency
    ).all()
    
    pl_data = []
    for r in results:
        pl_data.append({
            "category": r.category.value if hasattr(r.category, "value") else str(r.category),
            "currency": r.currency,
            "original_amount": float(r.amount_original),
            "amount_inr": float(r.amount_inr)
        })
    
    return pl_data


def generate_group_consolidated_pl(
    db: Session,
    company_ids: Optional[List[str]] = None,
    apply_eliminations: bool = True,
    elimination_mode: str = "tag_or_keyword",
) -> Dict[str, Any]:
    """Consolidate P&L across multiple companies in INR with optional intercompany elimination."""
    query = db.query(models.FinancialLedgerEntry)
    if company_ids:
        query = query.filter(models.FinancialLedgerEntry.company_id.in_(company_ids))

    entries = query.all()

    by_company: Dict[str, Dict[str, float]] = {}
    eliminated_by_company: Dict[str, float] = {}
    total_revenue = 0.0
    total_expense = 0.0
    eliminated_total = 0.0
    eliminated_entries = 0

    for entry in entries:
        cid = str(entry.company_id)
        by_company.setdefault(cid, {"revenue_inr": 0.0, "expense_inr": 0.0})

        amount = float(entry.amount_inr or 0)
        is_eliminated = apply_eliminations and _is_intercompany_entry(entry, elimination_mode)
        if is_eliminated:
            eliminated_entries += 1
            eliminated_total += amount
            eliminated_by_company[cid] = eliminated_by_company.get(cid, 0.0) + amount
            continue

        if entry.entry_type == models.LedgerEntryType.CREDIT:
            by_company[cid]["revenue_inr"] += amount
            total_revenue += amount
        else:
            by_company[cid]["expense_inr"] += amount
            total_expense += amount

    return {
        "company_count": len(by_company),
        "by_company": by_company,
        "consolidated_revenue_inr": total_revenue,
        "consolidated_expense_inr": total_expense,
        "consolidated_net_profit_inr": total_revenue - total_expense,
        "eliminations_applied": apply_eliminations,
        "elimination_mode": elimination_mode,
        "eliminated_entries": eliminated_entries,
        "eliminated_total_inr": eliminated_total,
        "eliminated_by_company": eliminated_by_company,
    }
