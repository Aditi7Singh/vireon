"""
AP Invoice generator.
FIX: company field populated on every Invoice.
"""

from datetime import timedelta, date as dt_date
import random

from data_generation.models import Invoice, InvoiceType, InvoiceStatus, InvoiceLineItem, _date_iso


def generate_ap_invoices(
    all_expenses: list,
    accounts: list,
    company_id: str = None,
    seed: int = 42,
) -> list:
    """
    Generate ACCOUNTS_PAYABLE invoices from expense records.
    Each vendor expense gets a corresponding AP bill/invoice.
    """
    rng = random.Random(seed)

    acct_map   = {a.name: a for a in accounts}
    ap_account = acct_map.get("Accounts Payable")

    invoices     = []
    bill_counter = 5000

    for exp in all_expenses:
        if not exp.contact:
            continue

        issue_date_str = exp.transaction_date
        if not issue_date_str:
            continue

        bill_counter += 1
        issue_dt = dt_date.fromisoformat(issue_date_str)
        due_dt   = issue_dt + timedelta(days=30)

        # Recent bills (Jan 2026+) are still open
        is_recent = (issue_dt.year == 2026 and issue_dt.month >= 1)
        if is_recent:
            status   = InvoiceStatus.OPEN
            paid_on  = None
            balance  = abs(exp.total_amount)
        else:
            pay_delay = rng.randint(0, 10)
            paid_on   = due_dt + timedelta(days=pay_delay)
            status    = InvoiceStatus.PAID
            balance   = 0.0

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
            company=company_id,     # FIX: was always null
            currency="USD",
            total_amount=amount,
            balance=balance,
            sub_total=amount,
            status=status,
            line_items=line_items,
        )
        invoices.append(inv)

    return invoices
