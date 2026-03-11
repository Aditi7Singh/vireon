from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Union
from datetime import datetime, date
from uuid import UUID

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

class SandboxData(BaseModel):
    company: CompanyCreate
    accounts: List[AccountCreate]
    contacts: List[ContactCreate]
    invoices: List[InvoiceCreate]
    expenses: List[ExpenseCreate]
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

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: UUID
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
    query: str
    company_id: UUID
