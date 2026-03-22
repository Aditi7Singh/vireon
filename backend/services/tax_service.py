from uuid import UUID
from datetime import date, timedelta
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
import importlib.util, sys
from pathlib import Path

import models

# Import config.py as a module (same pattern as analytics/metrics.py)
_config_path = Path(__file__).parent.parent / "config.py"
_spec = importlib.util.spec_from_file_location("config_module", _config_path)
config_module = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("config_module", config_module)
_spec.loader.exec_module(config_module)

def get_active_tax_rules(db: Session, company_id: UUID) -> List[models.TaxRule]:
    """Fetch all active tax rules for a company."""
    return db.query(models.TaxRule).filter(
        models.TaxRule.company_id == company_id,
        models.TaxRule.is_active == True
    ).all()


def calculate_tax_for_invoice(db: Session, company_id: UUID, invoice_base_amount: float, is_service: bool = True) -> Dict[str, float]:
    """
    Apply GST and TDS rules to an invoice based on active TaxRules.
    Falls back to config_module defaults if specific rules are not found.
    """
    rules = get_active_tax_rules(db, company_id)
    
    # Defaults
    gst_rate = config_module.GST_RATE_SERVICES if is_service else config_module.GST_RATE_SAAS
    tds_rate = config_module.TDS_RATE_CONTRACT
    
    # Override with DB rules if present
    for r in rules:
        name = r.tax_name.upper()
        if "GST" in name:
            gst_rate = float(r.rate)
        elif "TDS" in name:
            # Simple threshold check
            if r.threshold_amount and invoice_base_amount < float(r.threshold_amount):
                tds_rate = 0.0
            else:
                tds_rate = float(r.rate)
                
    gst_amount = round(invoice_base_amount * gst_rate, 2)
    total_invoice = round(invoice_base_amount + gst_amount, 2)
    tds_deducted = round(invoice_base_amount * tds_rate, 2)
    net_cash_expected = round(total_invoice - tds_deducted, 2)
    
    return {
        "invoice_base": invoice_base_amount,
        "gst_amount": gst_amount,
        "tds_deducted": tds_deducted,
        "total_invoice": total_invoice,
        "net_cash_expected": net_cash_expected
    }


def calculate_tax_for_payroll(db: Session, company_id: UUID, gross_monthly: float) -> Dict[str, float]:
    """
    Apply PF, ESI, PT rules based on active TaxRules for payroll calculations.
    """
    rules = get_active_tax_rules(db, company_id)
    
    # Defaults
    pt_tax = 200.0  # PT max fallback
    esi_rate = config_module.ESI_EMPLOYEE_RATE
    pf_rate = config_module.PF_EMPLOYER_RATE  # Using as employee deduction too usually
    
    for r in rules:
        name = r.tax_name.upper()
        if "PT" in name or "PROFESSIONAL TAX" in name:
            pt_tax = float(r.rate) if gross_monthly >= (r.threshold_amount or 0) else 0.0
        elif "ESI" in name:
            if not r.threshold_amount or gross_monthly <= float(r.threshold_amount):
                esi_rate = float(r.rate)
            else:
                esi_rate = 0.0
        elif "PF" in name or "PROVIDENT FUND" in name:
            pf_rate = float(r.rate)

    employee_esi = round(gross_monthly * esi_rate, 2)
    
    # PF traditionally calculated on basic (~40% of gross) up to 15k limit
    pf_basic = min(gross_monthly * 0.4, 15000.0)
    employee_pf = round(pf_basic * pf_rate, 2)
    
    # Simplified estimation for income tax (TDS on salary)
    income_tax_tds = 0.0
    annual_gross = gross_monthly * 12
    if annual_gross > 700000:
        income_tax_tds = round((annual_gross - 700000) * 0.1 / 12, 2)
        
    total_deductions = employee_esi + employee_pf + pt_tax + income_tax_tds
    
    return {
        "gross_pay": gross_monthly,
        "employee_pf": employee_pf,
        "employee_esi": employee_esi,
        "professional_tax": pt_tax,
        "income_tax_tds": income_tax_tds,
        "total_deductions": total_deductions,
        "net_pay": gross_monthly - total_deductions
    }


def calculate_quarterly_tax_summary(db: Session, company_id: UUID, year: int, quarter: int) -> Dict[str, Any]:
    """
    Aggregate collected GST and deducted TDS to summarize quarterly tax liability.
    Quarter 1 = Jan-Mar, 2 = Apr-Jun, 3 = Jul-Sep, 4 = Oct-Dec
    """
    start_month = (quarter - 1) * 3 + 1
    start_date = date(year, start_month, 1)
    
    if quarter == 4:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, start_month + 3, 1) - timedelta(days=1)
        
    # Aggregate GST on invoices (receivable/payable approximation)
    invoices = db.query(models.Invoice).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.issue_date >= start_date,
        models.Invoice.issue_date <= end_date,
        models.Invoice.status != "VOID"
    ).all()
    
    total_gst_collected = 0.0
    total_tds_receivable = 0.0
    for inv in invoices:
        if inv.type == "ACCOUNTS_RECEIVABLE":
            # Very rough estimate of GST/TDS applied if not tracked directly on Invoice model
            tax_data = calculate_tax_for_invoice(db, company_id, float(inv.sub_total))
            total_gst_collected += tax_data["gst_amount"]
            total_tds_receivable += tax_data["tds_deducted"]
            
    # Aggregate Payroll TDS (Income Tax deducted from employees) to be remitted
    payrolls = db.query(models.PayrollEntry).join(models.Employee).filter(
        models.Employee.company_id == company_id,
        models.PayrollEntry.pay_date >= start_date,
        models.PayrollEntry.pay_date <= end_date
    ).all()
    
    total_payroll_tds = 0.0
    for p in payrolls:
        # Simplified: assume federal_tax is the TDS on salary
        total_payroll_tds += float(p.federal_tax or 0.0)
        
    # Advance Tax Estimate (roughly 15% of annual projected profit, or 25% of current quarter profit if high)
    # For now, a simplified 10% of gross revenue as placeholder for profitable companies
    advance_tax = (total_gst_collected * 0.1) if total_gst_collected > 500000 else 0.0
    
    total_liability = total_gst_collected + total_payroll_tds + advance_tax
    
    return {
        "company_id": str(company_id),
        "year": year,
        "quarter": quarter,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "total_gst_collected_payable": round(total_gst_collected, 2),
        "total_tds_on_salary_payable": round(total_payroll_tds, 2),
        "total_tds_receivable_from_clients": round(total_tds_receivable, 2),
        "advance_tax_estimate": round(advance_tax, 2),
        "total_tax_liability": round(total_liability, 2)
    }


def create_quarterly_liability(db: Session, company_id: UUID, year: int, quarter: int) -> models.QuarterlyTaxLiability:
    """Compute and persist the quarterly tax liability for a company."""
    summary = calculate_quarterly_tax_summary(db, company_id, year, quarter)
    
    # Check if exists
    existing = db.query(models.QuarterlyTaxLiability).filter(
        models.QuarterlyTaxLiability.company_id == company_id,
        models.QuarterlyTaxLiability.year == year,
        models.QuarterlyTaxLiability.quarter == quarter
    ).first()
    
    if existing:
        existing.gst_liability = summary["total_gst_collected_payable"]
        existing.tds_liability = summary["total_tds_on_salary_payable"]
        existing.advance_tax_estimate = summary["advance_tax_estimate"]
        existing.total_liability = summary["total_tax_liability"]
        existing.remaining_balance = float(existing.total_liability) - float(existing.paid_amount)
        db.commit()
        return existing
        
    # Calculate due date (approx 15 days after quarter end for TDS/GST)
    # Q1: Mar 31 -> Apr 15
    # Q2: Jun 30 -> Jul 15
    # Q3: Sep 30 -> Oct 15
    # Q4: Dec 31 -> Jan 15
    end_date = date.fromisoformat(summary["end_date"])
    due_date = end_date + timedelta(days=15)
    
    new_liability = models.QuarterlyTaxLiability(
        company_id=company_id,
        year=year,
        quarter=quarter,
        gst_liability=summary["total_gst_collected_payable"],
        tds_liability=summary["total_tds_on_salary_payable"],
        advance_tax_estimate=summary["advance_tax_estimate"],
        total_liability=summary["total_tax_liability"],
        remaining_balance=summary["total_tax_liability"],
        due_date=due_date,
        status="pending"
    )
    
    db.add(new_liability)
    db.commit()
    db.refresh(new_liability)
    return new_liability


def get_payment_schedule(db: Session, company_id: UUID) -> List[Dict[str, Any]]:
    """Get all pending/upcoming tax payments for a company."""
    liabilities = db.query(models.QuarterlyTaxLiability).filter(
        models.QuarterlyTaxLiability.company_id == company_id,
        models.QuarterlyTaxLiability.status != "paid"
    ).order_by(models.QuarterlyTaxLiability.due_date.asc()).all()
    
    return [
        {
            "id": str(l.id),
            "year": l.year,
            "quarter": l.quarter,
            "total_liability": float(l.total_liability),
            "paid_amount": float(l.paid_amount),
            "remaining_balance": float(l.remaining_balance),
            "due_date": str(l.due_date),
            "status": l.status
        }
        for l in liabilities
    ]


def reconcile_tax_payment(db: Session, liability_id: UUID, amount: float, reference: str) -> Dict[str, Any]:
    """Record a tax payment and update the liability status."""
    liability = db.query(models.QuarterlyTaxLiability).filter(models.QuarterlyTaxLiability.id == liability_id).first()
    if not liability:
        return {"error": "Liability not found"}
        
    liability.paid_amount = float(liability.paid_amount or 0) + amount
    liability.remaining_balance = float(liability.total_liability) - float(liability.paid_amount)
    liability.payment_reference = reference
    liability.last_payment_date = date.today()
    
    if liability.remaining_balance <= 0:
        liability.status = "paid"
    elif liability.paid_amount > 0:
        liability.status = "partially_paid"
        
    db.commit()
    return {
        "status": "success",
        "new_status": liability.status,
        "remaining_balance": float(liability.remaining_balance)
    }

