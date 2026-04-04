"""
Scenario Modifiers - Financial Simulation
==========================================
This module allows for real-time simulation of business decisions
by modifying baseline financial metrics.
"""

from __future__ import annotations

from typing import Dict, Union, List, Optional, Any
from analytics.metrics import calculate_runway, calculate_net_burn


def _runway_result(current_cash: float, current_revenue: float, gross_burn: float) -> Dict[str, Union[float, str]]:
    net_burn = calculate_net_burn(current_revenue, gross_burn)
    runway = calculate_runway(current_cash, net_burn)
    return {
        "new_net_burn": round(net_burn, 2),
        "new_runway": runway,
    }

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


def simulate_price_change(
    current_cash: float,
    current_revenue: float,
    current_gross_burn: float,
    price_change_pct: float,
    gross_margin_pct: float = 70.0,
) -> Dict[str, Union[float, str]]:
    revenue_multiplier = 1 + (price_change_pct / 100.0)
    new_revenue = max(0.0, current_revenue * revenue_multiplier)
    margin_factor = max(0.0, min(1.0, gross_margin_pct / 100.0))
    revenue_delta = new_revenue - current_revenue
    gross_burn_delta = max(0.0, revenue_delta * (1 - margin_factor))
    result = _runway_result(current_cash, new_revenue, max(0.0, current_gross_burn - gross_burn_delta))
    return {
        "scenario": f"Price change of {price_change_pct:+.1f}%",
        "new_revenue": round(new_revenue, 2),
        "new_gross_burn": round(max(0.0, current_gross_burn - gross_burn_delta), 2),
        **result,
    }


def simulate_customer_churn(
    current_cash: float,
    current_revenue: float,
    current_gross_burn: float,
    churn_pct: float,
) -> Dict[str, Union[float, str]]:
    new_revenue = max(0.0, current_revenue * (1 - churn_pct / 100.0))
    result = _runway_result(current_cash, new_revenue, current_gross_burn)
    return {
        "scenario": f"Customer churn of {churn_pct:.1f}%",
        "new_revenue": round(new_revenue, 2),
        **result,
    }


def simulate_market_expansion(
    current_cash: float,
    current_revenue: float,
    current_gross_burn: float,
    expansion_investment: float,
    expected_roi_pct: float,
) -> Dict[str, Union[float, str]]:
    incremental_revenue = expansion_investment * (expected_roi_pct / 100.0)
    new_cash = max(0.0, current_cash - expansion_investment)
    new_revenue = current_revenue + incremental_revenue
    result = _runway_result(new_cash, new_revenue, current_gross_burn + expansion_investment / 12.0)
    return {
        "scenario": f"Market expansion with ${expansion_investment:,.0f} investment",
        "incremental_revenue": round(incremental_revenue, 2),
        "new_cash": round(new_cash, 2),
        **result,
    }


def simulate_equipment_purchase_vs_lease(
    current_cash: float,
    current_revenue: float,
    current_gross_burn: float,
    purchase_cost: float,
    lease_monthly: float,
    useful_life_months: int,
) -> Dict[str, Union[float, str]]:
    purchase_monthly_equivalent = purchase_cost / max(1, useful_life_months)
    purchase_result = _runway_result(current_cash - purchase_cost, current_revenue, current_gross_burn + purchase_monthly_equivalent)
    lease_result = _runway_result(current_cash, current_revenue, current_gross_burn + lease_monthly)
    return {
        "scenario": "Equipment purchase vs lease",
        "purchase": {
            "cash_impact": round(current_cash - purchase_cost, 2),
            "monthly_equivalent": round(purchase_monthly_equivalent, 2),
            **purchase_result,
        },
        "lease": {
            "cash_impact": round(current_cash, 2),
            "monthly_lease": round(lease_monthly, 2),
            **lease_result,
        },
    }


def simulate_inventory_optimization(
    current_cash: float,
    current_revenue: float,
    current_gross_burn: float,
    inventory_reduction_pct: float,
    carrying_cost_pct: float = 20.0,
) -> Dict[str, Union[float, str]]:
    burn_savings = current_gross_burn * (inventory_reduction_pct / 100.0) * (carrying_cost_pct / 100.0)
    new_burn = max(0.0, current_gross_burn - burn_savings)
    result = _runway_result(current_cash, current_revenue, new_burn)
    return {
        "scenario": f"Inventory reduction of {inventory_reduction_pct:.1f}%",
        "monthly_savings": round(burn_savings, 2),
        "new_gross_burn": round(new_burn, 2),
        **result,
    }


def simulate_pricing_strategy(
    current_cash: float,
    current_revenue: float,
    current_gross_burn: float,
    price_change_pct: float,
    demand_elasticity: float = -1.0,
) -> Dict[str, Union[float, str]]:
    demand_change_pct = price_change_pct * demand_elasticity
    revenue_change_pct = price_change_pct + demand_change_pct
    new_revenue = max(0.0, current_revenue * (1 + revenue_change_pct / 100.0))
    result = _runway_result(current_cash, new_revenue, current_gross_burn)
    return {
        "scenario": f"Pricing strategy change of {price_change_pct:+.1f}%",
        "demand_change_pct": round(demand_change_pct, 2),
        "revenue_change_pct": round(revenue_change_pct, 2),
        "new_revenue": round(new_revenue, 2),
        **result,
    }


def simulate_custom_scenario(
    current_cash: float,
    current_revenue: float,
    current_gross_burn: float,
    variables: Dict[str, float],
) -> Dict[str, Union[float, str, Dict[str, float]]]:
    cash = current_cash
    revenue = current_revenue
    gross_burn = current_gross_burn

    for key, value in variables.items():
        normalized = key.lower().strip()
        if normalized in {"cash", "cash_delta"}:
            cash += value
        elif normalized in {"revenue", "revenue_delta"}:
            revenue += value
        elif normalized in {"burn", "burn_delta", "expenses", "expense_delta"}:
            gross_burn += value
        elif normalized in {"revenue_pct", "revenue_change_pct"}:
            revenue *= 1 + (value / 100.0)
        elif normalized in {"burn_pct", "expense_pct"}:
            gross_burn *= 1 + (value / 100.0)

    result = _runway_result(max(0.0, cash), max(0.0, revenue), max(0.0, gross_burn))
    return {
        "scenario": "Custom scenario builder",
        "variables": variables,
        "new_cash": round(max(0.0, cash), 2),
        "new_revenue": round(max(0.0, revenue), 2),
        "new_gross_burn": round(max(0.0, gross_burn), 2),
        **result,
    }
