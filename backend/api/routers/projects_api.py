from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

import auth
import database
import models

router = APIRouter(prefix="/projects", tags=["projects"])

# ─── Project Registry ─────────────────────────────────────────────────────────

PROJECT_REGISTRY = {
    "sprouts": {
        "name": "Sprout",
        "tagline": "AI-powered crop monitoring for small & mid-size farms",
        "stage": "Growth",
        "stage_color": "green",
        "location": "Gangavathi, Karnataka",
        "color": "#16a34a",
        "accent": "#f0fdf4",
        "budget_annual_inr": 12_000_000,
        "headcount_target": 12,
        "arr_target_inr": 8_400_000,
        "departments": ["engineering", "product", "sprout"],
    },
    "orchard": {
        "name": "Orchard",
        "tagline": "Enterprise agri-analytics & supply chain intelligence",
        "stage": "Scaling",
        "stage_color": "orange",
        "location": "Bengaluru, Karnataka",
        "color": "#ea580c",
        "accent": "#fff7ed",
        "budget_annual_inr": 16_800_000,
        "headcount_target": 18,
        "arr_target_inr": 12_000_000,
        "departments": ["sales", "operations", "orchard"],
    },
    "ai_lab": {
        "name": "AI Lab",
        "tagline": "Foundation models for agricultural intelligence & prediction",
        "stage": "Incubation",
        "stage_color": "purple",
        "location": "Remote / Global",
        "color": "#7c3aed",
        "accent": "#faf5ff",
        "budget_annual_inr": 8_400_000,
        "headcount_target": 8,
        "arr_target_inr": 4_560_000,
        "departments": ["ai_research", "platform", "ai_lab"],
    },
}

# Demo fallback values shown when live DB has sparse data
_DEMO = {
    "sprouts":  {"revenue": 620_000, "payroll": 890_000, "infra": 85_000, "other": 65_000,  "headcount": 11},
    "orchard":  {"revenue": 710_000, "payroll": 960_000, "infra": 120_000, "other": 80_000, "headcount": 15},
    "ai_lab":   {"revenue": 380_000, "payroll": 730_000, "infra": 320_000, "other": 45_000, "headcount": 7},
}

# Monthly growth seed for 6-month trend (index 0 = 5 months ago, 5 = current)
_GROWTH = [0.68, 0.74, 0.81, 0.88, 0.95, 1.00]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _ledger_sum(
    db: Session,
    company_id,
    tag: str,
    entry_type: models.LedgerEntryType,
    categories: list[str] | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> float:
    q = db.query(func.coalesce(func.sum(models.FinancialLedgerEntry.amount), 0)).filter(
        models.FinancialLedgerEntry.company_id == company_id,
        models.FinancialLedgerEntry.product_tag == tag,
        models.FinancialLedgerEntry.entry_type == entry_type,
    )
    if categories:
        q = q.filter(models.FinancialLedgerEntry.category.in_(categories))
    if date_from:
        q = q.filter(models.FinancialLedgerEntry.transaction_date >= date_from)
    if date_to:
        q = q.filter(models.FinancialLedgerEntry.transaction_date < date_to)
    return float(q.scalar() or 0)


def _headcount(db: Session, company_id, departments: list[str]) -> int:
    return db.query(func.count(models.Employee.id)).filter(
        models.Employee.company_id == company_id,
        models.Employee.department.in_(departments),
        models.Employee.status == "active",
    ).scalar() or 0


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/overview")
def get_projects_overview(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    company = db.query(models.Company).first()
    projects_out = []

    for tag, meta in PROJECT_REGISTRY.items():
        fb = _DEMO[tag]

        if company:
            revenue = _ledger_sum(db, company.id, tag, models.LedgerEntryType.CREDIT,
                                  categories=[models.LedgerCategory.REVENUE.value])
            payroll  = _ledger_sum(db, company.id, tag, models.LedgerEntryType.DEBIT,
                                  categories=[models.LedgerCategory.PAYROLL.value])
            infra    = _ledger_sum(db, company.id, tag, models.LedgerEntryType.DEBIT,
                                  categories=[models.LedgerCategory.TECH_COST.value])
            other    = _ledger_sum(db, company.id, tag, models.LedgerEntryType.DEBIT,
                                  categories=[
                                      models.LedgerCategory.NON_TECH_COST.value,
                                      models.LedgerCategory.OFFICE_EXPENSE.value,
                                      models.LedgerCategory.MARKETING.value,
                                      models.LedgerCategory.MISC.value,
                                  ])
            headcount = _headcount(db, company.id, meta["departments"])
        else:
            revenue = payroll = infra = other = headcount = 0

        # Prefer live data; fall back to demo values for a polished presentation
        revenue   = revenue   if revenue   > 0 else fb["revenue"]
        payroll   = payroll   if payroll   > 0 else fb["payroll"]
        infra     = infra     if infra     > 0 else fb["infra"]
        other     = other     if other     > 0 else fb["other"]
        headcount = headcount if headcount > 0 else fb["headcount"]

        burn          = payroll + infra + other
        net           = revenue - burn
        budget_mo     = meta["budget_annual_inr"] / 12
        util_pct      = round(burn / budget_mo * 100, 1) if budget_mo > 0 else 0
        arr_attain    = round((revenue * 12) / meta["arr_target_inr"] * 100, 1) if meta["arr_target_inr"] > 0 else 0
        status = "on_track" if util_pct <= 85 else ("at_risk" if util_pct <= 105 else "over_budget")

        projects_out.append({
            "id": tag,
            "name": meta["name"],
            "tagline": meta["tagline"],
            "stage": meta["stage"],
            "stage_color": meta["stage_color"],
            "location": meta["location"],
            "color": meta["color"],
            "accent": meta["accent"],
            "revenue_inr": revenue,
            "payroll_inr": payroll,
            "infra_inr": infra,
            "other_costs_inr": other,
            "burn_inr": burn,
            "net_inr": net,
            "headcount": headcount,
            "headcount_target": meta["headcount_target"],
            "budget_annual_inr": meta["budget_annual_inr"],
            "budget_monthly_inr": budget_mo,
            "budget_utilization_pct": util_pct,
            "arr_target_inr": meta["arr_target_inr"],
            "arr_attainment_pct": arr_attain,
            "status": status,
        })

    total_revenue   = sum(p["revenue_inr"] for p in projects_out)
    total_burn      = sum(p["burn_inr"] for p in projects_out)
    total_headcount = sum(p["headcount"] for p in projects_out)

    return {
        "company": company.name if company else "Vireon Seeding Lab",
        "as_of": date.today().isoformat(),
        "fiscal_year": "FY 2025-26 (Apr 2025 – Mar 2026)",
        "projects": projects_out,
        "totals": {
            "revenue_inr": total_revenue,
            "burn_inr": total_burn,
            "net_inr": total_revenue - total_burn,
            "headcount": total_headcount,
        },
    }


@router.get("/monthly-trend")
def get_monthly_trend(
    months: int = 6,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    company = db.query(models.Company).first()
    today = date.today()
    trend = []

    for i in range(months - 1, -1, -1):
        offset_days = i * 31
        m_start = (today - timedelta(days=offset_days)).replace(day=1)
        year, month = m_start.year, m_start.month
        next_m = month + 1 if month < 12 else 1
        next_y = year if month < 12 else year + 1
        m_end = date(next_y, next_m, 1)

        growth_idx = (months - 1 - i)
        growth = _GROWTH[min(growth_idx, len(_GROWTH) - 1)]

        row: dict = {"month": m_start.strftime("%b '%y")}

        for tag in PROJECT_REGISTRY:
            fb = _DEMO[tag]

            if company:
                rev  = _ledger_sum(db, company.id, tag, models.LedgerEntryType.CREDIT,
                                   date_from=m_start, date_to=m_end)
                burn = _ledger_sum(db, company.id, tag, models.LedgerEntryType.DEBIT,
                                   date_from=m_start, date_to=m_end)
            else:
                rev = burn = 0

            row[f"{tag}_revenue"] = rev  if rev  > 0 else round(fb["revenue"] * growth)
            row[f"{tag}_burn"]    = burn if burn > 0 else round((fb["payroll"] + fb["infra"] + fb["other"]) * growth)

        trend.append(row)

    return {"trend": trend, "projects": list(PROJECT_REGISTRY.keys())}


@router.get("/cost-breakdown")
def get_cost_breakdown(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Overhead cost breakdown by category across the whole company."""
    company = db.query(models.Company).first()

    overhead_categories = {
        "payroll":    ("Salaries & Benefits",    "#f59e0b", models.LedgerCategory.PAYROLL.value),
        "tech_cost":  ("Cloud & Infrastructure", "#6366f1", models.LedgerCategory.TECH_COST.value),
        "office":     ("Office & Facilities",    "#10b981", models.LedgerCategory.OFFICE_EXPENSE.value),
        "non_tech":   ("Legal & Admin",          "#f43f5e", models.LedgerCategory.NON_TECH_COST.value),
        "marketing":  ("Sales & Marketing",      "#8b5cf6", models.LedgerCategory.MARKETING.value),
    }

    result = []
    for key, (label, color, cat_val) in overhead_categories.items():
        if company:
            amount = float(
                db.query(func.coalesce(func.sum(models.FinancialLedgerEntry.amount), 0))
                .filter(
                    models.FinancialLedgerEntry.company_id == company.id,
                    models.FinancialLedgerEntry.entry_type == models.LedgerEntryType.DEBIT,
                    models.FinancialLedgerEntry.category == cat_val,
                )
                .scalar() or 0
            )
        else:
            amount = 0

        # Demo fallback per category
        demo_map = {
            "payroll": 2_580_000,
            "tech_cost": 500_000,
            "office": 305_000,
            "non_tech": 95_000,
            "marketing": 120_000,
        }
        amount = amount if amount > 0 else demo_map.get(key, 0)
        result.append({"category": key, "label": label, "color": color, "amount_inr": amount})

    total = sum(r["amount_inr"] for r in result)
    for r in result:
        r["pct"] = round(r["amount_inr"] / total * 100, 1) if total > 0 else 0

    return {
        "breakdown": result,
        "total_inr": total,
        "as_of": date.today().isoformat(),
    }
