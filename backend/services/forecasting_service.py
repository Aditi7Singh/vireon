from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

import numpy as np
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

import models


def prepare_monthly_timeseries(
    company_id: UUID,
    db: Session,
    entry_type: str = "debit",
    category: Optional[str] = None,
    product_tag: Optional[str] = None,
) -> pd.DataFrame:
    # Handle database-specific date truncation
    engine_name = db.bind.name
    if engine_name == "postgresql":
        month_expr = func.date_trunc("month", models.FinancialLedgerEntry.transaction_date)
    else:
        # SQLite fallback: format date to YYYY-MM-01
        month_expr = func.strftime("%Y-%m-01", models.FinancialLedgerEntry.transaction_date)
        
    query = db.query(
        month_expr.label("month"),
        func.sum(models.FinancialLedgerEntry.amount_inr).label("total"),
    ).filter(
        models.FinancialLedgerEntry.company_id == company_id,
        models.FinancialLedgerEntry.entry_type == entry_type,
    )

    if category:
        query = query.filter(models.FinancialLedgerEntry.category == category)
    if product_tag:
        query = query.filter(models.FinancialLedgerEntry.product_tag == product_tag)

    rows = query.group_by("month").order_by("month").all()
    if not rows:
        return pd.DataFrame(columns=["ds", "y"])

    return pd.DataFrame(
        {"ds": [pd.to_datetime(r.month).date() for r in rows], "y": [float(r.total or 0) for r in rows]}
    )


def fit_sarima_model(df: pd.DataFrame) -> dict:
    """
    Fit the best available time-series model to monthly financial data.

    Model selection cascade:
      1. SARIMA with seasonal component (≥12 data points)
      2. SARIMA non-seasonal / ARIMA (≥6 data points)
      3. Exponential smoothing (≥4 data points)
      4. Prophet (≥3 data points)
      5. Flat forecast fallback
    """
    if df.empty:
        forecast_df = pd.DataFrame(
            {
                "ds": pd.date_range(start=pd.Timestamp.today().normalize(), periods=12, freq="MS"),
                "yhat": [0.0] * 12,
                "yhat_lower": [0.0] * 12,
                "yhat_upper": [0.0] * 12,
            }
        )
        return {"model_type": "empty", "fitted_model": None, "aic": None, "forecast_df": forecast_df}

    ts = pd.Series(df["y"].values, index=pd.to_datetime(df["ds"]))

    # ── 1. SARIMA with seasonal component (SARIMAX) ──
    if len(df) >= 12:
        try:
            from statsmodels.tsa.statespace.sarimax import SARIMAX

            model = SARIMAX(ts, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12),
                            enforce_stationarity=False, enforce_invertibility=False)
            fitted = model.fit(disp=False)
            forecast = fitted.get_forecast(steps=12)
            pred = forecast.predicted_mean
            ci = forecast.conf_int()
            forecast_df = pd.DataFrame(
                {
                    "ds": pred.index,
                    "yhat": pred.values,
                    "yhat_lower": ci.iloc[:, 0].values,
                    "yhat_upper": ci.iloc[:, 1].values,
                }
            )
            return {"model_type": "sarima_seasonal", "fitted_model": fitted,
                    "aic": float(fitted.aic), "forecast_df": forecast_df}
        except Exception:
            pass

    # ── 2. ARIMA / SARIMA non-seasonal (≥6 points) ──
    if len(df) >= 6:
        try:
            from statsmodels.tsa.statespace.sarimax import SARIMAX

            # Try pure ARIMA first (no seasonal)
            model = SARIMAX(ts, order=(1, 1, 1), seasonal_order=(0, 0, 0, 0),
                            enforce_stationarity=False, enforce_invertibility=False)
            fitted = model.fit(disp=False)
            forecast = fitted.get_forecast(steps=12)
            pred = forecast.predicted_mean
            ci = forecast.conf_int()
            forecast_df = pd.DataFrame(
                {
                    "ds": pred.index,
                    "yhat": pred.values,
                    "yhat_lower": ci.iloc[:, 0].values,
                    "yhat_upper": ci.iloc[:, 1].values,
                }
            )
            return {"model_type": "arima", "fitted_model": fitted,
                    "aic": float(fitted.aic), "forecast_df": forecast_df}
        except Exception:
            pass

    # ── 3. Exponential Smoothing (≥4 points) ──
    if len(df) >= 4:
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing

            model = ExponentialSmoothing(ts, trend="add", seasonal=None)
            fitted = model.fit(optimized=True)
            pred = fitted.forecast(12)
            # Build CI as ±15% of predicted (simple heuristic)
            forecast_df = pd.DataFrame(
                {
                    "ds": pred.index,
                    "yhat": pred.values,
                    "yhat_lower": pred.values * 0.85,
                    "yhat_upper": pred.values * 1.15,
                }
            )
            return {"model_type": "exponential_smoothing", "fitted_model": fitted,
                    "aic": float(fitted.aic) if hasattr(fitted, "aic") else None,
                    "forecast_df": forecast_df}
        except Exception:
            pass

    # ── 4. Prophet (≥3 points) ──
    try:
        from prophet import Prophet

        prophet_df = df.copy()
        prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])
        model = Prophet()
        model.fit(prophet_df)
        future = model.make_future_dataframe(periods=12, freq="MS")
        out = model.predict(future).tail(12)[["ds", "yhat", "yhat_lower", "yhat_upper"]]
        return {"model_type": "prophet", "fitted_model": model, "aic": None, "forecast_df": out}
    except Exception:
        pass

    # ── 5. Flat forecast fallback ──
    last_y = float(df["y"].iloc[-1]) if not df.empty else 0.0
    future_dates = pd.date_range(start=pd.to_datetime(df["ds"].iloc[-1]), periods=12, freq="MS")
    out = pd.DataFrame({"ds": future_dates, "yhat": [last_y] * 12,
                         "yhat_lower": [last_y * 0.9] * 12, "yhat_upper": [last_y * 1.1] * 12})
    return {"model_type": "fallback_flat", "fitted_model": None, "aic": None, "forecast_df": out}


def _current_cash_inr(company_id: UUID, db: Session) -> float:
    feed_balance = (
        db.query(func.sum(models.BankingTransaction.amount))
        .join(models.BankFeed, models.BankFeed.id == models.BankingTransaction.feed_id)
        .filter(models.BankFeed.company_id == company_id)
        .scalar()
    )
    if feed_balance is not None:
        return float(feed_balance)

    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if company and company.initial_cash:
        return float(company.initial_cash)
    return 0.0


def _runway_from_projection(current_cash: float, burn: pd.DataFrame, revenue: pd.DataFrame) -> dict:
    months = []
    cumulative = current_cash
    runway_months = 12.0
    runway_date = pd.Timestamp.today().date()

    for i in range(12):
        month = pd.to_datetime(burn.iloc[i]["ds"]).date() if i < len(burn) else pd.Timestamp.today().date()
        projected_burn = max(float(burn.iloc[i]["yhat"]), 0.0) if i < len(burn) else 0.0
        projected_revenue = max(float(revenue.iloc[i]["yhat"]), 0.0) if i < len(revenue) else 0.0
        net_burn = projected_burn - projected_revenue
        cumulative -= net_burn
        months.append(
            {
                "month": month.isoformat(),
                "projected_burn": projected_burn,
                "projected_revenue": projected_revenue,
                "net_burn": net_burn,
                "cumulative_cash": cumulative,
            }
        )
        if cumulative <= 0 and runway_months == 12.0:
            runway_months = float(i + 1)
            runway_date = month

    return {
        "runway_months": runway_months,
        "runway_date": runway_date,
        "monthly_projections": months,
    }


def calculate_dynamic_runway(company_id: UUID, db: Session) -> dict:
    current_cash = _current_cash_inr(company_id, db)

    burn_df = prepare_monthly_timeseries(company_id, db, entry_type="debit")
    revenue_df = prepare_monthly_timeseries(company_id, db, entry_type="credit")

    burn_model = fit_sarima_model(burn_df)
    revenue_model = fit_sarima_model(revenue_df)

    # --- Pending Hires Projection ---
    # Fetch employees with hire dates in the future
    today = date.today()
    pending_hires = db.query(models.Employee).filter(
        models.Employee.company_id == company_id,
        models.Employee.hire_date > today,
        models.Employee.status == "active"
    ).all()
    
    # Add pending hire costs to the burn projection
    if pending_hires:
        # Create a copy of the forecast to avoid mutating the model results directly
        burn_forecast = burn_model["forecast_df"].copy()
        for hire in pending_hires:
            monthly_salary = float(hire.salary) / 12.0
            hire_month = hire.hire_date.replace(day=1)
            
            for idx, row in burn_forecast.iterrows():
                forecast_month = pd.to_datetime(row["ds"]).date().replace(day=1)
                if forecast_month >= hire_month:
                    burn_forecast.at[idx, "yhat"] += monthly_salary
                    burn_forecast.at[idx, "yhat_upper"] += monthly_salary
                    burn_forecast.at[idx, "yhat_lower"] += monthly_salary
        burn_model["forecast_df"] = burn_forecast

    runway_data = _runway_from_projection(current_cash, burn_model["forecast_df"], revenue_model["forecast_df"])

    lower_projection = _runway_from_projection(
        current_cash,
        burn_model["forecast_df"].assign(yhat=lambda x: x["yhat_upper"]),
        revenue_model["forecast_df"].assign(yhat=lambda x: x["yhat_lower"]),
    )
    upper_projection = _runway_from_projection(
        current_cash,
        burn_model["forecast_df"].assign(yhat=lambda x: x["yhat_lower"]),
        revenue_model["forecast_df"].assign(yhat=lambda x: x["yhat_upper"]),
    )

    return {
        "current_cash_inr": current_cash,
        "runway_months": runway_data["runway_months"],
        "runway_date": runway_data["runway_date"],
        "monthly_projections": runway_data["monthly_projections"],
        "confidence_interval": {
            "lower_months": lower_projection["runway_months"],
            "upper_months": upper_projection["runway_months"],
        },
        "model_used": f"burn={burn_model['model_type']}, revenue={revenue_model['model_type']}",
        "last_updated": datetime.utcnow().isoformat(),
    }


def calculate_hiring_impact(
    company_id: UUID, 
    db: Session, 
    annual_ctc_inr: float, 
    join_month: str,
    equipment_cost: float = 0.0,
    onboarding_cost: float = 0.0,
    benefits_multiplier: float = 1.0
) -> dict:
    baseline = calculate_dynamic_runway(company_id, db)
    # Recurring monthly cost includes benefits
    monthly_salary = float(annual_ctc_inr) / 12.0
    recurring_monthly_cost = monthly_salary * float(benefits_multiplier)
    
    join_month_date = datetime.strptime(join_month, "%Y-%m").date().replace(day=1)
    one_time_cost = float(equipment_cost) + float(onboarding_cost)

    projections = []
    cumulative = baseline["current_cash_inr"]
    new_runway = 12.0
    
    for idx, row in enumerate(baseline["monthly_projections"]):
        month_date = datetime.strptime(row["month"], "%Y-%m-%d").date().replace(day=1)
        
        # Monthly recurring cost
        extra = recurring_monthly_cost if month_date >= join_month_date else 0.0
        
        # Add one-time costs in the join month
        if month_date == join_month_date:
            extra += one_time_cost
            
        net_burn = row["net_burn"] + extra
        cumulative -= net_burn
        projections.append({**row, "net_burn": net_burn, "cumulative_cash": cumulative})
        
        if cumulative <= 0 and new_runway == 12.0:
            new_runway = float(idx + 1)

    impact_months = baseline["runway_months"] - new_runway
    return {
        "baseline_runway_months": baseline["runway_months"],
        "new_runway_months": new_runway,
        "runway_impact_months": impact_months,
        "runway_impact_days": int(impact_months * 30),
        "one_time_hiring_costs": one_time_cost,
        "recurring_monthly_hiring_cost": recurring_monthly_cost,
        "break_even_month": None,
        "monthly_projections": projections,
    }


def save_forecast_to_db(company_id: UUID, forecast_data: dict, db: Session):
    projections = forecast_data.get("monthly_projections", [])
    for row in projections:
        forecast_date = datetime.strptime(row["month"], "%Y-%m-%d").date()
        item = models.Forecast(
            company_id=company_id,
            forecast_date=forecast_date,
            mrr_predicted=row.get("projected_revenue", 0),
            cash_predicted=row.get("cumulative_cash", 0),
            confidence_lower=row.get("cumulative_cash", 0) * 0.9,
            confidence_upper=row.get("cumulative_cash", 0) * 1.1,
        )
        db.add(item)
    db.commit()
