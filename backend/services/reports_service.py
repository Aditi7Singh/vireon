import pandas as pd
from typing import List, Dict, Any
from io import StringIO, BytesIO
from sqlalchemy.orm import Session
import models

def generate_ledger_csv(db: Session, company_id: str) -> str:
    """Generate a CSV string for all ledger entries."""
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
    """Mock PDF generation logic using existing pdf_utils if available, or just a placeholder."""
    # Since we don't have a full PDF library like ReportLab or WeasyPrint easily configurable,
    # we'll return a BytesIO object with a placeholder or simple text.
    # In production, this would use a real PDF generator.
    buffer = BytesIO()
    buffer.write(b"Financial Summary Report\n")
    buffer.write(f"Company ID: {company_id}\n".encode())
    buffer.write(b"Generated on: 2026-03-22\n")
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
