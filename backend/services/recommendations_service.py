from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

import requests
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
from services import burn_service, forecasting_service


def gather_financial_context(company_id: UUID, db: Session) -> dict:
    today = date.today()
    month = today.strftime("%Y-%m")
    burn_summary = burn_service.get_net_burn(company_id, db, month)

    trend = []
    for i in range(3):
        m = (today.replace(day=1) - timedelta(days=30 * i)).strftime("%Y-%m")
        trend.append({"month": m, **burn_service.get_net_burn(company_id, db, m)})

    runway = forecasting_service.calculate_dynamic_runway(company_id, db)

    product_pl = []
    for i in range(3):
        m = (today.replace(day=1) - timedelta(days=30 * i)).strftime("%Y-%m")
        product_pl.append({"month": m, "data": burn_service.get_product_pl(company_id, db, m)})

    headcount = burn_service.get_headcount_costs(company_id, db)

    anomalies = (
        db.query(models.Anomaly)
        .filter(models.Anomaly.company_id == company_id, models.Anomaly.created_at >= datetime.utcnow() - timedelta(days=30))
        .all()
    )

    upcoming = (
        db.query(models.FinancialLedgerEntry)
        .filter(models.FinancialLedgerEntry.company_id == company_id, models.FinancialLedgerEntry.transaction_date > today)
        .order_by(models.FinancialLedgerEntry.transaction_date.asc())
        .all()
    )

    top_growth = sorted(
        burn_summary.get("breakdown_by_category", {}).items(), key=lambda x: x[1], reverse=True
    )[:5]

    return {
        "burn_summary": burn_summary,
        "three_month_trend": trend,
        "runway": runway,
        "product_pl_last_3_months": product_pl,
        "pending_hires": headcount.get("pending_hires", []),
        "anomalies_last_30_days": [
            {"severity": a.severity, "type": a.type, "description": a.description, "actual": float(a.actual_value or 0)}
            for a in anomalies
        ],
        "upcoming_expenses": [
            {
                "date": x.transaction_date.isoformat(),
                "category": x.category.value,
                "amount_inr": float(x.amount_inr),
                "description": x.description,
            }
            for x in upcoming
        ],
        "top_5_cost_categories": [{"category": c, "amount": v} for c, v in top_growth],
    }


def _generate_logic_based_recommendations(context: dict) -> list:
    recommendations = []
    runway_months = context.get("runway", {}).get("runway_months", 0)
    burn_summary = context.get("burn_summary", {})
    net_burn = burn_summary.get("net_burn", 0)
    rev_growth = burn_summary.get("revenue_growth_mom", 0)
    cost_growth = burn_summary.get("expense_growth_mom", 0)

    # 1. Runway & Burn Rule
    if runway_months < 9:
        priority = "high" if runway_months < 6 else "medium"
        recommendations.append({
            "id": "rec-runway-1",
            "priority": priority,
            "category": "runway",
            "title": "Cash preservation required" if priority == "high" else "Runway monitoring",
            "finding": f"Runway is {runway_months:.1f} months. MoM costs grew {cost_growth:.1f}% while revenue grew {rev_growth:.1f}%.",
            "impact_inr": net_burn * 0.15,
            "impact_runway_days": 45 if priority == "high" else 20,
            "action": "Freeze non-essential hiring and reduce discretionary marketing spend by 15% immediately." if priority == "high" else "Monitor MoM burn and defer non-critical equipment purchases.",
            "confidence": 0.90
        })

    # 2. Product Profitability Rule
    product_data = context.get("product_pl_last_3_months", [])
    if product_data:
        latest = product_data[0].get("data", {})
        product_rows = []
        if isinstance(latest, dict):
            for product_name, values in latest.items():
                values = values or {}
                product_rows.append(
                    {
                        "product": product_name,
                        "gross_margin_pct": float(values.get("gross_margin_pct", 0) or 0),
                        "revenue": float(values.get("total_revenue", 0) or 0),
                    }
                )
        elif isinstance(latest, list):
            product_rows = latest

        for prod in product_rows:
            margin = float(prod.get("gross_margin_pct", 0) or 0)
            name = str(prod.get("product", "Unknown Product"))
            if margin < 30 and name.lower() != "ai_lab":
                impact_base = float(prod.get("revenue", 0) or 0)
                recommendations.append({
                    "id": f"rec-margin-{name.lower().replace(' ', '-')}",
                    "priority": "high",
                    "category": "profitability",
                    "title": f"Low Margin on {name}",
                    "finding": f"{name} is operating at a {margin:.1f}% gross margin, below the 40% target.",
                    "impact_inr": impact_base * 0.1,
                    "impact_runway_days": 12,
                    "action": f"Audit cost-to-serve for {name}, remove low-ROI infra usage, and revisit pricing for low-margin customer segments.",
                    "confidence": 0.85
                })

    # 3. Vendor Anomaly Rule
    anomalies = context.get("anomalies_last_30_days", [])
    for a in anomalies:
        if a.get("severity") == "high" or a.get("actual", 0) > 100000:
            recommendations.append({
                "id": f"rec-anomaly-{a.get('type')}",
                "priority": "medium",
                "category": "optimization",
                "title": f"Investigation: {a.get('type')}",
                "finding": f"Anomaly detected: {a.get('description')}. Actual impact: INR {a.get('actual'):,.0f}.",
                "impact_inr": a.get("actual", 0),
                "action": "Review the specific ledger entries for this anomaly and verify if this is a one-time setup cost or a recurring leak.",
                "confidence": 0.95
            })

    # 4. Tax/Statutory Rule (Simplified)
    # If cash is low vs impending tax liability (if we had upcoming tax logic)
    # Skipping for now to keep it concise, but can be added in next iteration.

    # Fallback if nothing specific found
    if not recommendations:
        recommendations = _fallback_recommendations(context)

    return recommendations


def _fallback_recommendations(context: dict) -> list:
    burn_summary = context.get("burn_summary", {})
    breakdown = burn_summary.get("breakdown_by_category", {}) or {}
    top_cost = sorted(breakdown.items(), key=lambda x: float(x[1] or 0), reverse=True)
    top_category, top_amount = top_cost[0] if top_cost else ("misc", 0.0)
    runway_months = float(context.get("runway", {}).get("runway_months", 0) or 0)
    runway_buffer_action = (
        "Build a 90-day cash defense plan and lock discretionary spend approvals to Finance."
        if runway_months and runway_months < 9
        else "Keep a monthly burn review rhythm and pre-approve only high-ROI growth spends."
    )

    return [
        {
            "id": "rec-fallback-burn-governance",
            "priority": "medium",
            "category": "governance",
            "title": "Tighten burn governance",
            "finding": f"Top expense category this month is {top_category} at INR {float(top_amount):,.0f}.",
            "impact_inr": float(top_amount) * 0.08,
            "impact_runway_days": 10,
            "action": "Introduce weekly owner-level spend reviews for the top 3 cost categories and cap unplanned spend.",
            "confidence": 0.78,
        },
        {
            "id": "rec-fallback-runway-buffer",
            "priority": "high" if runway_months and runway_months < 9 else "low",
            "category": "runway",
            "title": "Protect runway buffer",
            "finding": f"Current projected runway is {runway_months:.1f} months.",
            "impact_inr": abs(float(burn_summary.get("net_burn", 0) or 0)) * 0.1,
            "impact_runway_days": 15,
            "action": runway_buffer_action,
            "confidence": 0.82,
        },
    ]


def generate_recommendations(company_id: UUID, db: Session) -> dict:
    context = gather_financial_context(company_id, db)

    system_prompt = (
        "You are Vireon, the AI finance manager for Seedling Labs. "
        "Your job is to provide Chief Financial Officer level advice. "
        "You will be given financial context and a list of rule-based insights. "
        "Rewrite or improve these insights into a highly professional JSON list. "
        "Ensure each recommendation has a specific title, finding, action, and impact_inr."
    )

    # Combine logic-based rules with optional AI enrichment
    base_recommendations = _generate_logic_based_recommendations(context)
    recommendations = base_recommendations

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"},
                json={
                    "model": "anthropic/claude-sonnet-4",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": json.dumps(context)},
                    ],
                    "temperature": 0.2,
                },
                timeout=30,
            )
            if resp.ok:
                content = resp.json()["choices"][0]["message"]["content"]
                parsed = None
                if isinstance(content, str):
                    try:
                        parsed = json.loads(content)
                    except Exception:
                        parsed = None
                elif isinstance(content, list):
                    parsed = content
                if isinstance(parsed, list) and parsed:
                    recommendations = parsed
        except Exception:
            pass

    runway_at_gen = context.get("runway", {}).get("runway_months")
    report = models.RecommendationReport(
        company_id=company_id,
        generated_at=datetime.utcnow(),
        month=date.today().strftime("%Y-%m"),
        recommendations=recommendations,
        runway_at_generation=runway_at_gen,
        status=models.RecommendationStatus.ACTIVE,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {"report_id": str(report.id), "recommendations": recommendations, "runway_at_generation": runway_at_gen}


def generate_impact_alert(company_id: UUID, db: Session) -> Optional[dict]:
    runway = forecasting_service.calculate_dynamic_runway(company_id, db)
    runway_months = float(runway.get("runway_months", 0))

    if runway_months >= 9:
        return None

    level = models.RunwayAlertLevel.CRITICAL if runway_months < 6 else models.RunwayAlertLevel.WARNING
    top = sorted(
        runway.get("monthly_projections", []), key=lambda x: x.get("net_burn", 0), reverse=True
    )[:3]
    payload = {
        "level": level.value,
        "runway_months": runway_months,
        "runway_date": runway.get("runway_date").isoformat() if hasattr(runway.get("runway_date"), "isoformat") else str(runway.get("runway_date")),
        "top_3_burn_drivers": top,
        "suggested_immediate_actions": [
            "Freeze discretionary spend for 30 days.",
            "Defer non-critical hiring plans.",
            "Prioritize collections and shorten receivables cycle.",
        ],
    }

    alert = models.RunwayAlert(
        company_id=company_id,
        alert_level=level,
        runway_months=runway_months,
        runway_date=runway.get("runway_date"),
        alert_data=payload,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    return {"alert_id": str(alert.id), **payload}
