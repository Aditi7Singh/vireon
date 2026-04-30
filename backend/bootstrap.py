from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import uuid

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

import database
import models
import auth


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
        if not _column_exists(inspector, "companies", "settings"):
            statements.append("ALTER TABLE companies ADD COLUMN settings JSON")
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
        name="Vireon Seeding Lab",
        industry="Agritech SaaS",
        stage="seed",
        initial_cash=Decimal("25000000"),
        founding_date=date(2020, 1, 1),
        effective_tax_rate=Decimal("0.25"),
        notification_contacts={"email": ["outlandishaditi11@gmail.com", "admin@vireon.ai", "finley@vireon.ai"]},
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
        txn_date = date.today().replace(day=1)
        seeds = [
            # Revenue by project
            {
                "amount": Decimal("620000"),
                "entry_type": models.LedgerEntryType.CREDIT,
                "category": models.LedgerCategory.REVENUE,
                "product_tag": models.LedgerProductTag.SPROUTS,
                "office_tag": models.LedgerOfficeTag.GANGAVATHI,
                "description": "Sprout subscription revenue",
                "department": "sales",
                "source": models.LedgerSource.ERPNEXT,
                "entered_by_role": models.LedgerEnteredByRole.SYSTEM,
            },
            {
                "amount": Decimal("710000"),
                "entry_type": models.LedgerEntryType.CREDIT,
                "category": models.LedgerCategory.REVENUE,
                "product_tag": models.LedgerProductTag.ORCHARD,
                "office_tag": models.LedgerOfficeTag.BENGALURU,
                "description": "Orchard enterprise contracts",
                "department": "sales",
                "source": models.LedgerSource.ERPNEXT,
                "entered_by_role": models.LedgerEnteredByRole.SYSTEM,
            },
            {
                "amount": Decimal("380000"),
                "entry_type": models.LedgerEntryType.CREDIT,
                "category": models.LedgerCategory.REVENUE,
                "product_tag": models.LedgerProductTag.AI_LAB,
                "office_tag": models.LedgerOfficeTag.REMOTE,
                "description": "AI Lab pilot program revenue",
                "department": "ai_research",
                "source": models.LedgerSource.ERPNEXT,
                "entered_by_role": models.LedgerEnteredByRole.SYSTEM,
            },
            # Salary / payroll
            {
                "amount": Decimal("890000"),
                "entry_type": models.LedgerEntryType.DEBIT,
                "category": models.LedgerCategory.PAYROLL,
                "product_tag": models.LedgerProductTag.SPROUTS,
                "office_tag": models.LedgerOfficeTag.GANGAVATHI,
                "description": "Sprout team payroll",
                "department": "engineering",
                "source": models.LedgerSource.MANUAL_FINANCE,
                "entered_by_role": models.LedgerEnteredByRole.FINANCE,
            },
            {
                "amount": Decimal("960000"),
                "entry_type": models.LedgerEntryType.DEBIT,
                "category": models.LedgerCategory.PAYROLL,
                "product_tag": models.LedgerProductTag.ORCHARD,
                "office_tag": models.LedgerOfficeTag.BENGALURU,
                "description": "Orchard team payroll",
                "department": "engineering",
                "source": models.LedgerSource.MANUAL_FINANCE,
                "entered_by_role": models.LedgerEnteredByRole.FINANCE,
            },
            {
                "amount": Decimal("730000"),
                "entry_type": models.LedgerEntryType.DEBIT,
                "category": models.LedgerCategory.PAYROLL,
                "product_tag": models.LedgerProductTag.AI_LAB,
                "office_tag": models.LedgerOfficeTag.REMOTE,
                "description": "AI Lab payroll",
                "department": "ai_research",
                "source": models.LedgerSource.MANUAL_FINANCE,
                "entered_by_role": models.LedgerEnteredByRole.FINANCE,
            },
            # Infrastructure / cloud
            {
                "amount": Decimal("320000"),
                "entry_type": models.LedgerEntryType.DEBIT,
                "category": models.LedgerCategory.TECH_COST,
                "product_tag": models.LedgerProductTag.AI_LAB,
                "office_tag": models.LedgerOfficeTag.REMOTE,
                "description": "GPU inference cluster and model serving",
                "department": "platform",
                "source": models.LedgerSource.AWS_BILLING,
                "entered_by_role": models.LedgerEnteredByRole.CTO,
            },
            {
                "amount": Decimal("180000"),
                "entry_type": models.LedgerEntryType.DEBIT,
                "category": models.LedgerCategory.TECH_COST,
                "product_tag": models.LedgerProductTag.SHARED,
                "office_tag": models.LedgerOfficeTag.BENGALURU,
                "description": "Shared cloud, observability and CI tooling",
                "department": "platform",
                "source": models.LedgerSource.AWS_BILLING,
                "entered_by_role": models.LedgerEnteredByRole.CTO,
            },
            # Overheads / infra
            {
                "amount": Decimal("210000"),
                "entry_type": models.LedgerEntryType.DEBIT,
                "category": models.LedgerCategory.OFFICE_EXPENSE,
                "product_tag": models.LedgerProductTag.UNALLOCATED,
                "office_tag": models.LedgerOfficeTag.BENGALURU,
                "description": "Bengaluru HQ rent, internet and utilities",
                "department": "operations",
                "source": models.LedgerSource.MANUAL_FINANCE,
                "entered_by_role": models.LedgerEnteredByRole.FINANCE,
            },
            {
                "amount": Decimal("95000"),
                "entry_type": models.LedgerEntryType.DEBIT,
                "category": models.LedgerCategory.NON_TECH_COST,
                "product_tag": models.LedgerProductTag.SHARED,
                "office_tag": models.LedgerOfficeTag.BENGALURU,
                "description": "Legal, accounting and compliance overhead",
                "department": "finance",
                "source": models.LedgerSource.MANUAL_FINANCE,
                "entered_by_role": models.LedgerEnteredByRole.FINANCE,
            },
        ]

        for seed in seeds:
            db.add(
                models.FinancialLedgerEntry(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    transaction_date=txn_date,
                    amount=seed["amount"],
                    currency="INR",
                    amount_inr=seed["amount"],
                    entry_type=seed["entry_type"],
                    category=seed["category"],
                    product_tag=seed["product_tag"],
                    office_tag=seed["office_tag"],
                    source=seed["source"],
                    description=seed["description"],
                    entered_by_role=seed["entered_by_role"],
                    is_recurring=True,
                    department=seed["department"],
                )
            )

    db.commit()


_FULL_ROSTER = [
    # code,      first,     last,       email,                            title,                          dept,          salary,           hire_date
    ("EMP-001", "Aditi",   "Singh",    "outlandishaditi11@gmail.com",    "Chief Executive Officer",      "leadership",  Decimal("420000"), date(2023, 6, 1)),
    ("EMP-002", "Ravi",    "Kumar",    "ravi@vireon.ai",                 "Head of Finance (CFO)",        "finance",     Decimal("280000"), date(2023, 8, 1)),
    ("EMP-003", "Nina",    "Roy",      "nina@vireon.ai",                 "VP Operations",                "operations",  Decimal("260000"), date(2023, 9, 1)),
    # Sprout team (Gangavathi)
    ("EMP-004", "Karan",   "Patil",    "karan@vireon.ai",                "Sprout Tech Lead",             "engineering", Decimal("230000"), date(2023, 10, 1)),
    ("EMP-005", "Priya",   "Reddy",    "priya.r@vireon.ai",              "ML Engineer – Sprout",         "engineering", Decimal("210000"), date(2024, 1, 15)),
    ("EMP-006", "Sanjay",  "Nair",     "sanjay@vireon.ai",               "Backend Engineer – Sprout",    "engineering", Decimal("195000"), date(2024, 2, 1)),
    ("EMP-007", "Meena",   "Iyer",     "meena@vireon.ai",                "Product Manager – Sprout",     "product",     Decimal("220000"), date(2024, 3, 1)),
    ("EMP-008", "Arjun",   "Das",      "arjun@vireon.ai",                "Field IoT Engineer",           "engineering", Decimal("180000"), date(2024, 4, 1)),
    # Orchard team (Bengaluru)
    ("EMP-009", "Sam",     "Jain",     "sam@vireon.ai",                  "Orchard Lead Engineer",        "sales",       Decimal("240000"), date(2023, 11, 1)),
    ("EMP-010", "Ananya",  "Krishnan", "ananya@vireon.ai",               "Senior Backend Engineer",      "sales",       Decimal("215000"), date(2024, 1, 10)),
    ("EMP-011", "Vikram",  "Sharma",   "vikram@vireon.ai",               "Enterprise Sales Manager",     "sales",       Decimal("235000"), date(2024, 2, 15)),
    ("EMP-012", "Pooja",   "Mehta",    "pooja@vireon.ai",                "Frontend Engineer",            "operations",  Decimal("190000"), date(2024, 3, 15)),
    ("EMP-013", "Rahul",   "Gupta",    "rahul@vireon.ai",                "DevOps Engineer",              "operations",  Decimal("200000"), date(2024, 4, 15)),
    ("EMP-014", "Divya",   "Pillai",   "divya@vireon.ai",                "UX/Product Designer",          "product",     Decimal("185000"), date(2024, 5, 1)),
    # AI Lab (Remote)
    ("EMP-015", "Ira",     "Menon",    "ira@vireon.ai",                  "AI Research Lead",             "ai_research", Decimal("290000"), date(2023, 9, 1)),
    ("EMP-016", "Zara",    "Ahmed",    "zara@vireon.ai",                 "ML Researcher – NLP",          "ai_research", Decimal("260000"), date(2024, 1, 20)),
    ("EMP-017", "Neel",    "Kapoor",   "neel@vireon.ai",                 "ML Researcher – Vision",       "ai_research", Decimal("255000"), date(2024, 2, 20)),
    ("EMP-018", "Tanu",    "Bose",     "tanu@vireon.ai",                 "Data Engineer – AI Lab",       "platform",    Decimal("210000"), date(2024, 3, 20)),
]


def _seed_employees_and_payroll_if_empty(db: Session, company_id) -> None:
    for row in _FULL_ROSTER:
        code, first, last, email, title, dept, salary, hire_dt = row
        if db.query(models.Employee).filter(models.Employee.employee_id == code).first():
            continue
        db.add(
            models.Employee(
                id=uuid.uuid4(),
                company_id=company_id,
                employee_id=code,
                first_name=first,
                last_name=last,
                email=email,
                hire_date=hire_dt,
                salary=salary,
                pay_frequency="monthly",
                job_title=title,
                department=dept,
                status="active",
            )
        )
    db.commit()

    # Seed 6 months of payroll history
    today = date.today()
    employees = db.query(models.Employee).filter(
        models.Employee.company_id == company_id,
        models.Employee.status == "active",
    ).all()

    for offset in range(5, -1, -1):
        pay_month = (today.replace(day=1) - timedelta(days=offset * 31)).replace(day=1)
        year, month = pay_month.year, pay_month.month
        next_m = month + 1 if month < 12 else 1
        next_y = year if month < 12 else year + 1
        period_end = date(next_y, next_m, 1) - timedelta(days=1)
        pay_dt = period_end

        for employee in employees:
            exists = db.query(models.PayrollEntry).filter(
                models.PayrollEntry.employee_id == employee.id,
                models.PayrollEntry.pay_period_start == pay_month,
            ).first()
            if exists:
                continue

            gross = Decimal(employee.salary)
            # India: PF 12% + professional tax ~200
            pf = (gross * Decimal("0.12")).quantize(Decimal("1.00"))
            pt = Decimal("200")
            net = (gross - pf - pt).quantize(Decimal("1.00"))
            db.add(
                models.PayrollEntry(
                    id=uuid.uuid4(),
                    employee_id=employee.id,
                    pay_period_start=pay_month,
                    pay_period_end=period_end,
                    gross_pay=gross,
                    federal_tax=pf,      # mapped to PF contribution
                    state_tax=pt,        # mapped to Professional Tax
                    net_pay=net,
                    pay_date=pay_dt,
                    status="processed",
                    department=employee.department,
                )
            )
    db.commit()


def _seed_historical_ledger(db: Session, company_id) -> None:
    """Seed 6 months of realistic ledger entries per project (idempotent)."""
    today = date.today()

    monthly_seeds = [
        # (product_tag, category, entry_type, base_amount, description, department, source, entered_by)
        ("sprouts", "revenue", "credit", Decimal("560000"),  "Sprout subscription MRR",        "sales",       "erpnext",        "system"),
        ("orchard", "revenue", "credit", Decimal("640000"),  "Orchard enterprise contracts",   "sales",       "erpnext",        "system"),
        ("ai_lab",  "revenue", "credit", Decimal("310000"),  "AI Lab pilot licensing",          "ai_research", "erpnext",        "system"),
        ("sprouts", "payroll", "debit",  Decimal("810000"),  "Sprout team payroll",             "engineering", "manual_finance", "finance"),
        ("orchard", "payroll", "debit",  Decimal("880000"),  "Orchard team payroll",            "sales",       "manual_finance", "finance"),
        ("ai_lab",  "payroll", "debit",  Decimal("755000"),  "AI Lab payroll",                  "ai_research", "manual_finance", "finance"),
        ("ai_lab",  "tech_cost","debit", Decimal("290000"),  "GPU cluster & model serving",     "platform",    "aws_billing",    "cto"),
        ("shared",  "tech_cost","debit", Decimal("165000"),  "Shared cloud & CI tooling",       "platform",    "aws_billing",    "cto"),
        ("unallocated","office_expense","debit",Decimal("195000"),"HQ rent & utilities BLR",   "operations",  "manual_finance", "finance"),
        ("shared",  "non_tech_cost","debit",Decimal("88000"),"Legal & compliance overhead",    "finance",     "manual_finance", "finance"),
        ("orchard", "marketing","debit", Decimal("95000"),   "Paid campaigns & events",         "sales",       "manual_marketing","finance"),
    ]

    for offset in range(5, -1, -1):
        txn_month = (today.replace(day=1) - timedelta(days=offset * 31)).replace(day=1)
        growth = Decimal(str(round(0.68 + (5 - offset) * 0.064, 3)))

        for (tag, cat, etype, base_amt, desc, dept, src, role) in monthly_seeds:
            exists = db.query(models.FinancialLedgerEntry).filter(
                models.FinancialLedgerEntry.company_id == company_id,
                models.FinancialLedgerEntry.product_tag == tag,
                models.FinancialLedgerEntry.category == cat,
                models.FinancialLedgerEntry.transaction_date == txn_month,
                models.FinancialLedgerEntry.description == desc,
            ).first()
            if exists:
                continue

            amount = (base_amt * growth).quantize(Decimal("1.00"))
            db.add(
                models.FinancialLedgerEntry(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    transaction_date=txn_month,
                    amount=amount,
                    currency="INR",
                    amount_inr=amount,
                    entry_type=models.LedgerEntryType(etype),
                    category=models.LedgerCategory(cat),
                    product_tag=models.LedgerProductTag(tag),
                    office_tag=models.LedgerOfficeTag("bengaluru" if tag == "orchard" else ("gangavathi" if tag == "sprouts" else "remote")),
                    source=models.LedgerSource(src),
                    description=desc,
                    entered_by_role=models.LedgerEnteredByRole(role),
                    is_recurring=True,
                    department=dept,
                )
            )
    db.commit()


def _seed_presentation_users(db: Session) -> None:
    users = [
        {
            "username": "aditi_ceo",
            "email": "outlandishaditi11@gmail.com",
            "role": models.UserRole.CEO.value,
            "password": "VireonCEO@2026",
        },
        {
            "username": "vireon_admin",
            "email": "admin@vireon.ai",
            "role": models.UserRole.ADMIN.value,
            "password": "VireonAdmin@2026",
        },
        {
            "username": "finley_cfo",
            "email": "finley@vireon.ai",
            "role": models.UserRole.CFO.value,
            "password": "FinleyCFO@2026",
        },
    ]

    for user in users:
        existing = (
            db.query(models.User)
            .filter((models.User.username == user["username"]) | (models.User.email == user["email"]))
            .first()
        )
        if existing:
            existing.role = user["role"]
            existing.is_active = True
            continue

        db.add(
            models.User(
                id=uuid.uuid4(),
                username=user["username"],
                email=user["email"],
                hashed_password=auth.get_password_hash(user["password"]),
                role=user["role"],
                is_active=True,
            )
        )

    db.commit()


def run_bootstrap() -> None:
    """Deterministic local bootstrap used on app startup."""
    ensure_sqlite_compatibility()
    try:
        db = database.SessionLocal()
    except Exception as e:
        print(f"⚠️  Bootstrap: Could not connect to database ({e}). Skipping bootstrap.")
        return
    
    try:
        company = _seed_default_company(db)
        _seed_presentation_users(db)
        _seed_monthly_metrics_if_empty(db, company.id)
        _seed_exchange_rates_if_empty(db)
        _seed_transactions_if_empty(db, company.id)
        _seed_employees_and_payroll_if_empty(db, company.id)
        _seed_historical_ledger(db, company.id)
    except Exception as e:
        print(f"⚠️  Bootstrap error (non-fatal): {e}")
    finally:
        db.close()
