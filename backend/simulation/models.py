"""
Merge.dev Accounting API-aligned data models.

Every model mirrors the Merge.dev Unified Accounting API field names, types,
and enum values so the backend cannot distinguish simulated from live data.

Reference: https://docs.merge.dev/accounting/overview/
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import Optional, List
from uuid import uuid4
import json


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _uuid() -> str:
    """Generate a UUID4 string (Merge.dev uses UUIDs for `id`)."""
    return str(uuid4())


def _remote_id(prefix: str = "QB") -> str:
    """Generate a fake remote_id like QuickBooks would return."""
    return f"{prefix}-{uuid4().hex[:8].upper()}"


def _now_iso() -> str:
    """ISO 8601 timestamp for created_at / modified_at."""
    return datetime.utcnow().isoformat() + "Z"


def _date_iso(d: date) -> Optional[str]:
    """Convert a date to ISO 8601 string, or None."""
    return d.isoformat() if d else None


# ─── Enums (matching Merge.dev exactly) ───────────────────────────────────────

class AccountClassification:
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"


class AccountType:
    BANK = "BANK"
    CREDIT_CARD = "CREDIT_CARD"
    ACCOUNTS_PAYABLE = "ACCOUNTS_PAYABLE"
    ACCOUNTS_RECEIVABLE = "ACCOUNTS_RECEIVABLE"
    FIXED_ASSET = "FIXED_ASSET"
    OTHER_ASSET = "OTHER_ASSET"
    OTHER_CURRENT_ASSET = "OTHER_CURRENT_ASSET"
    OTHER_EXPENSE = "OTHER_EXPENSE"
    OTHER_INCOME = "OTHER_INCOME"
    COST_OF_GOODS_SOLD = "COST_OF_GOODS_SOLD"
    OTHER_CURRENT_LIABILITY = "OTHER_CURRENT_LIABILITY"
    LONG_TERM_LIABILITY = "LONG_TERM_LIABILITY"


class AccountStatus:
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    INACTIVE = "INACTIVE"


class ContactStatus:
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class InvoiceType:
    ACCOUNTS_RECEIVABLE = "ACCOUNTS_RECEIVABLE"
    ACCOUNTS_PAYABLE = "ACCOUNTS_PAYABLE"


class InvoiceStatus:
    PAID = "PAID"
    OPEN = "OPEN"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    VOID = "VOID"


class AddressType:
    BILLING = "BILLING"
    SHIPPING = "SHIPPING"


# ─── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class Address:
    """Merge.dev Address sub-object for Contacts."""
    type: str = AddressType.BILLING
    street_1: str = ""
    street_2: Optional[str] = None
    city: str = ""
    state: str = ""
    country: str = "US"
    zip_code: str = ""
    created_at: str = field(default_factory=_now_iso)
    modified_at: str = field(default_factory=_now_iso)


@dataclass
class PhoneNumber:
    """Merge.dev AccountingPhoneNumber sub-object."""
    number: str = ""
    type: str = "PRIMARY"
    created_at: str = field(default_factory=_now_iso)
    modified_at: str = field(default_factory=_now_iso)


@dataclass
class Account:
    """
    Merge.dev Account — represents a category in a company's chart of accounts.
    https://docs.merge.dev/accounting/accounts/
    """
    id: str = field(default_factory=_uuid)
    remote_id: str = field(default_factory=lambda: _remote_id("ACCT"))
    created_at: str = field(default_factory=_now_iso)
    modified_at: str = field(default_factory=_now_iso)
    name: str = ""
    description: str = ""
    classification: str = ""          # ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE
    account_type: str = ""            # BANK, CREDIT_CARD, ACCOUNTS_PAYABLE, etc.
    status: str = AccountStatus.ACTIVE
    current_balance: Optional[float] = None
    currency: str = "USD"
    remote_was_deleted: bool = False


@dataclass
class Contact:
    """
    Merge.dev Contact — customer or vendor (supplier).
    https://docs.merge.dev/accounting/contacts/
    """
    id: str = field(default_factory=_uuid)
    remote_id: str = field(default_factory=lambda: _remote_id("CONT"))
    created_at: str = field(default_factory=_now_iso)
    modified_at: str = field(default_factory=_now_iso)
    name: str = ""
    is_supplier: bool = False
    is_customer: bool = False
    email_address: Optional[str] = None
    tax_number: Optional[str] = None
    status: str = ContactStatus.ACTIVE
    currency: str = "USD"
    company: Optional[str] = None     # Company ID reference
    addresses: List[Address] = field(default_factory=list)
    phone_numbers: List[PhoneNumber] = field(default_factory=list)
    remote_was_deleted: bool = False


@dataclass
class ExpenseLine:
    """
    Merge.dev Expense line item.
    Each line within an Expense object.
    """
    id: str = field(default_factory=_uuid)
    remote_id: str = field(default_factory=lambda: _remote_id("EXLN"))
    item: Optional[str] = None        # Item ID reference
    description: str = ""
    net_amount: Optional[float] = None
    tax_amount: Optional[float] = 0.0
    total_amount: Optional[float] = None
    currency: str = "USD"
    account: Optional[str] = None     # Account ID reference
    contact: Optional[str] = None     # Contact ID reference
    tracking_categories: List[str] = field(default_factory=list)


@dataclass
class Expense:
    """
    Merge.dev Expense — direct purchase (check, credit card, cash).
    https://docs.merge.dev/accounting/expenses/
    Negative amounts = purchases, positive = refunds.
    """
    id: str = field(default_factory=_uuid)
    remote_id: str = field(default_factory=lambda: _remote_id("EXP"))
    created_at: str = field(default_factory=_now_iso)
    modified_at: str = field(default_factory=_now_iso)
    transaction_date: Optional[str] = None
    remote_created_at: Optional[str] = None
    account: Optional[str] = None     # Account ID (payment source: bank, credit card)
    contact: Optional[str] = None     # Contact ID (vendor)
    total_amount: Optional[float] = None
    sub_total: Optional[float] = None
    total_tax_amount: Optional[float] = 0.0
    currency: str = "USD"
    memo: Optional[str] = None
    lines: List[ExpenseLine] = field(default_factory=list)
    company: Optional[str] = None
    remote_was_deleted: bool = False


@dataclass
class InvoiceLineItem:
    """
    Merge.dev Invoice line item.
    """
    id: str = field(default_factory=_uuid)
    remote_id: str = field(default_factory=lambda: _remote_id("INVL"))
    description: str = ""
    unit_price: Optional[float] = None
    quantity: Optional[float] = 1.0
    total_amount: Optional[float] = None
    currency: str = "USD"
    account: Optional[str] = None     # Account ID reference
    item: Optional[str] = None
    tracking_categories: List[str] = field(default_factory=list)


@dataclass
class Invoice:
    """
    Merge.dev Invoice — AR (revenue) or AP (vendor bill).
    https://docs.merge.dev/accounting/invoices/
    """
    id: str = field(default_factory=_uuid)
    remote_id: str = field(default_factory=lambda: _remote_id("INV"))
    created_at: str = field(default_factory=_now_iso)
    modified_at: str = field(default_factory=_now_iso)
    type: str = InvoiceType.ACCOUNTS_RECEIVABLE   # AR or AP
    contact: Optional[str] = None     # Contact ID
    number: str = ""                  # Invoice number (e.g., INV-0001)
    issue_date: Optional[str] = None
    due_date: Optional[str] = None
    paid_on_date: Optional[str] = None
    memo: Optional[str] = None
    company: Optional[str] = None
    currency: str = "USD"
    total_amount: Optional[float] = None
    balance: Optional[float] = None   # Remaining unpaid balance
    total_tax_amount: Optional[float] = 0.0
    sub_total: Optional[float] = None
    status: str = InvoiceStatus.OPEN
    line_items: List[InvoiceLineItem] = field(default_factory=list)
    payments: List[str] = field(default_factory=list)  # Payment ID references
    remote_was_deleted: bool = False


@dataclass
class PaymentLineItem:
    """Applied-to line for a Payment."""
    id: str = field(default_factory=_uuid)
    remote_id: str = field(default_factory=lambda: _remote_id("PMLN"))
    applied_amount: Optional[float] = None
    applied_date: Optional[str] = None
    related_object_id: Optional[str] = None   # Invoice ID
    related_object_type: str = "INVOICE"


@dataclass
class Payment:
    """
    Merge.dev Payment — applied to invoices.
    https://docs.merge.dev/accounting/payments/
    """
    id: str = field(default_factory=_uuid)
    remote_id: str = field(default_factory=lambda: _remote_id("PMT"))
    created_at: str = field(default_factory=_now_iso)
    modified_at: str = field(default_factory=_now_iso)
    transaction_date: Optional[str] = None
    contact: Optional[str] = None     # Contact ID
    account: Optional[str] = None     # Account ID (bank account receiving/sending)
    total_amount: Optional[float] = None
    currency: str = "USD"
    company: Optional[str] = None
    applied_to_lines: List[PaymentLineItem] = field(default_factory=list)
    remote_was_deleted: bool = False


@dataclass
class TransactionLineItem:
    """Line item within a Transaction."""
    id: str = field(default_factory=_uuid)
    remote_id: str = field(default_factory=lambda: _remote_id("TXLN"))
    account: Optional[str] = None
    net_amount: Optional[float] = None
    description: str = ""


@dataclass
class Transaction:
    """
    Merge.dev Transaction — catch-all for non-expense, non-invoice transactions.
    https://docs.merge.dev/accounting/transactions/
    """
    id: str = field(default_factory=_uuid)
    remote_id: str = field(default_factory=lambda: _remote_id("TXN"))
    created_at: str = field(default_factory=_now_iso)
    modified_at: str = field(default_factory=_now_iso)
    transaction_type: Optional[str] = None
    number: Optional[str] = None
    transaction_date: Optional[str] = None
    account: Optional[str] = None
    contact: Optional[str] = None
    total_amount: Optional[float] = None
    currency: str = "USD"
    line_items: List[TransactionLineItem] = field(default_factory=list)
    remote_was_deleted: bool = False


@dataclass
class CompanyInfo:
    """
    Merge.dev CompanyInfo — basic metadata about the company.
    https://docs.merge.dev/accounting/company-info/
    """
    id: str = field(default_factory=_uuid)
    remote_id: str = field(default_factory=lambda: _remote_id("COMP"))
    created_at: str = field(default_factory=_now_iso)
    modified_at: str = field(default_factory=_now_iso)
    name: str = ""
    legal_name: Optional[str] = None
    tax_number: Optional[str] = None
    fiscal_year_end_month: Optional[int] = 12
    fiscal_year_end_day: Optional[int] = 31
    currency: str = "USD"
    urls: List[str] = field(default_factory=list)
    remote_was_deleted: bool = False


# ─── Serialization Helpers ────────────────────────────────────────────────────

class MergeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles dataclasses and dates."""
    def default(self, obj):
        if hasattr(obj, '__dataclass_fields__'):
            return asdict(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


def to_merge_response(items: list, model_name: str) -> dict:
    """
    Wrap a list of model objects in Merge.dev's standard list response format:
    { "next": null, "previous": null, "results": [...] }
    """
    return {
        "next": None,
        "previous": None,
        "results": [asdict(item) for item in items]
    }
