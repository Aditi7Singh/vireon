"""
Main Orchestrator — SeedlingLabs Financial Data Generator
=========================================================
Generates 12 months of realistic startup financial data aligned with
the Merge.dev Accounting API. Embeds 7 hidden anomalies for demo.

FIXES vs original:
  1. company_id threaded into ALL generators (was always null before)
  2. Monthly summary uses correct MRR (annual billing customers now
     contribute MRR every active month, not just invoice month)
  3. Account.type field (was account_type) propagated correctly

Usage:
    python -m data_generation.main
"""

import os
import sys
import io
from datetime import date
from dateutil.relativedelta import relativedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from data_generation.config import (
    COMPANY_NAME, COMPANY_LEGAL_NAME, COMPANY_TAX_ID,
    START_DATE, END_DATE, NUM_MONTHS, STARTING_CASH, SEED,
)
from data_generation.models import CompanyInfo

from data_generation.generators.accounts    import generate_accounts, get_account_by_name
from data_generation.generators.contacts    import generate_contacts
from data_generation.generators.revenue     import generate_revenue
from data_generation.generators.payroll     import generate_payroll
from data_generation.generators.cloud_costs import generate_cloud_costs
from data_generation.generators.expenses    import generate_operating_expenses
from data_generation.generators.invoices    import generate_ap_invoices
from data_generation.generators.payments    import generate_payments

from data_generation.anomaly_injector import inject_anomalies
from data_generation.export           import export_all


def compute_monthly_summary(
    monthly_mrr: dict,
    monthly_payroll: dict,
    monthly_cloud: dict,
    monthly_opex: dict,
    headcount_history: dict,
    anomaly_expenses: list,
) -> dict:
    """
    Per-month P&L summary.
    FIX: monthly_mrr now correctly reflects all customers' MRR every month
         (annual billing customers are no longer missing from non-invoice months).
    """
    summary       = {}
    cash_balance  = STARTING_CASH

    for month_num in range(1, NUM_MONTHS + 1):
        month_date = START_DATE + relativedelta(months=month_num - 1)

        revenue      = monthly_mrr.get(month_num, 0)
        payroll      = monthly_payroll.get(month_num, 0)
        cloud        = monthly_cloud.get(month_num, 0)
        opex_total   = sum(monthly_opex.get(month_num, {}).values())

        anomaly_cost = 0
        for aexp in anomaly_expenses:
            if aexp.transaction_date:
                aexp_dt = date.fromisoformat(aexp.transaction_date)
                if aexp_dt.year == month_date.year and aexp_dt.month == month_date.month:
                    anomaly_cost += abs(aexp.total_amount)

        total_expenses = payroll + cloud + opex_total + anomaly_cost
        net_burn       = total_expenses - revenue
        cash_balance  -= net_burn

        runway_months = round(cash_balance / net_burn, 1) if net_burn > 0 else float("inf")

        summary[month_num] = {
            "month":               month_date.strftime("%Y-%m"),
            "month_name":          month_date.strftime("%B %Y"),
            "revenue":             round(revenue, 2),
            "payroll":             round(payroll, 2),
            "cloud_costs":         round(cloud, 2),
            "operating_expenses":  round(opex_total, 2),
            "anomaly_costs":       round(anomaly_cost, 2),
            "total_expenses":      round(total_expenses, 2),
            "net_burn":            round(net_burn, 2),
            "cash_balance":        round(cash_balance, 2),
            "runway_months":       runway_months if runway_months != float("inf") else "N/A",
            "headcount":           headcount_history.get(month_num, 0),
        }

    return summary


def print_summary_report(summary: dict, manifest: list, record_counts: dict):
    print("\n" + "=" * 70)
    print("  SeedlingLabs Financial Data Generation Report")
    print("=" * 70)
    print(f"\n  Company:       {COMPANY_NAME}")
    print(f"  Period:        {START_DATE} -> {END_DATE} ({NUM_MONTHS} months)")
    print(f"  Starting Cash: ${STARTING_CASH:,.0f}")
    print(f"  Random Seed:   {SEED}")

    print(f"\n  Record Counts:")
    for model, count in record_counts.items():
        print(f"     {model:<22s} {count:>5d} records")

    print(f"\n  Monthly Financial Trajectory:")
    print(f"  {'Month':<15s} {'Revenue':>10s} {'Expenses':>12s} {'Net Burn':>10s} {'Cash':>12s} {'Runway':>8s} {'HC':>4s}")
    print(f"  {'-'*15} {'-'*10} {'-'*12} {'-'*10} {'-'*12} {'-'*8} {'-'*4}")

    for month_num in sorted(summary.keys()):
        m          = summary[month_num]
        runway_str = f"{m['runway_months']}mo" if m['runway_months'] != "N/A" else "INF"
        print(f"  {m['month_name']:<15s} "
              f"${m['revenue']:>9,.0f} "
              f"${m['total_expenses']:>11,.0f} "
              f"${m['net_burn']:>9,.0f} "
              f"${m['cash_balance']:>11,.0f} "
              f"{runway_str:>8s} "
              f"{m['headcount']:>4d}")

    final = summary[NUM_MONTHS]
    print(f"\n  Final State:")
    print(f"     Cash Balance:  ${final['cash_balance']:>12,.0f}")
    print(f"     Monthly Burn:  ${final['net_burn']:>12,.0f}")
    print(f"     Runway:        {final['runway_months']} months")
    print(f"     Headcount:     {final['headcount']} employees")
    print(f"     MRR:           ${final['revenue']:>12,.0f}")

    print(f"\n  Embedded Anomalies ({len(manifest)}):")
    for a in manifest:
        print(f"     [{a['id']}] Month {a['month']:>2d}: {a['type']:<20s} - {a['description'][:55]}")

    print("\n" + "=" * 70)
    print("  Generation complete. Data written to output/")
    print("=" * 70 + "\n")


def main():
    print(f"\n>> SeedlingLabs Financial Data Generator")
    print(f"   Generating {NUM_MONTHS} months ({START_DATE} -> {END_DATE})...\n")

    # ── 1. Company Info ──────────────────────────────────────────────────────
    print("  [1/8] Creating company info...")
    company_info = CompanyInfo(
        name=COMPANY_NAME,
        legal_name=COMPANY_LEGAL_NAME,
        tax_number=COMPANY_TAX_ID,
        currency="USD",
        urls=["https://seedlinglabs.com"],
    )
    company_id = company_info.id   # FIX: capture ID to thread into all generators
    print(f"         -> Company ID: {company_id}")

    # ── 2. Chart of Accounts ─────────────────────────────────────────────────
    print("  [2/8] Generating Chart of Accounts...")
    accounts = generate_accounts(company_id=company_id)
    print(f"         -> {len(accounts)} accounts (field: 'type' not 'account_type')")

    # ── 3. Contacts ───────────────────────────────────────────────────────────
    print("  [3/8] Generating Vendors & Customers...")
    contacts_data    = generate_contacts(company_id=company_id, seed=SEED)
    vendor_contacts  = contacts_data["vendors"]
    customer_contacts= contacts_data["customers"]
    all_contacts     = contacts_data["all"]
    print(f"         -> {len(vendor_contacts)} vendors, {len(customer_contacts)} customers")

    # ── 4. Revenue / MRR ──────────────────────────────────────────────────────
    print("  [4/8] Generating Revenue (MRR)...")
    revenue_data = generate_revenue(
        accounts=accounts,
        customer_contacts=customer_contacts,
        company_id=company_id,
        seed=SEED,
        churned_customer="Acme Corp",
        churn_month=11,
    )
    ar_invoices  = revenue_data["invoices"]
    monthly_mrr  = revenue_data["monthly_mrr"]
    print(f"         -> {len(ar_invoices)} AR invoices")
    print(f"         -> MRR: ${min(monthly_mrr.values()):,.0f} -> ${max(monthly_mrr.values()):,.0f}")
    print(f"         -> Annual billing MRR recognized monthly (not lump-sum)")

    # ── 5. Payroll ────────────────────────────────────────────────────────────
    print("  [5/8] Generating Payroll...")
    payroll_data     = generate_payroll(accounts=accounts, vendor_contacts=vendor_contacts,
                                        company_id=company_id, seed=SEED)
    payroll_expenses = payroll_data["expenses"]
    hiring_expenses  = payroll_data["hiring_expenses"]
    monthly_payroll  = payroll_data["monthly_payroll"]
    headcount_history= payroll_data["headcount_history"]
    print(f"         -> {len(payroll_expenses)} payroll runs, {len(hiring_expenses)} hiring events")
    print(f"         -> Headcount: {headcount_history[1]} -> {headcount_history[NUM_MONTHS]}")

    # ── 6. Cloud Costs ────────────────────────────────────────────────────────
    print("  [6/8] Generating Cloud Costs (AWS)...")
    cloud_data   = generate_cloud_costs(accounts=accounts, vendor_contacts=vendor_contacts,
                                        company_id=company_id, seed=SEED)
    cloud_expenses = cloud_data["expenses"]
    monthly_cloud  = cloud_data["monthly_cloud"]
    print(f"         -> {len(cloud_expenses)} cloud invoices")

    # ── 7. Operating Expenses ─────────────────────────────────────────────────
    print("  [7/8] Generating Operating Expenses...")
    opex_data    = generate_operating_expenses(accounts=accounts, vendor_contacts=vendor_contacts,
                                               company_id=company_id, seed=SEED)
    opex_expenses= opex_data["expenses"]
    monthly_opex = opex_data["monthly_opex"]
    print(f"         -> {len(opex_expenses)} expense records")

    # ── 8. Inject Anomalies ───────────────────────────────────────────────────
    print("  [8/8] Injecting Anomalies...")
    data_bundle = {
        "cloud_expenses":  cloud_expenses,
        "opex_expenses":   opex_expenses,
        "monthly_cloud":   monthly_cloud,
        "monthly_payroll": monthly_payroll,
        "monthly_mrr":     monthly_mrr,
        "anomaly_expenses":  [],
        "anomaly_contacts":  [],
    }
    manifest         = inject_anomalies(data_bundle, accounts, vendor_contacts, company_id=company_id)
    anomaly_expenses = data_bundle.get("anomaly_expenses", [])
    anomaly_contacts = data_bundle.get("anomaly_contacts", [])
    print(f"         -> {len(manifest)} anomalies injected")

    # ── Combine ───────────────────────────────────────────────────────────────
    all_expenses = (payroll_expenses + hiring_expenses + cloud_expenses +
                    opex_expenses + anomaly_expenses)

    print("\n  Generating AP Invoices from expenses...")
    ap_invoices  = generate_ap_invoices(all_expenses, accounts, company_id=company_id, seed=SEED)
    all_invoices = ar_invoices + ap_invoices
    print(f"  -> {len(ap_invoices)} AP invoices (bills)")

    print("  Generating Payments linked to invoices...")
    all_payments = generate_payments(all_invoices, accounts, company_id=company_id, seed=SEED)
    print(f"  -> {len(all_payments)} payments")

    final_contacts = all_contacts + anomaly_contacts

    # ── Monthly Summary ───────────────────────────────────────────────────────
    monthly_summary = compute_monthly_summary(
        monthly_mrr=monthly_mrr,
        monthly_payroll=monthly_payroll,
        monthly_cloud=data_bundle["monthly_cloud"],
        monthly_opex=monthly_opex,
        headcount_history=headcount_history,
        anomaly_expenses=anomaly_expenses,
    )

    # ── Export ────────────────────────────────────────────────────────────────
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

    record_counts = {
        "Accounts":         len(accounts),
        "Contacts":         len(final_contacts),
        "Expenses":         len(all_expenses),
        "Invoices (AR)":    len(ar_invoices),
        "Invoices (AP)":    len(ap_invoices),
        "Invoices (Total)": len(all_invoices),
        "Payments":         len(all_payments),
        "Anomalies":        len(manifest),
    }
    print_summary_report(monthly_summary, manifest, record_counts)


if __name__ == "__main__":
    main()
