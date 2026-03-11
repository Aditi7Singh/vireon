"""
Scenario Modifiers - Financial Simulation
==========================================
This module allows for real-time simulation of business decisions
by modifying baseline financial metrics.
"""

from typing import Dict, Union
from analytics.metrics import calculate_runway, calculate_net_burn

def simulate_hiring(
    current_cash: float,
    current_revenue: float,
    current_gross_burn: float,
    new_salary_annual: float,
    count: int = 1
) -> Dict[str, Union[float, str]]:
    """
    Simulates the impact of hiring new employees.
    """
    additional_monthly_burn = (new_salary_annual / 12) * count
    new_gross_burn = current_gross_burn + additional_monthly_burn
    new_net_burn = calculate_net_burn(current_revenue, new_gross_burn)
    new_runway = calculate_runway(current_cash, new_net_burn)
    
    return {
        "scenario": f"Hire {count} employee(s) at ${new_salary_annual:,.0f}/yr",
        "additional_monthly_burn": round(additional_monthly_burn, 2),
        "new_gross_burn": round(new_gross_burn, 2),
        "new_net_burn": round(new_net_burn, 2),
        "new_runway": new_runway
    }

def simulate_revenue_change(
    current_cash: float,
    current_revenue: float,
    current_gross_burn: float,
    percentage_change: float
) -> Dict[str, Union[float, str]]:
    """
    Simulates the impact of revenue growth or contraction.
    percentage_change: e.g. 0.1 for 10% growth, -0.2 for 20% drop.
    """
    new_revenue = current_revenue * (1 + percentage_change)
    new_net_burn = calculate_net_burn(new_revenue, current_gross_burn)
    new_runway = calculate_runway(current_cash, new_net_burn)
    
    return {
        "scenario": f"Revenue change of {percentage_change*100}%",
        "new_revenue": round(new_revenue, 2),
        "new_net_burn": round(new_net_burn, 2),
        "new_runway": new_runway
    }

def simulate_cost_reduction(
    current_cash: float,
    current_revenue: float,
    current_gross_burn: float,
    reduction_amount: float
) -> Dict[str, Union[float, str]]:
    """
    Simulates a one-time or recurring cost reduction.
    """
    new_gross_burn = max(0, current_gross_burn - reduction_amount)
    new_net_burn = calculate_net_burn(current_revenue, new_gross_burn)
    new_runway = calculate_runway(current_cash, new_net_burn)
    
    return {
        "scenario": f"Reduce monthly costs by ${reduction_amount:,.0f}",
        "new_gross_burn": round(new_gross_burn, 2),
        "new_net_burn": round(new_net_burn, 2),
        "new_runway": new_runway
    }
