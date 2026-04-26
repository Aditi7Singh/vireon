
import sys
import os
from pathlib import Path
from datetime import date

# Add backend to sys.path
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

from analytics import metrics
import config

def verify_payroll():
    print("--- Verifying Payroll Calculations ---")
    annual_ctc = 28_00_000
    print(f"Testing for Annual CTC: ₹{annual_ctc:,}")
    
    result = metrics.decompose_ctc(annual_ctc)
    per_emp = result["per_employee_monthly"]
    
    print(f"Monthly Basic (40%): ₹{per_emp['basic']:,}")
    print(f"Monthly HRA (50% basic): ₹{per_emp['hra']:,}")
    print(f"Gross Salary: ₹{per_emp['gross_salary']:,}")
    print(f"Employer PF (13% of basic): ₹{per_emp['employer_pf'] + per_emp['pf_admin_edli']:,}")
    print(f"Gratuity (4.81% basic): ₹{per_emp['gratuity_provision']:,}")
    print(f"Employer Monthly Outflow: ₹{per_emp['employer_total_cost']:,}")
    
    # Expected from spec: ₹2,35,467
    expected_outflow = 235467
    variance = abs(per_emp['employer_total_cost'] - expected_outflow)
    print(f"Expected Outflow: ₹{expected_outflow:,}")
    print(f"Variance: ₹{variance}")
    
    if variance < 100:
        print("✅ Payroll Outflow matches spec worked example.")
    else:
        print("❌ Payroll Outflow differs from spec.")

def verify_gst_tds():
    print("\n--- Verifying GST & TDS Logic ---")
    invoice_base = 6_65_000
    print(f"Testing for Invoice Base: ₹{invoice_base:,}")
    
    result = metrics.calculate_net_ar_receipt(invoice_base)
    print(f"GST Amount (18%): ₹{result['gst_amount']:,}")
    print(f"Total Invoice: ₹{result['total_invoice']:,}")
    print(f"TDS Deducted (2%): ₹{result['tds_deducted']:,}")
    print(f"Net Cash Received: ₹{result['net_cash_received']:,}")
    
    # Expected from spec: ₹7,71,400
    expected_cash = 771400
    variance = abs(result['net_cash_received'] - expected_cash)
    print(f"Expected Cash: ₹{expected_cash:,}")
    print(f"Variance: ₹{variance}")
    
    if variance < 10:
        print("✅ Net Cash Received matches spec worked example.")
    else:
        print("❌ Net Cash Received differs from spec.")

def verify_cash_position():
    print("\n--- Verifying Cash Position ---")
    bank_balance = 83_00_000
    ar = {"0_30_enterprise": 784700} # One Reliance invoice total
    ap = 100000
    # Using 28L CTC example context
    monthly_payroll = 235466.67
    monthly_mrr = 665000
    
    result = metrics.calculate_cash_position(bank_balance, ar, ap, monthly_payroll, monthly_mrr)
    print(f"Bank Balance: ₹{bank_balance:,}")
    print(f"AR Gross: ₹{sum(ar.values()):,}")
    print(f"AR Weighted (92% for enterprise 0-30): ₹{result['ar_weighted']:,}")
    print(f"Adjusted Cash Position: ₹{result['adjusted_cash_position']:,}")
    
    # Reliance invoice total is 7,84,700. 92% is 7,21,924.
    # Stat reserve is currently 0 in implementation placeholder.
    # 83L + 721,924 - 100k = 8,921,924
    expected_adj = 8300000 + (784700 * 0.92) - 100000
    if abs(result['adjusted_cash_position'] - expected_adj) < 10:
        print("✅ Adjusted Cash Position follows weighting logic.")
    else:
        print("❌ Adjusted Cash Position calculation error.")

def verify_scenarios():
    print("\n--- Verifying Scenario Functions ---")
    # Hire 2 engineers at 20L CTC
    avg_ctc = 2_000_000 # ₹20L
    hire_result = metrics.scenario_hire_india(2, avg_ctc) 
    print(f"Testing Hire Scenario: 2 hires at ₹{avg_ctc:,} CTC")
    print(f"Monthly Cost Total: ₹{hire_result['cost_breakdown']['monthly_cost_total']:,}")
    print(f"One-time Total: ₹{hire_result['cost_breakdown']['total_one_time']:,}")
    
    # Spec says ~1.77L per hire monthly cost for 20L CTC. Totals ~3.54L.
    if abs(hire_result['cost_breakdown']['monthly_cost_total'] - 354156) < 1000:
        print("✅ Hiring scenario costs are accurate.")
    else:
        print(f"❌ Hiring scenario costs differ. Got ₹{hire_result['cost_breakdown']['monthly_cost_total']:,}")

if __name__ == "__main__":
    verify_payroll()
    verify_gst_tds()
    verify_cash_position()
    verify_scenarios()
