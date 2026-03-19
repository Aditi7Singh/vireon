"""
Math Engine - Core Financial Metrics
====================================
This module implements deterministic financial formulas for startup metrics
based on industry standards.
"""

from typing import List, Dict, Union, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
import hashlib
import importlib.util
import sys
from pathlib import Path

# Import config.py as a module
config_path = Path(__file__).parent.parent / "config.py"
spec = importlib.util.spec_from_file_location("config_module", config_path)
config_module = importlib.util.module_from_spec(spec)
sys.modules["config_module"] = config_module
spec.loader.exec_module(config_module)
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class FinancialState:
    # --- Position ---
    cash_balance: float          # Actual bank balance (HDFC current account)
    ar_by_aging: Dict[str, float]  # {"0_30_enterprise": x, "0_30_midmarket": x, "31_60": x, ...}
    ap_due_30d: float            # AP invoices due within 30 days
    gst_itc_balance: float       # ITC carry-forward (NOT cash — tax credit only)
    tds_receivable: float        # TDS deducted by customers (NOT cash — 26AS credit)

    # --- Revenue ---
    monthly_mrr: float           # Current MRR (GST-exclusive, accrual basis)
    mrr_growth_rate: float       # Trailing 3-month average monthly growth rate
    monthly_churn_rate: float    # Trailing 3-month average monthly churn rate

    # --- Expenses (all as cash outflow figures, GST-adjusted) ---
    monthly_payroll: float       # Employer cash outflow (not CTC)
    monthly_cloud: float         # AWS base amount (GST-exclusive — ITC claimable)
    monthly_opex: float          # All other opex, net of TDS sent and GST ITC
    monthly_gst_net: float       # Net GST payable this month (output − ITC)

    # --- Metadata ---
    as_of_date: date
    fiscal_year: str             # "FY 2025-26"
    data_source: str             # "merge_dev_live" | "generated_simulation"

    @property
    def adjusted_cash_position(self) -> float:
        """Bank balance + weighted AR − AP due − statutory reserve. (Ref: Spec Section 7.1)"""
        ar_weighted = 0
        for bucket, amount in self.ar_by_aging.items():
            if "0_30_enterprise" in bucket:
                weight = 0.92  # 2% TDS + small risk
            elif "0_30_midmarket" in bucket:
                weight = 0.96  # 2% TDS
            elif "31_60" in bucket:
                weight = 0.78  # TDS + aging
            elif "61_90" in bucket:
                weight = 0.50  # Meaningful risk
            else:  # 90+
                weight = 0.20  # Near bad debt
            ar_weighted += amount * weight
            
        statutory_reserve = self._calculate_statutory_reserve()
        return round(self.cash_balance + ar_weighted - self.ap_due_30d - statutory_reserve, 2)

    @property
    def gross_burn(self) -> float:
        """All outflows: payroll + cloud + opex + gst_net."""
        return self.monthly_payroll + self.monthly_cloud + self.monthly_opex + self.monthly_gst_net

    @property
    def net_burn(self) -> float:
        """Gross burn − cash revenue collected (net of TDS)."""
        # Simplified - would need actual cash collection calculation
        cash_revenue = self.monthly_mrr * 0.98  # Assume 2% TDS deduction
        return max(0, self.gross_burn - cash_revenue)

    def _calculate_statutory_reserve(self) -> float:
        """
        Calculate minimum statutory reserve (3 months PF + 1 month TDS + 1 month GST + 6 months gratuity).
        Ref: Spec Section 7.1
        """
        # monthly_payroll is employer outflow (Gross + Employer PF + etc)
        # 3 months PF (13% of basic)
        monthly_basic_est = (self.monthly_payroll / 1.10) * config_module.BASIC_AS_PCT_OF_CTC # Rough estimate back from outflow
        pf_reserve = monthly_basic_est * 0.13 * 3
        
        # 1 month TDS (Assume 2% of MRR as placeholder for inward TDS liability buffer)
        tds_reserve = self.monthly_mrr * 0.02
        
        # 1 month GST
        gst_reserve = max(0, self.monthly_gst_net)
        
        # 6 months gratuity (4.81% of basic)
        gratuity_reserve = monthly_basic_est * config_module.GRATUITY_RATE * 6
        
        return round(pf_reserve + tds_reserve + gst_reserve + gratuity_reserve, 2)

def calculate_pf_outflow(basic_monthly: float, on_full_basic: bool = True) -> Dict[str, float]:
    """
    Calculate PF outflow for employer contribution.

    Args:
        basic_monthly: Monthly basic salary
        on_full_basic: Whether PF is calculated on full basic (default True)

    Returns:
        Dict with employer outflow breakdown
    """
    pf_basic = basic_monthly if on_full_basic else min(basic_monthly, 15_000)
    employer_pf = round(pf_basic * config_module.PF_EMPLOYER_RATE, 2)    # 12% employer share
    pf_admin = round(pf_basic * config_module.PF_ADMIN_CHARGES, 2)       # 0.50% admin charges
    edli = round(pf_basic * config_module.EDLI_RATE, 2)                  # 0.50% EDLI
    employee_pf = round(pf_basic * config_module.PF_EMPLOYER_RATE, 2)    # 12% employee share (withheld)

    return {
        "employer_outflow": employer_pf + pf_admin + edli,   # ← use for burn rate
        "total_epfo_remittance": employer_pf + employee_pf,   # ← what is remitted
        "employee_pf_deduction": employee_pf,                 # ← deducted from gross
        "pf_admin_edli": pf_admin + edli,
    }

def calculate_esi_outflow(gross_monthly: float) -> Dict[str, float]:
    """
    Calculate ESI outflow if applicable.

    Args:
        gross_monthly: Monthly gross salary

    Returns:
        Dict with ESI breakdown (zero if not applicable)
    """
    if gross_monthly > config_module.ESI_WAGE_CEILING:
        return {
            "employer_esi": 0.0,
            "employee_esi_deduction": 0.0,
            "total_esi_remittance": 0.0,
            "applicable": False
        }

    employer_esi = round(gross_monthly * config_module.ESI_EMPLOYER_RATE, 2)
    employee_esi = round(gross_monthly * config_module.ESI_EMPLOYEE_RATE, 2)

    return {
        "employer_esi": employer_esi,
        "employee_esi_deduction": employee_esi,
        "total_esi_remittance": employer_esi + employee_esi,
        "applicable": True
    }

def calculate_gratuity_provision(basic_monthly: float) -> float:
    """
    Calculate monthly gratuity provision.

    Args:
        basic_monthly: Monthly basic salary

    Returns:
        Monthly gratuity provision amount
    """
    return round(basic_monthly * config_module.GRATUITY_RATE, 2)

def calculate_pt_deduction(gross_monthly: float) -> float:
    """
    Calculate Professional Tax deduction for Karnataka.

    Args:
        gross_monthly: Monthly gross salary

    Returns:
        PT amount to be deducted from employee salary
    """
    for threshold, tax in config_module.PT_SLAB:
        if gross_monthly <= threshold:
            return tax
    return config_module.PT_SLAB[-1][1]  # Last slab for amounts above all thresholds

def decompose_ctc(annual_ctc: float, num_employees: int = 1) -> Dict[str, float]:
    """
    Decompose annual CTC into components for payroll calculation.

    Args:
        annual_ctc: Annual CTC per employee
        num_employees: Number of employees at this CTC level

    Returns:
        Dict with monthly cost breakdown per employee and totals
    """
    monthly_ctc = annual_ctc / 12

    monthly_basic = round(annual_ctc * config_module.BASIC_AS_PCT_OF_CTC / 12, 2)
    monthly_hra = round(monthly_basic * config_module.HRA_AS_PCT_OF_BASIC, 2)

    # Special allowance = CTC - Basic - HRA - Employer PF - Gratuity
    employer_pf_monthly = round(monthly_basic * config_module.PF_EMPLOYER_RATE, 2)
    gratuity_monthly = calculate_gratuity_provision(monthly_basic)
    special_allowance = round(monthly_ctc - monthly_basic - monthly_hra - employer_pf_monthly - gratuity_monthly, 2)

    gross_salary = round(monthly_basic + monthly_hra + special_allowance, 2)

    # Calculate employer costs
    pf_outflow = calculate_pf_outflow(monthly_basic)
    esi_outflow = calculate_esi_outflow(gross_salary)
    ghi_monthly = config_module.GHI_PER_EMPLOYEE_MONTHLY

    employer_monthly_total = round(
        gross_salary +
        pf_outflow["employer_outflow"] +
        esi_outflow["employer_esi"] +
        gratuity_monthly +
        ghi_monthly,
        2
    )

    # Employee deductions
    employee_pf = pf_outflow["employee_pf_deduction"]
    employee_esi = esi_outflow["employee_esi_deduction"]
    pt_deduction = calculate_pt_deduction(gross_salary)
    employee_total_deductions = round(employee_pf + employee_esi + pt_deduction, 2)
    take_home = round(gross_salary - employee_total_deductions, 2)

    return {
        "per_employee_monthly": {
            "basic": monthly_basic,
            "hra": monthly_hra,
            "special_allowance": special_allowance,
            "gross_salary": gross_salary,
            "employer_pf": pf_outflow["employer_outflow"],
            "pf_admin_edli": pf_outflow["pf_admin_edli"],
            "esi_employer": esi_outflow["employer_esi"],
            "gratuity_provision": gratuity_monthly,
            "ghi": ghi_monthly,
            "employer_total_cost": employer_monthly_total,
            "employee_pf_deduction": employee_pf,
            "employee_esi_deduction": employee_esi,
            "pt_deduction": pt_deduction,
            "total_employee_deductions": employee_total_deductions,
            "take_home_pay": take_home
        },
        "totals_monthly": {
            "num_employees": num_employees,
            "total_gross_payroll": gross_salary * num_employees,
            "total_employer_cost": employer_monthly_total * num_employees,
            "total_employee_deductions": employee_total_deductions * num_employees,
            "total_take_home": take_home * num_employees
        }
    }

def calculate_gst_position(month_output_gst: float, month_itc_claimed: float) -> Dict[str, float]:
    """
    Calculate GST position for a month.

    Args:
        month_output_gst: GST collected on sales/invoices
        month_itc_claimed: Input Tax Credit claimed

    Returns:
        Dict with GST position
    """
    net_gst = month_output_gst - month_itc_claimed

    return {
        "output_gst": month_output_gst,
        "itc_claimed": month_itc_claimed,
        "net_gst_payable": max(0, net_gst),
        "itc_carry_forward": max(0, -net_gst),
        "gst_liability": net_gst
    }

def calculate_net_ar_receipt(invoice_base: float, tds_rate: float = config_module.TDS_RATE_CONTRACT) -> Dict[str, float]:
    """
    Calculate net cash received from customer invoice after TDS.

    Args:
        invoice_base: Invoice base amount (GST-exclusive)
        tds_rate: Applicable TDS rate

    Returns:
        Dict with cash receipt breakdown
    """
    gst_amount = round(invoice_base * config_module.GST_RATE_SAAS, 2)
    total_invoice = round(invoice_base + gst_amount, 2)
    tds_deducted = round(invoice_base * tds_rate, 2)  # TDS on base amount only
    net_cash_received = round(total_invoice - tds_deducted, 2)

    return {
        "invoice_base": invoice_base,
        "gst_amount": gst_amount,
        "total_invoice": total_invoice,
        "tds_deducted": tds_deducted,
        "net_cash_received": net_cash_received,
        "tds_receivable": tds_deducted  # Can be claimed via Form 26AS
    }

def calculate_cash_position(
    bank_balance: float,
    ar_by_aging: Dict[str, float],
    ap_due_30d: float,
    monthly_payroll: float,
    monthly_mrr: float,
    monthly_gst_net: float = 0,
    gst_itc_balance: float = 0,
    tds_receivable: float = 0
) -> Dict[str, float]:
    """
    Calculate true liquid cash position. (Ref: Spec Section 7.1)
    """
    # Create temp state to use the property logic
    temp_state = FinancialState(
        cash_balance=bank_balance,
        ar_by_aging=ar_by_aging,
        ap_due_30d=ap_due_30d,
        gst_itc_balance=gst_itc_balance,
        tds_receivable=tds_receivable,
        monthly_mrr=monthly_mrr,
        mrr_growth_rate=0,
        monthly_churn_rate=0,
        monthly_payroll=monthly_payroll,
        monthly_cloud=0,
        monthly_opex=0,
        monthly_gst_net=monthly_gst_net,
        as_of_date=date.today(),
        fiscal_year=config_module.FISCAL_YEAR,
        data_source="verification"
    )
    
    statutory_reserve = temp_state._calculate_statutory_reserve()
    adjusted_cash = temp_state.adjusted_cash_position

    # Weighted AR for breakdown
    ar_weighted = adjusted_cash - bank_balance + ap_due_30d + statutory_reserve

    return {
        "bank_balance": bank_balance,
        "ar_gross": sum(ar_by_aging.values()),
        "ar_weighted": ar_weighted,
        "ap_due_30d": ap_due_30d,
        "statutory_reserve": statutory_reserve,
        "adjusted_cash_position": adjusted_cash,
        "gst_itc_balance": gst_itc_balance,
        "tds_receivable": tds_receivable
    }

def calculate_monthly_burn_india(
    payroll_employer_cost: float,
    cloud_base_cost: float,
    opex_net_cost: float,
    gst_net_payable: float,
    revenue_cash_collected: float
) -> Dict[str, float]:
    """
    Calculate monthly burn variants for India.

    Args:
        payroll_employer_cost: Employer payroll outflow
        cloud_base_cost: Cloud cost (GST-exclusive)
        opex_net_cost: Other expenses (net of TDS/GST)
        gst_net_payable: Net GST payable
        revenue_cash_collected: Cash revenue collected (net of TDS)

    Returns:
        Dict with burn variants
    """
    gross_burn = payroll_employer_cost + cloud_base_cost + opex_net_cost + gst_net_payable
    net_burn = max(0, gross_burn - revenue_cash_collected)

    return {
        "gross_burn": gross_burn,
        "net_burn": net_burn,
        "operational_burn": net_burn,  # Simplified - would exclude one-time items
        "payroll_component": payroll_employer_cost,
        "cloud_component": cloud_base_cost,
        "opex_component": opex_net_cost,
        "gst_component": gst_net_payable,
        "revenue_collected": revenue_cash_collected
    }

def calculate_mrr_arr_india(
    active_customer_mrrs: List[float],
    new_mrr_this_month: float = 0,
    churned_mrr_this_month: float = 0,
    expansion_mrr_this_month: float = 0,
    contraction_mrr_this_month: float = 0
) -> Dict[str, float]:
    """
    Calculate MRR and ARR with waterfall analysis.

    Args:
        active_customer_mrrs: List of MRR values for active customers
        new_mrr_this_month: New customer MRR added
        churned_mrr_this_month: MRR lost to churn
        expansion_mrr_this_month: MRR increase from existing customers
        contraction_mrr_this_month: MRR decrease from existing customers

    Returns:
        Dict with MRR metrics
    """
    beginning_mrr = sum(active_customer_mrrs)
    ending_mrr = (beginning_mrr + new_mrr_this_month + expansion_mrr_this_month -
                  contraction_mrr_this_month - churned_mrr_this_month)

    net_new_mrr = new_mrr_this_month + expansion_mrr_this_month - contraction_mrr_this_month - churned_mrr_this_month
    arr = ending_mrr * 12

    # NRR calculation
    prior_mrr = beginning_mrr
    nrr = ((prior_mrr + expansion_mrr_this_month - churned_mrr_this_month - contraction_mrr_this_month) / prior_mrr * 100) if prior_mrr > 0 else 0

    return {
        "beginning_mrr": beginning_mrr,
        "new_mrr": new_mrr_this_month,
        "expansion_mrr": expansion_mrr_this_month,
        "contraction_mrr": contraction_mrr_this_month,
        "churned_mrr": churned_mrr_this_month,
        "net_new_mrr": net_new_mrr,
        "ending_mrr": ending_mrr,
        "arr": arr,
        "nrr_percentage": nrr,
        "num_active_customers": len(active_customer_mrrs)
    }

def calculate_runway_india(
    cash_position: float,
    forward_net_burn: float,
    base_revenue_assumption: float = None,
    bull_revenue_multiplier: float = 1.2,
    bear_revenue_multiplier: float = 0.8
) -> Dict[str, Any]:
    """
    Calculate runway with base, bull, and bear scenarios.

    Args:
        cash_position: Adjusted cash position
        forward_net_burn: Forward-looking net burn rate
        base_revenue_assumption: Base revenue assumption (optional)
        bull_revenue_multiplier: Bull case revenue multiplier
        bear_revenue_multiplier: Bear case revenue multiplier

    Returns:
        Dict with runway scenarios
    """
    if forward_net_burn <= 0:
        infinite_runway = {
            "months": float('inf'),
            "zero_cash_date": None,
            "scenario": "profitable"
        }
        return {
            "base_runway": infinite_runway,
            "bull_runway": infinite_runway,
            "bear_runway": infinite_runway,
            "alert_level": "HEALTHY",
            "assumptions": ["Company is profitable - no burn rate"],
            "warnings": []
        }

    base_runway_months = round(cash_position / forward_net_burn, 1)

    # Simplified bull/bear - would use different burn assumptions too
    bull_runway_months = round(base_runway_months * bull_revenue_multiplier, 1)
    bear_runway_months = round(base_runway_months * bear_revenue_multiplier, 1)

    # Alert levels
    if bear_runway_months < 6:
        alert_level = "CRITICAL"
    elif bear_runway_months < 9:
        alert_level = "WARNING"
    elif bear_runway_months < 12:
        alert_level = "MONITOR"
    else:
        alert_level = "HEALTHY"

    # Zero cash dates (Spec Section 7.3)
    def calculate_zero_date(months):
        if months == float('inf'): return None
        days = int(months * 30.44) # Average days in month
        return (date.today() + timedelta(days=days)).isoformat()

    base_zero_date = calculate_zero_date(base_runway_months)
    bull_zero_date = calculate_zero_date(bull_runway_months)
    bear_zero_date = calculate_zero_date(bear_runway_months)

    return {
        "base_runway_months": base_runway_months,
        "bull_runway_months": bull_runway_months,
        "bear_runway_months": bear_runway_months,
        "zero_cash_dates": {
            "base": base_zero_date,
            "bull": bull_zero_date,
            "bear": bear_zero_date
        },
        "alert_level": alert_level,
        "assumptions": [
            "MRR: GST-exclusive, accrual basis",
            "Revenue in runway: cash basis (net of TDS 2%)",
            "Bull case: 20% higher revenue",
            "Bear case: 20% lower revenue"
        ],
        "warnings": []
    }

def scenario_hire_india(
    num_hires: int,
    avg_annual_ctc: float,
    start_month: str = "2025-10"
) -> Dict[str, Any]:
    """
    Scenario: Hiring impact on runway.

    Args:
        num_hires: Number of new hires
        avg_annual_ctc: Average annual CTC
        start_month: Month hiring starts

    Returns:
        Dict with hiring scenario impact
    """
    ctc_breakdown = decompose_ctc(avg_annual_ctc, num_hires)

    monthly_cost_per_hire = ctc_breakdown["per_employee_monthly"]["employer_total_cost"]
    monthly_cost_total = ctc_breakdown["totals_monthly"]["total_employer_cost"]

    # Apply productivity ramp (Spec Section 8.1)
    # Months 1-2: 0% productivity, Month 3-6: 50%, Month 7+: 100%
    # Note: ScenarioHire usually returns the cost impact. 
    # For runway impact, we assume the cost starts from month 1.
    
    # Improved runway impact estimation
    current_burn = 1000000 # Placeholder - in reality, would take current state
    new_burn = current_burn + monthly_cost_total
    current_cash = 8300000 # Placeholder
    
    current_runway = round(current_cash / current_burn, 1) if current_burn > 0 else float('inf')
    new_runway = round((current_cash - (80000 + 150000) * num_hires) / new_burn, 1) if new_burn > 0 else float('inf')
    delta_months = new_runway - current_runway if current_runway != float('inf') else 0

    # Break-even calculation
    additional_mrr_needed = monthly_cost_total
    additional_arr_needed = additional_mrr_needed * 12

    return {
        "scenario_type": "hire",
        "inputs": {
            "num_hires": num_hires,
            "avg_annual_ctc_inr": avg_annual_ctc,
            "start_month": start_month
        },
        "cost_breakdown": {
            "monthly_gross_per_hire": ctc_breakdown["per_employee_monthly"]["gross_salary"],
            "employer_pf_per_hire": ctc_breakdown["per_employee_monthly"]["employer_pf"],
            "gratuity_per_hire": ctc_breakdown["per_employee_monthly"]["gratuity_provision"],
            "monthly_cost_per_hire": monthly_cost_per_hire,
            "monthly_cost_total": monthly_cost_total,
            "one_time_equipment": 80000 * num_hires,
            "one_time_recruiting": 150000 * num_hires,
            "total_one_time": (80000 + 150000) * num_hires
        },
        "runway_impact": {
            "current_runway_months": current_runway,
            "new_runway_months": new_runway,
            "delta_months": delta_months,
            "zero_cash_date": "2026-01-15"  # Placeholder
        },
        "break_even": {
            "additional_mrr_needed": additional_mrr_needed,
            "additional_arr_needed": additional_arr_needed,
            "customers_at_avg_acv": additional_arr_needed / 5000000  # Assuming ₹50L avg contract
        },
        "risk_scenarios": {
            "if_mrr_flat_runway": new_runway * 0.6,
            "months_to_critical_threshold": 2.1
        }
    }

def scenario_reduce_cloud(
    reduction_pct: float,
    implementation_month: str = "2025-10"
) -> Dict[str, Any]:
    """
    Scenario: Cloud cost reduction impact.

    Args:
        reduction_pct: Percentage reduction in cloud costs
        implementation_month: Month reduction takes effect

    Returns:
        Dict with cloud reduction scenario
    """
    # Simplified - would need actual baseline calculation
    baseline_monthly = 1000000  # ₹10L baseline
    monthly_savings = baseline_monthly * (reduction_pct / 100)

    return {
        "scenario_type": "cloud_reduction",
        "inputs": {
            "reduction_percentage": reduction_pct,
            "implementation_month": implementation_month
        },
        "savings_breakdown": {
            "baseline_monthly_cloud": baseline_monthly,
            "monthly_savings": monthly_savings,
            "annual_savings": monthly_savings * 12,
            "implementation_lag_months": 1
        },
        "runway_impact": {
            "current_runway_months": 9.8,
            "new_runway_months": 9.8 + (monthly_savings / 100000) * 0.5,  # Rough estimate
            "delta_months": (monthly_savings / 100000) * 0.5,
            "payback_months": 0  # Immediate for reserved instances
        }
    }

def scenario_new_revenue(
    deal_arr: float,
    close_probability: float,
    billing_type: str = "annual_upfront",
    payment_terms_days: int = 30
) -> Dict[str, Any]:
    """
    Scenario: New revenue deal impact.

    Args:
        deal_arr: Annual contract value
        close_probability: Probability of closing (0-1)
        billing_type: "annual_upfront", "monthly", etc.
        payment_terms_days: Payment terms in days

    Returns:
        Dict with revenue scenario
    """
    expected_mrr_impact = (deal_arr / 12) * close_probability

    # Collection timing factor
    if billing_type == "annual_upfront":
        collection_factor = 0.98  # TDS deduction
        cash_timing = "immediate"
    elif payment_terms_days <= 30:
        collection_factor = 0.96
        cash_timing = "30 days"
    else:
        collection_factor = 0.90
        cash_timing = f"{payment_terms_days} days"

    expected_cash_impact = deal_arr * close_probability * collection_factor

    return {
        "scenario_type": "new_revenue",
        "inputs": {
            "deal_arr": deal_arr,
            "close_probability": close_probability,
            "billing_type": billing_type,
            "payment_terms_days": payment_terms_days
        },
        "revenue_impact": {
            "expected_mrr_impact": expected_mrr_impact,
            "expected_arr_impact": expected_mrr_impact * 12,
            "expected_cash_impact": expected_cash_impact,
            "collection_timing": cash_timing,
            "tds_impact": deal_arr * close_probability * 0.02
        },
        "runway_impact": {
            "current_runway_months": 9.8,
            "new_runway_months": 9.8 + (expected_cash_impact / 1000000),  # Rough estimate
            "delta_months": expected_cash_impact / 1000000,
            "break_even_delay_months": payment_terms_days / 30
        }
    }

def build_compliance_calendar(fy: str = None) -> Dict[str, List[str]]:
    """
    Build compliance calendar for the fiscal year.
    
    Args:
        fy: Fiscal year string
        
    Returns:
        Dict mapping months to compliance obligations
    """
    if fy is None:
        fy = config_module.FISCAL_YEAR

    # Simplified - would need full calendar
    return {
        "2025-04": ["GSTR-3B (Mar)", "GSTR-1 (Mar)", "Advance Tax Q4", "PF ECR (Mar)", "ESI (Mar)"],
        "2025-05": ["GSTR-3B (Apr)", "GSTR-1 (Apr)", "PF ECR (Apr)"],
        "2025-06": ["GSTR-3B (May)", "GSTR-1 (May)", "Advance Tax Q1", "PF ECR (May)"],
        "2025-07": ["GSTR-3B (Jun)", "GSTR-1 (Jun)", "TDS Return Q1", "PF ECR (Jun)"],
        "2025-08": ["GSTR-3B (Jul)", "GSTR-1 (Jul)", "PF ECR (Jul)"],
        "2025-09": ["GSTR-3B (Aug)", "GSTR-1 (Aug)", "Advance Tax Q2", "PF ECR (Aug)", "AGM"],
        "2025-10": ["GSTR-3B (Sep)", "GSTR-1 (Sep)", "TDS Return Q2", "PF ECR (Sep)", "ROC Annual Return"],
        "2025-11": ["GSTR-3B (Oct)", "GSTR-1 (Oct)", "PF ECR (Oct)"],
        "2025-12": ["GSTR-3B (Nov)", "GSTR-1 (Nov)", "Advance Tax Q3", "PF ECR (Nov)", "LWF payment"],
        "2026-01": ["GSTR-3B (Dec)", "GSTR-1 (Dec)", "TDS Return Q3", "PF ECR (Dec)"],
        "2026-02": ["GSTR-3B (Jan)", "GSTR-1 (Jan)", "PF ECR (Jan)"],
        "2026-03": ["GSTR-3B (Feb)", "GSTR-1 (Feb)", "Advance Tax Q4", "TDS Return Q4", "PF ECR (Feb)", "Year-end close"]
    }

def detect_anomaly_india(
    current_value: float,
    category: str,
    baseline_months: List[float],
    exclude_anomalies: List[int] = None
) -> Dict[str, Any]:
    """
    Detect anomalies using India-specific baselines.

    Args:
        current_value: Current month's value
        category: Expense/revenue category
        baseline_months: Last 3 months' values
        exclude_anomalies: Months to exclude from baseline

    Returns:
        Dict with anomaly detection result
    """
    if exclude_anomalies:
        baseline_values = [v for i, v in enumerate(baseline_months) if i not in exclude_anomalies]
    else:
        baseline_values = baseline_months

    if not baseline_values:
        return {"is_anomaly": False, "reason": "No baseline data"}

    baseline_mean = sum(baseline_values) / len(baseline_values)
    variance = abs(current_value - baseline_mean) / baseline_mean if baseline_mean > 0 else 0

    is_anomaly = variance > config_module.ANOMALY_VARIANCE_THRESHOLD
    severity = "alert" if variance > config_module.ANOMALY_ALERT_THRESHOLD else "monitor" if is_anomaly else "normal"

    return {
        "is_anomaly": is_anomaly,
        "severity": severity,
        "variance_percentage": variance * 100,
        "baseline_mean": baseline_mean,
        "current_value": current_value,
        "threshold_breached": config_module.ANOMALY_VARIANCE_THRESHOLD if is_anomaly else None
    }

# Standard return schema wrapper
def create_math_result(function_name: str, inputs: Dict[str, Any], result: Dict[str, Any],
                      assumptions: List[str] = None, warnings: List[str] = None) -> Dict[str, Any]:
    """
    Create standardized math engine result.

    Args:
        function_name: Name of the function
        inputs: Input parameters
        result: Calculation result
        assumptions: List of assumptions made
        warnings: List of warnings

    Returns:
        Standardized result dict
    """
    inputs_hash = hashlib.sha256(str(sorted(inputs.items())).encode()).hexdigest()[:16]

    return {
        "function": function_name,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "fiscal_period": config_module.FISCAL_YEAR,
        "inputs_hash": inputs_hash,
        "result": result,
        "assumptions": assumptions or [],
        "warnings": warnings or [],
        "confidence": "high"
    }

# Legacy functions (keeping for compatibility)
def calculate_gross_burn(expenses: List[float]) -> float:
    """
    Gross Burn = Total monthly operating expenses.
    """
    return sum(expenses)

def calculate_net_burn(revenue: float, gross_burn: float) -> float:
    """
    Net Burn = Total monthly revenue - Gross burn.
    (Usually expressed as a positive number for cash loss)
    """
    return max(0, gross_burn - revenue)

def calculate_runway(cash_balance: float, net_burn: float) -> Union[float, str]:
    """
    Runway (months) = Cash balance / Monthly net burn.
    If net burn is <= 0, runway is 'Infinite'.
    """
    if net_burn <= 0:
        return "Infinite"
    return round(cash_balance / net_burn, 2)

def calculate_mrr(subscription_invoices: List[Dict]) -> float:
    """
    MRR = Combined value of all recurring subscription invoices in a month.
    """
    return sum(inv.get('amount', 0) for inv in subscription_invoices)

def calculate_arr(mrr: float) -> float:
    """
    ARR = MRR * 12.
    """
    return mrr * 12

def calculate_gross_margin(revenue: float, cogs: float) -> float:
    """
    Gross Margin = (Revenue - COGS) / Revenue.
    """
    if revenue == 0:
        return 0
    return round((revenue - cogs) / revenue, 4)

def detect_anomaly(current_value: float, moving_average: float, threshold: float = 1.2) -> bool:
    """
    Simple threshold-based anomaly detection.
    Returns True if current_value is more than [threshold]% of moving_average.
    """
    if moving_average == 0:
        return False
    return current_value > (moving_average * threshold)

# ... existing functions continue ...

def calculate_gross_burn(expenses: List[float]) -> float:
    """
    Gross Burn = Total monthly operating expenses.
    """
    return sum(expenses)

def calculate_net_burn(revenue: float, gross_burn: float) -> float:
    """
    Net Burn = Total monthly revenue - Gross burn.
    (Usually expressed as a positive number for cash loss)
    """
    return max(0, gross_burn - revenue)

def calculate_runway(cash_balance: float, net_burn: float) -> Union[float, str]:
    """
    Runway (months) = Cash balance / Monthly net burn.
    If net burn is <= 0, runway is 'Infinite'.
    """
    if net_burn <= 0:
        return "Infinite"
    return round(cash_balance / net_burn, 2)

def calculate_mrr(subscription_invoices: List[Dict]) -> float:
    """
    MRR = Combined value of all recurring subscription invoices in a month.
    """
    return sum(inv.get('amount', 0) for inv in subscription_invoices)

def calculate_arr(mrr: float) -> float:
    """
    ARR = MRR * 12.
    """
    return mrr * 12

def calculate_gross_margin(revenue: float, cogs: float) -> float:
    """
    Gross Margin = (Revenue - COGS) / Revenue.
    """
    if revenue == 0:
        return 0
    return round((revenue - cogs) / revenue, 4)

def detect_anomaly(current_value: float, moving_average: float, threshold: float = 1.2) -> bool:
    """
    Simple threshold-based anomaly detection.
    Returns True if current_value is more than [threshold]% of moving_average.
    """
    if moving_average == 0:
        return False
    return current_value > (moving_average * threshold)

def calculate_budget_variance(actual: float, budget: float) -> Dict[str, Union[float, str]]:
    """
    Variance analysis: Actual vs Budget.
    - Positive variance for revenue is favorable.
    - Positive variance for expenses is unfavorable.
    """
    variance = actual - budget
    percent_variance = (variance / budget) if budget != 0 else 0
    
    return {
        "actual": actual,
        "budget": budget,
        "variance": round(variance, 2),
        "percent_variance": round(percent_variance * 100, 2)
    }


def calculate_tax_rate(total_amount: float, tax_amount: float) -> float:
    """
    Calculate effective tax rate.
    
    Args:
        total_amount: Total amount including tax
        tax_amount: Tax portion
        
    Returns:
        Tax rate as percentage
    """
    if total_amount == 0:
        return 0.0
    return (tax_amount / total_amount) * 100


def calculate_total_tax(db: Session, company_id: str, start_date: date, end_date: date) -> float:
    """
    Calculate total tax paid in a date range.
    
    Args:
        db: Database session
        company_id: Company ID
        start_date: Start date
        end_date: End date
        
    Returns:
        Total tax amount
    """
    from models import Expense, Invoice
    
    expense_tax = db.query(func.sum(Expense.tax_amount)).filter(
        Expense.company_id == company_id,
        Expense.transaction_date >= start_date,
        Expense.transaction_date <= end_date
    ).scalar() or 0.0
    
    # Assuming invoices have tax too, but model might not have tax_amount
    # For now, just expenses
    return float(expense_tax)


def calculate_gross_margin(revenue: float, cogs: float) -> Dict[str, float]:
    """
    Calculate gross margin metrics.
    
    Args:
        revenue: Total revenue
        cogs: Cost of goods sold
        
    Returns:
        Dict with gross profit, margin percentage
    """
    gross_profit = revenue - cogs
    margin_pct = (gross_profit / revenue) * 100 if revenue > 0 else 0
    
    return {
        "gross_profit": gross_profit,
        "gross_margin_percentage": margin_pct
    }


def estimate_cogs_from_expenses(db: Session, company_id: str, month: date) -> float:
    """
    Estimate COGS from expenses in COGS-related categories.
    
    This is a simple estimation - in production, would need proper accounting setup.
    """
    from models import Expense
    
    # Assume categories that are COGS
    cogs_categories = ["Cost of Goods Sold", "Inventory", "Direct Costs"]
    
    start = month.replace(day=1)
    end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    cogs = db.query(func.sum(Expense.total_amount)).filter(
        Expense.company_id == company_id,
        Expense.category.in_(cogs_categories),
        Expense.transaction_date >= start,
        Expense.transaction_date <= end
    ).scalar() or 0.0
    
    return float(cogs)


def calculate_quarterly_tax_estimate(profit_before_tax: float, tax_rate: float = 0.25) -> float:
    """
    Estimate quarterly tax payment based on profit.
    
    Args:
        profit_before_tax: Profit before tax for the quarter
        tax_rate: Estimated tax rate (default 25%)
        
    Returns:
        Estimated tax payment
    """
    return max(0, profit_before_tax * tax_rate)


def calculate_straight_line_depreciation(cost: float, salvage_value: float, useful_life_years: int, current_year: int) -> float:
    """
    Calculate annual straight-line depreciation.
    
    Args:
        cost: Original cost of asset
        salvage_value: Salvage value at end of life
        useful_life_years: Useful life in years
        current_year: Current year of depreciation (1-based)
        
    Returns:
        Depreciation expense for the year
    """
    if current_year > useful_life_years or useful_life_years == 0:
        return 0.0
    
    depreciable_amount = cost - salvage_value
    annual_depreciation = depreciable_amount / useful_life_years
    
    return annual_depreciation


def calculate_monthly_depreciation_schedule(cost: float, salvage_value: float, useful_life_years: int) -> List[float]:
    """
    Calculate monthly depreciation schedule.
    
    Returns:
        List of monthly depreciation amounts for the full life
    """
    annual_dep = calculate_straight_line_depreciation(cost, salvage_value, useful_life_years, 1)
    monthly_dep = annual_dep / 12
    
    return [monthly_dep] * (useful_life_years * 12)


def calculate_declining_balance_depreciation(cost: float, salvage_value: float, useful_life_years: int, current_year: int, factor: float = 2.0) -> float:
    """
    Calculate declining balance depreciation.
    
    Args:
        cost: Original cost
        salvage_value: Salvage value
        useful_life_years: Useful life in years
        current_year: Current year (1-based)
        factor: Depreciation factor (typically 2.0 for double declining)
        
    Returns:
        Depreciation expense for the year
    """
    if current_year > useful_life_years:
        return 0.0
    
    # Calculate depreciation rate
    rate = (factor / useful_life_years)
    
    # Book value at start of year
    book_value_start = cost
    for year in range(1, current_year):
        dep = book_value_start * rate
        book_value_start -= dep
        if book_value_start < salvage_value:
            book_value_start = salvage_value
    
    # Depreciation for current year
    depreciation = book_value_start * rate
    
    # Don't depreciate below salvage value
    if book_value_start - depreciation < salvage_value:
        depreciation = book_value_start - salvage_value
    
    return depreciation


def generate_depreciation_schedule(asset_id: str, db: Session) -> List[Dict[str, Any]]:
    """
    Generate complete depreciation schedule for an asset.
    
    Args:
        asset_id: Asset ID
        db: Database session
        
    Returns:
        List of depreciation entries
    """
    from models import FixedAsset, DepreciationEntry
    
    asset = db.query(FixedAsset).filter(FixedAsset.id == asset_id).first()
    if not asset:
        return []
    
    schedule = []
    accumulated_dep = 0
    current_date = asset.purchase_date
    
    for year in range(1, asset.useful_life_years + 1):
        if asset.depreciation_method == "straight_line":
            annual_dep = calculate_straight_line_depreciation(
                float(asset.purchase_cost), 
                float(asset.salvage_value), 
                asset.useful_life_years, 
                year
            )
        elif asset.depreciation_method == "declining_balance":
            annual_dep = calculate_declining_balance_depreciation(
                float(asset.purchase_cost),
                float(asset.salvage_value),
                asset.useful_life_years,
                year
            )
        else:
            continue
        
        # Monthly entries for the year
        monthly_dep = annual_dep / 12
        for month in range(12):
            accumulated_dep += monthly_dep
            book_value = float(asset.purchase_cost) - accumulated_dep
            
            # Stop if we've reached salvage value
            if book_value < float(asset.salvage_value):
                monthly_dep = book_value - float(asset.salvage_value)
                accumulated_dep += monthly_dep
                book_value = float(asset.salvage_value)
            
            schedule.append({
                "asset_id": asset_id,
                "depreciation_date": current_date,
                "depreciation_amount": monthly_dep,
                "accumulated_depreciation": accumulated_dep,
                "book_value": book_value
            })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
            
            # Stop if fully depreciated
            if book_value <= float(asset.salvage_value):
                break
        
        # Stop if fully depreciated
        if book_value <= float(asset.salvage_value):
            break
    
    return schedule


def calculate_monthly_depreciation_expense(db: Session, company_id: str, month: date) -> float:
    """
    Calculate total monthly depreciation expense for a company.
    
    Args:
        db: Database session
        company_id: Company ID
        month: Month to calculate for
        
    Returns:
        Total depreciation expense for the month
    """
    from models import DepreciationEntry
    
    start_of_month = month.replace(day=1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    total_dep = db.query(func.sum(DepreciationEntry.depreciation_amount)).filter(
        DepreciationEntry.depreciation_date >= start_of_month,
        DepreciationEntry.depreciation_date <= end_of_month,
        DepreciationEntry.asset.has(company_id=company_id)
    ).scalar() or 0.0
    
    # Fallback: estimate from active fixed assets if no manual entries
    if total_dep == 0:
        from models import FixedAsset
        active_assets = db.query(FixedAsset).filter(
            FixedAsset.company_id == company_id,
            FixedAsset.status == "active",
            FixedAsset.purchase_date <= end_of_month
        ).all()
        for asset in active_assets:
            if asset.useful_life_years > 0:
                monthly_dep = (float(asset.purchase_cost) - float(asset.salvage_value)) / (asset.useful_life_years * 12)
                total_dep += monthly_dep
    
    return float(total_dep)


def calculate_loan_payment_schedule(principal: float, annual_rate: float, term_months: int) -> List[Dict[str, float]]:
    """
    Calculate loan payment schedule with principal and interest breakdown.
    
    Args:
        principal: Loan principal amount
        annual_rate: Annual interest rate (e.g., 0.05 for 5%)
        term_months: Term in months
        
    Returns:
        List of payment dictionaries with date, payment, principal, interest, balance
    """
    if term_months <= 0 or principal <= 0:
        return []
    
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        # Interest-free loan
        monthly_payment = principal / term_months
        schedule = []
        balance = principal
        for month in range(1, term_months + 1):
            principal_paid = monthly_payment
            interest_paid = 0
            balance -= principal_paid
            schedule.append({
                "month": month,
                "payment": monthly_payment,
                "principal_paid": principal_paid,
                "interest_paid": interest_paid,
                "remaining_balance": max(0, balance)
            })
        return schedule
    
    # Standard loan formula: P * (r(1+r)^n) / ((1+r)^n - 1)
    monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)
    
    schedule = []
    balance = principal
    
    for month in range(1, term_months + 1):
        interest_paid = balance * monthly_rate
        principal_paid = monthly_payment - interest_paid
        balance -= principal_paid
        
        schedule.append({
            "month": month,
            "payment": monthly_payment,
            "principal_paid": principal_paid,
            "interest_paid": interest_paid,
            "remaining_balance": max(0, balance)
        })
    
    return schedule


def calculate_loan_metrics(db: Session, company_id: str) -> Dict[str, float]:
    """
    Calculate total loan metrics for a company.
    
    Args:
        db: Database session
        company_id: Company ID
        
    Returns:
        Dict with total debt, monthly payments, interest expense
    """
    from models import Loan, LoanPayment
    
    # Get all active loans
    loans = db.query(Loan).filter(
        Loan.company_id == company_id,
        Loan.status == "active"
    ).all()
    
    total_debt = sum(float(loan.remaining_balance or loan.principal_amount) for loan in loans)
    
    # Calculate next month's interest expense
    monthly_interest = 0
    for loan in loans:
        balance = float(loan.remaining_balance or loan.principal_amount)
        # Fix: Divide rate by 100 (e.g. 10.5% -> 0.105)
        monthly_rate = (float(loan.interest_rate) / 100) / 12
        monthly_interest += balance * monthly_rate
    
    # Calculate total monthly payments (simplified - assumes regular payments)
    monthly_payments = 0
    for loan in loans:
        if loan.term_months > 0:
            rate = float(loan.interest_rate) / 100 / 12
            monthly_payments += float(loan.principal_amount) * (rate * (1 + rate) ** loan.term_months) / \
                               ((1 + rate) ** loan.term_months - 1)
    
    return {
        "total_debt": total_debt,
        "monthly_interest_expense": monthly_interest,
        "monthly_debt_payments": monthly_payments,
        "debt_to_equity_ratio": 0.0  # Would need equity data
    }


def calculate_payroll_taxes(gross_pay: float) -> Dict[str, float]:
    """
    Calculate Indian payroll taxes/deductions (PF, ESI, PT) for an employee. (Ref: Spec Section 4)
    """
    # Note: Indian payroll usually works from CTC or Basic.
    # Here we assume gross_pay is the amount before employee deductions but including employer contributions.
    # For simplicity, we use the verified functions.
    
    # Estimate basic (usually 40-50% of gross)
    basic_est = gross_pay * 0.45
    
    pf = calculate_pf_outflow(basic_est)
    esi = calculate_esi_outflow(gross_pay)
    pt = calculate_pt_deduction(gross_pay)
    
    total_deductions = pf["employee_pf_deduction"] + esi["employee_esi_deduction"] + pt
    net_pay = gross_pay - total_deductions
    
    return {
        "gross_pay": gross_pay,
        "employee_pf": pf["employee_pf_deduction"],
        "employee_esi": esi["employee_esi_deduction"],
        "professional_tax": pt,
        "total_deductions": total_deductions,
        "net_pay": net_pay,
        "employer_pf": pf["employer_outflow"],
        "employer_esi": esi["employer_esi"]
    }


def calculate_monthly_payroll_cost(db: Session, company_id: str, month: date) -> Dict[str, float]:
    """
    Calculate total monthly payroll cost for a company.
    
    Args:
        db: Database session
        company_id: Company ID
        month: Month to calculate for
        
    Returns:
        Dict with payroll cost breakdown
    """
    from models import Employee, PayrollEntry
    
    # Get all active employees
    employees = db.query(Employee).filter(
        Employee.company_id == company_id,
        Employee.status == "active"
    ).all()
    
    # Calculate base salaries
    monthly_salaries = 0
    for emp in employees:
        if emp.pay_frequency == "monthly":
            monthly_salaries += float(emp.salary)
        elif emp.pay_frequency == "biweekly":
            monthly_salaries += float(emp.salary) * 26 / 12  # 26 biweekly periods per year
        elif emp.pay_frequency == "weekly":
            monthly_salaries += float(emp.salary) * 52 / 12  # 52 weekly periods per year
    
    # Get actual payroll entries for the month
    start_of_month = month.replace(day=1)
    # Correct end of month calculation
    if start_of_month.month == 12:
        end_of_month = date(start_of_month.year + 1, 1, 1) - timedelta(days=1)
    else:
        end_of_month = date(start_of_month.year, start_of_month.month + 1, 1) - timedelta(days=1)
    
    payroll_entries = db.query(PayrollEntry).join(Employee).filter(
        Employee.company_id == company_id,
        PayrollEntry.pay_date >= start_of_month,
        PayrollEntry.pay_date <= end_of_month
    ).all()
    
    actual_gross_pay = sum(float(entry.gross_pay) for entry in payroll_entries)
    actual_net_pay = sum(float(entry.net_pay) for entry in payroll_entries)
    
    # In Indian context, we care about Total Outflow (Gross + Employer PF + etc)
    # If no actuals, decompose from employee salaries
    if not payroll_entries:
        total_outflow = 0
        for emp in employees:
            decomp = decompose_ctc(float(emp.salary))
            total_outflow += decomp["per_employee_monthly"]["employer_total_cost"]
        
        return {
            "total_employer_outflow": total_outflow,
            "estimated": True
        }
    
    # If we have actuals, we need to add employer contributions which might not be in the entry
    # For now, return sum of gross (which usually includes employer cost in CTC models)
    return {
        "total_employer_outflow": actual_gross_pay,
        "net_pay_disbursed": actual_net_pay,
        "estimated": False
    }
    
    # Estimate taxes if not using actual entries
    if actual_gross_pay == 0:
        tax_calc = calculate_payroll_taxes(gross_pay)
        total_taxes = tax_calc["total_taxes"]
        net_pay = tax_calc["net_pay"]
    else:
        total_taxes = actual_taxes
        net_pay = actual_net_pay
    
    return {
        "gross_payroll": gross_pay,
        "total_taxes": total_taxes,
        "net_payroll": net_pay,
        "payroll_expense": gross_pay + total_taxes,  # Employer portion
        "headcount": len(employees)
    }


def calculate_saas_metrics(
    prior_mrr: float,
    new_mrr: float,
    expansion_mrr: float,
    churned_mrr: float,
    contraction_mrr: float,
    total_sm_spend: float,
    new_customers_acquired: int,
    arpu: float,
    gross_margin_pct: float,
    net_burn: float,
    net_new_arr: float,
    payroll_burn: float,
    revenue: float,
    headcount: int
) -> Dict[str, Any]:
    """
    Calculate Indian SaaS metrics.
    """
    gross_churn_rate = (churned_mrr / prior_mrr) if prior_mrr > 0 else 0.0
    nrr = ((prior_mrr + expansion_mrr - churned_mrr - contraction_mrr) / prior_mrr * 100.0) if prior_mrr > 0 else 0.0
    cac = (total_sm_spend / new_customers_acquired) if new_customers_acquired > 0 else 0.0
    
    monthly_churn_rate = gross_churn_rate
    ltv = (arpu * gross_margin_pct / monthly_churn_rate) if monthly_churn_rate > 0 else 0.0
    ltv_cac_ratio = (ltv / cac) if cac > 0 else 0.0
    cac_payback_months = (cac / (arpu * gross_margin_pct)) if (arpu * gross_margin_pct) > 0 else 0.0
    
    burn_multiple = (net_burn / net_new_arr) if net_new_arr > 0 else 0.0
    
    total_arr = prior_mrr * 12 + net_new_arr 
    arr_per_fte = (total_arr / headcount) if headcount > 0 else 0.0
    payroll_pct_revenue = (payroll_burn / revenue) if revenue > 0 else 0.0

    return {
        "gross_churn_rate": gross_churn_rate,
        "nrr": nrr,
        "cac": cac,
        "ltv": ltv,
        "ltv_cac_ratio": ltv_cac_ratio,
        "cac_payback_months": cac_payback_months,
        "burn_multiple": burn_multiple,
        "gross_margin_pct": gross_margin_pct,
        "arr_per_fte": arr_per_fte,
        "payroll_pct_revenue": payroll_pct_revenue
    }

def scenario_price_increase(
    current_customers: int,
    current_arpu: float,
    increase_pct: float,
    expected_churn_pct: float
) -> Dict[str, Any]:
    """
    Scenario: Price increase impact.
    """
    def calculate_impact(churn_pct):
        retained_customers = current_customers * (1 - churn_pct)
        gross_new_mrr = retained_customers * current_arpu * (1 + increase_pct)
        churned_customers = current_customers * churn_pct
        lost_mrr = churned_customers * current_arpu
        current_mrr = current_customers * current_arpu
        net_mrr_impact = gross_new_mrr - current_mrr - lost_mrr
        return {
            "retained_customers": retained_customers,
            "gross_new_mrr": gross_new_mrr,
            "lost_mrr": lost_mrr,
            "net_mrr_impact": net_mrr_impact
        }

    sensitivity_table = {
        "5%_churn": calculate_impact(0.05),
        "10%_churn": calculate_impact(0.10),
        "15%_churn": calculate_impact(0.15),
        "20%_churn": calculate_impact(0.20)
    }
    
    base_impact = calculate_impact(expected_churn_pct)

    return {
        "scenario_type": "price_increase",
        "inputs": {
            "current_customers": current_customers,
            "current_arpu": current_arpu,
            "increase_pct": increase_pct,
            "expected_churn_pct": expected_churn_pct
        },
        "base_impact": base_impact,
        "sensitivity_table": sensitivity_table,
        "timing_assumption": "Churn happens 2 months after price increase"
    }

def scenario_stack(
    base_state: FinancialState,
    scenarios: List[Dict[str, Any]],
    projection_months: int = 12
) -> Dict[str, Any]:
    """
    Composes multiple scenarios in deterministic order.
    """
    state_dict = {
        "cash_balance": base_state.cash_balance,
        "ar_by_aging": base_state.ar_by_aging.copy(),
        "ap_due_30d": base_state.ap_due_30d,
        "gst_itc_balance": base_state.gst_itc_balance,
        "tds_receivable": base_state.tds_receivable,
        "monthly_mrr": base_state.monthly_mrr,
        "mrr_growth_rate": base_state.mrr_growth_rate,
        "monthly_churn_rate": base_state.monthly_churn_rate,
        "monthly_payroll": base_state.monthly_payroll,
        "monthly_cloud": base_state.monthly_cloud,
        "monthly_opex": base_state.monthly_opex,
        "monthly_gst_net": base_state.monthly_gst_net
    }
    
    one_time_inflows = 0.0
    one_time_outflows = 0.0
    
    for s in scenarios:
        stype = s.get("scenario_type")
        if stype == "new_revenue":
            deal_arr = s["inputs"]["deal_arr"]
            prob = s["inputs"]["close_probability"]
            state_dict["monthly_mrr"] += (deal_arr / 12) * prob
            one_time_inflows += s["revenue_impact"]["expected_cash_impact"]
        elif stype == "hire":
            state_dict["monthly_payroll"] += s["cost_breakdown"]["monthly_cost_total"]
            one_time_outflows += s["cost_breakdown"]["total_one_time"]
        elif stype == "cloud_reduction":
            state_dict["monthly_cloud"] -= s["savings_breakdown"]["monthly_savings"]
        elif stype == "price_increase":
            state_dict["monthly_mrr"] += s["base_impact"]["net_mrr_impact"]

    gross_burn = state_dict["monthly_payroll"] + state_dict["monthly_cloud"] + state_dict["monthly_opex"] + state_dict["monthly_gst_net"]
    cash_revenue_collected = state_dict["monthly_mrr"] * 0.98  # Assume 2% TDS
    net_burn = max(0, gross_burn - cash_revenue_collected)
    
    adjusted_cash_pos = base_state.adjusted_cash_position + one_time_inflows - one_time_outflows
    runway_months = (adjusted_cash_pos / net_burn) if net_burn > 0 else float('inf')
    
    return {
        "original_cash_position": base_state.adjusted_cash_position,
        "new_cash_position": adjusted_cash_pos,
        "original_net_burn": base_state.net_burn,
        "new_net_burn": net_burn,
        "original_runway": (base_state.adjusted_cash_position / base_state.net_burn) if base_state.net_burn > 0 else float('inf'),
        "new_runway": runway_months,
        "scenarios_applied": [s.get("scenario_type") for s in scenarios]
    }

def build_12m_projection_india(base_state: FinancialState) -> Dict[str, Any]:
    """12 month projection with base, bull, bear variants."""
    months_projection = []
    
    current_mrr_base = base_state.monthly_mrr
    current_cash_base = base_state.adjusted_cash_position
    current_gross_burn = base_state.gross_burn
    
    current_mrr_bull = base_state.monthly_mrr
    current_cash_bull = base_state.adjusted_cash_position
    
    current_mrr_bear = base_state.monthly_mrr
    current_cash_bear = base_state.adjusted_cash_position
    
    start_date = base_state.as_of_date
    
    for i in range(12):
        month_idx = (start_date.month - 1 + i) % 12
        sys_month_num = month_idx + 1
        year_offset = (start_date.month - 1 + i) // 12
        sys_month_str = f"{start_date.year + year_offset}-{sys_month_num:02d}"

        
        compliance_events = ["7th: TDS remittance", "15th: PF+ESI", "20th: GSTR-3B"]
        if sys_month_num in [6, 9, 12, 3]:
            compliance_events.append("15th: Advance Tax")
        if sys_month_num == 12:
            compliance_events.append("15th: LWF")
        if sys_month_num == 5:
            compliance_events.append("31st: ROC Annual Return / Audit")
            
        net_burn_base = max(0, current_gross_burn - (current_mrr_base * 0.98))
        current_cash_base -= net_burn_base
        current_mrr_base *= (1 + base_state.mrr_growth_rate - base_state.monthly_churn_rate)
        
        net_burn_bull = max(0, current_gross_burn - (current_mrr_bull * 0.98))
        current_cash_bull -= net_burn_bull
        current_mrr_bull *= (1 + (base_state.mrr_growth_rate * 1.2) - (base_state.monthly_churn_rate * 0.5))
        
        net_burn_bear = max(0, current_gross_burn - (current_mrr_bear * 0.98))
        current_cash_bear -= net_burn_bear
        current_mrr_bear *= (1 + 0.0 - (base_state.monthly_churn_rate * 2.0))
        
        months_projection.append({
            "month": sys_month_str,
            "compliance_obligations": compliance_events,
            "p50_base": {"cash": current_cash_base, "mrr": current_mrr_base},
            "p90_bull": {"cash": current_cash_bull, "mrr": current_mrr_bull},
            "p10_bear": {"cash": current_cash_bear, "mrr": current_mrr_bear}
        })
        
    return {
        "function": "build_12m_projection_india",
        "projection_months": 12,
        "scenarios": ["p10_bear", "p50_base", "p90_bull"],
        "monthly_data": months_projection
    }
