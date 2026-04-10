"""
Prophet DSO Forecasting Service
=================================
Uses Days Sales Outstanding (DSO) trends from AR data to forecast
future cash collections — more accurate than simple revenue averages.

DSO = (Accounts Receivable / Revenue) × Days in Period

A rising DSO → cash collection is slowing → cash flow risk.
Prophet captures seasonality + trend in DSO and projects forward.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DSO Calculation
# ---------------------------------------------------------------------------


def calculate_dso_series(
    invoices: List[Dict],
    monthly_revenue: Optional[List[Dict]] = None,
    lookback_months: int = 12,
) -> pd.DataFrame:
    """
    Calculate monthly DSO from invoice data.

    DSO = (End-of-month AR balance / Monthly Revenue) × Days in Month

    Args:
        invoices:  [{due_date, amount_due, total_amount, paid_date, status}]
        monthly_revenue:  [{period, revenue}] — if not provided, estimated from invoices
        lookback_months:  How many months of history to compute

    Returns:
        DataFrame with columns: period, ar_balance, revenue, dso, days_in_month
    """
    if not invoices:
        return pd.DataFrame(columns=["period", "ar_balance", "revenue", "dso"])

    df = pd.DataFrame(invoices)
    df["total_amount"] = pd.to_numeric(df.get("total_amount", 0), errors="coerce").fillna(0)
    df["amount_due"] = pd.to_numeric(df.get("amount_due", 0), errors="coerce").fillna(0)

    # Parse dates
    for col in ["due_date", "paid_date", "issue_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Build monthly AR balance and revenue
    today = date.today()
    periods = []
    for i in range(lookback_months, 0, -1):
        period_start = (today.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        period_str = period_start.strftime("%Y-%m")

        # Outstanding AR at period end = invoices issued on/before period_end and not paid by period_end
        issued = df[
            df.get("issue_date", pd.Series(dtype="datetime64[ns]")).dt.date <= period_end
        ] if "issue_date" in df.columns else df

        paid = (
            issued[
                issued["paid_date"].dt.date <= period_end
            ] if "paid_date" in df.columns else pd.DataFrame()
        )

        outstanding = float(issued["amount_due"].sum()) if not issued.empty else 0.0
        paid_amount = float(paid["amount_due"].sum()) if not paid.empty else 0.0
        ar_balance = max(0, outstanding - paid_amount)

        # Revenue: invoices issued in this period
        month_invoices = issued[
            issued.get("issue_date", pd.Series(dtype="datetime64[ns]")).dt.to_period("M").astype(str) == period_str
        ] if "issue_date" in df.columns else df
        revenue = float(month_invoices["total_amount"].sum()) if not month_invoices.empty else 0.0

        # Fallback from monthly_revenue
        if revenue == 0.0 and monthly_revenue:
            for mr in monthly_revenue:
                if str(mr.get("period", "")) == period_str:
                    revenue = float(mr.get("revenue", 0))
                    break

        if revenue <= 0:
            revenue = max(ar_balance / 45, 1)  # placeholder to avoid division by zero

        days = (period_end - period_start).days + 1
        dso = (ar_balance / revenue) * days

        periods.append({
            "period": period_str,
            "ar_balance": round(ar_balance, 2),
            "revenue": round(revenue, 2),
            "dso": round(dso, 1),
            "days_in_month": days,
        })

    return pd.DataFrame(periods)


# ---------------------------------------------------------------------------
# Prophet DSO Forecast
# ---------------------------------------------------------------------------


def forecast_dso_with_prophet(
    dso_series: pd.DataFrame,
    forecast_months: int = 6,
) -> Tuple[List[Dict], Dict]:
    """
    Fit a Prophet model on the DSO time series and forecast forward.

    Returns (forecast_rows, model_metrics)
    """
    if dso_series.empty or len(dso_series) < 4:
        logger.warning("Insufficient DSO history for Prophet forecast (need ≥ 4 months)")
        return [], {"error": "insufficient_data"}

    try:
        from prophet import Prophet
    except ImportError:
        logger.error("Prophet not installed. Run: pip install prophet")
        return _fallback_dso_forecast(dso_series, forecast_months), {"error": "prophet_not_installed"}

    prophet_df = pd.DataFrame({
        "ds": pd.to_datetime(dso_series["period"] + "-01"),
        "y": dso_series["dso"].values,
    })

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10,
    )
    model.fit(prophet_df)

    future = model.make_future_dataframe(periods=forecast_months, freq="MS")
    forecast = model.predict(future)

    # Extract future rows only
    last_hist = prophet_df["ds"].max()
    future_fc = forecast[forecast["ds"] > last_hist].copy()

    forecast_rows = []
    for _, row in future_fc.iterrows():
        forecast_rows.append({
            "period": row["ds"].strftime("%Y-%m"),
            "dso_forecast": round(float(max(1, row["yhat"])), 1),
            "dso_lower": round(float(max(1, row["yhat_lower"])), 1),
            "dso_upper": round(float(max(1, row["yhat_upper"])), 1),
        })

    metrics = {
        "history_months": len(dso_series),
        "forecast_months": forecast_months,
        "current_dso": float(dso_series["dso"].iloc[-1]) if len(dso_series) > 0 else 0,
        "avg_historical_dso": round(float(dso_series["dso"].mean()), 1),
        "trend": "rising" if (dso_series["dso"].iloc[-1] > dso_series["dso"].iloc[0]) else "falling",
    }

    return forecast_rows, metrics


def _fallback_dso_forecast(
    dso_series: pd.DataFrame, forecast_months: int
) -> List[Dict]:
    """Simple linear extrapolation when Prophet is unavailable."""
    if dso_series.empty:
        return []

    values = dso_series["dso"].values
    last_period = dso_series["period"].iloc[-1]
    last_date = datetime.strptime(last_period + "-01", "%Y-%m-%d").date()

    if len(values) >= 2:
        slope = (values[-1] - values[0]) / max(len(values) - 1, 1)
    else:
        slope = 0.0

    rows = []
    for i in range(1, forecast_months + 1):
        month_date = (last_date.replace(day=1) + timedelta(days=32 * i)).replace(day=1)
        dso = max(1, values[-1] + slope * i)
        rows.append({
            "period": month_date.strftime("%Y-%m"),
            "dso_forecast": round(dso, 1),
            "dso_lower": round(max(1, dso * 0.85), 1),
            "dso_upper": round(dso * 1.15, 1),
        })
    return rows


# ---------------------------------------------------------------------------
# Cash Collection Forecast from DSO
# ---------------------------------------------------------------------------


def forecast_cash_collections(
    dso_forecast: List[Dict],
    revenue_forecast: List[Dict],
) -> List[Dict]:
    """
    Translate DSO forecast + revenue forecast → expected cash collection per month.

    Cash collections = Revenue × (Days_in_Month / DSO)

    When DSO rises, collections slow even if revenue stays flat.
    """
    rev_map = {r["period"]: float(r.get("revenue", r.get("cash_predicted", 0))) for r in revenue_forecast}

    collections = []
    for fc in dso_forecast:
        period = fc["period"]
        dso = fc["dso_forecast"]

        try:
            month_date = datetime.strptime(period + "-01", "%Y-%m-%d").date()
            days = (
                (month_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            ).day
        except ValueError:
            days = 30

        revenue = rev_map.get(period, 0.0)
        if dso > 0 and revenue > 0:
            collection_rate = min(1.0, days / dso)
            expected_cash = revenue * collection_rate
        else:
            expected_cash = revenue

        collections.append({
            "period": period,
            "dso_forecast": dso,
            "revenue": round(revenue, 2),
            "expected_cash_collection": round(expected_cash, 2),
            "collection_efficiency": round(min(1.0, days / max(dso, 1)) * 100, 1),
        })

    return collections


# ---------------------------------------------------------------------------
# Full DSO Forecasting Run
# ---------------------------------------------------------------------------


def run_dso_forecast(
    invoices: List[Dict],
    monthly_revenue: Optional[List[Dict]] = None,
    revenue_forecast: Optional[List[Dict]] = None,
    forecast_months: int = 6,
) -> Dict[str, Any]:
    """
    Run the full DSO-based cash flow forecast.

    Returns DSO history, forecast, and expected cash collections.
    """
    dso_series = calculate_dso_series(invoices, monthly_revenue, lookback_months=12)
    dso_forecast, metrics = forecast_dso_with_prophet(dso_series, forecast_months)

    # Generate cash collection forecast
    if revenue_forecast:
        collections = forecast_cash_collections(dso_forecast, revenue_forecast)
    else:
        # Estimate revenue as average of last 3 months
        if not dso_series.empty:
            avg_rev = float(dso_series["revenue"].tail(3).mean())
        else:
            avg_rev = 0.0

        today = date.today()
        simple_rev = []
        for i in range(1, forecast_months + 1):
            month = (today.replace(day=1) + timedelta(days=32 * i)).replace(day=1)
            simple_rev.append({"period": month.strftime("%Y-%m"), "revenue": avg_rev})
        collections = forecast_cash_collections(dso_forecast, simple_rev)

    # Risk assessment
    current_dso = float(dso_series["dso"].iloc[-1]) if not dso_series.empty else 30.0
    avg_dso = float(dso_series["dso"].mean()) if not dso_series.empty else 30.0
    risk_level = "high" if current_dso > 60 else "medium" if current_dso > 45 else "low"

    return {
        "history": dso_series.to_dict("records"),
        "dso_forecast": dso_forecast,
        "cash_collections": collections,
        "metrics": metrics,
        "risk_assessment": {
            "current_dso_days": round(current_dso, 1),
            "average_dso_days": round(avg_dso, 1),
            "trend": metrics.get("trend", "stable"),
            "risk_level": risk_level,
            "interpretation": (
                f"DSO of {current_dso:.0f} days means customers take {current_dso:.0f} days on average to pay. "
                f"{'Customers are paying slower — watch cash carefully.' if risk_level == 'high' else 'Collections are within normal range.'}"
            ),
        },
    }
