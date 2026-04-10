"""
Vendor Risk Intelligence + Zero-Shot Tax Code Classifier
==========================================================

MODULE 1 — Vendor Risk Intelligence
  Analyzes vendor payment patterns, concentration risk, and financial signals
  to generate a vendor risk score (0–100) and risk flags.

  Risk factors scored:
    - Payment concentration: single vendor > 30% of AP
    - Payment terms drift: avg days to pay increasing
    - Sole-source dependency: vendor with no alternative
    - Fraud signals: invoice number patterns, round numbers
    - Credit risk indicators: missing TIN/W-9, cash payments

MODULE 2 — Zero-Shot Tax Code Classifier
  Uses keyword matching + embedding-style heuristics to classify GL descriptions
  into IRS/GAAP account codes without a trained model.

  Supports:
    - COGS (5xxx)
    - R&D Expense (7xxx)
    - SG&A (6xxx)
    - Travel & Entertainment (6150)
    - Depreciation (7100)
    - Interest Expense (7200)
    - Software/SaaS (6400)
    - Payroll (6100)
    - Professional Services (6300)
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ===========================================================================
# MODULE 1 — Vendor Risk Intelligence
# ===========================================================================


_RISK_WEIGHTS = {
    "concentration": 25,
    "payment_drift": 20,
    "sole_source": 20,
    "fraud_signals": 20,
    "credit_signals": 15,
}


def analyze_vendor_risk(
    ap_entries: List[Dict],
    vendor_metadata: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Analyze vendor risk across all AP entries.

    Args:
        ap_entries: [{vendor, amount, invoice_date, paid_date, invoice_number, account}]
        vendor_metadata: [{vendor, tin_on_file, payment_terms_days, sole_source}]

    Returns:
        {
          overall_risk_score,
          vendors: [{vendor, risk_score, risk_flags, spend_amount, concentration_pct}],
          top_risks: [...],
          recommendations: [...],
        }
    """
    if not ap_entries:
        return {"error": "no_data", "message": "No AP entries provided"}

    df = pd.DataFrame(ap_entries)
    df["amount"] = pd.to_numeric(df.get("amount", 0), errors="coerce").fillna(0).abs()
    df["vendor"] = df.get("vendor", pd.Series(dtype=str)).fillna("Unknown").astype(str)

    for col in ["invoice_date", "paid_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    total_ap = float(df["amount"].sum())
    if total_ap == 0:
        total_ap = 1.0

    # Vendor metadata lookup
    meta_map: Dict[str, Dict] = {}
    if vendor_metadata:
        for m in vendor_metadata:
            meta_map[str(m.get("vendor", ""))] = m

    vendor_scores = []
    for vendor, grp in df.groupby("vendor"):
        vendor = str(vendor)
        spend = float(grp["amount"].sum())
        concentration = spend / total_ap
        flags: List[Dict] = []
        score_components: Dict[str, float] = {}

        # 1. Concentration risk
        if concentration > 0.40:
            conc_score = _RISK_WEIGHTS["concentration"]
            flags.append({
                "flag": "high_concentration",
                "severity": "high",
                "detail": f"This vendor represents {concentration*100:.0f}% of total AP (>${spend:,.0f})",
            })
        elif concentration > 0.25:
            conc_score = _RISK_WEIGHTS["concentration"] * 0.6
            flags.append({
                "flag": "moderate_concentration",
                "severity": "medium",
                "detail": f"Vendor represents {concentration*100:.0f}% of AP",
            })
        else:
            conc_score = 0
        score_components["concentration"] = conc_score

        # 2. Payment drift (days to pay increasing)
        drift_score = 0.0
        if "invoice_date" in df.columns and "paid_date" in df.columns:
            grp_valid = grp.dropna(subset=["invoice_date", "paid_date"])
            if len(grp_valid) >= 3:
                days_to_pay = (grp_valid["paid_date"] - grp_valid["invoice_date"]).dt.days
                days_to_pay = days_to_pay[days_to_pay >= 0]
                if len(days_to_pay) >= 3:
                    recent = float(days_to_pay.tail(3).mean())
                    historical = float(days_to_pay.mean())
                    if recent > historical * 1.3 and recent > 45:
                        drift_score = _RISK_WEIGHTS["payment_drift"]
                        flags.append({
                            "flag": "payment_drift",
                            "severity": "medium",
                            "detail": f"Avg payment time increased to {recent:.0f} days (vs {historical:.0f} historical)",
                        })
        score_components["payment_drift"] = drift_score

        # 3. Sole-source dependency
        sole_score = 0.0
        meta = meta_map.get(vendor, {})
        if meta.get("sole_source", False):
            sole_score = _RISK_WEIGHTS["sole_source"]
            flags.append({
                "flag": "sole_source",
                "severity": "high",
                "detail": "No identified alternative vendors — supply chain risk",
            })
        score_components["sole_source"] = sole_score

        # 4. Fraud signals
        fraud_score = 0.0
        inv_numbers = grp.get("invoice_number", pd.Series(dtype=str)).fillna("").astype(str)
        round_amounts = grp[grp["amount"] % 1000 == 0]["amount"].count()
        if round_amounts > len(grp) * 0.5 and len(grp) >= 3:
            fraud_score += _RISK_WEIGHTS["fraud_signals"] * 0.5
            flags.append({
                "flag": "round_dollar_invoices",
                "severity": "low",
                "detail": f"{round_amounts}/{len(grp)} invoices are round-dollar amounts",
            })
        # Duplicate invoice number check
        if len(inv_numbers) > 0:
            dupe_inv = inv_numbers[inv_numbers.duplicated()].unique()
            if len(dupe_inv) > 0:
                fraud_score += _RISK_WEIGHTS["fraud_signals"]
                flags.append({
                    "flag": "duplicate_invoice_numbers",
                    "severity": "high",
                    "detail": f"Duplicate invoice numbers detected: {', '.join(list(dupe_inv)[:3])}",
                })
        score_components["fraud_signals"] = fraud_score

        # 5. Credit signals
        credit_score = 0.0
        if not meta.get("tin_on_file", True):
            credit_score += _RISK_WEIGHTS["credit_signals"]
            flags.append({
                "flag": "no_tin_on_file",
                "severity": "high",
                "detail": "No TIN/W-9 on file — 1099 reporting required",
            })
        score_components["credit_signals"] = credit_score

        total_score = min(100, sum(score_components.values()))
        risk_level = "high" if total_score >= 50 else "medium" if total_score >= 25 else "low"

        vendor_scores.append({
            "vendor": vendor,
            "risk_score": round(total_score, 1),
            "risk_level": risk_level,
            "spend_amount": round(spend, 2),
            "concentration_pct": round(concentration * 100, 1),
            "invoice_count": len(grp),
            "flags": flags,
            "score_breakdown": {k: round(v, 1) for k, v in score_components.items()},
        })

    vendor_scores.sort(key=lambda v: v["risk_score"], reverse=True)

    # Overall portfolio risk
    if vendor_scores:
        weighted_risk = sum(
            v["risk_score"] * v["spend_amount"] for v in vendor_scores
        ) / total_ap
    else:
        weighted_risk = 0.0

    top_risks = vendor_scores[:5]
    recommendations = _generate_vendor_recommendations(vendor_scores, total_ap)

    return {
        "total_ap_analyzed": round(total_ap, 2),
        "vendor_count": len(vendor_scores),
        "overall_risk_score": round(weighted_risk, 1),
        "overall_risk_level": "high" if weighted_risk >= 50 else "medium" if weighted_risk >= 25 else "low",
        "vendors": vendor_scores,
        "top_risks": top_risks,
        "recommendations": recommendations,
        "summary": (
            f"Analyzed {len(vendor_scores)} vendors (${total_ap:,.0f} AP). "
            f"Weighted risk score: {weighted_risk:.0f}/100. "
            f"{sum(1 for v in vendor_scores if v['risk_level'] == 'high')} high-risk vendors identified."
        ),
    }


def _generate_vendor_recommendations(vendors: List[Dict], total_ap: float) -> List[Dict]:
    recs = []
    high_risk = [v for v in vendors if v["risk_level"] == "high"]
    for v in high_risk[:3]:
        for flag in v["flags"]:
            if flag["flag"] == "high_concentration":
                recs.append({
                    "priority": "high",
                    "vendor": v["vendor"],
                    "action": f"Diversify suppliers — {v['vendor']} is {v['concentration_pct']}% of AP",
                })
            elif flag["flag"] == "duplicate_invoice_numbers":
                recs.append({
                    "priority": "high",
                    "vendor": v["vendor"],
                    "action": f"Investigate duplicate invoices from {v['vendor']} — possible fraud",
                })
            elif flag["flag"] == "no_tin_on_file":
                recs.append({
                    "priority": "high",
                    "vendor": v["vendor"],
                    "action": f"Collect W-9 from {v['vendor']} before next payment",
                })
    return recs[:5]


# ===========================================================================
# MODULE 2 — Zero-Shot Tax Code Classifier
# ===========================================================================


_TAX_CODE_RULES: List[Dict] = [
    {
        "code": "6100",
        "name": "Payroll & Compensation",
        "keywords": ["salary", "wage", "payroll", "compensation", "bonus", "commission",
                     "benefits", "401k", "health insurance", "dental", "vision", "pto"],
    },
    {
        "code": "5000",
        "name": "Cost of Goods Sold",
        "keywords": ["cogs", "cost of goods", "direct cost", "material", "manufacturing",
                     "production", "inventory", "raw material", "supplier", "fulfillment"],
    },
    {
        "code": "6200",
        "name": "Research & Development",
        "keywords": ["r&d", "research", "development", "engineering", "prototype",
                     "testing", "experimentation", "innovation", "laboratory", "scientist"],
    },
    {
        "code": "6300",
        "name": "Professional Services",
        "keywords": ["legal", "accounting", "audit", "consulting", "advisory", "attorney",
                     "lawyer", "cpa", "outsourced", "contractor", "freelance", "agency"],
    },
    {
        "code": "6150",
        "name": "Travel & Entertainment",
        "keywords": ["travel", "hotel", "flight", "airfare", "uber", "lyft", "taxi",
                     "entertainment", "meal", "dinner", "lunch", "conference", "event"],
    },
    {
        "code": "6400",
        "name": "Software & SaaS",
        "keywords": ["software", "saas", "subscription", "license", "aws", "azure", "gcp",
                     "google cloud", "stripe", "salesforce", "hubspot", "slack", "zoom",
                     "github", "notion", "figma", "linear"],
    },
    {
        "code": "6500",
        "name": "Marketing & Advertising",
        "keywords": ["marketing", "advertising", "ad spend", "google ads", "facebook ads",
                     "meta", "pr", "brand", "seo", "campaign", "content", "social media"],
    },
    {
        "code": "7100",
        "name": "Depreciation & Amortization",
        "keywords": ["depreciation", "amortization", "d&a", "fixed assets", "capex",
                     "equipment", "furniture", "vehicle", "property"],
    },
    {
        "code": "7200",
        "name": "Interest Expense",
        "keywords": ["interest", "loan fee", "financing", "debt service", "bank charge",
                     "credit facility", "line of credit"],
    },
    {
        "code": "6600",
        "name": "Rent & Facilities",
        "keywords": ["rent", "lease", "office", "facility", "utilities", "electricity",
                     "water", "internet", "telephone", "coworking"],
    },
    {
        "code": "6700",
        "name": "Insurance",
        "keywords": ["insurance", "liability", "d&o", "directors", "officers", "workers comp",
                     "property insurance", "cyber insurance"],
    },
    {
        "code": "4000",
        "name": "Revenue",
        "keywords": ["revenue", "sales", "income", "subscription revenue", "service revenue",
                     "product sales", "consulting revenue", "mrr"],
    },
]

_CONFIDENCE_EXACT = 0.95
_CONFIDENCE_PARTIAL = 0.75
_CONFIDENCE_WEAK = 0.55
_CONFIDENCE_DEFAULT = 0.30


def classify_transaction(
    description: str,
    amount: float = 0.0,
    vendor: str = "",
    existing_account: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Zero-shot classify a GL entry into a tax/account code.

    Returns best match + confidence + alternatives.
    """
    text = f"{description} {vendor}".lower().strip()
    text = re.sub(r"[^a-z0-9 &/]", " ", text)

    scores: List[Tuple[Dict, float, List[str]]] = []

    for rule in _TAX_CODE_RULES:
        matched_keywords = []
        for kw in rule["keywords"]:
            if kw.lower() in text:
                matched_keywords.append(kw)

        if not matched_keywords:
            continue

        # Score based on number and quality of keyword matches
        score = 0.0
        for kw in matched_keywords:
            # Exact word match scores higher
            if re.search(rf"\b{re.escape(kw)}\b", text):
                score += _CONFIDENCE_EXACT / len(rule["keywords"])
            else:
                score += _CONFIDENCE_PARTIAL / len(rule["keywords"])

        score = min(0.97, score * len(matched_keywords))
        scores.append((rule, score, matched_keywords))

    scores.sort(key=lambda x: x[1], reverse=True)

    if not scores:
        # Return uncategorized with low confidence
        return {
            "account_code": "9999",
            "account_name": "Uncategorized",
            "confidence": _CONFIDENCE_DEFAULT,
            "matched_keywords": [],
            "alternatives": [],
            "suggestion": "Review manually — no matching tax category found",
        }

    best_rule, best_score, best_kw = scores[0]
    alternatives = [
        {
            "code": r["code"],
            "name": r["name"],
            "confidence": round(s, 3),
            "matched_keywords": kws,
        }
        for r, s, kws in scores[1:4]
    ]

    return {
        "account_code": best_rule["code"],
        "account_name": best_rule["name"],
        "confidence": round(best_score, 3),
        "matched_keywords": best_kw,
        "alternatives": alternatives,
        "suggestion": (
            f"Classify as '{best_rule['name']}' (code {best_rule['code']}) "
            f"— {round(best_score*100):.0f}% confidence based on: {', '.join(best_kw[:3])}"
        ),
    }


def classify_gl_batch(
    gl_entries: List[Dict],
) -> Dict[str, Any]:
    """
    Classify a batch of GL entries.

    Args:
        gl_entries: [{id, description, amount, vendor, account}]

    Returns:
        {classified: [...], unclassified: [...], summary: {...}}
    """
    classified = []
    unclassified = []
    code_distribution: Dict[str, int] = defaultdict(int)

    for entry in gl_entries:
        description = str(entry.get("description", ""))
        vendor = str(entry.get("vendor", ""))
        amount = float(entry.get("amount", 0))
        existing = entry.get("account", "")

        result = classify_transaction(description, amount, vendor, existing)
        result["entry_id"] = entry.get("id", entry.get("entry_id", ""))
        result["original_description"] = description
        result["original_account"] = existing

        if result["confidence"] >= 0.5:
            classified.append(result)
            code_distribution[result["account_code"]] += 1
        else:
            unclassified.append(result)

    total = len(gl_entries)
    classification_rate = len(classified) / max(total, 1)

    return {
        "total_entries": total,
        "classified_count": len(classified),
        "unclassified_count": len(unclassified),
        "classification_rate_pct": round(classification_rate * 100, 1),
        "classified": classified,
        "unclassified": unclassified,
        "code_distribution": dict(code_distribution),
        "summary": (
            f"Classified {len(classified)}/{total} entries "
            f"({classification_rate*100:.0f}% auto-classified). "
            f"{len(unclassified)} require manual review."
        ),
    }
