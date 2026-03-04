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

class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    remote_id = Column(String(255), unique=True, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255))
    department = Column(String(100))
    job_title = Column(String(100))
    salary = Column(Numeric(15, 2))
    pay_frequency = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

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

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    email = Column(String(255), unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
