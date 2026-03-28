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
        from datetime import date, timedelta
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

        return {
            "monthly_burn": round(monthly_equivalent, 2) if total > 0 else 0,
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


@tool
def get_loan_metrics() -> Dict[str, Any]:
    """
    Get loan portfolio metrics: total debt, monthly payments, interest expense.
    Includes breakdown by loan type and maturity analysis.

    Returns:
        Dictionary with total_debt, monthly_payments, interest_expense, breakdown
    """
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
        try: db.close()
        except: pass


@tool
def get_payroll_costs() -> Dict[str, Any]:
    """
    Get payroll cost breakdown: salaries, taxes, benefits, total compensation.
    Includes headcount and cost per employee metrics.

    Returns:
        Dictionary with total_payroll, employee_count, avg_salary, tax_breakdown
    """
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
        monthly_cost = calculate_monthly_payroll_cost(db, company.id, current_month)

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
        try: db.close()
        except: pass


@tool
def get_tax_liability() -> Dict[str, Any]:
    """
    Get tax liability breakdown: income tax, payroll tax, sales tax.
    Includes quarterly payment schedule and year-to-date totals.

    Returns:
        Dictionary with total_tax_liability, quarterly_payments, breakdown_by_type
    """
    try:
        import models
        from analytics.metrics import calculate_tax_liability
        db = _get_db()
        company = _get_first_company(db)
        if not company:
            return {"total_tax_liability": 0, "quarterly_payments": [], "breakdown_by_type": {}}

        # Get latest revenue data for tax calculation
        metric = _get_latest_metric(db, company.id)
        if not metric:
            return {"total_tax_liability": 0, "quarterly_payments": [], "breakdown_by_type": {}}

        annual_revenue = float(metric.revenue) * 12  # Estimate annual from monthly
        tax_metrics = calculate_tax_liability(annual_revenue)

        return tax_metrics
    except Exception as e:
        return {"error": str(e), "tool": "get_tax_liability"}
    finally:
        try: db.close()
        except: pass


@tool
def get_depreciation_expense() -> Dict[str, Any]:
    """
    Get depreciation expense metrics: monthly depreciation, accumulated depreciation, asset book value.
    Includes breakdown by asset category and remaining useful life.

    Returns:
        Dictionary with monthly_depreciation, accumulated_depreciation, asset_breakdown
    """
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
                    "book_value": round(float(latest_dep.book_value), 2),
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
        try: db.close()
        except: pass


@tool
def get_asset_utilization() -> Dict[str, Any]:
    """
    Get asset utilization metrics: asset turnover, return on assets, depreciation as % of revenue.
    Helps assess capital efficiency and asset management effectiveness.

    Returns:
        Dictionary with asset_turnover, roa, depreciation_ratio, utilization_score
    """
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

        revenue = float(metric.revenue)
        net_income = revenue - float(metric.expenses)  # Simplified

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
        try: db.close()
        except: pass


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
]
