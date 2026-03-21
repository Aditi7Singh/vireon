from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

import models


def _month_bounds(month: str):
    start = datetime.strptime(month, "%Y-%m").date().replace(day=1)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def _query_month(company_id: UUID, db: Session, month: str):
    start, end = _month_bounds(month)
    return db.query(models.FinancialLedgerEntry).filter(
        models.FinancialLedgerEntry.company_id == company_id,
        models.FinancialLedgerEntry.transaction_date >= start,
        models.FinancialLedgerEntry.transaction_date < end,
    )


def get_net_burn(company_id: UUID, db: Session, month: str) -> dict:
    rows = _query_month(company_id, db, month).all()
    total_credits = sum(float(r.amount_inr) for r in rows if r.entry_type == models.LedgerEntryType.CREDIT)
    total_debits = sum(float(r.amount_inr) for r in rows if r.entry_type == models.LedgerEntryType.DEBIT)
    net_burn = total_debits - total_credits

    categories = [
        models.LedgerCategory.TECH_COST,
        models.LedgerCategory.MARKETING,
        models.LedgerCategory.PAYROLL,
        models.LedgerCategory.OFFICE_EXPENSE,
        models.LedgerCategory.HIRING,
        models.LedgerCategory.MISC,
    ]
    breakdown = {c.value: 0.0 for c in categories}
    for r in rows:
        if r.entry_type == models.LedgerEntryType.DEBIT and r.category in categories:
            breakdown[r.category.value] += float(r.amount_inr)

    prev_month = (datetime.strptime(month, "%Y-%m") - timedelta(days=1)).strftime("%Y-%m")
    prev_rows = _query_month(company_id, db, prev_month).all()
    prev_net = sum(float(r.amount_inr) for r in prev_rows if r.entry_type == models.LedgerEntryType.DEBIT) - sum(
        float(r.amount_inr) for r in prev_rows if r.entry_type == models.LedgerEntryType.CREDIT
    )
    mom_change_pct = ((net_burn - prev_net) / prev_net * 100) if prev_net else 0.0

    return {
        "total_credits": total_credits,
        "total_debits": total_debits,
        "net_burn": net_burn,
        "breakdown_by_category": breakdown,
        "mom_change_pct": mom_change_pct,
    }


def get_burn_multiple(company_id: UUID, db: Session, month: str) -> dict:
    burn = get_net_burn(company_id, db, month)
    start, end = _month_bounds(month)

    new_arr = (
        db.query(func.sum(models.Invoice.total_amount))
        .filter(
            models.Invoice.company_id == company_id,
            models.Invoice.issue_date >= start,
            models.Invoice.issue_date < end,
        )
        .scalar()
        or 0
    )
    new_arr = float(new_arr) * 12

    burn_multiple = burn["net_burn"] / new_arr if new_arr else 0.0
    interpretation = "great" if burn_multiple < 1 else "ok" if burn_multiple <= 1.5 else "concerning"
    return {
        "burn_multiple": burn_multiple,
        "net_burn": burn["net_burn"],
        "new_arr": new_arr,
        "interpretation": interpretation,
    }


def get_product_pl(company_id: UUID, db: Session, month: str) -> dict:
    rows = _query_month(company_id, db, month).all()
    products = ["orchard", "sprouts", "ai_lab", "shared"]
    data = {p: {"total_revenue": 0.0, "total_cost": 0.0} for p in products}

    for r in rows:
        p = r.product_tag.value if hasattr(r.product_tag, "value") else str(r.product_tag)
        if p not in data:
            p = "shared"
        if r.entry_type == models.LedgerEntryType.CREDIT:
            data[p]["total_revenue"] += float(r.amount_inr)
        else:
            data[p]["total_cost"] += float(r.amount_inr)

    # Split shared cost equally into product views
    shared_cost = data["shared"]["total_cost"]
    for p in ["orchard", "sprouts", "ai_lab"]:
        data[p]["total_cost"] += shared_cost / 3 if shared_cost else 0

    for p in products:
        revenue = data[p]["total_revenue"]
        cost = data[p]["total_cost"]
        margin = revenue - cost
        data[p]["gross_margin"] = margin
        data[p]["gross_margin_pct"] = (margin / revenue * 100) if revenue else 0.0

    return data


def get_expense_breakdown(company_id: UUID, db: Session, month: str) -> dict:
    rows = [r for r in _query_month(company_id, db, month).all() if r.entry_type == models.LedgerEntryType.DEBIT]
    tech_rows = [r for r in rows if r.category == models.LedgerCategory.TECH_COST]
    non_tech = [r for r in rows if r.category in [models.LedgerCategory.MARKETING, models.LedgerCategory.OFFICE_EXPENSE, models.LedgerCategory.MISC]]

    by_product = {"orchard": 0.0, "sprouts": 0.0, "ai_lab": 0.0}
    for r in tech_rows:
        key = r.product_tag.value if hasattr(r.product_tag, "value") else str(r.product_tag)
        if key in by_product:
            by_product[key] += float(r.amount_inr)

    payroll_rows = [r for r in rows if r.category == models.LedgerCategory.PAYROLL]
    employees = db.query(models.Employee).filter(models.Employee.company_id == company_id, models.Employee.status == "active").all()
    recurring = sum(float(r.amount_inr) for r in rows if r.is_recurring)
    one_off = sum(float(r.amount_inr) for r in rows if not r.is_recurring)

    return {
        "tech_costs": {
            "aws_total": sum(float(r.amount_inr) for r in tech_rows if (r.tags or {}).get("cost_type", "").startswith("aws")),
            "licenses_total": sum(float(r.amount_inr) for r in tech_rows if "license" in ((r.tags or {}).get("cost_type", ""))),
            "saas_total": sum(float(r.amount_inr) for r in tech_rows if "saas" in ((r.tags or {}).get("cost_type", ""))),
            "by_product": by_product,
        },
        "non_tech_costs": {
            "marketing": sum(float(r.amount_inr) for r in non_tech if r.category == models.LedgerCategory.MARKETING),
            "office_bengaluru": sum(float(r.amount_inr) for r in non_tech if (r.office_tag == models.LedgerOfficeTag.BENGALURU)),
            "office_gangavathi": sum(float(r.amount_inr) for r in non_tech if (r.office_tag == models.LedgerOfficeTag.GANGAVATHI)),
            "misc": sum(float(r.amount_inr) for r in non_tech if r.category == models.LedgerCategory.MISC),
        },
        "payroll": {
            "total": sum(float(r.amount_inr) for r in payroll_rows),
            "by_department": {},
        },
        "overhead": {
            "per_employee_cost": (sum(float(r.amount_inr) for r in rows) / len(employees)) if employees else 0.0,
            "total_headcount": len(employees),
        },
        "one_off_vs_recurring": {"recurring": recurring, "one_off": one_off},
    }


def get_headcount_costs(company_id: UUID, db: Session) -> dict:
    employees = db.query(models.Employee).filter(models.Employee.company_id == company_id, models.Employee.status == "active").all()
    payroll_monthly = (
        db.query(func.sum(models.PayrollEntry.gross_pay))
        .join(models.Employee, models.Employee.id == models.PayrollEntry.employee_id)
        .filter(models.Employee.company_id == company_id)
        .scalar()
        or 0
    )

    pending = (
        db.query(models.FinancialLedgerEntry)
        .filter(
            models.FinancialLedgerEntry.company_id == company_id,
            models.FinancialLedgerEntry.category == models.LedgerCategory.HIRING,
            models.FinancialLedgerEntry.entry_type == models.LedgerEntryType.DEBIT,
        )
        .all()
    )
    pending_hires = []
    total_committed = float(payroll_monthly)
    for item in pending:
        tags = item.tags or {}
        if tags.get("is_confirmed") is False:
            monthly_cost = float(tags.get("monthly_cost", 0))
            pending_hires.append(
                {
                    "role": tags.get("role_title", "Unknown"),
                    "department": tags.get("department", "Unknown"),
                    "product": item.product_tag.value,
                    "monthly_cost": monthly_cost,
                    "join_date": tags.get("expected_join_date"),
                }
            )
            total_committed += monthly_cost

    return {
        "current_headcount": len(employees),
        "monthly_payroll_inr": float(payroll_monthly),
        "pending_hires": pending_hires,
        "total_committed_monthly_cost": total_committed,
    }
