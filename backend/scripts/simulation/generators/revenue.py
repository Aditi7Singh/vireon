"""
MRR / subscription revenue generator.
Creates revenue records with realistic growth, churn, and invoicing.
"""

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import random

from simulation.config import (
    CUSTOMERS, START_DATE, MRR_GROWTH_RATE, NUM_MONTHS,
)
from simulation.models import (
    Invoice, InvoiceType, InvoiceStatus, InvoiceLineItem, _date_iso,
)


def generate_revenue(
    accounts: list,
    customer_contacts: dict,
    seed: int = 42,
    churned_customer: str = "Acme Corp",
    churn_month: int = 11,
) -> dict:
    """
    Generate monthly subscription revenue invoices (ACCOUNTS_RECEIVABLE).

    Args:
        accounts: list of Account objects (need 'SaaS Subscription Revenue' + 'Accounts Receivable')
        customer_contacts: dict mapping customer name → Contact object
        seed: random seed
        churned_customer: name of customer that churns (Anomaly #7)
        churn_month: month number when churn happens

    Returns:
        dict with:
            'invoices': list of AR Invoice objects
            'monthly_mrr': dict of month_num → total MRR
            'customer_mrr_history': dict of customer_name → {month: mrr}
    """
    rng = random.Random(seed)

    # Find relevant accounts
    revenue_account = None
    ar_account = None
    for acct in accounts:
        if acct.name == "SaaS Subscription Revenue":
            revenue_account = acct
        elif acct.name == "Accounts Receivable":
            ar_account = acct

    invoices = []
    monthly_mrr = {}
    customer_mrr_history = {}
    invoice_counter = 1000

    for month_num in range(1, NUM_MONTHS + 1):
        month_date = START_DATE + relativedelta(months=month_num - 1)
        month_total_mrr = 0.0

        for cust_def in CUSTOMERS:
            cust_name = cust_def["name"]

            # Customer hasn't started yet
            if month_num < cust_def["start_month"]:
                continue

            # Churn check (Anomaly #7)
            if cust_name == churned_customer and month_num >= churn_month:
                continue

            # Calculate MRR with growth
            months_active = month_num - cust_def["start_month"]
            base_mrr = cust_def["mrr"]
            # Small organic growth per customer (1-2% monthly)
            current_mrr = base_mrr * (1 + 0.015) ** months_active
            current_mrr = round(current_mrr, 2)

            # Track history
            if cust_name not in customer_mrr_history:
                customer_mrr_history[cust_name] = {}
            customer_mrr_history[cust_name][month_num] = current_mrr

            month_total_mrr += current_mrr

            # For annual billing, only invoice in the start month and every 12th month
            if cust_def["billing"] == "annual":
                months_since_start = month_num - cust_def["start_month"]
                if months_since_start % 12 != 0:
                    continue
                invoice_amount = current_mrr * 12  # annual amount
            else:
                invoice_amount = current_mrr

            # Create AR Invoice
            invoice_counter += 1
            issue = month_date.replace(day=1)
            payment_terms = cust_def.get("payment_terms", 30)
            due = issue + timedelta(days=payment_terms)

            # Determine if paid (most customers pay on time, some late)
            days_late = 0
            if cust_name == "GreenLeaf Ventures":
                # This customer consistently pays late (~45 days past due)
                days_late = rng.randint(30, 50)
            elif rng.random() < 0.15:
                # 15% chance of being slightly late
                days_late = rng.randint(5, 15)

            paid_date = due + timedelta(days=days_late) if month_num < NUM_MONTHS else None
            status = InvoiceStatus.PAID if paid_date else InvoiceStatus.OPEN
            balance = 0.0 if status == InvoiceStatus.PAID else invoice_amount

            contact_obj = customer_contacts.get(cust_name)
            contact_id = contact_obj.id if contact_obj else None

            line_item = InvoiceLineItem(
                description=f"SaaS Subscription — {cust_name} — {month_date.strftime('%B %Y')}",
                unit_price=invoice_amount,
                quantity=1.0,
                total_amount=invoice_amount,
                account=revenue_account.id if revenue_account else None,
            )

            inv = Invoice(
                type=InvoiceType.ACCOUNTS_RECEIVABLE,
                contact=contact_id,
                number=f"INV-{invoice_counter:05d}",
                issue_date=_date_iso(issue),
                due_date=_date_iso(due),
                paid_on_date=_date_iso(paid_date) if paid_date else None,
                memo=f"Subscription invoice for {cust_name}",
                currency="USD",
                total_amount=invoice_amount,
                balance=balance,
                sub_total=invoice_amount,
                status=status,
                line_items=[line_item],
            )
            invoices.append(inv)

        monthly_mrr[month_num] = round(month_total_mrr, 2)

    return {
        "invoices": invoices,
        "monthly_mrr": monthly_mrr,
        "customer_mrr_history": customer_mrr_history,
    }
