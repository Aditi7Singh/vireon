from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

import auth
import database
import models

router = APIRouter(prefix="/financial-reports", tags=["financial_reports"])


REVENUE_CODES = {"4100", "4200", "4300"}
COGS_CODES: set[str] = set()  # expand as needed
OPEX_CODES = {"5100", "5200", "5210", "5220", "5300", "5400", "5500", "5600", "5999"}
ASSET_CODES = {"1010", "1200", "1300", "1400", "1500", "1501"}
LIABILITY_CODES = {"2100", "2200", "2300", "2400"}
EQUITY_CODES = {"3100", "3200"}


def _float(v) -> float:
    return float(v) if v is not None else 0.0


def _gl_totals(
    db: Session,
    company_id: UUID,
    start: date,
    end: date,
) -> dict[str, dict[str, float]]:
    """Returns {account_code: {name, debit, credit}} for the period."""
    rows = (
        db.query(
            models.GeneralLedger.account_code,
            models.GeneralLedger.account_name,
            func.sum(models.GeneralLedger.debit_amount).label("debit"),
            func.sum(models.GeneralLedger.credit_amount).label("credit"),
        )
        .filter(
            models.GeneralLedger.company_id == company_id,
            models.GeneralLedger.transaction_date >= start,
            models.GeneralLedger.transaction_date <= end,
        )
        .group_by(models.GeneralLedger.account_code, models.GeneralLedger.account_name)
        .all()
    )
    result = {}
    for row in rows:
        code = row.account_code.value if hasattr(row.account_code, "value") else str(row.account_code)
        result[code] = {
            "name": row.account_name,
            "debit": _float(row.debit),
            "credit": _float(row.credit),
        }
    return result


def _gl_balance_sheet_totals(
    db: Session,
    company_id: UUID,
    as_of: date,
) -> dict[str, dict[str, float]]:
    """Cumulative GL balances up to as_of date for balance sheet."""
    rows = (
        db.query(
            models.GeneralLedger.account_code,
            models.GeneralLedger.account_name,
            func.sum(models.GeneralLedger.debit_amount).label("debit"),
            func.sum(models.GeneralLedger.credit_amount).label("credit"),
        )
        .filter(
            models.GeneralLedger.company_id == company_id,
            models.GeneralLedger.transaction_date <= as_of,
        )
        .group_by(models.GeneralLedger.account_code, models.GeneralLedger.account_name)
        .all()
    )
    result = {}
    for row in rows:
        code = row.account_code.value if hasattr(row.account_code, "value") else str(row.account_code)
        result[code] = {
            "name": row.account_name,
            "debit": _float(row.debit),
            "credit": _float(row.credit),
        }
    return result


@router.get("/income-statement")
def income_statement(
    company_id: UUID,
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    gl = _gl_totals(db, company_id, period_start, period_end)

    # Revenue: credit balances on revenue accounts
    revenue_lines = []
    total_revenue = 0.0
    for code in REVENUE_CODES:
        if code in gl:
            amount = gl[code]["credit"] - gl[code]["debit"]
            revenue_lines.append({"account": gl[code]["name"], "code": code, "amount": round(amount, 2)})
            total_revenue += amount

    # COGS
    cogs_lines = []
    total_cogs = 0.0
    for code in COGS_CODES:
        if code in gl:
            amount = gl[code]["debit"] - gl[code]["credit"]
            cogs_lines.append({"account": gl[code]["name"], "code": code, "amount": round(amount, 2)})
            total_cogs += amount

    gross_profit = total_revenue - total_cogs
    gross_margin_pct = round((gross_profit / total_revenue * 100), 1) if total_revenue > 0 else 0.0

    # OpEx
    opex_lines = []
    total_opex = 0.0
    for code in OPEX_CODES:
        if code in gl:
            amount = gl[code]["debit"] - gl[code]["credit"]
            if amount != 0:
                opex_lines.append({"account": gl[code]["name"], "code": code, "amount": round(amount, 2)})
                total_opex += amount

    ebitda = gross_profit - total_opex
    depreciation = sum(l["amount"] for l in opex_lines if l["code"] == "5500")
    ebit = ebitda - depreciation
    net_income = ebit  # simplified (no interest/tax line here)

    return {
        "period": {"start": period_start.isoformat(), "end": period_end.isoformat()},
        "revenue": {"lines": revenue_lines, "total": round(total_revenue, 2)},
        "cogs": {"lines": cogs_lines, "total": round(total_cogs, 2)},
        "gross_profit": round(gross_profit, 2),
        "gross_margin_pct": gross_margin_pct,
        "opex": {"lines": opex_lines, "total": round(total_opex, 2)},
        "ebitda": round(ebitda, 2),
        "ebit": round(ebit, 2),
        "net_income": round(net_income, 2),
        "net_margin_pct": round((net_income / total_revenue * 100), 1) if total_revenue > 0 else 0.0,
    }


@router.get("/balance-sheet")
def balance_sheet(
    company_id: UUID,
    as_of: date = Query(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    gl = _gl_balance_sheet_totals(db, company_id, as_of)

    def asset_balance(code: str) -> float:
        if code not in gl:
            return 0.0
        return gl[code]["debit"] - gl[code]["credit"]

    def liability_balance(code: str) -> float:
        if code not in gl:
            return 0.0
        return gl[code]["credit"] - gl[code]["debit"]

    assets = [
        {"account": gl[c]["name"] if c in gl else c, "code": c, "amount": round(asset_balance(c), 2)}
        for c in ASSET_CODES
    ]
    total_assets = sum(a["amount"] for a in assets)

    liabilities = [
        {"account": gl[c]["name"] if c in gl else c, "code": c, "amount": round(liability_balance(c), 2)}
        for c in LIABILITY_CODES
    ]
    total_liabilities = sum(l["amount"] for l in liabilities)

    equity_lines = [
        {"account": gl[c]["name"] if c in gl else c, "code": c, "amount": round(liability_balance(c), 2)}
        for c in EQUITY_CODES
    ]
    total_equity = total_assets - total_liabilities

    return {
        "as_of": as_of.isoformat(),
        "assets": {"lines": assets, "total": round(total_assets, 2)},
        "liabilities": {"lines": liabilities, "total": round(total_liabilities, 2)},
        "equity": {
            "lines": equity_lines,
            "retained_earnings": round(total_equity - sum(e["amount"] for e in equity_lines), 2),
            "total": round(total_equity, 2),
        },
        "liabilities_and_equity": round(total_liabilities + total_equity, 2),
        "balanced": abs((total_liabilities + total_equity) - total_assets) < 1.0,
    }


@router.get("/cash-flow")
def cash_flow(
    company_id: UUID,
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Indirect method cash flow statement derived from GL and MonthlyMetric."""
    # Use MonthlyMetric as primary source for cash flow data
    metrics = (
        db.query(models.MonthlyMetric)
        .filter(
            models.MonthlyMetric.company_id == company_id,
            models.MonthlyMetric.metric_month >= period_start,
            models.MonthlyMetric.metric_month <= period_end,
        )
        .order_by(models.MonthlyMetric.metric_month.asc())
        .all()
    )

    operating_cash = sum(_float(m.net_cash_flow) for m in metrics)
    total_expenses = sum(_float(m.total_expenses) for m in metrics)
    total_revenue = sum(_float(m.total_revenue) for m in metrics)

    # Depreciation from GL (non-cash add-back)
    gl = _gl_totals(db, company_id, period_start, period_end)
    depreciation = 0.0
    if "5500" in gl:
        depreciation = gl["5500"]["debit"] - gl["5500"]["credit"]

    net_income = total_revenue - total_expenses

    # AR/AP changes
    ar_change = 0.0
    if "1200" in gl:
        ar_change = -(gl["1200"]["debit"] - gl["1200"]["credit"])  # increase in AR = cash outflow
    ap_change = 0.0
    if "2100" in gl:
        ap_change = gl["2100"]["credit"] - gl["2100"]["debit"]  # increase in AP = cash inflow

    cfo = net_income + depreciation + ar_change + ap_change

    # Capex: equipment purchases from GL
    capex = 0.0
    if "1500" in gl:
        capex = -(gl["1500"]["debit"] - gl["1500"]["credit"])

    # Financing: debt changes
    debt_change = 0.0
    for code in ["2300", "2400"]:
        if code in gl:
            debt_change += gl[code]["credit"] - gl[code]["debit"]

    net_change = cfo + capex + debt_change
    ending_cash = _float(metrics[-1].ending_cash) if metrics else 0.0
    beginning_cash = ending_cash - net_change

    return {
        "period": {"start": period_start.isoformat(), "end": period_end.isoformat()},
        "operating": {
            "net_income": round(net_income, 2),
            "add_depreciation": round(depreciation, 2),
            "change_in_ar": round(ar_change, 2),
            "change_in_ap": round(ap_change, 2),
            "net_operating": round(cfo, 2),
        },
        "investing": {
            "capex": round(capex, 2),
            "net_investing": round(capex, 2),
        },
        "financing": {
            "net_debt_change": round(debt_change, 2),
            "net_financing": round(debt_change, 2),
        },
        "summary": {
            "beginning_cash": round(beginning_cash, 2),
            "net_change": round(net_change, 2),
            "ending_cash": round(ending_cash, 2),
        },
    }


@router.get("/department-breakdown")
def department_breakdown(
    company_id: UUID,
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """OpEx split by department from GL dimensional data."""
    rows = (
        db.query(
            models.GeneralLedger.department,
            func.sum(models.GeneralLedger.debit_amount).label("total"),
        )
        .filter(
            models.GeneralLedger.company_id == company_id,
            models.GeneralLedger.transaction_date >= period_start,
            models.GeneralLedger.transaction_date <= period_end,
            models.GeneralLedger.account_code.in_([
                models.GLAccountCode.PAYROLL_EXPENSE,
                models.GLAccountCode.MARKETING_EXPENSE,
                models.GLAccountCode.OFFICE_EXPENSE,
                models.GLAccountCode.TECH_COST_AWS,
                models.GLAccountCode.TECH_COST_SAAS,
                models.GLAccountCode.MISC,
            ]),
        )
        .group_by(models.GeneralLedger.department)
        .all()
    )

    breakdown = [
        {
            "department": row.department.value if row.department else "unallocated",
            "amount": round(_float(row.total), 2),
        }
        for row in rows
    ]
    total = sum(d["amount"] for d in breakdown)
    for d in breakdown:
        d["pct"] = round(d["amount"] / total * 100, 1) if total > 0 else 0.0

    return {"period": {"start": period_start.isoformat(), "end": period_end.isoformat()}, "departments": breakdown, "total": round(total, 2)}
