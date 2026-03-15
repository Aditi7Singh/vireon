"""Tool definitions for LangGraph agent — calls FastAPI backend endpoints.

Each tool:
  - Has a precise docstring for LLM decision-making
  - Calls the correct FastAPI endpoint using httpx
  - Has typed arguments with sensible defaults
  - Returns raw JSON dict on success
  - Returns {"error": str(e), "tool": "tool_name"} on failure (never raises)
  - Has a 10-second timeout
  
PRINCIPLE: Never self-calculate financial metrics. Always call the correct tool.
"""

import httpx
from typing import Any, Dict
from langchain_core.tools import tool
from backend.config.settings import Settings

# Initialize HTTP client configuration
BACKEND_URL = Settings.BACKEND_URL
TIMEOUT = 10.0  # seconds


@tool
def get_cash_balance() -> Dict[str, Any]:
    """
    Get current cash position: bank balance, AR, AP, net cash.
    Call before any runway calculation.
    
    Returns: {cash, ar, ap, net_cash}
    """
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(f"{BACKEND_URL}/cash-balance")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e), "tool": "get_cash_balance"}


@tool
def get_burn_rate(period_days: int = 30) -> Dict[str, Any]:
    """
    Get monthly cash burn. Use period_days=90 for a more stable average.
    Returns breakdown by category and trend vs prior period.
    
    Args:
        period_days: Number of days to calculate burn over (default 30)
    
    Returns: {monthly_burn, breakdown_by_category, trend}
    """
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            params = {"period": period_days}
            response = client.get(f"{BACKEND_URL}/burn-rate", params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e), "tool": "get_burn_rate"}


@tool
def get_runway() -> Dict[str, Any]:
    """
    Get cash runway in months at current burn.
    Returns runway_months, zero_date, confidence_interval.
    NEVER calculate runway yourself — always call this tool.
    
    Returns: {runway_months, zero_date, confidence_interval}
    """
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(f"{BACKEND_URL}/runway")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e), "tool": "get_runway"}


@tool
def simulate_hire(n_engineers: int, avg_annual_salary: int = 120000) -> Dict[str, Any]:
    """
    Simulate hiring N engineers. Returns new_runway_months, runway_delta (negative = reduction),
    monthly_burn_increase, break_even_mrr needed.
    
    Args:
        n_engineers: Number of engineers to hire
        avg_annual_salary: Average annual salary per engineer (default $120,000)
    
    Returns: {new_runway_months, runway_delta, monthly_burn_increase, break_even_mrr}
    """
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            payload = {"engineers": n_engineers, "avg_salary": avg_annual_salary}
            response = client.post(f"{BACKEND_URL}/scenario/hire", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e), "tool": "simulate_hire"}


@tool
def simulate_revenue_change(mrr_delta: float, probability: float = 1.0) -> Dict[str, Any]:
    """
    Simulate MRR change impact on runway. mrr_delta positive=gain, negative=loss.
    probability 0-1 weights the scenario.
    
    Args:
        mrr_delta: Monthly recurring revenue change amount (positive or negative)
        probability: Confidence in this change, 0-1 (default 1.0 = certain)
    
    Returns: {new_runway_months, runway_delta, revenue_impact}
    """
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            payload = {"mrr_delta": mrr_delta, "probability": probability}
            response = client.post(f"{BACKEND_URL}/scenario/revenue", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e), "tool": "simulate_revenue_change"}


@tool
def simulate_expense_change(category: str, change_pct: float) -> Dict[str, Any]:
    """
    Simulate expense change for a GL category (aws/payroll/saas/marketing).
    change_pct: -30 means reduce 30%, +20 means increase 20%.
    
    Args:
        category: Expense category name (e.g., 'aws', 'payroll', 'saas', 'marketing')
        change_pct: Percentage change (-100 to +100, negative = reduction)
    
    Returns: {new_runway_months, runway_delta, monthly_savings, affected_burn}
    """
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            payload = {"category": category, "change_pct": change_pct}
            response = client.post(f"{BACKEND_URL}/scenario/expense", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e), "tool": "simulate_expense_change"}


@tool
def get_active_alerts() -> Dict[str, Any]:
    """
    Get all active anomaly alerts with severity (critical/warning/info),
    amount vs baseline, and recommended actions. Proactively check this for spending questions.
    
    Returns: {alerts: [{severity, category, amount, baseline, delta_pct, action}]}
    """
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(f"{BACKEND_URL}/alerts")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e), "tool": "get_active_alerts"}


@tool
def get_expense_breakdown(period_months: int = 3) -> Dict[str, Any]:
    """
    Get expenses by GL category for the past N months with month-over-month trend and largest movers.
    
    Args:
        period_months: Number of months to include in breakdown (default 3)
    
    Returns: {breakdown: {category: amount}, trend: {...}, movers: [{category, pct_change}]}
    """
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            params = {"months": period_months}
            response = client.get(f"{BACKEND_URL}/expenses", params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e), "tool": "get_expense_breakdown"}


@tool
def get_revenue_metrics() -> Dict[str, Any]:
    """
    Get MRR, ARR, growth rate, churn rate, and net revenue retention with 12-month trend.
    
    Returns: {mrr, arr, growth_pct, churn_rate, nrr, trend_12m: [...]}
    """
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(f"{BACKEND_URL}/revenue")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e), "tool": "get_revenue_metrics"}


@tool
def get_financial_scorecard() -> Dict[str, Any]:
    """
    Get the complete financial health scorecard: liquidity ratios, burn multiple,
    magic number, CAC payback, gross margin. Use for overview questions.
    
    Returns: {cash_balance, monthly_burn, runway_months, mrr, churn_rate,
             burn_multiple, magic_number, cac_payback_months, gross_margin_pct}
    """
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(f"{BACKEND_URL}/scorecard")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e), "tool": "get_financial_scorecard"}


# Export all tools for LangGraph agent
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


def get_all_tools():
    """Return all tools for LangGraph agent."""
    return ALL_TOOLS


if __name__ == "__main__":
    # Verify all tools loaded correctly
    print("Financial Tools Loaded:")
    print("=" * 70)
    for i, tool_func in enumerate(ALL_TOOLS, 1):
        print(f"\n{i}. {tool_func.name}")
        print(f"   Docstring: {tool_func.description[:100]}...")
    
    print("\n" + "=" * 70)
    print(f"Total tools: {len(ALL_TOOLS)}")
    print("Status: All 10 tools ready for LangGraph agent")
