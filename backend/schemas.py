from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Union
from datetime import datetime, date
from uuid import UUID
from enum import Enum


class LedgerEntryType(str, Enum):
    credit = "credit"
    debit = "debit"


class LedgerCategory(str, Enum):
    revenue = "revenue"
    tech_cost = "tech_cost"
    non_tech_cost = "non_tech_cost"
    office_expense = "office_expense"
    marketing = "marketing"
    payroll = "payroll"
    hiring = "hiring"
    loan_repayment = "loan_repayment"
    misc = "misc"


class LedgerProductTag(str, Enum):
    orchard = "orchard"
    sprouts = "sprouts"
    ai_lab = "ai_lab"
    shared = "shared"
    unallocated = "unallocated"


class LedgerOfficeTag(str, Enum):
    bengaluru = "bengaluru"
    gangavathi = "gangavathi"
    remote = "remote"
    na = "na"


class LedgerSource(str, Enum):
    erpnext = "erpnext"
    manual_cto = "manual_cto"
    manual_marketing = "manual_marketing"
    manual_finance = "manual_finance"
    bank_feed = "bank_feed"
    aws_billing = "aws_billing"
    sandbox = "sandbox"


class LedgerEnteredByRole(str, Enum):
    ceo = "ceo"
    cto = "cto"
    cso = "cso"
    marketing = "marketing"
    finance = "finance"
    system = "system"

class CompanyBase(BaseModel):
    name: str
    industry: Optional[str] = None
    stage: Optional[str] = None
    initial_cash: Optional[float] = None
    founding_date: Optional[date] = None

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AccountBase(BaseModel):
    remote_id: str
    name: str
    description: Optional[str] = None
    classification: str
    type: str
    status: str = "active"
    current_balance: float = 0.0
    currency: str = "USD"
    remote_created_at: Optional[datetime] = None
    remote_modified_at: Optional[datetime] = None

class AccountCreate(AccountBase):
    company_id: Optional[UUID] = None

class Account(AccountBase):
    id: UUID
    company_id: UUID
    model_config = ConfigDict(from_attributes=True)

class ContactBase(BaseModel):
    remote_id: str
    name: str
    type: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str = "active"
    payment_terms: Optional[str] = None
    currency: str = "USD"
    billing_address: Optional[dict] = None
    shipping_address: Optional[dict] = None
    tax_number: Optional[str] = None

class ContactCreate(ContactBase):
    company_id: Optional[UUID] = None

class Contact(ContactBase):
    id: UUID
    company_id: UUID
    model_config = ConfigDict(from_attributes=True)

class InvoiceBase(BaseModel):
    remote_id: str
    invoice_number: str
    contact_remote_id: str
    issue_date: date
    due_date: date
    payment_date: Optional[date] = None
    status: str
    type: str
    sub_total: float
    tax_amount: float = 0.0
    total_amount: float
    amount_paid: float = 0.0
    amount_due: float
    currency: str = "USD"
    memo: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    company_id: Optional[UUID] = None

class Invoice(InvoiceBase):
    id: UUID
    company_id: UUID
    contact_id: UUID
    model_config = ConfigDict(from_attributes=True)

class ExpenseBase(BaseModel):
    remote_id: str
    transaction_date: date
    account_remote_id: str
    contact_remote_id: Optional[str] = None
    total_amount: float
    sub_total: Optional[float] = None
    tax_amount: float = 0.0
    currency: str = "USD"
    category: Optional[str] = None
    payment_method: Optional[str] = None
    memo: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    company_id: Optional[UUID] = None

class Expense(ExpenseBase):
    id: UUID
    company_id: UUID
    account_id: UUID
    contact_id: Optional[UUID] = None
    model_config = ConfigDict(from_attributes=True)

class MonthlyMetricBase(BaseModel):
    metric_month: date
    total_revenue: float = 0.0
    total_expenses: float = 0.0
    total_tax_liability: float = 0.0
    net_cash_flow: float = 0.0
    burn_rate: float = 0.0
    runway_months: float = 0.0
    ending_cash: float = 0.0

class MonthlyMetricCreate(MonthlyMetricBase):
    company_id: Optional[UUID] = None

class MonthlyMetric(MonthlyMetricBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AnomalyBase(BaseModel):
    remote_id: Optional[str] = None
    anomaly_date: date
    severity: str
    type: str
    description: str
    expected_value: Optional[float] = None
    actual_value: Optional[float] = None
    status: str = "open"

class AnomalyCreate(AnomalyBase):
    company_id: Optional[UUID] = None

class Anomaly(AnomalyBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class Alert(BaseModel):
    id: str
    severity: str
    alert_type: str
    category: str
    description: str
    amount: float
    baseline: float
    delta_pct: float
    runway_impact: float
    suggested_owner: str
    created_at: str
    status: str

class AlertsResponse(BaseModel):
    alerts: List[Alert]
    total: int
    critical_count: int
    warning_count: int
    last_scan_at: str

class SandboxData(BaseModel):
    company: CompanyCreate
    accounts: List[AccountCreate]
    contacts: List[ContactCreate]
    invoices: List[InvoiceCreate]
    expenses: List[ExpenseCreate]
    employees: List[EmployeeCreate] = []
    payroll_entries: List[PayrollEntryCreate] = []
    loans: List[LoanCreate] = []
    fixed_assets: List[FixedAssetCreate] = []
    metrics: List[MonthlyMetricCreate] = []
    anomalies: List[AnomalyCreate] = []

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    role: Optional[str] = "VIEWER"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: UUID
    role: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

# --- Scenario Simulation Schemas ---

class HiringScenarioRequest(BaseModel):
    num_employees: int
    avg_salary: float
    company_id: UUID

class RevenueScenarioRequest(BaseModel):
    percentage_change: float # 0.1 for 10%
    company_id: UUID

class ScenarioResponse(BaseModel):
    scenario: str
    impact_metrics: dict
    new_runway: Union[float, str]

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    company_id: Optional[UUID] = None

class BudgetLineBase(BaseModel):
    category: str
    monthly_amount: float

class BudgetLine(BudgetLineBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

class BudgetBase(BaseModel):
    name: str
    fiscal_year: int
    status: str = "active"

class Budget(BudgetBase):
    id: UUID
    lines: List[BudgetLine]
    model_config = ConfigDict(from_attributes=True)

class ForecastBase(BaseModel):
    forecast_date: date
    mrr_predicted: float
    cash_predicted: float
    confidence_lower: float
    confidence_upper: float

class Forecast(ForecastBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


# Loan Schemas
class LoanPaymentBase(BaseModel):
    payment_date: date
    payment_amount: float
    principal_paid: float
    interest_paid: float
    remaining_balance: float

class LoanPayment(LoanPaymentBase):
    id: UUID
    loan_id: UUID
    model_config = ConfigDict(from_attributes=True)

class LoanBase(BaseModel):
    loan_name: str
    principal_amount: float
    interest_rate: float
    term_months: int
    start_date: date
    loan_type: str = "term_loan"
    lender: Optional[str] = None
    status: str = "active"
    remaining_balance: Optional[float] = None

class LoanCreate(LoanBase):
    pass

class Loan(LoanBase):
    id: UUID
    payments: List[LoanPayment] = []
    model_config = ConfigDict(from_attributes=True)


# Payroll Schemas
class PayrollEntryBase(BaseModel):
    pay_period_start: date
    pay_period_end: date
    gross_pay: float
    federal_tax: float = 0
    state_tax: float = 0
    social_security: float = 0
    medicare: float = 0
    other_deductions: float = 0
    net_pay: float
    pay_date: date
    status: str = "processed"

class PayrollEntryCreate(PayrollEntryBase):
    employee_id: UUID

class PayrollEntry(PayrollEntryBase):
    id: UUID
    employee_id: UUID
    model_config = ConfigDict(from_attributes=True)

class EmployeeBase(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    email: str
    hire_date: date
    termination_date: Optional[date] = None
    salary: float
    pay_frequency: str = "monthly"
    job_title: Optional[str] = None
    department: Optional[str] = None
    status: str = "active"

class EmployeeCreate(EmployeeBase):
    pass

class Employee(EmployeeBase):
    id: UUID
    payroll_entries: List[PayrollEntry] = []
    model_config = ConfigDict(from_attributes=True)


# Depreciation Schemas
class DepreciationEntryBase(BaseModel):
    depreciation_date: date
    depreciation_amount: float
    accumulated_depreciation: float
    book_value: float

class DepreciationEntry(DepreciationEntryBase):
    id: UUID
    asset_id: UUID
    model_config = ConfigDict(from_attributes=True)

class FixedAssetBase(BaseModel):
    asset_name: str
    asset_category: Optional[str] = None
    purchase_date: date
    purchase_cost: float
    salvage_value: float = 0
    useful_life_years: int
    depreciation_method: str = "straight_line"
    location: Optional[str] = None
    serial_number: Optional[str] = None
    status: str = "active"
    disposal_date: Optional[date] = None
    disposal_value: Optional[float] = None

class FixedAssetCreate(FixedAssetBase):
    pass

class FixedAsset(FixedAssetBase):
    id: UUID
    accumulated_depreciation: float = 0
    book_value: Optional[float] = None
    depreciation_entries: List[DepreciationEntry] = []
    model_config = ConfigDict(from_attributes=True)


# Document / OCR Schemas
class DocumentBase(BaseModel):
    file_name: str
    file_type: str
    status: str = "pending" # pending, processing, completed, failed
    ocr_text: Optional[str] = None
    extracted_data: Optional[dict] = None
    structured_data: Optional[dict] = None

class DocumentCreate(DocumentBase):
    company_id: UUID

class Document(DocumentBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Report Schemas
class ReportRequest(BaseModel):
    report_type: str # runway, profit_loss, balance_sheet
    start_date: date
    end_date: date
    company_id: UUID

class ReportResponse(BaseModel):
    download_url: str
    generated_at: datetime


# Cloud Cost Schemas
class CloudAccountBase(BaseModel):
    provider: str
    account_id: str
    account_name: str
    status: str = "active"

class CloudAccountCreate(CloudAccountBase):
    company_id: UUID

class CloudAccount(CloudAccountBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CloudCostDetailBase(BaseModel):
    service_name: str
    amount: float
    currency: str = "USD"
    usage_date: date
    region: Optional[str] = None

class CloudCostDetailCreate(CloudCostDetailBase):
    account_id: UUID

class CloudCostDetail(CloudCostDetailBase):
    id: UUID
    account_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Banking Schemas
class BankFeedBase(BaseModel):
    bank_name: str
    account_name: str
    account_type: str
    account_number_last4: str
    currency: str = "USD"
    status: str = "active"

class BankFeedCreate(BankFeedBase):
    company_id: UUID

class BankFeed(BankFeedBase):
    id: UUID
    company_id: UUID
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class BankingTransactionBase(BaseModel):
    transaction_date: date
    amount: float
    description: str
    merchant_name: Optional[str] = None
    category: Optional[str] = None
    is_saas: bool = False

class BankingTransactionCreate(BankingTransactionBase):
    feed_id: UUID

class BankingTransaction(BankingTransactionBase):
    id: UUID
    feed_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LedgerEntryCreate(BaseModel):
    company_id: UUID
    transaction_date: date
    amount: float
    currency: str = "INR"
    amount_inr: Optional[float] = None
    entry_type: LedgerEntryType
    category: LedgerCategory
    product_tag: LedgerProductTag = LedgerProductTag.unallocated
    office_tag: LedgerOfficeTag = LedgerOfficeTag.na
    source: LedgerSource = LedgerSource.manual_finance
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    description: str
    entered_by_role: LedgerEnteredByRole = LedgerEnteredByRole.system
    is_recurring: bool = False
    tags: Optional[dict] = None


class LedgerEntryRead(LedgerEntryCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StandardWriteResponse(BaseModel):
    success: bool
    ledger_entry_id: str
    message: str


class DocumentWriteResponse(BaseModel):
    success: bool
    document_id: str
    message: str


class HiringImpactRequest(BaseModel):
    company_id: UUID
    annual_ctc_inr: float
    join_month: str
    equipment_cost: float = 0.0
    onboarding_cost: float = 0.0
    benefits_multiplier: float = 1.0 # factor to apply to salary, e.g. 1.2


class NotificationContactsUpdate(BaseModel):
    email_recipients: Optional[List[str]] = None
    ceo: Optional[str] = None
    founders: Optional[List[str]] = None
    finance: Optional[List[str]] = None
    cto: Optional[str] = None


class AlertThresholdsUpdate(BaseModel):
    critical_months: int
    warning_months: int


# ─── SERIES B+ SCHEMAS ──────────────────────────────────────────────────────

class GLAccountCodeEnum(str, Enum):
    CASH = "1010"
    ACCOUNTS_RECEIVABLE = "1200"
    INVENTORY = "1300"
    PREPAID_EXPENSES = "1400"
    EQUIPMENT = "1500"
    ACCUMULATED_DEPRECIATION = "1501"
    ACCOUNTS_PAYABLE = "2100"
    ACCRUED_EXPENSES = "2200"
    SHORT_TERM_DEBT = "2300"
    LONG_TERM_DEBT = "2400"
    COMMON_STOCK = "3100"
    RETAINED_EARNINGS = "3200"
    PRODUCT_REVENUE = "4100"
    SERVICE_REVENUE = "4200"
    SUBSCRIPTION_REVENUE = "4300"
    PAYROLL_EXPENSE = "5100"
    TECH_COST_AWS = "5200"
    TECH_COST_SAAS = "5210"
    TECH_COST_INFRASTRUCTURE = "5220"
    MARKETING_EXPENSE = "5300"
    OFFICE_EXPENSE = "5400"
    DEPRECIATION_EXPENSE = "5500"


class DepartmentEnum(str, Enum):
    ENGINEERING = "engineering"
    PRODUCT = "product"
    MARKETING = "marketing"
    SALES = "sales"
    OPERATIONS = "operations"
    FINANCE = "finance"
    PEOPLE = "people"
    DESIGN = "design"
    SUPPORT = "support"


class GeneralLedgerCreate(BaseModel):
    company_id: UUID
    account_code: GLAccountCodeEnum
    account_name: str
    transaction_date: date
    debit_amount: float = 0
    credit_amount: float = 0
    description: str
    department: Optional[DepartmentEnum] = None
    product_tag: Optional[LedgerProductTag] = None
    office_tag: Optional[LedgerOfficeTag] = None
    source_ledger_id: Optional[UUID] = None
    source_type: Optional[str] = None
    reference_id: Optional[str] = None


class GeneralLedgerRead(GeneralLedgerCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CustomerCohortCreate(BaseModel):
    company_id: UUID
    cohort_name: str
    cohort_type: str  # "acquisition_month", "product_line", "customer_segment", "geo"
    cohort_value: str  # e.g., "2025-03", "orchard", "enterprise", "india"
    product_tag: Optional[LedgerProductTag] = None
    customer_acquired_date: Optional[date] = None
    customer_count: int = 0
    mrr_total: float = 0
    arr_total: float = 0
    churn_rate: Optional[float] = None
    ltv_estimate: Optional[float] = None
    cac_estimate: Optional[float] = None
    nrr: Optional[float] = None
    gross_margin_pct: Optional[float] = None
    payback_months: Optional[float] = None
    health_score: Optional[float] = None
    tags: Optional[dict] = None


class CustomerCohortRead(CustomerCohortCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DepartmentPLSummary(BaseModel):
    department: str
    total_revenue: float
    total_expense: float
    net_income: float
    margin_pct: float
    headcount: int
    revenue_per_head: float


class CohortHealthMetrics(BaseModel):
    cohort_id: UUID
    cohort_name: str
    health_status: str  # "healthy", "at_risk", "churning"
    nrr: float
    ltv_cac_ratio: float  # LTV / CAC, >3 is good
    payback_months: float
    retention_health: str  # percentage of monthly cohort retained
