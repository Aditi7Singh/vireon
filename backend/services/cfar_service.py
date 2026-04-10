"""
Cash Flow at Risk (CFaR) — Monte Carlo Simulation
====================================================
Applies Value-at-Risk methodology to cash flow forecasting.

Standard CFaR approach:
  1. Fit historical cash flow volatility (mean + std of monthly changes)
  2. Simulate N paths of future cash balances using GBM or normal shocks
  3. Report:
     - Expected cash balance (median path)
     - CFaR at 95% confidence: worst-case loss over the horizon
     - Probability of cash dropping below a threshold
     - Fan chart data (percentile bands) for visualization

N_PATHS default = 10,000 paths over 12-month horizon
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

N_PATHS = 10_000
RANDOM_SEED = 42


def _parse_historical_cash(
    monthly_cash: List[Dict],
) -> Tuple[np.ndarray, List[str]]:
    """
    Parse historical monthly cash balances.

    Args:
        monthly_cash: [{period: 'YYYY-MM', cash_balance: float}]

    Returns:
        (cash_values array, period strings)
    """
    df = pd.DataFrame(monthly_cash)
    df = df.sort_values("period")
    return df["cash_balance"].astype(float).values, df["period"].tolist()


def _compute_drift_and_vol(cash_values: np.ndarray) -> Tuple[float, float]:
    """
    Compute mean monthly change and standard deviation from historical cash.
    """
    if len(cash_values) < 2:
        return 0.0, cash_values[0] * 0.05 if len(cash_values) > 0 else 10_000

    changes = np.diff(cash_values)
    return float(np.mean(changes)), float(np.std(changes, ddof=1))


def run_cfar_simulation(
    monthly_cash: List[Dict],
    forecast_months: int = 12,
    confidence_level: float = 0.95,
    cash_threshold: Optional[float] = None,
    n_paths: int = N_PATHS,
) -> Dict[str, Any]:
    """
    Run the Monte Carlo CFaR simulation.

    Args:
        monthly_cash:      Historical cash balances [{period, cash_balance}]
        forecast_months:   How far forward to simulate
        confidence_level:  Confidence level for CFaR (default 0.95 = 95%)
        cash_threshold:    Alert threshold (e.g., 3 months of burn). Default = 20% of current cash.
        n_paths:           Number of Monte Carlo paths

    Returns:
        {
          current_cash, drift, volatility,
          cfar_95, probability_below_threshold,
          fan_chart: [{period, p5, p25, median, p75, p95}],
          paths_sample: list of 10 sample paths for viz,
          risk_assessment: {...},
        }
    """
    if not monthly_cash:
        return {"error": "no_data", "message": "No historical cash data provided"}

    cash_values, periods = _parse_historical_cash(monthly_cash)
    current_cash = float(cash_values[-1])

    if cash_threshold is None:
        cash_threshold = current_cash * 0.20  # default: 20% of current cash

    drift, vol = _compute_drift_and_vol(cash_values)

    # If volatility is zero, add a small floor
    if vol == 0:
        vol = abs(current_cash) * 0.03 + 1_000

    # -----------------------------------------------------------------------
    # Monte Carlo simulation
    # -----------------------------------------------------------------------
    rng = np.random.default_rng(RANDOM_SEED)

    # Shape: (n_paths, forecast_months)
    shocks = rng.normal(loc=drift, scale=vol, size=(n_paths, forecast_months))
    cumulative_changes = np.cumsum(shocks, axis=1)
    paths = current_cash + cumulative_changes  # (n_paths, forecast_months)

    # -----------------------------------------------------------------------
    # Compute percentiles for fan chart
    # -----------------------------------------------------------------------
    today = date.today()
    future_periods = []
    for i in range(1, forecast_months + 1):
        month_date = (today.replace(day=1) + timedelta(days=32 * i)).replace(day=1)
        future_periods.append(month_date.strftime("%Y-%m"))

    fan_chart = []
    for i, period in enumerate(future_periods):
        col = paths[:, i]
        fan_chart.append({
            "period": period,
            "p5": round(float(np.percentile(col, 5)), 2),
            "p25": round(float(np.percentile(col, 25)), 2),
            "median": round(float(np.percentile(col, 50)), 2),
            "p75": round(float(np.percentile(col, 75)), 2),
            "p95": round(float(np.percentile(col, 95)), 2),
        })

    # -----------------------------------------------------------------------
    # CFaR metrics
    # -----------------------------------------------------------------------
    # Terminal cash distribution (at end of horizon)
    terminal_cash = paths[:, -1]

    # CFaR at confidence_level: worst-case loss at the given percentile
    alpha = 1 - confidence_level
    cfar_percentile = float(np.percentile(terminal_cash, alpha * 100))
    cfar = current_cash - cfar_percentile  # expected loss in worst-case scenario

    # Min cash along each path (maximum drawdown concern)
    min_cash_per_path = paths.min(axis=1)
    prob_below_threshold = float(np.mean(min_cash_per_path < cash_threshold))

    # Probability of going negative (cash crisis)
    prob_negative = float(np.mean(min_cash_per_path < 0))

    # Expected shortfall (CVaR): mean of worst alpha% outcomes
    cutoff = np.percentile(terminal_cash, alpha * 100)
    cvar = float(np.mean(terminal_cash[terminal_cash <= cutoff]))

    # -----------------------------------------------------------------------
    # Sample 10 paths for visualization
    # -----------------------------------------------------------------------
    sample_indices = rng.choice(n_paths, size=min(10, n_paths), replace=False)
    paths_sample = []
    for idx in sample_indices:
        path_data = [current_cash] + paths[idx].tolist()
        paths_sample.append({
            "path_id": int(idx),
            "values": [round(v, 2) for v in path_data],
        })

    # -----------------------------------------------------------------------
    # Risk assessment
    # -----------------------------------------------------------------------
    risk_level = (
        "critical" if prob_negative > 0.20 else
        "high" if prob_below_threshold > 0.30 else
        "medium" if prob_below_threshold > 0.10 else
        "low"
    )

    return {
        "current_cash": round(current_cash, 2),
        "simulation_params": {
            "n_paths": n_paths,
            "forecast_months": forecast_months,
            "confidence_level": confidence_level,
            "monthly_drift": round(drift, 2),
            "monthly_volatility": round(vol, 2),
            "cash_threshold": round(cash_threshold, 2),
        },
        "cfar_metrics": {
            "cfar_95": round(cfar, 2),
            "cfar_99": round(current_cash - float(np.percentile(terminal_cash, 1)), 2),
            "expected_shortfall_cvar": round(cvar, 2),
            "probability_below_threshold_pct": round(prob_below_threshold * 100, 1),
            "probability_negative_pct": round(prob_negative * 100, 1),
            "worst_case_terminal_cash": round(float(np.min(terminal_cash)), 2),
            "best_case_terminal_cash": round(float(np.max(terminal_cash)), 2),
            "median_terminal_cash": round(float(np.median(terminal_cash)), 2),
        },
        "fan_chart": fan_chart,
        "paths_sample": paths_sample,
        "risk_assessment": {
            "risk_level": risk_level,
            "interpretation": _risk_interpretation(
                risk_level, prob_below_threshold, cfar, cash_threshold, forecast_months
            ),
            "recommendation": _risk_recommendation(risk_level, prob_negative, cfar),
        },
    }


def _risk_interpretation(
    risk_level: str,
    prob: float,
    cfar: float,
    threshold: float,
    months: int,
) -> str:
    if risk_level == "critical":
        return (
            f"CRITICAL: There is a >20% probability of cash going negative within {months} months. "
            f"CFaR: ${cfar:,.0f} at 95% confidence."
        )
    elif risk_level == "high":
        return (
            f"HIGH RISK: {prob*100:.0f}% chance cash falls below ${threshold:,.0f} threshold. "
            f"CFaR: ${cfar:,.0f} — immediate contingency planning needed."
        )
    elif risk_level == "medium":
        return (
            f"MODERATE: {prob*100:.0f}% probability of hitting the cash buffer threshold. "
            f"Consider securing a credit line or accelerating collections."
        )
    else:
        return (
            f"LOW RISK: Cash position appears stable over the {months}-month horizon. "
            f"CFaR at 95% confidence: ${cfar:,.0f}."
        )


def _risk_recommendation(risk_level: str, prob_negative: float, cfar: float) -> str:
    if risk_level == "critical":
        return "Immediately contact investors/lenders. Pause discretionary spending."
    elif risk_level == "high":
        return f"Secure a ${cfar:,.0f} credit facility. Accelerate AR collections."
    elif risk_level == "medium":
        return "Review burn rate. Consider extending payment terms with key vendors."
    else:
        return "Maintain current trajectory. Continue monitoring monthly."
