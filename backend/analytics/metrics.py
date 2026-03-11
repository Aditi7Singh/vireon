"""
Math Engine - Core Financial Metrics
====================================
This module implements deterministic financial formulas for startup metrics
based on industry standards.
"""

from typing import List, Dict, Union

def calculate_gross_burn(expenses: List[float]) -> float:
    """
    Gross Burn = Total monthly operating expenses.
    """
    return sum(expenses)

def calculate_net_burn(revenue: float, gross_burn: float) -> float:
    """
    Net Burn = Total monthly revenue - Gross burn.
    (Usually expressed as a positive number for cash loss)
    """
    return max(0, gross_burn - revenue)

def calculate_runway(cash_balance: float, net_burn: float) -> Union[float, str]:
    """
    Runway (months) = Cash balance / Monthly net burn.
    If net burn is <= 0, runway is 'Infinite'.
    """
    if net_burn <= 0:
        return "Infinite"
    return round(cash_balance / net_burn, 2)

def calculate_mrr(subscription_invoices: List[Dict]) -> float:
    """
    MRR = Combined value of all recurring subscription invoices in a month.
    """
    return sum(inv.get('amount', 0) for inv in subscription_invoices)

def calculate_arr(mrr: float) -> float:
    """
    ARR = MRR * 12.
    """
    return mrr * 12

def calculate_gross_margin(revenue: float, cogs: float) -> float:
    """
    Gross Margin = (Revenue - COGS) / Revenue.
    """
    if revenue == 0:
        return 0
    return round((revenue - cogs) / revenue, 4)

def detect_anomaly(current_value: float, moving_average: float, threshold: float = 1.2) -> bool:
    """
    Simple threshold-based anomaly detection.
    Returns True if current_value is more than [threshold]% of moving_average.
    """
    if moving_average == 0:
        return False
    return current_value > (moving_average * threshold)

def calculate_budget_variance(actual: float, budget: float) -> Dict[str, Union[float, str]]:
    """
    Variance analysis: Actual vs Budget.
    - Positive variance for revenue is favorable.
    - Positive variance for expenses is unfavorable.
    """
    variance = actual - budget
    percent_variance = (variance / budget) if budget != 0 else 0
    
    return {
        "actual": actual,
        "budget": budget,
        "variance": round(variance, 2),
        "percent_variance": round(percent_variance * 100, 2)
    }
