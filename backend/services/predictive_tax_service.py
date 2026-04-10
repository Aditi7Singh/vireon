"""
Predictive Tax Provisioning Service
=====================================
Computes quarterly tax estimates from GL + payroll + jurisdiction data.
Provides deduction optimization suggestions.

Covers:
  - Corporate income tax (multi-jurisdiction)
  - Payroll tax (employer-side)
  - Sales/VAT estimates
  - R&D tax credit identification
  - Estimated quarterly payment schedule
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Jurisdiction name normalization — handles "US", "us", "Us" → canonical key
_JURISDICTION_ALIASES: Dict[str, str] = {
    "us": "US", "usa": "US", "united states": "US",
    "uk": "UK", "gb": "UK", "united kingdom": "UK", "britain": "UK",
    "dubai": "Dubai", "uae": "Dubai", "united arab emirates": "Dubai",
    "india": "India", "in": "India",
    "singapore": "Singapore", "sg": "Singapore",
    "eu": "EU", "europe": "EU",
}


def _normalize_jurisdiction(j: str) -> str:
    """Canonical jurisdiction key from any user-supplied string."""
    return _JURISDICTION_ALIASES.get(j.strip().lower(), j.strip())


# ---------------------------------------------------------------------------
# Tax rate tables (2026 approximations)
# ---------------------------------------------------------------------------

_CORPORATE_TAX_RATES: Dict[str, Dict] = {
    "US": {
        "federal_rate": 0.21,
        "state_rates": {
            "CA": 0.0884, "NY": 0.0685, "TX": 0.0, "DE": 0.0875,
            "WA": 0.0, "FL": 0.055, "default": 0.055,
        },
        "currency": "USD",
    },
    "UK": {"rate": 0.25, "small_profit_rate": 0.19, "small_profit_threshold": 50_000, "currency": "GBP"},
    "Dubai": {"rate": 0.09, "threshold": 375_000, "currency": "AED"},
    "India": {"rate": 0.25, "surcharge": 0.07, "cess": 0.04, "currency": "INR"},
    "Singapore": {"rate": 0.17, "partial_exemption_up_to": 10_000, "currency": "SGD"},
    "EU": {"average_rate": 0.215, "currency": "EUR"},
}

_PAYROLL_TAX_RATES: Dict[str, Dict] = {
    "US": {
        "fica_employer": 0.0765,
        "futa": 0.006,
        "suta": 0.027,
        "total_employer_rate": 0.1095,
    },
    "UK":    {"national_insurance_employer": 0.138},
    "Dubai": {"no_income_tax": True, "visa_medical_estimate_pct": 0.05},
    "India": {"pf_employer": 0.12, "esic_employer": 0.0325},
}

_RD_CREDIT_RATES: Dict[str, float] = {
    "US": 0.20,   # Section 41 R&D credit
    "UK": 0.086,  # RDEC
    "Singapore": 0.25,
    "France": 0.30,
}

# ---------------------------------------------------------------------------
# Core calculation
# ---------------------------------------------------------------------------


def estimate_corporate_tax(
    taxable_income: float,
    jurisdiction: str,
    state: Optional[str] = None,
    ytd_paid: float = 0.0,
) -> Dict[str, Any]:
    """Estimate corporate income tax for a given jurisdiction."""
    jurisdiction = _normalize_jurisdiction(jurisdiction)
    info = _CORPORATE_TAX_RATES.get(jurisdiction, _CORPORATE_TAX_RATES["US"])

    if jurisdiction == "US":
        federal = max(0, taxable_income) * info["federal_rate"]
        state_rate = info["state_rates"].get(state or "default", info["state_rates"]["default"])
        state_tax = max(0, taxable_income) * state_rate
        total = federal + state_tax
        return {
            "federal_tax": round(federal, 2),
            "state_tax": round(state_tax, 2),
            "total_tax": round(total, 2),
            "effective_rate": round(total / max(taxable_income, 1) * 100, 2),
            "remaining_due": round(max(0, total - ytd_paid), 2),
        }

    elif jurisdiction == "Dubai":
        threshold = info.get("threshold", 375_000)
        taxable = max(0, taxable_income - threshold)
        total = taxable * info["rate"]
        return {
            "total_tax": round(total, 2),
            "effective_rate": round(total / max(taxable_income, 1) * 100, 2),
            "remaining_due": round(max(0, total - ytd_paid), 2),
            "note": f"First AED {threshold:,} exempt under UAE Corporate Tax Law",
        }

    elif jurisdiction == "UK":
        rate = info["small_profit_rate"] if taxable_income <= info.get("small_profit_threshold", 50_000) else info["rate"]
        total = max(0, taxable_income) * rate
        return {
            "total_tax": round(total, 2),
            "effective_rate": round(rate * 100, 2),
            "remaining_due": round(max(0, total - ytd_paid), 2),
        }

    else:
        rate = info.get("rate", info.get("average_rate", 0.21))
        total = max(0, taxable_income) * rate
        return {
            "total_tax": round(total, 2),
            "effective_rate": round(rate * 100, 2),
            "remaining_due": round(max(0, total - ytd_paid), 2),
        }


def estimate_payroll_tax(
    total_gross_payroll: float,
    jurisdiction: str,
) -> Dict[str, Any]:
    """Estimate employer-side payroll tax costs."""
    jurisdiction = _normalize_jurisdiction(jurisdiction)
    rates = _PAYROLL_TAX_RATES.get(jurisdiction, _PAYROLL_TAX_RATES["US"])

    if jurisdiction == "US":
        employer_cost = total_gross_payroll * rates["total_employer_rate"]
        return {
            "fica": round(total_gross_payroll * rates["fica_employer"], 2),
            "futa": round(total_gross_payroll * rates["futa"], 2),
            "suta_estimate": round(total_gross_payroll * rates["suta"], 2),
            "total_employer_tax": round(employer_cost, 2),
            "effective_rate_pct": round(rates["total_employer_rate"] * 100, 2),
        }

    elif jurisdiction == "UK":
        ni = total_gross_payroll * rates["national_insurance_employer"]
        return {
            "national_insurance": round(ni, 2),
            "total_employer_tax": round(ni, 2),
            "effective_rate_pct": round(rates["national_insurance_employer"] * 100, 2),
        }

    elif jurisdiction == "India":
        pf = total_gross_payroll * rates["pf_employer"]
        esic = total_gross_payroll * rates["esic_employer"]
        total = pf + esic
        return {
            "provident_fund": round(pf, 2),
            "esic": round(esic, 2),
            "total_employer_tax": round(total, 2),
            "effective_rate_pct": round((pf + esic) / max(total_gross_payroll, 1) * 100, 2),
        }

    else:
        rate = 0.10
        total = total_gross_payroll * rate
        return {
            "total_employer_tax": round(total, 2),
            "effective_rate_pct": round(rate * 100, 2),
            "note": f"Estimated rate for {jurisdiction}",
        }


def identify_rd_credits(
    rd_expenses: float,
    jurisdiction: str,
) -> Dict[str, Any]:
    """Calculate R&D tax credit eligibility."""
    jurisdiction = _normalize_jurisdiction(jurisdiction)
    if jurisdiction == "US":
        rate = _RD_CREDIT_RATES.get("US", 0.20)
        credit = rd_expenses * rate
        return {
            "qualifying_expenses": round(rd_expenses, 2),
            "credit_rate": f"{rate*100:.0f}%",
            "estimated_credit": round(credit, 2),
            "note": "IRC Section 41 R&D Credit. Consult tax advisor for full qualification.",
        }
    elif jurisdiction == "UK":
        rate = _RD_CREDIT_RATES.get("UK", 0.086)
        credit = rd_expenses * rate
        return {
            "qualifying_expenses": round(rd_expenses, 2),
            "credit_rate": f"{rate*100:.1f}%",
            "estimated_credit": round(credit, 2),
            "note": "UK RDEC (Research and Development Expenditure Credit).",
        }
    else:
        rate = _RD_CREDIT_RATES.get(jurisdiction, 0.15)
        credit = rd_expenses * rate
        return {
            "qualifying_expenses": round(rd_expenses, 2),
            "estimated_credit": round(credit, 2),
        }


def generate_quarterly_schedule(
    annual_tax_estimate: float,
    current_quarter: int,
    ytd_paid: float = 0.0,
) -> Dict[str, Any]:
    """Generate quarterly estimated tax payment schedule."""
    quarterly = annual_tax_estimate / 4
    schedule = []
    due_months = {1: "Apr 15", 2: "Jun 15", 3: "Sep 15", 4: "Jan 15"}

    for q in range(1, 5):
        if q < current_quarter:
            status = "past"
        elif q == current_quarter:
            status = "due_now"
        else:
            status = "upcoming"

        schedule.append({
            "quarter": f"Q{q}",
            "due_date": due_months[q],
            "amount": round(quarterly, 2),
            "status": status,
        })

    remaining = max(0, annual_tax_estimate - ytd_paid)
    quarters_left = max(1, 5 - current_quarter)
    catch_up = remaining / quarters_left

    return {
        "schedule": schedule,
        "annual_estimate": round(annual_tax_estimate, 2),
        "ytd_paid": round(ytd_paid, 2),
        "remaining_balance": round(remaining, 2),
        "catch_up_per_quarter": round(catch_up, 2),
    }


# ---------------------------------------------------------------------------
# Deduction Optimizer
# ---------------------------------------------------------------------------


def optimize_deductions(
    gl_entries: List[Dict],
    jurisdiction: str = "US",
) -> List[Dict]:
    """
    Scan GL entries and suggest deduction opportunities.

    Looks for:
    - Section 179 / bonus depreciation eligible assets
    - Home office / remote work deductions
    - Business meals (50% deductible)
    - R&D qualifying expenses
    - Retirement plan contributions
    """
    opportunities = []

    if not gl_entries:
        return opportunities

    import pandas as pd
    df = pd.DataFrame(gl_entries)
    if "amount" not in df.columns:
        return opportunities

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["account"] = df.get("account", pd.Series(dtype=str)).fillna("").str.lower()
    df["description"] = df.get("description", pd.Series(dtype=str)).fillna("").str.lower()

    jurisdiction = _normalize_jurisdiction(jurisdiction)

    # R&D expenses
    rd_mask = df["account"].str.contains("r&d|research|development|engineering", na=False)
    rd_total = float(df[rd_mask]["amount"].sum())
    if rd_total > 0 and jurisdiction == "US":
        credit = rd_total * 0.20
        opportunities.append({
            "type": "R&D Tax Credit",
            "amount": round(rd_total, 2),
            "potential_saving": round(credit, 2),
            "description": f"${rd_total:,.0f} in R&D expenses may qualify for Section 41 credit (${credit:,.0f} benefit).",
            "action": "File Form 6765 with CPA",
        })

    # Business meals (50% deductible)
    meals_mask = df["account"].str.contains("meal|entertainment|dining", na=False) | df["description"].str.contains("meal|dinner|lunch", na=False)
    meals_total = float(df[meals_mask]["amount"].sum())
    if meals_total > 0:
        deductible = meals_total * 0.50
        opportunities.append({
            "type": "Business Meals (50%)",
            "amount": round(meals_total, 2),
            "potential_saving": round(deductible * 0.21, 2),
            "description": f"${meals_total:,.0f} in meals/entertainment — 50% deductible = ${deductible:,.0f} deduction.",
            "action": "Ensure receipts and business purpose are documented",
        })

    # Home office / remote
    home_mask = df["account"].str.contains("home|remote|internet|phone", na=False)
    home_total = float(df[home_mask]["amount"].sum())
    if home_total > 500:
        opportunities.append({
            "type": "Remote Work Expenses",
            "amount": round(home_total, 2),
            "potential_saving": round(home_total * 0.21, 2),
            "description": f"${home_total:,.0f} in remote-work-related expenses may be fully deductible.",
            "action": "Allocate to business use and document percentage",
        })

    return opportunities


# ---------------------------------------------------------------------------
# Full Provisioning Run
# ---------------------------------------------------------------------------


def run_tax_provisioning(
    gl_entries: List[Dict],
    payroll_entries: List[Dict],
    jurisdiction: str = "US",
    state: Optional[str] = None,
    current_quarter: int = 1,
    ytd_tax_paid: float = 0.0,
) -> Dict[str, Any]:
    """
    Run the full predictive tax provisioning analysis.

    Returns quarterly estimates, payroll taxes, R&D credits, and deduction tips.
    """
    import pandas as pd

    jurisdiction = _normalize_jurisdiction(jurisdiction)

    # Compute taxable income from GL
    df = pd.DataFrame(gl_entries) if gl_entries else pd.DataFrame()
    if not df.empty and "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        revenue = float(df[df["amount"] > 0]["amount"].sum())
        expenses = float(df[df["amount"] < 0]["amount"].abs().sum())
    else:
        revenue = 0.0
        expenses = 0.0

    taxable_income = revenue - expenses

    # Payroll
    total_payroll = 0.0
    if payroll_entries:
        for pe in payroll_entries:
            total_payroll += float(pe.get("gross_pay", 0))

    # Corporate tax
    corp_tax = estimate_corporate_tax(taxable_income, jurisdiction, state, ytd_tax_paid)

    # Payroll tax
    payroll_tax = estimate_payroll_tax(total_payroll, jurisdiction)

    # R&D expenses
    rd_expenses = 0.0
    if not df.empty and "account" in df.columns:
        df["account_lower"] = df["account"].astype(str).str.lower()
        rd_mask = df["account_lower"].str.contains("r&d|research|development|engineering", na=False)
        rd_expenses = float(df[rd_mask]["amount"].abs().sum())

    rd_credit = identify_rd_credits(rd_expenses, jurisdiction)

    # Quarterly schedule
    annual_estimate = corp_tax["total_tax"] + payroll_tax.get("total_employer_tax", 0)
    quarterly = generate_quarterly_schedule(annual_estimate, current_quarter, ytd_tax_paid)

    # Deduction opportunities
    deductions = optimize_deductions(gl_entries, jurisdiction)

    net_after_credits = corp_tax["total_tax"] - rd_credit.get("estimated_credit", 0)

    return {
        "jurisdiction": jurisdiction,
        "state": state,
        "period": f"Q{current_quarter} {date.today().year}",
        "taxable_income": round(taxable_income, 2),
        "total_revenue": round(revenue, 2),
        "total_expenses": round(expenses, 2),
        "corporate_tax": corp_tax,
        "payroll_tax": payroll_tax,
        "rd_credit": rd_credit,
        "net_tax_after_credits": round(max(0, net_after_credits), 2),
        "quarterly_schedule": quarterly,
        "deduction_opportunities": deductions,
        "total_deduction_savings": round(sum(d.get("potential_saving", 0) for d in deductions), 2),
        "summary": (
            f"Estimated annual tax: ${annual_estimate:,.0f}. "
            f"Net after R&D credit: ${max(0, net_after_credits):,.0f}. "
            f"{len(deductions)} deduction opportunities found."
        ),
    }
