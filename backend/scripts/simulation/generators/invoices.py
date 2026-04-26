"""
AP Invoice generator.
Creates ACCOUNTS_PAYABLE invoices from vendor expenses (bills).
AR invoices are already created by revenue.py.
"""

from datetime import timedelta
from dateutil.relativedelta import relativedelta
import random

from simulation.config import START_DATE, NUM_MONTHS
from simulation.models import (
    Invoice, InvoiceType, InvoiceStatus, InvoiceLineItem, _date_iso,
)


def generate_ap_invoices(
    all_expenses: list,
    accounts: list,
    seed: int = 42,
) -> list:
    """
    Generate ACCOUNTS_PAYABLE invoices from expense records.
    Each vendor expense gets a corresponding AP invoice (bill).

    Args:
        all_expenses: Combined list of all Expense objects
        accounts: list of Account objects

    Returns:
        list of AP Invoice objects
    """
    rng = random.Random(seed)

    ap_account = None
    for acct in accounts:
        if acct.name == "Accounts Payable":
            ap_account = acct
            break

    invoices = []
    bill_counter = 5000

    for exp in all_expenses:
        if not exp.contact:
            # Skip internal expenses (no vendor)
            continue

        bill_counter += 1

        # Parse transaction date
        issue_date_str = exp.transaction_date
        if not issue_date_str:
            continue

        # Due date is Net 30 by default
        from datetime import date as dt_date
        issue_dt = dt_date.fromisoformat(issue_date_str)
        due_dt = issue_dt + timedelta(days=30)

        # Determine payment status
        # Most bills are paid on time, a few remain open
        is_recent = (issue_dt.year == 2026 and issue_dt.month >= 1)
        if is_recent:
            status = InvoiceStatus.OPEN
            paid_on = None
            balance = abs(exp.total_amount)
        else:
            pay_delay = rng.randint(0, 10)
            paid_on = due_dt + timedelta(days=pay_delay)
            status = InvoiceStatus.PAID
            balance = 0.0

        # Create line items from expense lines
        line_items = []
        for eline in exp.lines:
            line_items.append(InvoiceLineItem(
                description=eline.description,
                unit_price=abs(eline.total_amount) if eline.total_amount else 0,
                quantity=1.0,
                total_amount=abs(eline.total_amount) if eline.total_amount else 0,
                account=eline.account,
            ))

        amount = abs(exp.total_amount) if exp.total_amount else 0

        inv = Invoice(
            type=InvoiceType.ACCOUNTS_PAYABLE,
            contact=exp.contact,
            number=f"BILL-{bill_counter:05d}",
            issue_date=issue_date_str,
            due_date=_date_iso(due_dt),
            paid_on_date=_date_iso(paid_on) if paid_on else None,
            memo=exp.memo,
            currency="USD",
            total_amount=amount,
            balance=balance,
            sub_total=amount,
            status=status,
            line_items=line_items,
        )
        invoices.append(inv)

    return invoices
