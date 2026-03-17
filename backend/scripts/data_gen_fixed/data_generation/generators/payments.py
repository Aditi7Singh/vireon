"""
Payment generator.
FIX: company field populated on every Payment.
"""

from data_generation.models import Payment, PaymentLineItem, InvoiceStatus, _date_iso


def generate_payments(
    all_invoices: list,
    accounts: list,
    company_id: str = None,
    seed: int = 42,
) -> list:
    """Generate Payment objects linked to paid invoices."""

    acct_map     = {a.name: a for a in accounts}
    bank_account = acct_map.get("Operating Checking Account")

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
            company=company_id,     # FIX: was always null
            applied_to_lines=[payment_line],
        )
        payments.append(pmt)

        # Back-link payment ID onto invoice
        inv.payments.append(pmt.id)

    return payments
