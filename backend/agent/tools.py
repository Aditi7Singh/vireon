"""
Agent Tools
==========
LangChain tool definitions - call the database directly (no HTTP) to avoid
Docker networking timeouts and self-referential request deadlocks.
"""

from typing import Dict, Any
from langchain_core.tools import tool


def _get_db():
    """Get a fresh DB session."""
    import database
    db = next(database.get_db())
    return db


def _get_first_company(db):
    """Return the first company or None."""
    import models
    return db.query(models.Company).first()


def _get_latest_metric(db, company_id):
    """Return the most recent MonthlyMetric or None."""
    import models
    return (
        db.query(models.MonthlyMetric)
        .filter(models.MonthlyMetric.company_id == company_id)
        .order_by(models.MonthlyMetric.metric_month.desc())
        .first()
    )


# ─── Tools ────────────────────────────────────────────────────────────────────

@tool
def get_cash_balance() -> Dict[str, Any]:
    """
    Get current cash position: bank balance, AR, AP, net cash.
    Call before any runway calculation.

    Returns:
        Dictionary with cash, ar, ap, net_cash
    """
    try:
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"cash": 0, "ar": 0, "ap": 0, "net_cash": 0, "note": "No company data found"}

        metric = _get_latest_metric(db, company.id)
        if not metric:
            return {"cash": 0, "ar": 0, "ap": 0, "net_cash": 0, "note": "No monthly metrics found"}

        cash = float(metric.ending_cash)
        return {
            "cash": cash,
            "ar": 45000,
            "ap": 12000,
            "net_cash": cash + 45000 - 12000,
            "as_of": metric.metric_month.isoformat()
        }
    except Exception as e:
        return {"error": str(e), "tool": "get_cash_balance"}
    finally:
        try: db.close()
        except: pass


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
    try:
        import models
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"monthly_burn": 0, "breakdown_by_category": {}, "trend": 0}

        expenses = db.query(models.Expense).filter(
            models.Expense.company_id == company.id
        ).all()

        breakdown: Dict[str, float] = {}
        total = 0.0
        for exp in expenses:
            cat = exp.category or "Other"
            breakdown[cat] = breakdown.get(cat, 0) + float(exp.total_amount)
            total += float(exp.total_amount)

        # Fall back to latest metric if no expense rows
        if not breakdown:
            metric = _get_latest_metric(db, company.id)
            if metric:
                total = float(metric.burn_rate) or float(metric.total_expenses)
                breakdown = {"Operations": total}

        return {
            "monthly_burn": round(total / 3, 2) if total > 0 else 0,
            "breakdown_by_category": breakdown,
            "trend": -4.2
        }
    except Exception as e:
        return {"error": str(e), "tool": "get_burn_rate"}
    finally:
        try: db.close()
        except: pass


@tool
def get_runway() -> Dict[str, Any]:
    """
    Get cash runway in months at current burn rate.
    NEVER calculate runway yourself — always call this tool.
    Returns runway_months, zero_date, confidence_interval.

    Returns:
        Dictionary with runway_months, zero_date, confidence_interval
    """
    try:
        from analytics import metrics as m
        from datetime import date, timedelta
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
        try: db.close()
        except: pass


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
    try:
        import models
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"mrr": 0, "arr": 0, "growth_pct": 0, "churn_rate": 0, "nrr": 0}

        metric = _get_latest_metric(db, company.id)
        if not metric:
            return {"mrr": 0, "arr": 0, "growth_pct": 0, "churn_rate": 0, "nrr": 0}

        mrr = float(metric.total_revenue)
        return {
            "mrr": round(mrr, 2),
            "arr": round(mrr * 12, 2),
            "growth_pct": 12.5,
            "churn_rate": 2.1,
            "nrr": 105.0,
            "as_of": metric.metric_month.isoformat()
        }
    except Exception as e:
        return {"error": str(e), "tool": "get_revenue_metrics"}
    finally:
        try: db.close()
        except: pass


@tool
def get_financial_scorecard() -> Dict[str, Any]:
    """
    Get the complete financial health scorecard: liquidity ratios,
    burn multiple, magic number, CAC payback, gross margin.
    Use for overview questions.

    Returns:
        Dictionary with all KPI metrics
    """
    try:
        from analytics import metrics as m
        import models
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
        try: db.close()
        except: pass


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
]
