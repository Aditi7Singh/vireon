from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import uuid

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

import database
import models


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _column_exists(inspector, table_name: str, column_name: str) -> bool:
    if not _table_exists(inspector, table_name):
        return False
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def ensure_sqlite_compatibility() -> None:
    """Adds critical missing columns in reused local SQLite DBs.

    This prevents startup/runtime errors when model definitions evolve but old
    SQLite files remain mounted.
    """
    if database.engine.dialect.name != "sqlite":
        return

    inspector = inspect(database.engine)
    statements: list[str] = []

    if _table_exists(inspector, "companies"):
        if not _column_exists(inspector, "companies", "notification_contacts"):
            statements.append("ALTER TABLE companies ADD COLUMN notification_contacts JSON")
        if not _column_exists(inspector, "companies", "alert_thresholds"):
            statements.append("ALTER TABLE companies ADD COLUMN alert_thresholds JSON")
        if not _column_exists(inspector, "companies", "updated_at"):
            statements.append("ALTER TABLE companies ADD COLUMN updated_at DATETIME")
        if not _column_exists(inspector, "companies", "last_sync_erpnext"):
            statements.append("ALTER TABLE companies ADD COLUMN last_sync_erpnext DATETIME")
        if not _column_exists(inspector, "companies", "last_sync_merge"):
            statements.append("ALTER TABLE companies ADD COLUMN last_sync_merge DATETIME")

    if _table_exists(inspector, "expenses") and not _column_exists(inspector, "expenses", "department"):
        statements.append("ALTER TABLE expenses ADD COLUMN department VARCHAR(50)")

    if _table_exists(inspector, "monthly_metrics") and not _column_exists(inspector, "monthly_metrics", "total_tax_liability"):
        statements.append("ALTER TABLE monthly_metrics ADD COLUMN total_tax_liability NUMERIC(15,2) DEFAULT 0")

    if _table_exists(inspector, "financial_ledger_entries") and not _column_exists(inspector, "financial_ledger_entries", "department"):
        statements.append("ALTER TABLE financial_ledger_entries ADD COLUMN department VARCHAR(50)")

    if _table_exists(inspector, "payroll_entries") and not _column_exists(inspector, "payroll_entries", "department"):
        statements.append("ALTER TABLE payroll_entries ADD COLUMN department VARCHAR(50)")

    if _table_exists(inspector, "documents") and not _column_exists(inspector, "documents", "structured_data"):
        statements.append("ALTER TABLE documents ADD COLUMN structured_data JSON")

    if not statements:
        return

    with database.engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


def _seed_default_company(db: Session) -> models.Company:
    company = db.query(models.Company).first()
    if company:
        return company

    company = models.Company(
        id=uuid.uuid4(),
        name="Seedling Labs",
        industry="Agritech SaaS",
        stage="series_a",
        initial_cash=Decimal("25000000"),
        founding_date=date(2020, 1, 1),
        effective_tax_rate=Decimal("0.25"),
        notification_contacts={"email": ["founder@seedlinglabs.io"]},
        alert_thresholds={"critical_months": 3, "warning_months": 6},
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def _seed_monthly_metrics_if_empty(db: Session, company_id) -> None:
    has_metrics = db.query(models.MonthlyMetric).filter(models.MonthlyMetric.company_id == company_id).first()
    if has_metrics:
        return

    today = date.today().replace(day=1)
    sample = models.MonthlyMetric(
        id=uuid.uuid4(),
        company_id=company_id,
        metric_month=today,
        total_revenue=Decimal("420000"),
        total_expenses=Decimal("780000"),
        net_cash_flow=Decimal("-360000"),
        burn_rate=Decimal("360000"),
        runway_months=Decimal("8.5"),
        ending_cash=Decimal("25000000"),
        created_at=datetime.utcnow(),
    )
    db.add(sample)
    db.commit()


def _seed_exchange_rates_if_empty(db: Session) -> None:
    has_rates = db.query(models.ExchangeRate).first()
    if has_rates:
        return

    base_date = date.today()
    rates = [
        ("USD", "INR", Decimal("83.000000")),
        ("EUR", "INR", Decimal("90.000000")),
        ("GBP", "INR", Decimal("105.000000")),
    ]
    for base, target, rate in rates:
        db.add(
            models.ExchangeRate(
                id=uuid.uuid4(),
                base_currency=base,
                target_currency=target,
                exchange_rate=rate,
                effective_date=base_date,
                status="active",
            )
        )
    db.commit()


def _seed_transactions_if_empty(db: Session, company_id) -> None:
    has_expenses = db.query(models.Expense).filter(models.Expense.company_id == company_id).first()
    if not has_expenses:
        db.add(
            models.Expense(
                id=uuid.uuid4(),
                company_id=company_id,
                transaction_date=date.today(),
                total_amount=Decimal("185000"),
                sub_total=Decimal("185000"),
                tax_amount=Decimal("0"),
                currency="INR",
                category="Cloud Infrastructure",
                payment_method="bank_transfer",
                memo="AWS monthly bill",
                department="engineering",
            )
        )

    has_ledger = db.query(models.FinancialLedgerEntry).filter(models.FinancialLedgerEntry.company_id == company_id).first()
    if not has_ledger:
        db.add(
            models.FinancialLedgerEntry(
                id=uuid.uuid4(),
                company_id=company_id,
                transaction_date=date.today(),
                amount=Decimal("420000"),
                currency="INR",
                amount_inr=Decimal("420000"),
                entry_type=models.LedgerEntryType.CREDIT,
                category=models.LedgerCategory.REVENUE,
                product_tag=models.LedgerProductTag.ORCHARD,
                office_tag=models.LedgerOfficeTag.BENGALURU,
                source=models.LedgerSource.SANDBOX,
                description="Bootstrap monthly revenue",
                entered_by_role=models.LedgerEnteredByRole.SYSTEM,
                is_recurring=True,
                department="sales",
            )
        )

    db.commit()


def run_bootstrap() -> None:
    """Deterministic local bootstrap used on app startup."""
    ensure_sqlite_compatibility()
    db = database.SessionLocal()
    try:
        company = _seed_default_company(db)
        _seed_monthly_metrics_if_empty(db, company.id)
        _seed_exchange_rates_if_empty(db)
        _seed_transactions_if_empty(db, company.id)
    finally:
        db.close()
