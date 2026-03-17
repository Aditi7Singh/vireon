"""
Merge.dev Accounting API-aligned data models.
Reference: https://docs.merge.dev/accounting/overview/

FIXES vs original:
  1. Account field renamed: account_type -> type  (Merge.dev uses "type")
  2. parent_account field added to Account
  3. company field added/populated on Account, Contact, Invoice, Expense, Payment
  4. ExpenseLine.contact removed (not in Merge.dev ExpenseLineItem schema)
  5. tracking_categories added to Invoice
  6. ContactStatus.ARCHIVED added (Merge.dev: ACTIVE | ARCHIVED)
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import Optional, List
from uuid import uuid4
import json


# ── Helpers ───────────────────────────────────────────────────────────────────

def _uuid() -> str:
    return str(uuid4())

def _remote_id(prefix: str = "QB") -> str:
    return f"{prefix}-{uuid4().hex[:8].upper()}"

def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"

def _date_iso(d: date) -> Optional[str]:
    return d.isoformat() if d else None


# ── Enums ─────────────────────────────────────────────────────────────────────

class AccountClassification:
    ASSET     = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY    = "EQUITY"
    REVENUE   = "REVENUE"
    EXPENSE   = "EXPENSE"

class AccountType:
    # These are the values for Account.type (NOT account_type)
    BANK                    = "BANK"
    CREDIT_CARD             = "CREDIT_CARD"
    ACCOUNTS_PAYABLE        = "ACCOUNTS_PAYABLE"
    ACCOUNTS_RECEIVABLE     = "ACCOUNTS_RECEIVABLE"
    FIXED_ASSET             = "FIXED_ASSET"
    OTHER_ASSET             = "OTHER_ASSET"
    OTHER_CURRENT_ASSET     = "OTHER_CURRENT_ASSET"
    OTHER_EXPENSE           = "OTHER_EXPENSE"
    OTHER_INCOME            = "OTHER_INCOME"
    COST_OF_GOODS_SOLD      = "COST_OF_GOODS_SOLD"
    OTHER_CURRENT_LIABILITY = "OTHER_CURRENT_LIABILITY"
    LONG_TERM_LIABILITY     = "LONG_TERM_LIABILITY"
    EQUITY                  = "EQUITY"

class AccountStatus:
    ACTIVE   = "ACTIVE"
    PENDING  = "PENDING"
    INACTIVE = "INACTIVE"

class ContactStatus:
    ACTIVE   = "ACTIVE"
    ARCHIVED = "ARCHIVED"   # FIX: Merge.dev uses ARCHIVED not INACTIVE

class InvoiceType:
    ACCOUNTS_RECEIVABLE = "ACCOUNTS_RECEIVABLE"
    ACCOUNTS_PAYABLE    = "ACCOUNTS_PAYABLE"

class InvoiceStatus:
    PAID           = "PAID"
    OPEN           = "OPEN"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    DRAFT          = "DRAFT"
    VOID           = "VOID"

class AddressType:
    BILLING  = "BILLING"
    SHIPPING = "SHIPPING"


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class Address:
    type:        str           = AddressType.BILLING
    street_1:    str           = ""
    street_2:    Optional[str] = None
    city:        str           = ""
    state:       str           = ""
    country:     str           = "US"
    zip_code:    str           = ""
    created_at:  str           = field(default_factory=_now_iso)
    modified_at: str           = field(default_factory=_now_iso)

@dataclass
class PhoneNumber:
    number:      str = ""
    type:        str = "PRIMARY"
    created_at:  str = field(default_factory=_now_iso)
    modified_at: str = field(default_factory=_now_iso)

@dataclass
class Account:
    """
    Merge.dev Account (chart of accounts entry).
    https://docs.merge.dev/accounting/accounts/
    KEY FIX: field is named 'type' in Merge.dev, NOT 'account_type'.
    """
    id:                 str            = field(default_factory=_uuid)
    remote_id:          str            = field(default_factory=lambda: _remote_id("ACCT"))
    created_at:         str            = field(default_factory=_now_iso)
    modified_at:        str            = field(default_factory=_now_iso)
    name:               str            = ""
    description:        str            = ""
    classification:     str            = ""   # ASSET | LIABILITY | EQUITY | REVENUE | EXPENSE
    type:               str            = ""   # FIX: was 'account_type' — Merge.dev calls it 'type'
    status:             str            = AccountStatus.ACTIVE
    current_balance:    Optional[float]= None
    currency:           str            = "USD"
    company:            Optional[str]  = None  # CompanyInfo.id
    parent_account:     Optional[str]  = None  # FIX: added for COA hierarchy
    remote_was_deleted: bool           = False

@dataclass
class Contact:
    """https://docs.merge.dev/accounting/contacts/"""
    id:                 str               = field(default_factory=_uuid)
    remote_id:          str               = field(default_factory=lambda: _remote_id("CONT"))
    created_at:         str               = field(default_factory=_now_iso)
    modified_at:        str               = field(default_factory=_now_iso)
    name:               str               = ""
    is_supplier:        bool              = False
    is_customer:        bool              = False
    email_address:      Optional[str]     = None
    tax_number:         Optional[str]     = None
    status:             str               = ContactStatus.ACTIVE
    currency:           str               = "USD"
    company:            Optional[str]     = None  # CompanyInfo.id
    addresses:          List[Address]     = field(default_factory=list)
    phone_numbers:      List[PhoneNumber] = field(default_factory=list)
    remote_was_deleted: bool              = False

@dataclass
class ExpenseLine:
    """
    Merge.dev ExpenseLineItem.
    https://docs.merge.dev/accounting/expenses/
    FIX: removed 'contact' field — Merge.dev does NOT have contact at line level.
    """
    id:                  str            = field(default_factory=_uuid)
    remote_id:           str            = field(default_factory=lambda: _remote_id("EXLN"))
    item:                Optional[str]  = None
    description:         str            = ""
    net_amount:          Optional[float]= None
    tax_amount:          Optional[float]= 0.0
    total_amount:        Optional[float]= None
    currency:            str            = "USD"
    account:             Optional[str]  = None   # Account.id
    tracking_categories: List[str]      = field(default_factory=list)

@dataclass
class Expense:
    """
    Merge.dev Expense.
    https://docs.merge.dev/accounting/expenses/
    Negative total_amount = outflow/purchase. Positive = refund.
    """
    id:                  str               = field(default_factory=_uuid)
    remote_id:           str               = field(default_factory=lambda: _remote_id("EXP"))
    created_at:          str               = field(default_factory=_now_iso)
    modified_at:         str               = field(default_factory=_now_iso)
    transaction_date:    Optional[str]     = None
    remote_created_at:   Optional[str]     = None
    account:             Optional[str]     = None   # Account.id (bank/CC paying)
    contact:             Optional[str]     = None   # Contact.id (vendor)
    total_amount:        Optional[float]   = None
    sub_total:           Optional[float]   = None
    total_tax_amount:    Optional[float]   = 0.0
    currency:            str               = "USD"
    memo:                Optional[str]     = None
    lines:               List[ExpenseLine] = field(default_factory=list)
    tracking_categories: List[str]         = field(default_factory=list)
    company:             Optional[str]     = None   # FIX: CompanyInfo.id, was always null
    remote_was_deleted:  bool              = False

@dataclass
class InvoiceLineItem:
    """Merge.dev Invoice line item."""
    id:                  str            = field(default_factory=_uuid)
    remote_id:           str            = field(default_factory=lambda: _remote_id("INVL"))
    description:         str            = ""
    unit_price:          Optional[float]= None
    quantity:            Optional[float]= 1.0
    total_amount:        Optional[float]= None
    currency:            str            = "USD"
    account:             Optional[str]  = None
    item:                Optional[str]  = None
    tracking_categories: List[str]      = field(default_factory=list)

@dataclass
class Invoice:
    """
    Merge.dev Invoice — AR or AP.
    https://docs.merge.dev/accounting/invoices/
    """
    id:                  str                   = field(default_factory=_uuid)
    remote_id:           str                   = field(default_factory=lambda: _remote_id("INV"))
    created_at:          str                   = field(default_factory=_now_iso)
    modified_at:         str                   = field(default_factory=_now_iso)
    type:                str                   = InvoiceType.ACCOUNTS_RECEIVABLE
    contact:             Optional[str]         = None
    number:              str                   = ""
    issue_date:          Optional[str]         = None
    due_date:            Optional[str]         = None
    paid_on_date:        Optional[str]         = None
    memo:                Optional[str]         = None
    company:             Optional[str]         = None   # FIX: CompanyInfo.id, was always null
    currency:            str                   = "USD"
    total_amount:        Optional[float]       = None
    balance:             Optional[float]       = None
    total_tax_amount:    Optional[float]       = 0.0
    sub_total:           Optional[float]       = None
    status:              str                   = InvoiceStatus.OPEN
    line_items:          List[InvoiceLineItem] = field(default_factory=list)
    payments:            List[str]             = field(default_factory=list)
    tracking_categories: List[str]             = field(default_factory=list)  # FIX: was missing
    remote_was_deleted:  bool                  = False

@dataclass
class PaymentLineItem:
    """Applied-to line: links a payment to an invoice."""
    id:                  str            = field(default_factory=_uuid)
    remote_id:           str            = field(default_factory=lambda: _remote_id("PMLN"))
    applied_amount:      Optional[float]= None
    applied_date:        Optional[str]  = None
    related_object_id:   Optional[str]  = None   # Invoice.id
    related_object_type: str            = "INVOICE"

@dataclass
class Payment:
    """
    Merge.dev Payment.
    https://docs.merge.dev/accounting/payments/
    """
    id:                 str                   = field(default_factory=_uuid)
    remote_id:          str                   = field(default_factory=lambda: _remote_id("PMT"))
    created_at:         str                   = field(default_factory=_now_iso)
    modified_at:        str                   = field(default_factory=_now_iso)
    transaction_date:   Optional[str]         = None
    contact:            Optional[str]         = None
    account:            Optional[str]         = None
    total_amount:       Optional[float]       = None
    currency:           str                   = "USD"
    company:            Optional[str]         = None   # FIX: CompanyInfo.id, was always null
    applied_to_lines:   List[PaymentLineItem] = field(default_factory=list)
    remote_was_deleted: bool                  = False

@dataclass
class CompanyInfo:
    """
    Merge.dev CompanyInfo.
    https://docs.merge.dev/accounting/company-info/
    """
    id:                    str           = field(default_factory=_uuid)
    remote_id:             str           = field(default_factory=lambda: _remote_id("COMP"))
    created_at:            str           = field(default_factory=_now_iso)
    modified_at:           str           = field(default_factory=_now_iso)
    name:                  str           = ""
    legal_name:            Optional[str] = None
    tax_number:            Optional[str] = None
    fiscal_year_end_month: Optional[int] = 12
    fiscal_year_end_day:   Optional[int] = 31
    currency:              str           = "USD"
    urls:                  List[str]     = field(default_factory=list)
    remote_was_deleted:    bool          = False


# ── Serialization ─────────────────────────────────────────────────────────────

class MergeEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__dataclass_fields__'):
            return asdict(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

def to_merge_response(items: list, model_name: str) -> dict:
    return {
        "next": None,
        "previous": None,
        "results": [asdict(item) for item in items]
    }
