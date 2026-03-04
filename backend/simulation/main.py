"""
Main Orchestrator — SeedlingLabs Financial Data Generator
=========================================================

Generates 12 months of realistic startup financial data aligned with
the Merge.dev Accounting API. Embeds 7 hidden anomalies for the AI
detection engine to discover.

Usage:
    python -m simulation.main

Output:
    simulation/output/
    ├── json/   — Merge.dev format JSON (one file per model)
    ├── csv/    — Flat CSVs for Pandas
    └── sql/    — PostgreSQL INSERT statements
"""

import os
import io
import sys as _sys
import sys
from datetime import date
from dateutil.relativedelta import relativedelta

# Ensure the parent directory is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Fix Windows console encoding
if _sys.platform == 'win32':
    _sys.stdout = io.TextIOWrapper(_sys.stdout.buffer, encoding='utf-8', errors='replace')
    _sys.stderr = io.TextIOWrapper(_sys.stderr.buffer, encoding='utf-8', errors='replace')

from simulation.config import (
    COMPANY_NAME, COMPANY_LEGAL_NAME, COMPANY_TAX_ID,
    START_DATE, END_DATE, NUM_MONTHS,
    STARTING_CASH, SEED,
)
from simulation.models import CompanyInfo

from simulation.generators.accounts import generate_accounts, get_account_by_name
from simulation.generators.contacts import generate_contacts
from simulation.generators.revenue import generate_revenue
from simulation.generators.payroll import generate_payroll
from simulation.generators.cloud_costs import generate_cloud_costs
from simulation.generators.expenses import generate_operating_expenses
from simulation.generators.invoices import generate_ap_invoices
from simulation.generators.payments import generate_payments

from simulation.anomaly_injector import inject_anomalies
from simulation.export import export_all


def compute_monthly_summary(
    monthly_mrr: dict,
    monthly_payroll: dict,
    monthly_cloud: dict,
    monthly_opex: dict,
    headcount_history: dict,
    anomaly_expenses: list,
) -> dict:
    """
    Compute a per-month financial summary with:
    - Cash balance, burn rate, revenue, runway
    """
    summary = {}
    cash_balance = STARTING_CASH

    for month_num in range(1, NUM_MONTHS + 1):
        month_date = START_DATE + relativedelta(months=month_num - 1)

        # Revenue
        revenue = monthly_mrr.get(month_num, 0)

        # Expenses
        payroll = monthly_payroll.get(month_num, 0)
        cloud = monthly_cloud.get(month_num, 0)

        # OpEx: sum all categories for this month
        opex_cats = monthly_opex.get(month_num, {})
        opex_total = sum(opex_cats.values())

        # Anomaly expenses for this month
        anomaly_cost = 0
        for aexp in anomaly_expenses:
            if aexp.transaction_date:
                aexp_date = date.fromisoformat(aexp.transaction_date)
                if (aexp_date.year == month_date.year and
                    aexp_date.month == month_date.month):
                    anomaly_cost += abs(aexp.total_amount)

        total_expenses = payroll + cloud + opex_total + anomaly_cost
        net_burn = total_expenses - revenue
        cash_balance -= net_burn

        # Runway calculation
        if net_burn > 0:
            runway_months = round(cash_balance / net_burn, 1)
        else:
            runway_months = float('inf')  # Not burning cash

        summary[month_num] = {
            "month": month_date.strftime("%Y-%m"),
            "month_name": month_date.strftime("%B %Y"),
            "revenue": round(revenue, 2),
            "payroll": round(payroll, 2),
            "cloud_costs": round(cloud, 2),
            "operating_expenses": round(opex_total, 2),
            "anomaly_costs": round(anomaly_cost, 2),
            "total_expenses": round(total_expenses, 2),
            "net_burn": round(net_burn, 2),
            "cash_balance": round(cash_balance, 2),
            "runway_months": runway_months if runway_months != float('inf') else "N/A",
            "headcount": headcount_history.get(month_num, 0),
        }

    return summary


def print_summary_report(summary: dict, manifest: list, record_counts: dict):
    """Print a human-readable summary of the generated data."""

    print("\n" + "=" * 70)
    print("  [BANK]  SeedlingLabs Financial Data Generation Report")
    print("=" * 70)

    print(f"\n  Company:       {COMPANY_NAME}")
    print(f"  Period:        {START_DATE} -> {END_DATE} ({NUM_MONTHS} months)")
    print(f"  Starting Cash: ${STARTING_CASH:,.0f}")
    print(f"  Random Seed:   {SEED}")

    # Record counts
    print(f"\n  [STATS] Record Counts:")
    for model, count in record_counts.items():
        print(f"     {model:<20s} {count:>6d} records")

    # Monthly trajectory
    print(f"\n  [$] Monthly Financial Trajectory:")
    print(f"  {'Month':<15s} {'Revenue':>10s} {'Expenses':>12s} {'Net Burn':>10s} {'Cash':>12s} {'Runway':>8s} {'HC':>4s}")
    print(f"  {'-'*15} {'-'*10} {'-'*12} {'-'*10} {'-'*12} {'-'*8} {'-'*4}")

    for month_num in sorted(summary.keys(), key=int):
        m = summary[month_num]
        runway_str = f"{m['runway_months']}mo" if m['runway_months'] != "N/A" else "INF"
        print(f"  {m['month_name']:<15s} "
              f"${m['revenue']:>9,.0f} "
              f"${m['total_expenses']:>11,.0f} "
              f"${m['net_burn']:>9,.0f} "
              f"${m['cash_balance']:>11,.0f} "
              f"{runway_str:>8s} "
              f"{m['headcount']:>4d}")

    # Final state
    final = summary[NUM_MONTHS]
    print(f"\n  [+] Final State:")
    print(f"     Cash Balance:  ${final['cash_balance']:>12,.0f}")
    print(f"     Monthly Burn:  ${final['net_burn']:>12,.0f}")
    print(f"     Runway:        {final['runway_months']} months")
    print(f"     Headcount:     {final['headcount']} employees")
    print(f"     MRR:           ${final['revenue']:>12,.0f}")

    # Anomalies
    print(f"\n  [!] Embedded Anomalies ({len(manifest)}):")
    for a in manifest:
        print(f"     [{a['id']}] Month {a['month']:>2d}: {a['type']:<20s} - {a['description'][:60]}")

    print("\n" + "=" * 70)
    print("  [OK] Generation complete! Data written to output directory.")
    print("=" * 70 + "\n")


def main():
    """Main entry point — orchestrates the entire data generation pipeline."""

    print("\n>> SeedlingLabs Financial Data Generator")
    print(f"   Generating {NUM_MONTHS} months of data ({START_DATE} -> {END_DATE})...\n")

    # ── Step 1: Company Info ──
    print("  [1/8] Creating company info...")
    company_info = CompanyInfo(
        name=COMPANY_NAME,
        legal_name=COMPANY_LEGAL_NAME,
        tax_number=COMPANY_TAX_ID,
        currency="USD",
        urls=["https://seedlinglabs.com"],
    )

    # ── Step 2: Chart of Accounts ──
    print("  [2/8] Generating Chart of Accounts...")
    accounts = generate_accounts()
    print(f"         -> {len(accounts)} accounts created")

    # ── Step 3: Contacts (Vendors + Customers) ──
    print("  [3/8] Generating Vendors & Customers...")
    contacts_data = generate_contacts(seed=SEED)
    vendor_contacts = contacts_data["vendors"]
    customer_contacts = contacts_data["customers"]
    all_contacts = contacts_data["all"]
    print(f"         -> {len(vendor_contacts)} vendors, {len(customer_contacts)} customers")

    # ── Step 4: Revenue / MRR ──
    print("  [4/8] Generating Revenue (MRR)...")
    revenue_data = generate_revenue(
        accounts=accounts,
        customer_contacts=customer_contacts,
        seed=SEED,
        churned_customer="Acme Corp",  # Anomaly #7
        churn_month=11,
    )
    ar_invoices = revenue_data["invoices"]
    monthly_mrr = revenue_data["monthly_mrr"]
    print(f"         -> {len(ar_invoices)} AR invoices, MRR range: "
          f"${min(monthly_mrr.values()):,.0f} -> ${max(monthly_mrr.values()):,.0f}")

    # ── Step 5: Payroll ──
    print("  [5/8] Generating Payroll...")
    payroll_data = generate_payroll(accounts=accounts, vendor_contacts=vendor_contacts, seed=SEED)
    payroll_expenses = payroll_data["expenses"]
    hiring_expenses = payroll_data["hiring_expenses"]
    monthly_payroll = payroll_data["monthly_payroll"]
    headcount_history = payroll_data["headcount_history"]
    print(f"         -> {len(payroll_expenses)} payroll runs, {len(hiring_expenses)} hiring events")
    print(f"         -> Headcount: {headcount_history[1]} -> {headcount_history[NUM_MONTHS]}")

    # ── Step 6: Cloud Costs ──
    print("  [6/8] Generating Cloud Costs (AWS)...")
    cloud_data = generate_cloud_costs(accounts=accounts, vendor_contacts=vendor_contacts, seed=SEED)
    cloud_expenses = cloud_data["expenses"]
    monthly_cloud = cloud_data["monthly_cloud"]
    print(f"         -> {len(cloud_expenses)} cloud invoices, range: "
          f"${min(monthly_cloud.values()):,.0f} -> ${max(monthly_cloud.values()):,.0f}/mo")

    # ── Step 7: Operating Expenses ──
    print("  [7/8] Generating Operating Expenses...")
    opex_data = generate_operating_expenses(
        accounts=accounts, vendor_contacts=vendor_contacts, seed=SEED,
    )
    opex_expenses = opex_data["expenses"]
    monthly_opex = opex_data["monthly_opex"]
    print(f"         -> {len(opex_expenses)} expense records")

    # ── Step 8: Inject Anomalies ──
    print("  [8/8] Injecting Anomalies...")
    data_bundle = {
        "cloud_expenses": cloud_expenses,
        "opex_expenses": opex_expenses,
        "monthly_cloud": monthly_cloud,
        "monthly_payroll": monthly_payroll,
        "monthly_mrr": monthly_mrr,
        "anomaly_expenses": [],
        "anomaly_contacts": [],
    }
    manifest = inject_anomalies(data_bundle, accounts, vendor_contacts)
    anomaly_expenses = data_bundle.get("anomaly_expenses", [])
    anomaly_contacts = data_bundle.get("anomaly_contacts", [])
    print(f"         -> {len(manifest)} anomalies injected")

    # ── Combine all expenses ──
    all_expenses = (payroll_expenses + hiring_expenses + cloud_expenses +
                    opex_expenses + anomaly_expenses)

    # ── Generate AP Invoices from expenses ──
    print("\n  Generating AP Invoices from expenses...")
    ap_invoices = generate_ap_invoices(all_expenses, accounts, seed=SEED)
    all_invoices = ar_invoices + ap_invoices
    print(f"  -> {len(ap_invoices)} AP invoices (bills)")

    # ── Generate Payments ──
    print("  Generating Payments linked to invoices...")
    all_payments = generate_payments(all_invoices, accounts, seed=SEED)
    print(f"  -> {len(all_payments)} payments")

    # ── Combine all contacts ──
    final_contacts = all_contacts + anomaly_contacts

    # ── Compute Monthly Summary ──
    monthly_summary = compute_monthly_summary(
        monthly_mrr=monthly_mrr,
        monthly_payroll=monthly_payroll,
        monthly_cloud=data_bundle["monthly_cloud"],  # Updated by anomaly injector
        monthly_opex=monthly_opex,
        headcount_history=headcount_history,
        anomaly_expenses=anomaly_expenses,
    )

    # ── Export ──
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    export_all(
        accounts=accounts,
        contacts=final_contacts,
        expenses=all_expenses,
        invoices=all_invoices,
        payments=all_payments,
        company_info=company_info,
        manifest=manifest,
        monthly_summary=monthly_summary,
        output_dir=output_dir,
    )

    # ── Summary Report ──
    record_counts = {
        "Accounts": len(accounts),
        "Contacts": len(final_contacts),
        "Expenses": len(all_expenses),
        "Invoices (AR)": len(ar_invoices),
        "Invoices (AP)": len(ap_invoices),
        "Invoices (Total)": len(all_invoices),
        "Payments": len(all_payments),
        "Anomalies": len(manifest),
    }
    print_summary_report(monthly_summary, manifest, record_counts)


if __name__ == "__main__":
    main()
