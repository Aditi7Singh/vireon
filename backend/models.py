from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, JSON, Date, Boolean, Text, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import datetime
import enum
from database import Base
import uuid

# ─── Enums ──────────────────────────────────────────────────────────────────

class AccountClassification(str, enum.Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"

class AccountType(str, enum.Enum):
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

class ContactType(str, enum.Enum):
    VENDOR = "VENDOR"
    CUSTOMER = "CUSTOMER"
    EMPLOYEE = "EMPLOYEE"
    OTHER = "OTHER"

class InvoiceType(str, enum.Enum):
    ACCOUNTS_RECEIVABLE = "ACCOUNTS_RECEIVABLE"
    ACCOUNTS_PAYABLE = "ACCOUNTS_PAYABLE"

class InvoiceStatus(str, enum.Enum):
    PAID = "PAID"
    OPEN = "OPEN"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    VOID = "VOID"
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    OVERDUE = "OVERDUE"

# ─── Models ──────────────────────────────────────────────────────────────────

class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    industry = Column(String(100))
    stage = Column(String(50))  # seed, series_a, series_b, growth
    initial_cash = Column(Numeric(15, 2), nullable=True) # Changed to nullable
    founding_date = Column(Date)
    effective_tax_rate = Column(Numeric(5, 4), default=0.2500) # Decimals for fast percentage mapping (e.g. 25.00%)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    accounts = relationship("Account", back_populates="company")

class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    remote_id = Column(String(255), unique=True, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    classification = Column(String(50)) # Using string to match simulation more easily
    type = Column(String(50))
    status = Column(String(20), default="active")
    current_balance = Column(Numeric(15, 2), default=0)
    currency = Column(String(3), default="USD")
    remote_created_at = Column(DateTime)
    remote_modified_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    company = relationship("Company", back_populates="accounts")

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    remote_id = Column(String(255), unique=True, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)
    type = Column(String(50))
    email = Column(String(255))
    phone = Column(String(50))
    status = Column(String(20), default="active")
    payment_terms = Column(String(50))
    currency = Column(String(3), default="USD")
    billing_address = Column(JSON)
    shipping_address = Column(JSON)
    tax_number = Column(String(100))
    remote_created_at = Column(DateTime)
    remote_modified_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    remote_id = Column(String(255), unique=True, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    invoice_number = Column(String(100), unique=True, nullable=False)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"))
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    payment_date = Column(Date)
    status = Column(String(50))
    type = Column(String(50))
    sub_total = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), nullable=False)
    amount_paid = Column(Numeric(15, 2), default=0)
    amount_due = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD")
    memo = Column(Text)
    remote_created_at = Column(DateTime)
    remote_modified_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    remote_id = Column(String(255), unique=True, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    transaction_date = Column(Date, nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"))
    total_amount = Column(Numeric(15, 2), nullable=False)
    sub_total = Column(Numeric(15, 2))
    tax_amount = Column(Numeric(15, 2), default=0)
    currency = Column(String(3), default="USD")
    category = Column(String(100))
    payment_method = Column(String(50))
    memo = Column(Text)
    remote_created_at = Column(DateTime)
    remote_modified_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class MonthlyMetric(Base):
    __tablename__ = "monthly_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    metric_month = Column(Date, nullable=False)
    total_revenue = Column(Numeric(15, 2), default=0)
    total_expenses = Column(Numeric(15, 2), default=0)
    net_cash_flow = Column(Numeric(15, 2), default=0)
    burn_rate = Column(Numeric(15, 2), default=0)
    runway_months = Column(Numeric(5, 2), default=0)
    ending_cash = Column(Numeric(15, 2), default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    remote_id = Column(String(255), unique=True, index=True) # Added remote_id
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    anomaly_date = Column(Date, nullable=False)
    severity = Column(String(20))
    type = Column(String(50))
    description = Column(Text, nullable=False)
    expected_value = Column(Numeric(15, 2))
    actual_value = Column(Numeric(15, 2))
    status = Column(String(20), default="open")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    VIEWER = "VIEWER"
    EDITOR = "EDITOR"

class Budget(Base):
    __tablename__ = "budgets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)
    fiscal_year = Column(Integer)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    lines = relationship("BudgetLine", back_populates="budget")

class BudgetLine(Base):
    __tablename__ = "budget_lines"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_id = Column(UUID(as_uuid=True), ForeignKey("budgets.id", ondelete="CASCADE"))
    category = Column(String(100), nullable=False)
    monthly_amount = Column(Numeric(15, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    budget = relationship("Budget", back_populates="lines")

class Forecast(Base):
    __tablename__ = "forecasts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    forecast_date = Column(Date, nullable=False)
    mrr_predicted = Column(Numeric(15, 2))
    cash_predicted = Column(Numeric(15, 2))
    confidence_lower = Column(Numeric(15, 2))
    confidence_upper = Column(Numeric(15, 2))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Document(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    file_name = Column(String(255))
    file_type = Column(String(50)) # receipt, invoice, bank_statement
    status = Column(String(20), default="processed")
    ocr_text = Column(Text)
    extracted_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    email = Column(String(255), unique=True, index=True)
    role = Column(String(50), default=UserRole.VIEWER) # Default to Viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    employee_id = Column(String(50), unique=True, index=True)  # Company employee ID
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True)
    hire_date = Column(Date, nullable=False)
    termination_date = Column(Date)
    salary = Column(Numeric(15, 2), nullable=False)
    pay_frequency = Column(String(50), default="monthly")  # monthly, biweekly, weekly
    job_title = Column(String(100))
    department = Column(String(100))
    status = Column(String(20), default="active")  # active, terminated, on_leave
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    payroll_entries = relationship("PayrollEntry", back_populates="employee")


class PayrollEntry(Base):
    __tablename__ = "payroll_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"))
    pay_period_start = Column(Date, nullable=False)
    pay_period_end = Column(Date, nullable=False)
    gross_pay = Column(Numeric(15, 2), nullable=False)
    federal_tax = Column(Numeric(15, 2), default=0)
    state_tax = Column(Numeric(15, 2), default=0)
    social_security = Column(Numeric(15, 2), default=0)
    medicare = Column(Numeric(15, 2), default=0)
    other_deductions = Column(Numeric(15, 2), default=0)
    net_pay = Column(Numeric(15, 2), nullable=False)
    pay_date = Column(Date, nullable=False)
    status = Column(String(20), default="processed")  # pending, processed, cancelled
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    employee = relationship("Employee", back_populates="payroll_entries")


class Loan(Base):
    __tablename__ = "loans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    loan_name = Column(String(255), nullable=False)
    principal_amount = Column(Numeric(15, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False)  # Annual rate
    term_months = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    loan_type = Column(String(50), default="term_loan")  # term_loan, line_of_credit, etc.
    lender = Column(String(255))
    status = Column(String(20), default="active")  # active, paid_off, defaulted
    remaining_balance = Column(Numeric(15, 2))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    payments = relationship("LoanPayment", back_populates="loan")


class LoanPayment(Base):
    __tablename__ = "loan_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id = Column(UUID(as_uuid=True), ForeignKey("loans.id", ondelete="CASCADE"))
    payment_date = Column(Date, nullable=False)
    payment_amount = Column(Numeric(15, 2), nullable=False)
    principal_paid = Column(Numeric(15, 2), nullable=False)
    interest_paid = Column(Numeric(15, 2), nullable=False)
    remaining_balance = Column(Numeric(15, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    loan = relationship("Loan", back_populates="payments")


class FixedAsset(Base):
    __tablename__ = "fixed_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    asset_name = Column(String(255), nullable=False)
    asset_category = Column(String(100))  # Equipment, Vehicles, Buildings, etc.
    purchase_date = Column(Date, nullable=False)
    purchase_cost = Column(Numeric(15, 2), nullable=False)
    salvage_value = Column(Numeric(15, 2), default=0)
    useful_life_years = Column(Integer, nullable=False)
    depreciation_method = Column(String(50), default="straight_line")  # straight_line, declining_balance
    accumulated_depreciation = Column(Numeric(15, 2), default=0)
    book_value = Column(Numeric(15, 2))
    location = Column(String(255))
    serial_number = Column(String(100))
    status = Column(String(20), default="active")  # active, disposed, fully_depreciated
    disposal_date = Column(Date)
    disposal_value = Column(Numeric(15, 2))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    depreciation_entries = relationship("DepreciationEntry", back_populates="asset")


class DepreciationEntry(Base):
    __tablename__ = "depreciation_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("fixed_assets.id", ondelete="CASCADE"))
    depreciation_date = Column(Date, nullable=False)
    depreciation_amount = Column(Numeric(15, 2), nullable=False)
    accumulated_depreciation = Column(Numeric(15, 2), nullable=False)
    book_value = Column(Numeric(15, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    asset = relationship("FixedAsset", back_populates="depreciation_entries")


class TaxRule(Base):
    __tablename__ = "tax_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    tax_name = Column(String(255), nullable=False) # e.g., "TDS Section 194J", "GST 18%"
    rate = Column(Numeric(5, 4), nullable=False) # e.g., 0.1000 for 10%
    threshold_amount = Column(Numeric(15, 2)) # Min amount for tax to trigger, if applicable
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    base_currency = Column(String(3), nullable=False) # e.g., "USD"
    target_currency = Column(String(3), nullable=False) # e.g., "INR"
    exchange_rate = Column(Numeric(15, 6), nullable=False) # Exact conversion multiplier
    effective_date = Column(Date, nullable=False)
    status = Column(String(50), default="active")
    hire_date = Column(Date)
    termination_date = Column(Date)
    salary = Column(Numeric(15, 2))
    pay_frequency = Column(String(20), default="monthly")
    job_title = Column(String(100))
    department = Column(String(100))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class CloudAccount(Base):
    __tablename__ = "cloud_accounts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    provider = Column(String(50)) # AWS, GCP, Azure
    account_id = Column(String(100))
    account_name = Column(String(255))
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    costs = relationship("CloudCostDetail", back_populates="account")

class CloudCostDetail(Base):
    __tablename__ = "cloud_cost_details"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("cloud_accounts.id", ondelete="CASCADE"))
    service_name = Column(String(100)) # e.g., EC2, RDS, S3
    amount = Column(Numeric(15, 2))
    currency = Column(String(3), default="USD")
    usage_date = Column(Date)
    region = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    account = relationship("CloudAccount", back_populates="costs")

class BankFeed(Base):
    __tablename__ = "bank_feeds"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    bank_name = Column(String(100))
    account_name = Column(String(255))
    account_type = Column(String(50)) # checking, savings, credit_card
    account_number_last4 = Column(String(4))
    currency = Column(String(3), default="USD")
    status = Column(String(20), default="active")
    last_synced_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    transactions = relationship("BankingTransaction", back_populates="feed")

class BankingTransaction(Base):
    __tablename__ = "banking_transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feed_id = Column(UUID(as_uuid=True), ForeignKey("bank_feeds.id", ondelete="CASCADE"))
    transaction_date = Column(Date)
    amount = Column(Numeric(15, 2))
    description = Column(String(255))
    merchant_name = Column(String(255))
    category = Column(String(100)) # e.g., Software, Travel, Food
    is_saas = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    feed = relationship("BankFeed", back_populates="transactions")
