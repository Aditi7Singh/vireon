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


def _fallback_recommendations(context: dict) -> list:
    runway = context.get("runway", {}).get("runway_months", 0)
    burn = context.get("burn_summary", {}).get("net_burn", 0)
    return [
        {
            "id": "rec-1",
            "priority": "high" if runway < 9 else "medium",
            "category": "runway",
            "title": "Protect runway against current burn",
            "finding": f"Current monthly net burn is INR {burn:,.0f} with runway at {runway:.1f} months.",
            "impact_inr": burn * 0.1,
            "impact_runway_days": 20,
            "action": "Reduce non-critical discretionary spend by 10% over the next 30 days.",
            "confidence": 0.78,
        }
    ]


def generate_recommendations(company_id: UUID, db: Session) -> dict:
    context = gather_financial_context(company_id, db)

    system_prompt = (
        "You are Vireon, the AI finance manager for Seedling Labs, an Indian startup building three products: "
        "Orchard, Sprouts, and AI Lab. You have two offices: Bengaluru (HQ) and Gangavathi (new). "
        "Your job is to act as a Chief Financial Officer. You will be given financial data. Generate 4-6 specific, actionable recommendations. "
        "Each recommendation must: (1) name the exact issue or opportunity, (2) give a specific number/impact in INR or months of runway, "
        "(3) suggest a concrete action. Do NOT give generic advice. Format as JSON array."
    )

    recommendations = _fallback_recommendations(context)

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
                parsed = json.loads(content) if isinstance(content, str) else content
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
