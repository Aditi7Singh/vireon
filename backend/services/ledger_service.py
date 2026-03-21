from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List
from uuid import UUID

from sqlalchemy.orm import Session

import models


DEFAULT_INR_RATES: Dict[str, Decimal] = {
    "INR": Decimal("1"),
    "USD": Decimal("83.00"),
    "EUR": Decimal("90.00"),
    "GBP": Decimal("105.00"),
}


def _to_inr(db: Session, amount: Decimal | float | int, currency: str) -> Decimal:
    currency_code = (currency or "INR").upper()
    if currency_code == "INR":
        return Decimal(str(amount or 0))

    rate_row = (
        db.query(models.ExchangeRate)
        .filter(
            models.ExchangeRate.base_currency == currency_code,
            models.ExchangeRate.target_currency == "INR",
            models.ExchangeRate.status == "active",
        )
        .order_by(models.ExchangeRate.effective_date.desc())
        .first()
    )
    rate = Decimal(str(rate_row.exchange_rate)) if rate_row else DEFAULT_INR_RATES.get(currency_code, Decimal("1"))
    return Decimal(str(amount or 0)) * rate


def _expense_category(raw: str | None) -> models.LedgerCategory:
    value = (raw or "").lower()
    if any(k in value for k in ["aws", "cloud", "infra", "software", "saas"]):
        return models.LedgerCategory.TECH_COST
    if any(k in value for k in ["rent", "office", "internet", "utilities"]):
        return models.LedgerCategory.OFFICE_EXPENSE
    if any(k in value for k in ["marketing", "ad", "campaign", "event"]):
        return models.LedgerCategory.MARKETING
    if any(k in value for k in ["loan", "emi", "repayment"]):
        return models.LedgerCategory.LOAN_REPAYMENT
    return models.LedgerCategory.NON_TECH_COST


def _product_tag(text: str | None) -> models.LedgerProductTag:
    value = (text or "").lower()
    if "orchard" in value:
        return models.LedgerProductTag.ORCHARD
    if "sprouts" in value:
        return models.LedgerProductTag.SPROUTS
    if any(k in value for k in ["ai lab", "ai_lab", "ai"]):
        return models.LedgerProductTag.AI_LAB
    if "shared" in value:
        return models.LedgerProductTag.SHARED
    return models.LedgerProductTag.UNALLOCATED


def create_ledger_entry(db: Session, payload: dict) -> models.FinancialLedgerEntry:
    amount = Decimal(str(payload.get("amount", 0)))
    currency = (payload.get("currency") or "INR").upper()
    amount_inr = payload.get("amount_inr")
    if amount_inr is None:
        amount_inr = _to_inr(db, amount, currency)

    entry = models.FinancialLedgerEntry(
        company_id=payload["company_id"],
        transaction_date=payload["transaction_date"],
        amount=amount,
        currency=currency,
        amount_inr=Decimal(str(amount_inr)),
        entry_type=payload["entry_type"],
        category=payload["category"],
        product_tag=payload.get("product_tag", models.LedgerProductTag.UNALLOCATED),
        office_tag=payload.get("office_tag", models.LedgerOfficeTag.NA),
        source=payload.get("source", models.LedgerSource.SANDBOX),
        reference_id=payload.get("reference_id"),
        reference_type=payload.get("reference_type"),
        description=payload.get("description", ""),
        entered_by_role=payload.get("entered_by_role", models.LedgerEnteredByRole.SYSTEM),
        is_recurring=payload.get("is_recurring", False),
        tags=payload.get("tags"),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def sync_existing_to_ledger(company_id: UUID, db: Session) -> dict:
    """Backfill ledger from existing tables for one company."""
    created = 0

    expenses = db.query(models.Expense).filter(models.Expense.company_id == company_id).all()
    for exp in expenses:
        payload = {
            "company_id": company_id,
            "transaction_date": exp.transaction_date,
            "amount": exp.total_amount,
            "currency": exp.currency or "INR",
            "entry_type": models.LedgerEntryType.DEBIT,
            "category": _expense_category(exp.category),
            "product_tag": _product_tag((exp.memo or "") + " " + (exp.category or "")),
            "source": models.LedgerSource.ERPNEXT,
            "reference_id": str(exp.id),
            "reference_type": "expense",
            "description": exp.memo or f"Expense: {exp.category or 'non_tech_cost'}",
            "entered_by_role": models.LedgerEnteredByRole.SYSTEM,
            "is_recurring": False,
            "tags": {"payment_method": exp.payment_method, "legacy_category": exp.category},
        }
        create_ledger_entry(db, payload)
        created += 1

    invoices = db.query(models.Invoice).filter(models.Invoice.company_id == company_id).all()
    for inv in invoices:
        payload = {
            "company_id": company_id,
            "transaction_date": inv.issue_date,
            "amount": inv.total_amount,
            "currency": inv.currency or "INR",
            "entry_type": models.LedgerEntryType.CREDIT,
            "category": models.LedgerCategory.REVENUE,
            "product_tag": _product_tag(inv.memo),
            "source": models.LedgerSource.ERPNEXT,
            "reference_id": str(inv.id),
            "reference_type": "invoice",
            "description": inv.memo or f"Invoice {inv.invoice_number}",
            "entered_by_role": models.LedgerEnteredByRole.SYSTEM,
            "is_recurring": True,
            "tags": {"invoice_number": inv.invoice_number, "status": inv.status},
        }
        create_ledger_entry(db, payload)
        created += 1

    payroll_entries = (
        db.query(models.PayrollEntry)
        .join(models.Employee, models.Employee.id == models.PayrollEntry.employee_id)
        .filter(models.Employee.company_id == company_id)
        .all()
    )
    for pay in payroll_entries:
        payload = {
            "company_id": company_id,
            "transaction_date": pay.pay_date,
            "amount": pay.gross_pay,
            "currency": "INR",
            "entry_type": models.LedgerEntryType.DEBIT,
            "category": models.LedgerCategory.PAYROLL,
            "product_tag": models.LedgerProductTag.UNALLOCATED,
            "source": models.LedgerSource.SANDBOX,
            "reference_id": str(pay.id),
            "reference_type": "payroll",
            "description": "Payroll expense",
            "entered_by_role": models.LedgerEnteredByRole.SYSTEM,
            "is_recurring": True,
            "tags": {"net_pay": float(pay.net_pay)},
        }
        create_ledger_entry(db, payload)
        created += 1

    cloud_costs = (
        db.query(models.CloudCostDetail)
        .join(models.CloudAccount, models.CloudAccount.id == models.CloudCostDetail.account_id)
        .filter(models.CloudAccount.company_id == company_id)
        .all()
    )
    for cost in cloud_costs:
        payload = {
            "company_id": company_id,
            "transaction_date": cost.usage_date or date.today(),
            "amount": cost.amount,
            "currency": cost.currency or "USD",
            "entry_type": models.LedgerEntryType.DEBIT,
            "category": models.LedgerCategory.TECH_COST,
            "product_tag": models.LedgerProductTag.UNALLOCATED,
            "source": models.LedgerSource.AWS_BILLING,
            "reference_id": str(cost.id),
            "reference_type": "cloud_cost",
            "description": f"Cloud spend: {cost.service_name or 'service'}",
            "entered_by_role": models.LedgerEnteredByRole.SYSTEM,
            "is_recurring": True,
            "tags": {"region": cost.region, "service": cost.service_name},
        }
        create_ledger_entry(db, payload)
        created += 1

    return {
        "company_id": str(company_id),
        "synced_records": created,
        "synced_at": datetime.utcnow().isoformat(),
    }
