"""
Payment generator.
Links payments to both AR invoices (customer payments) and AP invoices (vendor payments).
"""

from datetime import timedelta, date as dt_date
import random

from simulation.models import (
    Payment, PaymentLineItem, InvoiceStatus, _date_iso,
)


def generate_payments(
    all_invoices: list,
    accounts: list,
    seed: int = 42,
) -> list:
    """
    Generate Payment objects linked to paid invoices.

    Args:
        all_invoices: Combined list of AR + AP invoices
        accounts: list of Account objects

    Returns:
        list of Payment objects
    """
    rng = random.Random(seed)

    bank_account = None
    for acct in accounts:
        if acct.name == "Operating Checking Account":
            bank_account = acct
            break

    payments = []

    for inv in all_invoices:
        if inv.status != InvoiceStatus.PAID:
            continue
        if not inv.paid_on_date:
            continue

        payment_line = PaymentLineItem(
            applied_amount=inv.total_amount,
            applied_date=inv.paid_on_date,
            related_object_id=inv.id,
            related_object_type="INVOICE",
        )

        pmt = Payment(
            transaction_date=inv.paid_on_date,
            contact=inv.contact,
            account=bank_account.id if bank_account else None,
            total_amount=inv.total_amount,
            currency="USD",
            applied_to_lines=[payment_line],
        )
        payments.append(pmt)

        # Link payment back to invoice
        inv.payments.append(pmt.id)

    return payments
