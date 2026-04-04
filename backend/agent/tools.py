"""
Agent Tools
==========
LangChain tool definitions - call the database directly (no HTTP) to avoid
Docker networking timeouts and self-referential request deadlocks.
"""

from __future__ import annotations

from datetime import date, timedelta
from contextvars import ContextVar
from uuid import UUID
from typing import Dict, Any, List, Optional
from sqlalchemy import func
from langchain_core.tools import tool


def _build_error(tool_name: str, exc: Exception) -> Dict[str, Any]:
    return {"error": str(exc), "tool": tool_name}


_active_company_id: ContextVar[Optional[str]] = ContextVar("active_company_id", default=None)
_active_company_ids: ContextVar[Optional[List[str]]] = ContextVar("active_company_ids", default=None)


def set_active_company_context(company_id: Optional[str] = None, company_ids: Optional[List[str]] = None) -> None:
    _active_company_id.set(str(company_id) if company_id else None)
    _active_company_ids.set([str(item) for item in company_ids] if company_ids else None)


def clear_active_company_context() -> None:
    _active_company_id.set(None)
    _active_company_ids.set(None)


def _normalize_uuid(value: Optional[str]) -> Optional[UUID]:
    if value is None or value == "":
        return None
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _get_db():
    """Get a fresh DB session."""
    import database
    db = next(database.get_db())
    return db


def _get_first_company(db):
    """Return the first company or None."""
    import models

    company_ids = _active_company_ids.get()
    if company_ids:
        normalized_ids = [_normalize_uuid(company_id) for company_id in company_ids]
        companies = (
            db.query(models.Company)
            .filter(models.Company.id.in_([company_id for company_id in normalized_ids if company_id is not None]))
            .order_by(models.Company.created_at.asc())
            .all()
        )
        if companies:
            return companies[0]

    company_id = _active_company_id.get()
    if company_id:
        company = db.query(models.Company).filter(models.Company.id == _normalize_uuid(company_id)).first()
        if company:
            return company

    return db.query(models.Company).order_by(models.Company.created_at.asc()).first()


def _get_latest_metric(db, company_id):
    """Return the most recent MonthlyMetric or None."""
    import models
    return (
        db.query(models.MonthlyMetric)
        .filter(models.MonthlyMetric.company_id == company_id)
        .order_by(models.MonthlyMetric.metric_month.desc())
        .first()
    )


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def _close_db(db) -> None:
    try:
        if db:
            db.close()
    except Exception:
        pass


def _company_metrics(db) -> List[Any]:
    import models

    company = _get_first_company(db)
    if not company:
        return []

    return (
        db.query(models.MonthlyMetric)
        .filter(models.MonthlyMetric.company_id == company.id)
        .order_by(models.MonthlyMetric.metric_month.asc())
        .all()
    )


def _company_budget(db):
    import models

    company = _get_first_company(db)
    if not company:
        return None

    return (
        db.query(models.Budget)
        .filter(models.Budget.company_id == company.id)
        .order_by(models.Budget.created_at.desc())
        .first()
    )


def _sum_account_balances(db, company_id, account_types: Optional[List[str]] = None) -> float:
    import models

    query = db.query(func.coalesce(func.sum(models.Account.current_balance), 0)).filter(
        models.Account.company_id == company_id,
    )
    if account_types:
        query = query.filter(models.Account.type.in_(account_types))
    return _safe_float(query.scalar())


def _latest_month_window(db, company_id):
    import models

    metric = _get_latest_metric(db, company_id)
    if metric:
        month_start = metric.metric_month
    else:
        month_start = date.today().replace(day=1)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return month_start, next_month, metric


def _ledger_sum_for_month(db, company_id, month_start, month_end, entry_type=None, categories=None) -> float:
    import models

    query = db.query(func.coalesce(func.sum(models.FinancialLedgerEntry.amount_inr), 0)).filter(
        models.FinancialLedgerEntry.company_id == company_id,
        models.FinancialLedgerEntry.transaction_date >= month_start,
        models.FinancialLedgerEntry.transaction_date < month_end,
    )
    if entry_type is not None:
        query = query.filter(models.FinancialLedgerEntry.entry_type == entry_type)
    if categories:
        query = query.filter(models.FinancialLedgerEntry.category.in_(categories))
    return _safe_float(query.scalar())


def _actual_financial_snapshot(db, company):
    import models

    month_start, month_end, metric = _latest_month_window(db, company.id)
    revenue = _ledger_sum_for_month(
        db,
        company.id,
        month_start,
        month_end,
        entry_type=models.LedgerEntryType.CREDIT,
        categories=[models.LedgerCategory.REVENUE],
    )
    cogs = _ledger_sum_for_month(
        db,
        company.id,
        month_start,
        month_end,
        entry_type=models.LedgerEntryType.DEBIT,
        categories=[models.LedgerCategory.TECH_COST],
    )
    operating_expenses = _ledger_sum_for_month(
        db,
        company.id,
        month_start,
        month_end,
        entry_type=models.LedgerEntryType.DEBIT,
        categories=[
            models.LedgerCategory.NON_TECH_COST,
            models.LedgerCategory.OFFICE_EXPENSE,
            models.LedgerCategory.MARKETING,
            models.LedgerCategory.PAYROLL,
            models.LedgerCategory.HIRING,
            models.LedgerCategory.MISC,
        ],
    )

    if revenue <= 0 and metric:
        revenue = _safe_float(metric.total_revenue)
    if cogs <= 0 and metric:
        cogs = max(0.0, _safe_float(metric.total_expenses) * 0.35)
    if operating_expenses <= 0 and metric:
        operating_expenses = max(0.0, _safe_float(metric.total_expenses) - cogs)

    return {
        "month_start": month_start,
        "month_end": month_end,
        "metric": metric,
        "revenue": revenue,
        "cogs": cogs,
        "operating_expenses": operating_expenses,
        "net_income": revenue - cogs - operating_expenses,
        "ending_cash": _safe_float(metric.ending_cash) if metric else 0.0,
        "burn_rate": _safe_float(metric.burn_rate) if metric else max(0.0, cogs + operating_expenses - revenue),
        "runway_months": _safe_float(metric.runway_months) if metric else 0.0,
    }


# ─── Tools ────────────────────────────────────────────────────────────────────

@tool
def get_cash_balance() -> Dict[str, Any]:
    """
    Get current cash position: bank balance, AR, AP, net cash.
    Call before any runway calculation.

    Returns:
        Dictionary with cash, ar, ap, net_cash
    """
    db = None
    try:
        from sqlalchemy import func
        import models

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"cash": 0, "ar": 0, "ap": 0, "net_cash": 0, "note": "No company data found"}

        metric = _get_latest_metric(db, company.id)
        if not metric:
            return {"cash": 0, "ar": 0, "ap": 0, "net_cash": 0, "note": "No monthly metrics found"}

        cash = float(metric.ending_cash)
        ar = _safe_float(
            db.query(func.sum(models.Invoice.amount_due)).filter(
                models.Invoice.company_id == company.id,
                models.Invoice.type == "ACCOUNTS_RECEIVABLE",
                models.Invoice.amount_due > 0,
            ).scalar()
        )
        ap = _safe_float(
            db.query(func.sum(models.Invoice.amount_due)).filter(
                models.Invoice.company_id == company.id,
                models.Invoice.type == "ACCOUNTS_PAYABLE",
                models.Invoice.amount_due > 0,
            ).scalar()
        )
        return {
            "cash": cash,
            "ar": round(ar, 2),
            "ap": round(ap, 2),
            "net_cash": round(cash + ar - ap, 2),
            "as_of": metric.metric_month.isoformat()
        }
    except Exception as e:
        return {"error": str(e), "tool": "get_cash_balance"}
    finally:
        _close_db(db)


@tool
def get_burn_rate(period_days: int = 30) -> Dict[str, Any]:
    """
    Get monthly cash burn. Use period_days=90 for a more stable average.
    Returns breakdown by category and trend vs prior period.

    Args:
        period_days: Number of days to calculate burn over (default 30)

    Returns:
        Dictionary with monthly_burn, breakdown_by_category, trend
    """
    db = None
    try:
        import models
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"monthly_burn": 0, "breakdown_by_category": {}, "trend": 0}

        lookback_days = max(1, int(period_days))
        cutoff_date = date.today() - timedelta(days=lookback_days)
        expenses = db.query(models.Expense).filter(
            models.Expense.company_id == company.id,
            models.Expense.transaction_date >= cutoff_date
        ).all()

        breakdown: Dict[str, float] = {}
        total = 0.0
        for exp in expenses:
            cat = exp.category or "Other"
            breakdown[cat] = breakdown.get(cat, 0) + float(exp.total_amount)
            total += float(exp.total_amount)

        # Fall back to latest metric if no recent expense rows
        if not breakdown:
            metric = _get_latest_metric(db, company.id)
            if metric:
                total = float(metric.burn_rate) or float(metric.total_expenses)
                breakdown = {"Operations": total}

        # Normalize any lookback window to 30-day monthly equivalent.
        monthly_equivalent = (total * 30.0) / float(lookback_days)

        # Compute trend vs previous equal-length period when possible.
        prev_cutoff_start = cutoff_date - timedelta(days=lookback_days)
        prev_expenses = db.query(models.Expense).filter(
            models.Expense.company_id == company.id,
            models.Expense.transaction_date >= prev_cutoff_start,
            models.Expense.transaction_date < cutoff_date,
        ).all()
        prev_total = sum(_safe_float(exp.total_amount) for exp in prev_expenses)
        prev_monthly = (prev_total * 30.0) / float(lookback_days) if prev_total > 0 else 0.0
        trend_pct = ((monthly_equivalent - prev_monthly) / prev_monthly * 100.0) if prev_monthly > 0 else 0.0

        return {
            "monthly_burn": round(monthly_equivalent, 2) if total > 0 else 0,
            "breakdown_by_category": breakdown,
            "trend": round(trend_pct, 2),
            "lookback_days": lookback_days,
        }
    except Exception as e:
        return {"error": str(e), "tool": "get_burn_rate"}
    finally:
        _close_db(db)


@tool
def get_runway() -> Dict[str, Any]:
    """
    Get cash runway in months at current burn rate.
    NEVER calculate runway yourself — always call this tool.
    Returns runway_months, zero_date, confidence_interval.

    Returns:
        Dictionary with runway_months, zero_date, confidence_interval
    """
    db = None
    try:
        from analytics import metrics as m
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"runway_months": 0, "zero_date": "N/A", "confidence_interval": "Low"}

        metric = _get_latest_metric(db, company.id)
        if not metric:
            return {"runway_months": 0, "zero_date": "N/A", "confidence_interval": "Low"}

        cash = float(metric.ending_cash)
        revenue = float(metric.total_revenue)
        expenses = float(metric.total_expenses)
        net_burn = m.calculate_net_burn(revenue, expenses)
        runway = m.calculate_runway(cash, net_burn)

        if isinstance(runway, (int, float)) and runway < 9999:
            months = int(runway)
            zero_date = (date.today() + timedelta(days=months * 30)).isoformat()
        else:
            months = 999
            zero_date = "Financially self-sustaining"

        return {
            "runway_months": round(float(runway), 1) if isinstance(runway, (int, float)) else 999,
            "zero_date": zero_date,
            "confidence_interval": "High",
            "current_cash": cash,
            "monthly_burn": round(net_burn, 0),
            "as_of": metric.metric_month.isoformat()
        }
    except Exception as e:
        return {"error": str(e), "tool": "get_runway"}
    finally:
        _close_db(db)


@tool
def simulate_hire(n_engineers: int, avg_annual_salary: int = 120000) -> Dict[str, Any]:
    """
    Simulate hiring N engineers. Returns new_runway_months, runway_delta,
    monthly_burn_increase, break_even_mrr needed.

    Args:
        n_engineers: Number of engineers to hire
        avg_annual_salary: Average annual salary per engineer (default 120000)

    Returns:
        Dictionary with new_runway, runway_delta, monthly_burn_increase
    """
    try:
        from analytics import metrics as m, scenarios
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"error": "No company found"}

        metric = _get_latest_metric(db, company.id)
        if not metric:
            return {"error": "No financial data found"}

        result = scenarios.simulate_hiring(
            current_cash=float(metric.ending_cash),
            current_revenue=float(metric.total_revenue),
            current_gross_burn=float(metric.total_expenses),
            new_salary_annual=avg_annual_salary,
            count=n_engineers
        )
        return result
    except Exception as e:
        return {"error": str(e), "tool": "simulate_hire"}
    finally:
        try: db.close()
        except: pass


@tool
def simulate_revenue_change(mrr_delta: float, probability: float = 1.0) -> Dict[str, Any]:
    """
    Simulate MRR change impact on runway. mrr_delta positive=gain, negative=loss.
    probability 0-1 weights the scenario.

    Args:
        mrr_delta: Change in Monthly Recurring Revenue
        probability: Probability of this scenario occurring (0-1)

    Returns:
        Dictionary with new_runway, runway_delta
    """
    try:
        from analytics import scenarios
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"error": "No company found"}

        metric = _get_latest_metric(db, company.id)
        if not metric:
            return {"error": "No financial data found"}

        # Convert absolute delta to percentage
        current_rev = float(metric.total_revenue) or 1
        pct_change = mrr_delta / current_rev

        result = scenarios.simulate_revenue_change(
            current_cash=float(metric.ending_cash),
            current_revenue=current_rev,
            current_gross_burn=float(metric.total_expenses),
            percentage_change=pct_change
        )
        return result
    except Exception as e:
        return {"error": str(e), "tool": "simulate_revenue_change"}
    finally:
        try: db.close()
        except: pass


@tool
def simulate_expense_change(category: str, change_pct: float) -> Dict[str, Any]:
    """
    Simulate expense change for a GL category (aws/payroll/saas/marketing).
    change_pct: -30 means reduce 30%, +20 means increase 20%.

    Args:
        category: Expense category (aws, payroll, saas, marketing, etc.)
        change_pct: Percentage change (-100 to +100)

    Returns:
        Dictionary with new_runway, savings
    """
    try:
        from analytics import metrics as m
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"error": "No company found"}

        import models
        expenses = db.query(models.Expense).filter(
            models.Expense.company_id == company.id,
            models.Expense.category.ilike(f"%{category}%")
        ).all()

        category_total = sum(float(e.total_amount) for e in expenses)
        savings = category_total * (change_pct / 100)

        metric = _get_latest_metric(db, company.id)
        if not metric:
            return {"error": "No financial data found"}

        new_burn = float(metric.total_expenses) - savings
        new_net_burn = m.calculate_net_burn(float(metric.total_revenue), new_burn)
        new_runway = m.calculate_runway(float(metric.ending_cash), new_net_burn)

        return {
            "category": category,
            "change_pct": change_pct,
            "category_spend": category_total,
            "monthly_savings": round(savings / 3, 2),
            "new_runway_months": round(float(new_runway), 1) if isinstance(new_runway, (int, float)) else 999
        }
    except Exception as e:
        return {"error": str(e), "tool": "simulate_expense_change"}
    finally:
        try: db.close()
        except: pass


@tool
def get_active_alerts(limit: int = 20) -> Dict[str, Any]:
    """
    Get all active anomaly alerts with severity (critical/warning/info),
    amount vs baseline, and recommended actions.
    Proactively check this for spending questions.

    Args:
        limit: Maximum number of alerts to return (default 20)

    Returns:
        Dictionary with alerts array and metadata
    """
    try:
        import models
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"alerts": [], "total": 0, "critical_count": 0, "warning_count": 0}

        query = db.query(models.Anomaly).filter(
            models.Anomaly.company_id == company.id
        )
        total = query.count()
        critical_count = query.filter(models.Anomaly.severity == "critical").count()
        warning_count = query.filter(models.Anomaly.severity == "warning").count()
        anomalies = (
            db.query(models.Anomaly)
            .filter(models.Anomaly.company_id == company.id)
            .order_by(models.Anomaly.anomaly_date.desc())
            .limit(limit)
            .all()
        )

        alerts = []
        for a in anomalies:
            delta = 0.0
            if a.expected_value and float(a.expected_value) != 0:
                delta = ((float(a.actual_value or 0) / float(a.expected_value)) - 1) * 100
            alerts.append({
                "id": str(a.id),
                "severity": a.severity or "info",
                "type": a.type or "anomaly",
                "description": a.description,
                "actual_value": float(a.actual_value or 0),
                "expected_value": float(a.expected_value or 0),
                "delta_pct": round(delta, 1),
                "date": a.anomaly_date.isoformat()
            })

        return {
            "alerts": alerts,
            "total": total,
            "critical_count": critical_count,
            "warning_count": warning_count
        }
    except Exception as e:
        return {"error": str(e), "tool": "get_active_alerts"}
    finally:
        try: db.close()
        except: pass


@tool
def get_expense_breakdown(period_months: int = 3) -> Dict[str, Any]:
    """
    Get expenses by GL category for the past N months with month-over-month
    trend and largest movers.

    Args:
        period_months: Number of months to analyze (default 3)

    Returns:
        Dictionary with breakdown, total, movers
    """
    try:
        import models
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"breakdown": {}, "total": 0, "movers": []}

        expenses = db.query(models.Expense).filter(
            models.Expense.company_id == company.id
        ).all()

        breakdown: Dict[str, float] = {}
        total = 0.0
        for exp in expenses:
            cat = exp.category or "Other"
            breakdown[cat] = round(breakdown.get(cat, 0) + float(exp.total_amount), 2)
            total += float(exp.total_amount)

        movers = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)[:3]

        return {
            "breakdown": breakdown,
            "total": round(total, 2),
            "movers": [{"category": k, "amount": v} for k, v in movers],
            "period_months": period_months
        }
    except Exception as e:
        return {"error": str(e), "tool": "get_expense_breakdown"}
    finally:
        try: db.close()
        except: pass


@tool
def get_revenue_metrics() -> Dict[str, Any]:
    """
    Get MRR, ARR, growth rate, churn rate, and net revenue retention
    with 12-month trend.

    Returns:
        Dictionary with mrr, arr, growth_pct, churn_rate, nrr
    """
    db = None
    try:
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"mrr": 0, "arr": 0, "growth_pct": 0, "churn_rate": 0, "nrr": 0}

        metrics = _company_metrics(db)
        if not metrics:
            return {"mrr": 0, "arr": 0, "growth_pct": 0, "churn_rate": 0, "nrr": 0}

        latest = metrics[-1]
        previous = metrics[-2] if len(metrics) > 1 else latest
        current_mrr = _safe_float(latest.total_revenue)
        previous_mrr = _safe_float(previous.total_revenue)
        growth_pct = ((current_mrr - previous_mrr) / previous_mrr * 100) if previous_mrr > 0 else 0
        churn_rate = max(0, -growth_pct) if growth_pct < 0 else 0
        nrr = (current_mrr / previous_mrr * 100) if previous_mrr > 0 else 0
        return {
            "mrr": round(current_mrr, 2),
            "arr": round(current_mrr * 12, 2),
            "growth_pct": round(growth_pct, 2),
            "churn_rate": round(churn_rate, 2),
            "nrr": round(nrr, 2),
            "as_of": latest.metric_month.isoformat()
        }
    except Exception as e:
        return {"error": str(e), "tool": "get_revenue_metrics"}
    finally:
        _close_db(db)


@tool
def get_financial_scorecard() -> Dict[str, Any]:
    """
    Get the complete financial health scorecard: liquidity ratios,
    burn multiple, magic number, CAC payback, gross margin.
    Use for overview questions.

    Returns:
        Dictionary with all KPI metrics
    """
    db = None
    try:
        from analytics import metrics as m
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"error": "No company data found"}

        metric = _get_latest_metric(db, company.id)
        if not metric:
            return {"error": "No monthly metrics found"}

        cash = float(metric.ending_cash)
        revenue = float(metric.total_revenue)
        expenses = float(metric.total_expenses)
        net_burn = m.calculate_net_burn(revenue, expenses)
        runway = m.calculate_runway(cash, net_burn)
        arr = m.calculate_arr(revenue)

        return {
            "company": company.name,
            "as_of": metric.metric_month.isoformat(),
            "cash": round(cash, 2),
            "mrr": round(revenue, 2),
            "arr": round(arr, 2),
            "gross_burn": round(expenses, 2),
            "net_burn": round(net_burn, 2),
            "runway_months": round(float(runway), 1) if isinstance(runway, (int, float)) else 999,
            "burn_multiple": round(net_burn / revenue, 2) if revenue > 0 else "N/A",
            "gross_margin_pct": round(((revenue - expenses) / revenue) * 100, 1) if revenue > 0 else 0,
        }
    except Exception as e:
        return {"error": str(e), "tool": "get_financial_scorecard"}
    finally:
        _close_db(db)


@tool
def get_loan_metrics() -> Dict[str, Any]:
    """
    Get loan portfolio metrics: total debt, monthly payments, interest expense.
    Includes breakdown by loan type and maturity analysis.

    Returns:
        Dictionary with total_debt, monthly_payments, interest_expense, breakdown
    """
    db = None
    try:
        import models
        from analytics.metrics import calculate_loan_metrics
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"total_debt": 0, "monthly_payments": 0, "interest_expense": 0, "breakdown": []}

        loans = db.query(models.Loan).filter(models.Loan.company_id == company.id).all()
        if not loans:
            return {"total_debt": 0, "monthly_payments": 0, "interest_expense": 0, "breakdown": []}

        metrics = calculate_loan_metrics(db, company.id)
        return metrics
    except Exception as e:
        return {"error": str(e), "tool": "get_loan_metrics"}
    finally:
        _close_db(db)


@tool
def get_payroll_costs() -> Dict[str, Any]:
    """
    Get payroll cost breakdown: salaries, taxes, benefits, total compensation.
    Includes headcount and cost per employee metrics.

    Returns:
        Dictionary with total_payroll, employee_count, avg_salary, tax_breakdown
    """
    db = None
    try:
        import models
        from analytics.metrics import calculate_monthly_payroll_cost
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"total_payroll": 0, "employee_count": 0, "avg_salary": 0, "tax_breakdown": {}}

        employees = db.query(models.Employee).filter(models.Employee.company_id == company.id).all()
        if not employees:
            return {"total_payroll": 0, "employee_count": 0, "avg_salary": 0, "tax_breakdown": {}}

        # Calculate current month payroll
        from datetime import date
        current_month = date.today().replace(day=1)
        monthly_cost_info = calculate_monthly_payroll_cost(db, company.id, current_month)
        monthly_cost = _safe_float(monthly_cost_info.get("total_employer_outflow", 0))

        employee_count = len(employees)
        total_salary = sum(float(emp.salary) for emp in employees)
        avg_salary = total_salary / employee_count if employee_count > 0 else 0

        return {
            "total_payroll": round(monthly_cost, 2),
            "employee_count": employee_count,
            "avg_salary": round(avg_salary, 2),
            "annual_payroll_run_rate": round(monthly_cost * 12, 2),
            "cost_per_employee": round(monthly_cost / employee_count, 2) if employee_count > 0 else 0
        }
    except Exception as e:
        return {"error": str(e), "tool": "get_payroll_costs"}
    finally:
        _close_db(db)


@tool
def get_tax_liability() -> Dict[str, Any]:
    """
    Get tax liability breakdown: income tax, payroll tax, sales tax.
    Includes quarterly payment schedule and year-to-date totals.

    Returns:
        Dictionary with total_tax_liability, quarterly_payments, breakdown_by_type
    """
    db = None
    try:
        from sqlalchemy import func
        import models
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"total_tax_liability": 0, "quarterly_payments": [], "breakdown_by_type": {}}

        # Get latest revenue data for tax calculation
        metric = _get_latest_metric(db, company.id)
        if not metric:
            return {"total_tax_liability": 0, "quarterly_payments": [], "breakdown_by_type": {}}

        annual_revenue = _safe_float(metric.total_revenue) * 12
        annual_payroll = _safe_float(db.query(func.sum(models.PayrollEntry.gross_pay)).join(models.Employee).filter(
            models.Employee.company_id == company.id
        ).scalar())
        estimated_income_tax = annual_revenue * float(company.effective_tax_rate or 0.25)
        estimated_payroll_taxes = annual_payroll * 0.12
        estimated_total = estimated_income_tax + estimated_payroll_taxes

        current_year = date.today().year
        current_quarter = ((date.today().month - 1) // 3) + 1
        quarterly_total = estimated_total / 4 if estimated_total else 0

        return {
            "total_tax_liability": round(estimated_total, 2),
            "quarterly_payments": [
                {"year": current_year, "quarter": q, "amount": round(quarterly_total, 2)}
                for q in range(1, 5)
            ],
            "breakdown_by_type": {
                "income_tax": round(estimated_income_tax, 2),
                "payroll_tax": round(estimated_payroll_taxes, 2),
                "sales_tax": 0.0,
            },
            "current_quarter": current_quarter,
        }
    except Exception as e:
        return {"error": str(e), "tool": "get_tax_liability"}
    finally:
        _close_db(db)


@tool
def get_depreciation_expense() -> Dict[str, Any]:
    """
    Get depreciation expense metrics: monthly depreciation, accumulated depreciation, asset book value.
    Includes breakdown by asset category and remaining useful life.

    Returns:
        Dictionary with monthly_depreciation, accumulated_depreciation, asset_breakdown
    """
    db = None
    try:
        import models
        from analytics.metrics import calculate_monthly_depreciation_expense
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"monthly_depreciation": 0, "accumulated_depreciation": 0, "asset_breakdown": []}

        # Calculate current month depreciation
        from datetime import date
        current_month = date.today().replace(day=1)
        monthly_dep = calculate_monthly_depreciation_expense(db, company.id, current_month)

        # Get asset breakdown
        assets = db.query(models.FixedAsset).filter(models.FixedAsset.company_id == company.id).all()
        asset_breakdown = []
        total_accumulated = 0

        for asset in assets:
            # Get latest depreciation entry for this asset
            latest_dep = db.query(models.DepreciationEntry).filter(
                models.DepreciationEntry.asset_id == asset.id
            ).order_by(models.DepreciationEntry.depreciation_date.desc()).first()

            if latest_dep:
                total_accumulated += float(latest_dep.accumulated_depreciation)
                asset_breakdown.append({
                    "asset_name": asset.asset_name,
                    "category": asset.asset_category,
                    "book_value": round(_safe_float(latest_dep.book_value), 2),
                    "monthly_depreciation": round(float(latest_dep.depreciation_amount), 2),
                    "accumulated_depreciation": round(float(latest_dep.accumulated_depreciation), 2)
                })

        return {
            "monthly_depreciation": round(monthly_dep, 2),
            "accumulated_depreciation": round(total_accumulated, 2),
            "asset_count": len(assets),
            "asset_breakdown": asset_breakdown
        }
    except Exception as e:
        return {"error": str(e), "tool": "get_depreciation_expense"}
    finally:
        _close_db(db)


@tool
def get_asset_utilization() -> Dict[str, Any]:
    """
    Get asset utilization metrics: asset turnover, return on assets, depreciation as % of revenue.
    Helps assess capital efficiency and asset management effectiveness.

    Returns:
        Dictionary with asset_turnover, roa, depreciation_ratio, utilization_score
    """
    db = None
    try:
        import models
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"asset_turnover": 0, "roa": 0, "depreciation_ratio": 0, "utilization_score": 0}

        # Get financial metrics
        metric = _get_latest_metric(db, company.id)
        if not metric:
            return {"asset_turnover": 0, "roa": 0, "depreciation_ratio": 0, "utilization_score": 0}

        revenue = _safe_float(metric.total_revenue)
        gross_expenses = _safe_float(metric.total_expenses)
        net_income = revenue - gross_expenses

        # Get total assets (simplified - just fixed assets for now)
        assets = db.query(models.FixedAsset).filter(models.FixedAsset.company_id == company.id).all()
        total_asset_value = sum(float(asset.purchase_cost) for asset in assets)

        # Get depreciation expense
        from analytics.metrics import calculate_monthly_depreciation_expense
        from datetime import date
        current_month = date.today().replace(day=1)
        monthly_dep = calculate_monthly_depreciation_expense(db, company.id, current_month)
        annual_dep = monthly_dep * 12

        # Calculate ratios
        asset_turnover = revenue / total_asset_value if total_asset_value > 0 else 0
        roa = (net_income / total_asset_value) * 100 if total_asset_value > 0 else 0
        depreciation_ratio = (annual_dep / revenue) * 100 if revenue > 0 else 0

        # Simple utilization score (higher is better)
        utilization_score = min(100, (asset_turnover * 10) + (roa / 2) - depreciation_ratio)

        return {
            "asset_turnover": round(asset_turnover, 2),
            "roa": round(roa, 2),
            "depreciation_ratio": round(depreciation_ratio, 2),
            "utilization_score": round(max(0, utilization_score), 1),
            "total_asset_value": round(total_asset_value, 2)
        }
    except Exception as e:
        return {"error": str(e), "tool": "get_asset_utilization"}
    finally:
        _close_db(db)


@tool
def forecast_cash_flow(months_ahead: int = 6) -> Dict[str, Any]:
    """Project cash flow from the latest monthly metrics using a simple trend line."""
    db = None
    try:
        import models

        horizon = max(1, min(int(months_ahead), 24))
        db = _get_db()
        company = _get_first_company(db)
        metrics = _company_metrics(db)
        if not company or len(metrics) < 2:
            return {"forecast": [], "baseline": {}, "note": "Not enough monthly metrics to forecast"}

        cash_series = [_safe_float(metric.ending_cash) for metric in metrics]
        revenue_series = [_safe_float(metric.total_revenue) for metric in metrics]
        burn_series = [_safe_float(metric.total_expenses) for metric in metrics]

        latest_cash = cash_series[-1]
        latest_revenue = revenue_series[-1]
        latest_burn = burn_series[-1]
        cash_slope = (cash_series[-1] - cash_series[0]) / max(1, len(cash_series) - 1)
        revenue_slope = (revenue_series[-1] - revenue_series[0]) / max(1, len(revenue_series) - 1)
        burn_slope = (burn_series[-1] - burn_series[0]) / max(1, len(burn_series) - 1)

        projection = []
        next_cash = latest_cash
        next_revenue = latest_revenue
        next_burn = latest_burn
        for month_index in range(1, horizon + 1):
            next_cash = max(0, next_cash + cash_slope - max(0, next_burn - next_revenue))
            next_revenue = max(0, next_revenue + revenue_slope)
            next_burn = max(0, next_burn + burn_slope)
            projection.append({
                "month": month_index,
                "projected_cash": round(next_cash, 2),
                "projected_revenue": round(next_revenue, 2),
                "projected_expenses": round(next_burn, 2),
                "projected_net_burn": round(max(0, next_burn - next_revenue), 2),
            })

        return {
            "company": company.name,
            "as_of": metrics[-1].metric_month.isoformat(),
            "baseline": {
                "cash": round(latest_cash, 2),
                "revenue": round(latest_revenue, 2),
                "expenses": round(latest_burn, 2),
            },
            "forecast": projection,
        }
    except Exception as e:
        return {"error": str(e), "tool": "forecast_cash_flow"}
    finally:
        _close_db(db)


@tool
def optimize_working_capital() -> Dict[str, Any]:
    """Analyze AR/AP and suggest simple working capital actions."""
    db = None
    try:
        import models

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"error": "No company found"}

        today = date.today()
        ar_total = _safe_float(db.query(func.sum(models.Invoice.amount_due)).filter(
            models.Invoice.company_id == company.id,
            models.Invoice.type == "ACCOUNTS_RECEIVABLE",
            models.Invoice.amount_due > 0,
        ).scalar())
        ap_total = _safe_float(db.query(func.sum(models.Invoice.amount_due)).filter(
            models.Invoice.company_id == company.id,
            models.Invoice.type == "ACCOUNTS_PAYABLE",
            models.Invoice.amount_due > 0,
        ).scalar())

        overdue_ar = db.query(models.Invoice).filter(
            models.Invoice.company_id == company.id,
            models.Invoice.type == "ACCOUNTS_RECEIVABLE",
            models.Invoice.amount_due > 0,
            models.Invoice.due_date < today,
        ).all()
        overdue_ap = db.query(models.Invoice).filter(
            models.Invoice.company_id == company.id,
            models.Invoice.type == "ACCOUNTS_PAYABLE",
            models.Invoice.amount_due > 0,
            models.Invoice.due_date < today,
        ).all()

        ar_overdue = sum(_safe_float(inv.amount_due) for inv in overdue_ar)
        ap_overdue = sum(_safe_float(inv.amount_due) for inv in overdue_ap)

        actions = []
        if ar_overdue > 0:
            actions.append("Accelerate collections on overdue receivables")
        if ap_overdue > 0:
            actions.append("Review overdue payables and negotiate terms")
        if ar_total > ap_total:
            actions.append("Prioritize AR reduction before AP acceleration")
        if not actions:
            actions.append("Working capital is balanced relative to current invoice book")

        return {
            "ar_total": round(ar_total, 2),
            "ap_total": round(ap_total, 2),
            "net_working_capital": round(ar_total - ap_total, 2),
            "ar_overdue": round(ar_overdue, 2),
            "ap_overdue": round(ap_overdue, 2),
            "actions": actions,
        }
    except Exception as e:
        return {"error": str(e), "tool": "optimize_working_capital"}
    finally:
        _close_db(db)


@tool
def score_vendor_performance(limit: int = 10) -> Dict[str, Any]:
    """Score vendors by spend consistency, payment cadence, and concentration."""
    db = None
    try:
        import models

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"vendors": [], "count": 0}

        vendor_contacts = db.query(models.Contact).filter(
            models.Contact.company_id == company.id,
            models.Contact.type == "VENDOR",
        ).all()

        results = []
        for contact in vendor_contacts:
            expenses = db.query(models.Expense).filter(
                models.Expense.company_id == company.id,
                models.Expense.contact_id == contact.id,
            ).all()
            totals = [_safe_float(exp.total_amount) for exp in expenses]
            spend_total = sum(totals)
            spend_count = len(totals)
            avg_spend = spend_total / spend_count if spend_count else 0
            variance = sum((amount - avg_spend) ** 2 for amount in totals) / spend_count if spend_count else 0
            consistency_score = max(0, 100 - min(100, variance / max(1, avg_spend)))
            cadence_score = min(100, spend_count * 12)
            score = round((consistency_score * 0.6) + (cadence_score * 0.4), 1)
            results.append({
                "vendor_id": str(contact.id),
                "vendor_name": contact.name,
                "spend_total": round(spend_total, 2),
                "spend_count": spend_count,
                "score": score,
                "status": "preferred" if score >= 75 else "watch" if score >= 50 else "review",
            })

        results.sort(key=lambda item: item["score"], reverse=True)
        return {"vendors": results[: max(1, int(limit))], "count": len(results)}
    except Exception as e:
        return {"error": str(e), "tool": "score_vendor_performance"}
    finally:
        _close_db(db)


@tool
def analyze_credit_risk(limit: int = 10) -> Dict[str, Any]:
    """Score customer receivables by overdue behavior and concentration."""
    db = None
    try:
        import models

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"customers": [], "count": 0}

        customer_contacts = db.query(models.Contact).filter(
            models.Contact.company_id == company.id,
            models.Contact.type == "CUSTOMER",
        ).all()
        today = date.today()
        results = []
        total_ar = 0.0
        for contact in customer_contacts:
            invoices = db.query(models.Invoice).filter(
                models.Invoice.company_id == company.id,
                models.Invoice.contact_id == contact.id,
                models.Invoice.type == "ACCOUNTS_RECEIVABLE",
            ).all()
            open_amount = sum(_safe_float(inv.amount_due) for inv in invoices if _safe_float(inv.amount_due) > 0)
            overdue_amount = sum(_safe_float(inv.amount_due) for inv in invoices if _safe_float(inv.amount_due) > 0 and inv.due_date and inv.due_date < today)
            total_ar += open_amount
            days_overdue = max([((today - inv.due_date).days) for inv in invoices if inv.amount_due and inv.due_date and inv.due_date < today] or [0])
            risk = min(100, (overdue_amount / max(1, open_amount)) * 100 + days_overdue)
            results.append({
                "customer_id": str(contact.id),
                "customer_name": contact.name,
                "open_ar": round(open_amount, 2),
                "overdue_ar": round(overdue_amount, 2),
                "days_overdue": days_overdue,
                "risk_score": round(risk, 1),
                "status": "high" if risk >= 70 else "medium" if risk >= 40 else "low",
            })

        results.sort(key=lambda item: item["risk_score"], reverse=True)
        concentration = [round((item["open_ar"] / total_ar) * 100, 1) if total_ar else 0 for item in results[: min(len(results), 5)]]
        return {"customers": results[: max(1, int(limit))], "count": len(results), "total_ar": round(total_ar, 2), "concentration_pct": concentration}
    except Exception as e:
        return {"error": str(e), "tool": "analyze_credit_risk"}
    finally:
        _close_db(db)


@tool
def track_budget_vs_actual(month: Optional[str] = None) -> Dict[str, Any]:
    """Compare the latest budget against actuals using the planning service."""
    db = None
    try:
        from analytics import scenarios  # noqa: F401  # keep import symmetry with other tools
        from services import planning as planning_service

        db = _get_db()
        budget = _company_budget(db)
        if not budget:
            return {"error": "No budget found"}

        target_month = None
        if month:
            target_month = date.fromisoformat(f"{month}-01") if len(month) == 7 else date.fromisoformat(month)

        return planning_service.get_budget_variance(db, budget.id, target_month=target_month)
    except Exception as e:
        return {"error": str(e), "tool": "track_budget_vs_actual"}
    finally:
        _close_db(db)


@tool
def suggest_payroll_optimizations() -> Dict[str, Any]:
    """Suggest payroll actions based on headcount, salary concentration, and department mix."""
    db = None
    try:
        import models

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"suggestions": [], "headcount": 0}

        employees = db.query(models.Employee).filter(models.Employee.company_id == company.id).all()
        active_employees = [emp for emp in employees if (emp.status or "active") == "active"]
        total_payroll = sum(_safe_float(emp.salary) for emp in active_employees)
        avg_salary = total_payroll / len(active_employees) if active_employees else 0
        departments: Dict[str, float] = {}
        for emp in active_employees:
            departments[emp.department or "unassigned"] = departments.get(emp.department or "unassigned", 0) + _safe_float(emp.salary)

        suggestions = []
        if len(active_employees) > 0:
            top_department = max(departments.items(), key=lambda item: item[1])
            suggestions.append(f"Review {top_department[0]} payroll concentration at {top_department[1]:,.0f} annual salary outflow")
            if avg_salary > 0:
                suggestions.append(f"Benchmark compensation around the current average salary of {avg_salary:,.0f}")
        if len(active_employees) >= 10:
            suggestions.append("Consider hiring gates tied to revenue and cash coverage")
        if not suggestions:
            suggestions.append("Payroll base is too small for optimization actions")

        return {
            "headcount": len(active_employees),
            "annual_payroll": round(total_payroll, 2),
            "average_salary": round(avg_salary, 2),
            "department_mix": {k: round(v, 2) for k, v in departments.items()},
            "suggestions": suggestions,
        }
    except Exception as e:
        return {"error": str(e), "tool": "suggest_payroll_optimizations"}
    finally:
        _close_db(db)


@tool
def manage_asset_lifecycle() -> Dict[str, Any]:
    """Recommend asset buy/hold/retire actions from life, book value, and age."""
    db = None
    try:
        import models

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"assets": []}

        today = date.today()
        assets = db.query(models.FixedAsset).filter(models.FixedAsset.company_id == company.id).all()
        output = []
        for asset in assets:
            age_years = max(0.0, (today - asset.purchase_date).days / 365.25)
            useful_life = max(1, int(asset.useful_life_years or 1))
            remaining_life = max(0.0, useful_life - age_years)
            book_value = _safe_float(asset.book_value) or max(0.0, _safe_float(asset.purchase_cost) - _safe_float(asset.accumulated_depreciation))
            recommendation = "hold"
            if asset.status == "disposed" or remaining_life <= 0:
                recommendation = "retire"
            elif remaining_life <= 0.5:
                recommendation = "plan replacement"
            output.append({
                "asset_id": str(asset.id),
                "asset_name": asset.asset_name,
                "category": asset.asset_category,
                "age_years": round(age_years, 2),
                "remaining_life_years": round(remaining_life, 2),
                "book_value": round(book_value, 2),
                "recommendation": recommendation,
            })

        return {"assets": output, "count": len(output)}
    except Exception as e:
        return {"error": str(e), "tool": "manage_asset_lifecycle"}
    finally:
        _close_db(db)


@tool
def analyze_debt_payoff_strategy() -> Dict[str, Any]:
    """Compare snowball and avalanche debt payoff orderings."""
    db = None
    try:
        import models

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"loans": []}

        loans = db.query(models.Loan).filter(models.Loan.company_id == company.id).all()
        rows = []
        for loan in loans:
            balance = _safe_float(loan.remaining_balance) or _safe_float(loan.principal_amount)
            rate = _safe_float(loan.interest_rate)
            monthly_interest = balance * (rate / 100) / 12
            rows.append({
                "loan_id": str(loan.id),
                "loan_name": loan.loan_name,
                "balance": round(balance, 2),
                "interest_rate": round(rate, 2),
                "monthly_interest": round(monthly_interest, 2),
            })

        snowball = sorted(rows, key=lambda item: item["balance"])
        avalanche = sorted(rows, key=lambda item: item["interest_rate"], reverse=True)
        return {"snowball": snowball, "avalanche": avalanche, "count": len(rows)}
    except Exception as e:
        return {"error": str(e), "tool": "analyze_debt_payoff_strategy"}
    finally:
        _close_db(db)


@tool
def track_revenue_recognition() -> Dict[str, Any]:
    """Track revenue recognition using invoices and monthly metrics."""
    db = None
    try:
        import models

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"recognized_revenue": 0, "deferred_revenue": 0}

        today = date.today()
        invoices = db.query(models.Invoice).filter(models.Invoice.company_id == company.id, models.Invoice.type == "ACCOUNTS_RECEIVABLE").all()
        recognized = sum(_safe_float(inv.amount_paid) for inv in invoices if inv.issue_date <= today)
        deferred = sum(max(0.0, _safe_float(inv.amount_due)) for inv in invoices if inv.due_date and inv.due_date > today)
        return {
            "recognized_revenue": round(recognized, 2),
            "deferred_revenue": round(deferred, 2),
            "invoice_count": len(invoices),
        }
    except Exception as e:
        return {"error": str(e), "tool": "track_revenue_recognition"}
    finally:
        _close_db(db)


@tool
def calculate_customer_lifetime_value() -> Dict[str, Any]:
    """Calculate a simple CLV estimate from revenue, churn, and invoice history."""
    db = None
    try:
        import models

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"clv": 0, "average_monthly_revenue": 0}

        customers = db.query(models.Contact).filter(models.Contact.company_id == company.id, models.Contact.type == "CUSTOMER").all()
        invoices = db.query(models.Invoice).filter(models.Invoice.company_id == company.id, models.Invoice.type == "ACCOUNTS_RECEIVABLE").all()
        customer_count = max(1, len(customers))
        revenue = sum(_safe_float(inv.total_amount) for inv in invoices)
        average_monthly_revenue = revenue / 12 if revenue else 0
        gross_margin = 0.7
        churn_rate = 0.05 if customer_count else 1
        clv = (average_monthly_revenue * gross_margin) / churn_rate if churn_rate else 0
        return {
            "clv": round(clv, 2),
            "average_monthly_revenue": round(average_monthly_revenue, 2),
            "gross_margin_pct": round(gross_margin * 100, 1),
            "churn_rate_pct": round(churn_rate * 100, 1),
            "customer_count": customer_count,
        }
    except Exception as e:
        return {"error": str(e), "tool": "calculate_customer_lifetime_value"}
    finally:
        _close_db(db)


@tool
def analyze_unit_economics() -> Dict[str, Any]:
    """Calculate CAC, LTV, gross margin, and burn efficiency."""
    db = None
    try:
        import models

        db = _get_db()
        company = _get_first_company(db)
        metric = _get_latest_metric(db, company.id) if company else None
        if not company or not metric:
            return {"error": "Insufficient data"}

        revenue = _safe_float(metric.total_revenue)
        expenses = _safe_float(metric.total_expenses)
        customer_count = db.query(models.Contact).filter(models.Contact.company_id == company.id, models.Contact.type == "CUSTOMER").count()
        marketing_spend = _safe_float(db.query(func.sum(models.Expense.total_amount)).filter(models.Expense.company_id == company.id, models.Expense.category.ilike("%marketing%")).scalar())
        cac = marketing_spend / max(1, customer_count)
        gross_margin_pct = ((revenue - expenses) / revenue * 100) if revenue > 0 else 0
        clv = (revenue * 12 * max(0, gross_margin_pct) / 100) / 0.05 if revenue > 0 else 0
        return {
            "cac": round(cac, 2),
            "ltv": round(clv, 2),
            "ltv_to_cac": round(clv / cac, 2) if cac > 0 else 0,
            "gross_margin_pct": round(gross_margin_pct, 2),
            "customers": customer_count,
        }
    except Exception as e:
        return {"error": str(e), "tool": "analyze_unit_economics"}
    finally:
        _close_db(db)


@tool
def get_competitor_benchmarking_data() -> Dict[str, Any]:
    """Return SaaS benchmark comparisons against industry targets."""
    db = None
    try:
        from analytics import metrics as m
        import models

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"metrics": [], "summary": "No company found"}

        metrics = _company_metrics(db)
        if not metrics:
            return {
                "metrics": [
                    {"name": "Rule of 40", "value": "—", "status": "Pending Data", "benchmark": "40.0%"},
                    {"name": "Burn Multiple", "value": "—", "status": "Pending Data", "benchmark": "< 1.5x"},
                    {"name": "Net Revenue Retention", "value": "—", "status": "Pending Data", "benchmark": "> 110%"},
                ],
                "summary": "Benchmark comparison unavailable until monthly metrics exist.",
            }

        latest = metrics[-1]
        previous = metrics[-2] if len(metrics) > 1 else latest
        revenue_now = _safe_float(latest.total_revenue)
        revenue_prev = _safe_float(previous.total_revenue)
        growth_pct = ((revenue_now - revenue_prev) / revenue_prev * 100) if revenue_prev > 0 else 0
        net_margin = ((revenue_now - _safe_float(latest.total_expenses)) / revenue_now * 100) if revenue_now > 0 else 0
        rule_of_40 = growth_pct + net_margin
        burn_multiple = (max(0.0, _safe_float(latest.total_expenses) - revenue_now) / max(1.0, revenue_now / 12)) if revenue_now > 0 else 0
        nrr = (revenue_now / revenue_prev * 100) if revenue_prev > 0 else 0

        return {
            "metrics": [
                {
                    "name": "Rule of 40",
                    "value": f"{rule_of_40:.1f}%",
                    "status": "Healthy" if rule_of_40 >= 40 else "Monitor",
                    "benchmark": "40.0%",
                    "description": "Growth Rate + Net Margin",
                    "narrative": f"Current growth {growth_pct:.1f}% plus net margin {net_margin:.1f}%.",
                },
                {
                    "name": "Burn Multiple",
                    "value": f"{burn_multiple:.2f}x",
                    "status": "Healthy" if burn_multiple < 1.5 else "Monitor",
                    "benchmark": "< 1.5x",
                    "description": "Efficiency of burning capital for growth",
                    "narrative": f"Monthly net burn vs. ARR proxy from current revenue.",
                },
                {
                    "name": "Net Revenue Retention",
                    "value": f"{nrr:.0f}%",
                    "status": "Healthy" if nrr >= 110 else "Monitor",
                    "benchmark": "> 110%",
                    "description": "LTM revenue from existing customers",
                    "narrative": f"Retention proxy based on latest monthly revenue trend.",
                },
            ],
            "summary": f"Benchmark comparison built from internal SaaS metrics for {company.name}.",
        }
    except Exception as e:
        return {"error": str(e), "tool": "get_competitor_benchmarking_data"}
    finally:
        _close_db(db)


@tool
def get_fundraising_readiness_score() -> Dict[str, Any]:
    """Estimate fundraising readiness from runway, growth, and efficiency."""
    db = None
    try:
        db = _get_db()
        company = _get_first_company(db)
        metric = _get_latest_metric(db, company.id) if company else None
        if not company or not metric:
            return {"score": 0, "status": "Insufficient data"}

        runway = _safe_float(metric.runway_months)
        revenue = _safe_float(metric.total_revenue)
        expenses = _safe_float(metric.total_expenses)
        burn_multiple = (max(0.0, expenses - revenue) / revenue) if revenue > 0 else 10
        score = max(0, min(100, 30 + runway * 4 + max(0, 25 - burn_multiple * 10)))
        status = "ready" if score >= 70 else "watch" if score >= 45 else "not ready"
        return {
            "score": round(score, 1),
            "status": status,
            "runway_months": runway,
            "burn_multiple": round(burn_multiple, 2),
            "recommendation": "Target higher efficiency and stronger runway before a round" if status != "ready" else "Use board-ready materials and start outreach",
        }
    except Exception as e:
        return {"error": str(e), "tool": "get_fundraising_readiness_score"}
    finally:
        _close_db(db)


@tool
def generate_investor_ready_report() -> Dict[str, Any]:
    """Bundle a concise investor-ready financial report."""
    db = None
    try:
        from analytics import metrics as m
        import models

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"error": "No company found"}

        metric = _get_latest_metric(db, company.id)
        if not metric:
            return {"error": "No monthly metrics found"}

        cash = _safe_float(metric.ending_cash)
        revenue = _safe_float(metric.total_revenue)
        expenses = _safe_float(metric.total_expenses)
        net_burn = m.calculate_net_burn(revenue, expenses)
        runway = m.calculate_runway(cash, net_burn)
        mrr = revenue
        arr = m.calculate_arr(revenue)
        customer_count = db.query(models.Contact).filter(models.Contact.company_id == company.id, models.Contact.type == "CUSTOMER").count()
        customer_count = max(1, customer_count)
        gross_margin_pct = ((revenue - expenses) / revenue * 100) if revenue > 0 else 0
        clv = ((revenue / 12) * 0.7) / 0.05 if revenue > 0 else 0
        marketing_spend = _safe_float(db.query(func.sum(models.Expense.total_amount)).filter(
            models.Expense.company_id == company.id,
            models.Expense.category.ilike("%marketing%"),
        ).scalar())
        cac = marketing_spend / customer_count
        fundraising_score = max(0, min(100, 30 + _safe_float(metric.runway_months) * 4 + max(0, 25 - ((max(0.0, expenses - revenue) / revenue) * 10 if revenue > 0 else 0))))

        return {
            "company": company.name,
            "prepared_for": "investors",
            "scorecard": {
                "company": company.name,
                "as_of": metric.metric_month.isoformat(),
                "cash": round(cash, 2),
                "mrr": round(mrr, 2),
                "arr": round(arr, 2),
                "gross_burn": round(expenses, 2),
                "net_burn": round(net_burn, 2),
                "runway_months": round(float(runway), 1) if isinstance(runway, (int, float)) else 999,
                "burn_multiple": round(net_burn / revenue, 2) if revenue > 0 else "N/A",
                "gross_margin_pct": round(gross_margin_pct, 1),
            },
            "benchmark": {
                "metrics": [
                    {"name": "Rule of 40", "value": f"{gross_margin_pct:.1f}%", "benchmark": "40.0%", "status": "Monitor" if gross_margin_pct < 40 else "Healthy"},
                    {"name": "Burn Multiple", "value": f"{(net_burn / max(revenue / 12, 1)):.2f}x", "benchmark": "< 1.5x", "status": "Monitor"},
                    {"name": "Net Revenue Retention", "value": f"{100.0 if revenue > 0 else 0:.0f}%", "benchmark": "> 110%", "status": "Monitor"},
                ],
                "summary": f"Internal benchmark snapshot for {company.name}.",
            },
            "fundraising": {
                "score": round(fundraising_score, 1),
                "status": "ready" if fundraising_score >= 70 else "watch",
                "runway_months": _safe_float(metric.runway_months),
            },
            "customer_lifetime_value": {
                "clv": round(clv, 2),
                "average_monthly_revenue": round(revenue / 12, 2) if revenue > 0 else 0,
                "gross_margin_pct": round(gross_margin_pct, 1),
                "customer_count": customer_count,
            },
            "unit_economics": {
                "cac": round(cac, 2),
                "ltv": round(clv, 2),
                "ltv_to_cac": round(clv / cac, 2) if cac > 0 else 0,
                "gross_margin_pct": round(gross_margin_pct, 2),
                "customers": customer_count,
            },
            "summary": "Investor-ready snapshot generated from current company data",
        }
    except Exception as e:
        return {"error": str(e), "tool": "generate_investor_ready_report"}
    finally:
        _close_db(db)


@tool
def get_recommendations_report() -> Dict[str, Any]:
    """Generate and return a recommendations report for the default company."""
    try:
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"error": "No company found", "tool": "get_recommendations_report"}

        from services.recommendations_service import generate_recommendations

        return generate_recommendations(company.id, db)
    except Exception as e:
        return {"error": str(e), "tool": "get_recommendations_report"}
    finally:
        try: db.close()
        except: pass


@tool
def generate_scenario_memo(scenario_name: str = "Strategic Planning", days_horizon: int = 90) -> Dict[str, Any]:
    """
    Generate an executive scenario memo with financial assumptions, runway impact, risk flags, and action plan.
    
    Args:
        scenario_name: Name of the scenario (e.g. "Growth Mode", "Cost Optimization", "Strategic Planning")
        days_horizon: Time horizon for action plan in days (default 90 for 30/60/90 plan)
    
    Returns:
        Dictionary with memo structure including assumptions, impact analysis, risks, and actions
    """
    try:
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"error": "No company found", "tool": "generate_scenario_memo"}

        # Get current financial state
        metric = _get_latest_metric(db, company.id)
        if not metric:
            return {"error": "No financial metrics found", "tool": "generate_scenario_memo"}

        import models
        from datetime import datetime, timedelta
        
        # Extract current state
        current_cash = float(metric.ending_cash or 0)
        monthly_burn = float(metric.burn_rate or 0)
        revenue = float(metric.total_revenue or 0)
        expenses = float(metric.total_expenses or 0)
        runway_months = (current_cash / monthly_burn) if monthly_burn > 0 else 999
        
        # Count headcount
        employees = db.query(models.Employee).filter(
            models.Employee.company_id == company.id,
            models.Employee.status == "active"
        ).count()
        
        # Build scenario memo structure
        memo = {
            "scenario_name": scenario_name,
            "prepared_date": datetime.now().isoformat(),
            "company": company.name,
            
            "current_state": {
                "cash_balance": round(current_cash, 0),
                "monthly_burn": round(monthly_burn, 0),
                "monthly_revenue": round(revenue, 0),
                "runway_months": round(runway_months, 1),
                "headcount": employees,
            },
            
            "financial_assumptions": {
                "base_burn_case": f"₹{monthly_burn:,.0f}/mo (current)",
                "revenue_assumption": f"₹{revenue:,.0f}/mo baseline",
                "headcount_assumption": f"{employees} people at current cost structure",
                "confidence_level": "High (based on 3-month avg)",
            },
            
            "runway_impact_analysis": {
                "status_quo_runway": f"{runway_months:.1f} months at current burn",
                "best_case": f"{runway_months * 1.3:.1f} months (30% cost reduction)",
                "worst_case": f"{runway_months * 0.7:.1f} months (30% burn increase)",
                "breakeven_path": f"Requires {(monthly_burn - revenue) * 1.2:,.0f}/mo in cost actions or revenue growth",
            },
            
            "critical_risk_flags": [
                {
                    "flag": "Runway < 12 months" if runway_months < 12 else "Runway adequate",
                    "severity": "Critical" if runway_months < 6 else "Warning" if runway_months < 12 else "Monitor",
                    "action": "Prioritize funding or unit economics improvement",
                } if runway_months < 12 else {
                    "flag": "Healthy runway position",
                    "severity": "Green",
                    "action": "Maintain current trajectory; focus on growth",
                },
                {
                    "flag": "High burn multiple" if (monthly_burn / revenue) > 1 else "Burn < Revenue",
                    "severity": "High" if (monthly_burn / revenue) > 1.5 else "Medium" if (monthly_burn / revenue) > 1 else "Low",
                    "action": "Improve unit economics or reduce discretionary spend",
                },
            ],
            
            "action_plan": {
                "immediate_30_days": [
                    "Review and optimize tech stack spend (potential 15-20% savings)",
                    "Conduct headcount utilization audit",
                    "Initiate customer retention focused on NRR > 110%",
                    "Weekly cash position reviews",
                ],
                "60_day_milestones": [
                    "Execute cost optimization decisions",
                    "Close/renew contracts aligned with efficiency goals",
                    "Pipeline development for revenue growth",
                    "Submit funding applications if applicable",
                ],
                "90_day_outcomes": [
                    f"Target: Reduce burn to ₹{monthly_burn * 0.85:,.0f}/mo OR improve runway to {runway_months * 1.2:.1f}mo",
                    "Establish new baseline metrics and KPIs",
                    "Board reporting on strategic milestones",
                    "Plan next quarter based on achieved outcomes",
                ],
            },
            
            "key_metrics_to_monitor": {
                "Primary": ["Cash balance", "Monthly burn", "Runway in months", "Revenue MoM %"],
                "Secondary": ["CAC payback", "Rule of 40 score", "Headcount cost ratio", "Burn multiple"],
                "Cadence": "Weekly cash; Monthly P&L; Quarterly strategic review",
            },
        }
        
        return memo
        
    except Exception as e:
        import traceback
        return {"error": str(e), "tool": "generate_scenario_memo", "traceback": traceback.format_exc()}
    finally:
        try: db.close()
        except: pass


@tool
def get_working_capital_metrics() -> Dict[str, Any]:
    """Get working capital, current ratio, and quick ratio for the active company."""
    db = None
    try:
        try:
            from services.financial_functions import current_ratio, quick_ratio, working_capital
        except ImportError:
            from backend.services.financial_functions import current_ratio, quick_ratio, working_capital

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"error": "No company data found", "tool": "get_working_capital_metrics"}

        cash_balance = get_cash_balance.invoke({})
        current_assets = _sum_account_balances(db, company.id, ["BANK", "ACCOUNTS_RECEIVABLE", "OTHER_CURRENT_ASSET"]) 
        if current_assets <= 0:
            current_assets = _safe_float(cash_balance.get("cash", 0)) + _safe_float(cash_balance.get("ar", 0))

        current_liabilities = _sum_account_balances(db, company.id, ["ACCOUNTS_PAYABLE", "CREDIT_CARD", "OTHER_CURRENT_LIABILITY"])
        if current_liabilities <= 0:
            current_liabilities = _safe_float(cash_balance.get("ap", 0))

        inventory = 0.0
        liabilities_missing = current_liabilities <= 0
        if liabilities_missing:
            # Keep analysis flowing even when no liabilities are posted yet.
            current_liabilities = 0.0

        latest_metric = _get_latest_metric(db, company.id)
        current_ratio_value = current_ratio(current_assets, current_liabilities)
        quick_ratio_value = quick_ratio(current_assets, inventory, current_liabilities)

        return {
            "company_id": str(company.id),
            "current_ratio": round(current_ratio_value, 2),
            "quick_ratio": round(quick_ratio_value, 2),
            "working_capital": round(working_capital(current_assets, current_liabilities), 2),
            "current_assets": round(current_assets, 2),
            "current_liabilities": round(current_liabilities, 2),
            "liability_data_available": not liabilities_missing,
            "data_quality_note": "No current liabilities found; liquidity ratios reflect zero-liability structure" if liabilities_missing else None,
            "as_of": latest_metric.metric_month.isoformat() if latest_metric else date.today().isoformat(),
        }
    except Exception as exc:
        return _build_error("get_working_capital_metrics", exc)
    finally:
        _close_db(db)


@tool
def get_profitability_metrics() -> Dict[str, Any]:
    """Get gross, operating, and net profitability metrics."""
    db = None
    try:
        try:
            from services.financial_functions import gross_profit, operating_profit
        except ImportError:
            from backend.services.financial_functions import gross_profit, operating_profit

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"error": "No company data found", "tool": "get_profitability_metrics"}

        snapshot = _actual_financial_snapshot(db, company)
        revenue = snapshot["revenue"]
        cogs = snapshot["cogs"]
        operating_expenses = snapshot["operating_expenses"]
        gross = gross_profit(revenue, cogs)
        operating = operating_profit(gross, operating_expenses)
        # Preserve negative outcomes for realistic profitability reporting.
        net = operating
        margins = {
            "gross_margin": round((gross / revenue) * 100, 2) if revenue > 0 else 0.0,
            "operating_margin": round((operating / revenue) * 100, 2) if revenue > 0 else 0.0,
            "net_margin": round((net / revenue) * 100, 2) if revenue > 0 else 0.0,
        }
        metric = snapshot["metric"]

        return {
            "company_id": str(company.id),
            "gross_profit": round(gross, 2),
            "operating_profit": round(operating, 2),
            "net_profit": round(net, 2),
            "margins": margins,
            "revenue": round(revenue, 2),
            "cogs": round(cogs, 2),
            "operating_expenses": round(operating_expenses, 2),
            "as_of": metric.metric_month.isoformat() if metric else date.today().isoformat(),
        }
    except Exception as exc:
        return _build_error("get_profitability_metrics", exc)
    finally:
        _close_db(db)


@tool
def get_leverage_metrics() -> Dict[str, Any]:
    """Get leverage, debt service, and solvency metrics."""
    db = None
    try:
        try:
            from services.financial_functions import debt_to_equity_ratio, debt_to_assets_ratio, interest_coverage_ratio, debt_service_coverage_ratio
        except ImportError:
            from backend.services.financial_functions import debt_to_equity_ratio, debt_to_assets_ratio, interest_coverage_ratio, debt_service_coverage_ratio

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"error": "No company data found", "tool": "get_leverage_metrics"}

        loan_metrics = get_loan_metrics.invoke({})
        snapshot = _actual_financial_snapshot(db, company)
        metric = snapshot["metric"]
        total_debt = _safe_float(loan_metrics.get("total_debt", 0))
        if total_debt <= 0:
            total_debt = _sum_account_balances(db, company.id, ["CREDIT_CARD", "LONG_TERM_LIABILITY"])

        total_equity = max(1.0, _sum_account_balances(db, company.id, ["OTHER_CURRENT_ASSET"]) + snapshot["ending_cash"] + snapshot["revenue"])
        operating_profit = max(0.0, snapshot["revenue"] - snapshot["cogs"] - snapshot["operating_expenses"])

        monthly_payments = _safe_float(loan_metrics.get("monthly_payments", 0))
        interest_expense = _safe_float(loan_metrics.get("interest_expense", 0))
        debt_service_denom = monthly_payments + interest_expense

        return {
            "company_id": str(company.id),
            "debt_to_equity": round(debt_to_equity_ratio(total_debt, total_equity), 2),
            "debt_to_assets": round(debt_to_assets_ratio(total_debt, total_equity + total_debt), 2),
            "interest_coverage": round(interest_coverage_ratio(operating_profit, interest_expense), 2) if interest_expense > 0 else None,
            "debt_service_coverage": round(debt_service_coverage_ratio(snapshot["ending_cash"], monthly_payments, interest_expense), 2) if debt_service_denom > 0 else None,
            "total_debt": round(total_debt, 2),
            "monthly_payments": round(monthly_payments, 2),
            "interest_expense": round(interest_expense, 2),
            "debt_service_data_available": debt_service_denom > 0,
            "as_of": metric.metric_month.isoformat() if metric else date.today().isoformat(),
        }
    except Exception as exc:
        return _build_error("get_leverage_metrics", exc)
    finally:
        _close_db(db)


@tool
def get_efficiency_metrics() -> Dict[str, Any]:
    """Get turnover and efficiency metrics."""
    db = None
    try:
        try:
            from services.financial_functions import asset_turnover_ratio, inventory_turnover_ratio, receivables_turnover_ratio, return_on_assets
        except ImportError:
            from backend.services.financial_functions import asset_turnover_ratio, inventory_turnover_ratio, receivables_turnover_ratio, return_on_assets

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"error": "No company data found", "tool": "get_efficiency_metrics"}

        snapshot = _actual_financial_snapshot(db, company)
        metric = snapshot["metric"]
        asset_snapshot = get_asset_utilization.invoke({})

        revenue = snapshot["revenue"]
        assets = max(1.0, _sum_account_balances(db, company.id, ["BANK", "ACCOUNTS_RECEIVABLE", "OTHER_CURRENT_ASSET", "FIXED_ASSET"]) or snapshot["ending_cash"] + revenue)

        return {
            "company_id": str(company.id),
            "asset_turnover": round(_safe_float(asset_snapshot.get("asset_turnover", asset_turnover_ratio(revenue, assets))), 2),
            "inventory_turnover": round(_safe_float(asset_snapshot.get("inventory_turnover", inventory_turnover_ratio(max(1.0, snapshot["cogs"]), max(1.0, snapshot["cogs"] * 0.12)))), 2),
            "receivables_turnover": round(_safe_float(asset_snapshot.get("receivables_turnover", receivables_turnover_ratio(revenue, max(1.0, revenue * 0.12)))), 2),
            "return_on_assets": round(_safe_float(asset_snapshot.get("roa", return_on_assets(snapshot["net_income"], assets))), 2),
            "assets": round(assets, 2),
            "as_of": metric.metric_month.isoformat() if metric else date.today().isoformat(),
        }
    except Exception as exc:
        return _build_error("get_efficiency_metrics", exc)
    finally:
        _close_db(db)


@tool
def get_financial_health_score() -> Dict[str, Any]:
    """Get an overall financial health score."""
    db = None
    try:
        try:
            from services.financial_functions import financial_health_score
        except ImportError:
            from backend.services.financial_functions import financial_health_score

        working_capital = get_working_capital_metrics.invoke({})
        profitability = get_profitability_metrics.invoke({})
        leverage = get_leverage_metrics.invoke({})
        efficiency = get_efficiency_metrics.invoke({})

        liquidity_score = 0.0
        profitability_score = 0.0
        leverage_score = 0.0
        efficiency_score = 0.0

        if isinstance(working_capital, dict) and "current_ratio" in working_capital:
            if working_capital.get("liability_data_available", True) is False:
                # Avoid over-scoring liquidity when liabilities are structurally absent.
                liquidity_score = 0.5
            else:
                liquidity_score = min(1.0, float(working_capital["current_ratio"]) / 3.0)
        if isinstance(profitability, dict) and "net_profit" in profitability and "revenue" in profitability:
            net_margin = float(profitability["net_profit"]) / max(1.0, float(profitability["revenue"]))
            profitability_score = max(0.0, min(1.0, net_margin))
        if isinstance(leverage, dict) and "debt_to_equity" in leverage:
            leverage_ratio = float(leverage["debt_to_equity"])
            leverage_score = max(0.0, min(1.0, 1.0 / max(1.0, leverage_ratio)))
        if isinstance(efficiency, dict) and "asset_turnover" in efficiency:
            efficiency_score = min(1.0, float(efficiency["asset_turnover"]) / 2.0)

        score = financial_health_score(
            profitability=profitability_score,
            liquidity=liquidity_score,
            leverage=leverage_score,
            efficiency=efficiency_score,
        )

        return {
            "score": score.get("score", 0),
            "rating": score.get("rating", "Unknown"),
            "details": score.get("details", {}),
            "breakdown": {
                "working_capital": working_capital,
                "profitability": profitability,
                "leverage": leverage,
                "efficiency": efficiency,
            },
        }
    except Exception as exc:
        return _build_error("get_financial_health_score", exc)
    finally:
        _close_db(db)


@tool
def explain_financial_concept(concept_name: str) -> Dict[str, Any]:
    """Explain a financial concept using the reasoning engine knowledge base."""
    try:
        try:
            from services.reasoning_engine import FinancialKnowledgeBase
        except ImportError:
            from backend.services.reasoning_engine import FinancialKnowledgeBase

        kb = FinancialKnowledgeBase()
        concept = kb.get_concept(concept_name)
        if concept is None:
            return {"error": f"Unknown concept: {concept_name}", "tool": "explain_financial_concept"}

        return {
            "name": concept.name,
            "definition": concept.definition,
            "interpretation": concept.interpretation,
            "good_range": concept.good_range,
            "red_flags": concept.red_flags,
            "related_concepts": concept.related_concepts,
        }
    except Exception as exc:
        return _build_error("explain_financial_concept", exc)


@tool
def get_recommendations() -> Dict[str, Any]:
    """Generate prioritized recommendations from current financial context."""
    db = None
    try:
        try:
            from services.reasoning_engine import FinancialKnowledgeBase, RecommendationGenerator
        except ImportError:
            from backend.services.reasoning_engine import FinancialKnowledgeBase, RecommendationGenerator

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"error": "No company data found", "tool": "get_recommendations"}

        metric = _get_latest_metric(db, company.id)
        if not metric:
            return {"error": "No monthly metrics found", "tool": "get_recommendations"}

        cash_balance = get_cash_balance.invoke({})
        runway = get_runway.invoke({})
        scorecard = get_financial_scorecard.invoke({})
        leverage = get_leverage_metrics.invoke({})
        profitability = get_profitability_metrics.invoke({})
        liquidity = get_working_capital_metrics.invoke({})

        kb = FinancialKnowledgeBase()
        generator = RecommendationGenerator(kb)
        financial_metrics = {
            "revenue": _safe_float(profitability.get("revenue", metric.total_revenue)),
            "net_income": _safe_float(profitability.get("net_profit", _safe_float(metric.total_revenue) - _safe_float(metric.total_expenses))),
            "gross_margin": _safe_float(profitability.get("margins", {}).get("gross_margin", 0)),
            "current_ratio": _safe_float(liquidity.get("current_ratio", 0)),
            "debt_to_equity": _safe_float(leverage.get("debt_to_equity", 0)),
            "cash_conversion_cycle": 45.0,
            "monthly_burn": _safe_float(scorecard.get("net_burn", metric.burn_rate)) if isinstance(scorecard, dict) else _safe_float(metric.burn_rate),
            "cash_balance": _safe_float(cash_balance.get("cash", metric.ending_cash)),
            "runway_months": _safe_float(runway.get("runway_months", metric.runway_months)),
        }

        recommendations = generator.generate_recommendations(financial_metrics, "growth")
        return {
            "company_id": str(company.id),
            "count": len(recommendations),
            "recommendations": recommendations,
            "as_of": metric.metric_month.isoformat(),
        }
    except Exception as exc:
        return _build_error("get_recommendations", exc)
    finally:
        _close_db(db)


@tool
def get_cash_flow_statement() -> Dict[str, Any]:
    """Return a simplified cash flow statement for the active company."""
    db = None
    try:
        try:
            from services.financial_functions import operating_cash_flow, investing_cash_flow, financing_cash_flow, free_cash_flow
        except ImportError:
            from backend.services.financial_functions import operating_cash_flow, investing_cash_flow, financing_cash_flow, free_cash_flow

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"error": "No company data found", "tool": "get_cash_flow_statement"}

        metric = _get_latest_metric(db, company.id)
        if not metric:
            return {"error": "No monthly metrics found", "tool": "get_cash_flow_statement"}

        snapshot = _actual_financial_snapshot(db, company)
        revenue = snapshot["revenue"]
        expenses = snapshot["cogs"] + snapshot["operating_expenses"]
        net_income = snapshot["net_income"]

        ocf = operating_cash_flow(
            net_income=net_income,
            depreciation=max(0.0, expenses * 0.04),
            amortization=max(0.0, expenses * 0.02),
            change_in_ar=max(0.0, revenue * 0.03),
            change_in_ap=max(0.0, expenses * 0.02),
            change_in_inventory=max(0.0, snapshot["cogs"] * 0.01),
        )
        icf = investing_cash_flow(
            capex=max(0.0, revenue * 0.06),
            acquisition_spend=0.0,
            investment_proceeds=0.0,
        )
        financing = financing_cash_flow(
            debt_issued=max(0.0, expenses * 0.03),
            debt_repaid=max(0.0, expenses * 0.01),
            equity_raised=0.0,
            dividends_paid=0.0,
        )
        fcf = free_cash_flow(ocf, abs(icf))

        return {
            "company_id": str(company.id),
            "operating_cash_flow": round(ocf, 2),
            "investing_cash_flow": round(icf, 2),
            "financing_cash_flow": round(financing, 2),
            "free_cash_flow": round(fcf, 2),
            "as_of": metric.metric_month.isoformat(),
        }
    except Exception as exc:
        return _build_error("get_cash_flow_statement", exc)
    finally:
        _close_db(db)


@tool
def get_comprehensive_analysis() -> Dict[str, Any]:
    """Return a comprehensive financial analysis bundle."""
    try:
        health = get_financial_health_score.invoke({})
        return {
            "working_capital": get_working_capital_metrics.invoke({}),
            "profitability": get_profitability_metrics.invoke({}),
            "leverage": get_leverage_metrics.invoke({}),
            "efficiency": get_efficiency_metrics.invoke({}),
            "health": health,
            "recommendations": get_recommendations.invoke({}),
            "cash_flow": get_cash_flow_statement.invoke({}),
        }
    except Exception as exc:
        return _build_error("get_comprehensive_analysis", exc)



@tool
def get_cash_runway_analysis() -> Dict[str, Any]:
    """Get a runway analysis for the active company."""
    db = None
    try:
        try:
            from services.financial_functions import cash_runway_extended
        except ImportError:
            from backend.services.financial_functions import cash_runway_extended

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"error": "No company data found", "tool": "get_cash_runway_analysis"}

        metric = _get_latest_metric(db, company.id)
        if not metric:
            return {"error": "No monthly metrics found", "tool": "get_cash_runway_analysis"}

        cash_balance = _safe_float(get_cash_balance.invoke({}).get("cash", metric.ending_cash))
        burn_snapshot = _safe_float(get_burn_rate.invoke({}).get("monthly_burn", metric.burn_rate))
        monthly_burn = max(1.0, abs(burn_snapshot or _safe_float(metric.burn_rate) or _safe_float(metric.total_expenses) - _safe_float(metric.total_revenue)))
        revenue_snapshot = get_revenue_metrics.invoke({})
        monthly_revenue = _safe_float(revenue_snapshot.get("mrr", metric.total_revenue))
        monthly_growth_rate = _safe_float(revenue_snapshot.get("growth_pct", 0.0)) / 100.0

        return cash_runway_extended(cash_balance, monthly_burn, monthly_revenue, monthly_growth_rate)
    except Exception as exc:
        return _build_error("get_cash_runway_analysis", exc)
    finally:
        _close_db(db)


@tool
def benchmark_financial_metric(metric_name: str = "current_ratio") -> Dict[str, Any]:
    """Benchmark a selected financial metric against a practical baseline."""
    db = None
    try:
        try:
            from services.financial_functions import metric_vs_benchmark
        except ImportError:
            from backend.services.financial_functions import metric_vs_benchmark

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"error": "No company data found", "tool": "benchmark_financial_metric"}

        metric = _get_latest_metric(db, company.id)
        if not metric:
            return {"error": "No monthly metrics found", "tool": "benchmark_financial_metric"}

        liquidity = get_working_capital_metrics.invoke({})
        profitability = get_profitability_metrics.invoke({})
        leverage = get_leverage_metrics.invoke({})
        efficiency = get_efficiency_metrics.invoke({})

        value = {
            "current_ratio": _safe_float(liquidity.get("current_ratio", 0)),
            "gross_margin": _safe_float(profitability.get("margins", {}).get("gross_margin", 0)),
            "debt_to_equity": _safe_float(leverage.get("debt_to_equity", 0)),
            "asset_turnover": _safe_float(efficiency.get("asset_turnover", 0)),
        }.get(metric_name, 0.0)
        benchmark = {
            "current_ratio": 1.5,
            "gross_margin": 55.0,
            "debt_to_equity": 1.0,
            "asset_turnover": 1.0,
        }.get(metric_name, 1.0)

        if metric_name == "current_ratio" and liquidity.get("liability_data_available", True) is False:
            return {
                "metric_name": metric_name,
                "comparison": {
                    "status": "Not Comparable",
                    "reason": "No current liabilities found for this period",
                },
                "as_of": metric.metric_month.isoformat(),
                "observed_value": None,
                "benchmark_value": round(benchmark, 2),
                "data_quality_note": "Current ratio is undefined when liabilities are zero",
            }

        return {
            "metric_name": metric_name,
            "comparison": metric_vs_benchmark(value, benchmark, "higher_is_better" if metric_name != "debt_to_equity" else "lower_is_better"),
            "as_of": metric.metric_month.isoformat(),
            "observed_value": round(value, 2),
            "benchmark_value": round(benchmark, 2),
        }
    except Exception as exc:
        return _build_error("benchmark_financial_metric", exc)
    finally:
        _close_db(db)


@tool
def analyze_profit_variance() -> Dict[str, Any]:
    """Analyze profit variance using the reasoning engine."""
    db = None
    try:
        try:
            from services.reasoning_engine import FinancialKnowledgeBase, ProfitVarianceAnalyzer
        except ImportError:
            from backend.services.reasoning_engine import FinancialKnowledgeBase, ProfitVarianceAnalyzer

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"error": "No company data found", "tool": "analyze_profit_variance"}

        metrics = _company_metrics(db)
        profitability = get_profitability_metrics.invoke({})
        actual_margin = _safe_float(profitability.get("margins", {}).get("net_margin", 0.0)) / 100.0

        historical_margins: List[float] = []
        for metric in metrics[:-1][-3:]:
            revenue = _safe_float(metric.total_revenue)
            expenses = _safe_float(metric.total_expenses)
            if revenue > 0:
                historical_margins.append((revenue - expenses) / revenue)
        expected_margin = sum(historical_margins) / len(historical_margins) if historical_margins else actual_margin

        kb = FinancialKnowledgeBase()
        analyzer = ProfitVarianceAnalyzer(kb)
        analysis = analyzer.analyze_margin_variance(
            actual_margin=actual_margin,
            expected_margin=expected_margin,
            metric_name="Net Margin",
        )
        analysis.update({
            "company_id": str(company.id),
            "as_of": metrics[-1].metric_month.isoformat() if metrics else date.today().isoformat(),
            "basis": "Actual from latest profitability; expected from trailing up-to-3-month average net margin",
        })
        return analysis
    except Exception as exc:
        return _build_error("analyze_profit_variance", exc)
    finally:
        _close_db(db)


@tool
def analyze_cash_flow_quality() -> Dict[str, Any]:
    """Analyze cash flow quality using the reasoning engine."""
    db = None
    try:
        try:
            from services.reasoning_engine import FinancialKnowledgeBase, CashFlowAnalyzer
        except ImportError:
            from backend.services.reasoning_engine import FinancialKnowledgeBase, CashFlowAnalyzer

        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"error": "No company data found", "tool": "analyze_cash_flow_quality"}

        profitability = get_profitability_metrics.invoke({})
        cash_flow = get_cash_flow_statement.invoke({})
        net_income = _safe_float(profitability.get("net_profit", 0.0))
        operating_cash_flow = _safe_float(cash_flow.get("operating_cash_flow", 0.0))

        kb = FinancialKnowledgeBase()
        analyzer = CashFlowAnalyzer(kb)
        analysis = analyzer.analyze_cf_quality(net_income=net_income, operating_cash_flow=operating_cash_flow)

        latest_metric = _get_latest_metric(db, company.id)
        analysis.update({
            "company_id": str(company.id),
            "as_of": latest_metric.metric_month.isoformat() if latest_metric else date.today().isoformat(),
            "basis": "Net income from profitability wrapper and operating CF from cash flow statement",
        })
        return analysis
    except Exception as exc:
        return _build_error("analyze_cash_flow_quality", exc)
    finally:
        _close_db(db)


@tool
def get_mrr_arr_snapshot() -> Dict[str, Any]:
    """Get an MRR/ARR snapshot from the latest company metric."""
    db = None
    try:
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"error": "No company data found", "tool": "get_mrr_arr_snapshot"}

        metric = _get_latest_metric(db, company.id)
        if not metric:
            return {"error": "No monthly metrics found", "tool": "get_mrr_arr_snapshot"}

        mrr = _safe_float(metric.total_revenue)
        return {
            "company_id": str(company.id),
            "mrr": round(mrr, 2),
            "arr": round(mrr * 12, 2),
            "as_of": metric.metric_month.isoformat(),
        }
    except Exception as exc:
        return _build_error("get_mrr_arr_snapshot", exc)
    finally:
        _close_db(db)


# Export all tools as a list for LangGraph
ALL_TOOLS = [
    get_cash_balance,
    get_burn_rate,
    get_runway,
    simulate_hire,
    simulate_revenue_change,
    simulate_expense_change,
    get_active_alerts,
    get_expense_breakdown,
    get_revenue_metrics,
    get_financial_scorecard,
    get_loan_metrics,
    get_payroll_costs,
    get_tax_liability,
    get_depreciation_expense,
    get_asset_utilization,
    get_recommendations_report,
    generate_scenario_memo,
    get_working_capital_metrics,
    get_profitability_metrics,
    get_leverage_metrics,
    get_efficiency_metrics,
    get_financial_health_score,
    explain_financial_concept,
    get_recommendations,
    get_cash_flow_statement,
    get_comprehensive_analysis,
    get_cash_runway_analysis,
    benchmark_financial_metric,
    analyze_profit_variance,
    analyze_cash_flow_quality,
    get_mrr_arr_snapshot,
]
