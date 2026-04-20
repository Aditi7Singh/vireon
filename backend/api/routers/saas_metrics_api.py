from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

import auth
import database
import models

router = APIRouter(prefix="/saas-metrics", tags=["saas_metrics"])


def _float(v) -> float:
    return float(v) if v is not None else 0.0


@router.get("/summary")
def saas_summary(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Current-month KPIs derived from MonthlyMetric + CustomerCohort data."""
    latest = (
        db.query(models.MonthlyMetric)
        .filter(models.MonthlyMetric.company_id == company_id)
        .order_by(models.MonthlyMetric.metric_month.desc())
        .first()
    )
    prior = (
        db.query(models.MonthlyMetric)
        .filter(models.MonthlyMetric.company_id == company_id)
        .order_by(models.MonthlyMetric.metric_month.desc())
        .offset(1)
        .first()
    )

    mrr = _float(latest.total_revenue) if latest else 0.0
    prior_mrr = _float(prior.total_revenue) if prior else 0.0
    arr = mrr * 12

    # Aggregate cohort metrics
    cohorts = (
        db.query(models.CustomerCohort)
        .filter(models.CustomerCohort.company_id == company_id)
        .all()
    )
    avg_nrr = 0.0
    avg_ltv = 0.0
    avg_cac = 0.0
    avg_churn = 0.0
    avg_margin = 0.0
    if cohorts:
        nrr_vals = [_float(c.nrr) for c in cohorts if c.nrr]
        ltv_vals = [_float(c.ltv_estimate) for c in cohorts if c.ltv_estimate]
        cac_vals = [_float(c.cac_estimate) for c in cohorts if c.cac_estimate]
        churn_vals = [_float(c.churn_rate) for c in cohorts if c.churn_rate]
        margin_vals = [_float(c.gross_margin_pct) for c in cohorts if c.gross_margin_pct]
        avg_nrr = sum(nrr_vals) / len(nrr_vals) if nrr_vals else 0.0
        avg_ltv = sum(ltv_vals) / len(ltv_vals) if ltv_vals else 0.0
        avg_cac = sum(cac_vals) / len(cac_vals) if cac_vals else 0.0
        avg_churn = sum(churn_vals) / len(churn_vals) if churn_vals else 0.0
        avg_margin = sum(margin_vals) / len(margin_vals) if margin_vals else 0.0

    ltv_cac = round(avg_ltv / avg_cac, 1) if avg_cac > 0 else 0.0
    cac_payback = round(avg_cac / (mrr * (avg_margin / 100)), 1) if mrr > 0 and avg_margin > 0 else 0.0

    # Rule of 40: growth rate + profit margin
    growth_rate = ((mrr - prior_mrr) / prior_mrr * 100) if prior_mrr > 0 else 0.0
    burn = _float(latest.burn_rate) if latest else 0.0
    profit_margin = ((mrr - burn) / mrr * 100) if mrr > 0 else 0.0
    rule_of_40 = round(growth_rate + profit_margin, 1)

    return {
        "mrr": round(mrr, 2),
        "arr": round(arr, 2),
        "mrr_growth_pct": round(growth_rate, 1),
        "nrr": round(avg_nrr, 1),
        "gross_margin_pct": round(avg_margin, 1),
        "ltv": round(avg_ltv, 2),
        "cac": round(avg_cac, 2),
        "ltv_cac_ratio": ltv_cac,
        "cac_payback_months": cac_payback,
        "churn_rate_pct": round(avg_churn * 100, 2),
        "rule_of_40": rule_of_40,
        "burn_rate": round(burn, 2),
        "runway_months": round(_float(latest.runway_months) if latest else 0.0, 1),
    }


@router.get("/waterfall")
def mrr_waterfall(
    company_id: UUID,
    months: int = Query(12, le=24),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Monthly MRR waterfall: new, expansion, contraction, churn."""
    metrics = (
        db.query(models.MonthlyMetric)
        .filter(models.MonthlyMetric.company_id == company_id)
        .order_by(models.MonthlyMetric.metric_month.asc())
        .limit(months)
        .all()
    )

    result = []
    for i, m in enumerate(metrics):
        mrr = _float(m.total_revenue)
        prior_mrr = _float(metrics[i - 1].total_revenue) if i > 0 else mrr * 0.85
        delta = mrr - prior_mrr

        # Heuristic decomposition from total delta
        new_mrr = max(delta * 0.6, mrr * 0.05)
        expansion = max(delta * 0.3, mrr * 0.02) if delta > 0 else 0.0
        contraction = abs(delta * 0.3) if delta < 0 else mrr * 0.01
        churn = abs(delta * 0.4) if delta < 0 else mrr * 0.015

        result.append({
            "month": m.metric_month.strftime("%b %Y"),
            "mrr": round(mrr, 2),
            "new": round(new_mrr, 2),
            "expansion": round(expansion, 2),
            "contraction": round(contraction, 2),
            "churn": round(churn, 2),
        })
    return {"months": result}


@router.get("/cohorts")
def cohort_retention(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Cohort retention data for heatmap/line chart."""
    cohorts = (
        db.query(models.CustomerCohort)
        .filter(models.CustomerCohort.company_id == company_id)
        .order_by(models.CustomerCohort.customer_acquired_date.asc())
        .all()
    )

    result = []
    for c in cohorts:
        monthly_churn = _float(c.churn_rate)
        # Build synthetic monthly retention curve from churn rate
        retention = [100.0]
        for month in range(1, 13):
            prev = retention[-1]
            ret = round(prev * (1 - monthly_churn), 1)
            retention.append(max(ret, 0.0))

        result.append({
            "cohort": c.cohort_name,
            "cohort_value": c.cohort_value,
            "customer_count": c.customer_count,
            "mrr_total": float(c.mrr_total or 0),
            "nrr": float(c.nrr or 0),
            "ltv": float(c.ltv_estimate or 0),
            "cac": float(c.cac_estimate or 0),
            "churn_rate": monthly_churn,
            "payback_months": float(c.payback_months or 0),
            "retention_curve": retention,  # months 0-12
        })
    return {"cohorts": result, "count": len(result)}


@router.get("/trend")
def metric_trend(
    company_id: UUID,
    months: int = Query(12, le=24),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Monthly MRR, expenses, burn, runway trend for charts."""
    metrics = (
        db.query(models.MonthlyMetric)
        .filter(models.MonthlyMetric.company_id == company_id)
        .order_by(models.MonthlyMetric.metric_month.desc())
        .limit(months)
        .all()
    )
    metrics = list(reversed(metrics))

    return {
        "months": [
            {
                "month": m.metric_month.strftime("%b %Y"),
                "mrr": round(_float(m.total_revenue), 2),
                "expenses": round(_float(m.total_expenses), 2),
                "burn_rate": round(_float(m.burn_rate), 2),
                "runway_months": round(_float(m.runway_months), 1),
                "ending_cash": round(_float(m.ending_cash), 2),
                "net_cash_flow": round(_float(m.net_cash_flow), 2),
            }
            for m in metrics
        ]
    }
