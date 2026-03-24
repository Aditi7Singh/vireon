#!/usr/bin/env python3
"""Seed realistic operational data for the active/default company.

This script is idempotent for records marked with the `seed_operational_v2` tag
or `SEED-OPS-V2-*` references.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
import sys

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from database import SessionLocal, Base, engine
import models
from services.tax_service import create_quarterly_liability


def month_start(offset: int) -> date:
    base = date.today().replace(day=1)
    y = base.year
    m = base.month - offset
    while m <= 0:
        m += 12
        y -= 1
    return date(y, m, 1)


def ensure_company(db):
    company = db.query(models.Company).order_by(models.Company.created_at.asc()).first()
    if company:
        return company
    company = models.Company(
        id=uuid.uuid4(),
        name="Vireon Demo",
        industry="Technology",
        stage="seed",
        initial_cash=Decimal("3000000"),
        notification_contacts={
            "ceo": "ceo@vireon.ai",
            "finance": ["finance@vireon.ai"],
            "email_recipients": ["ops@vireon.ai"],
        },
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def upsert_monthly_metrics(db, company_id):
    for i in range(5, -1, -1):
        m = month_start(i)
        existing = (
            db.query(models.MonthlyMetric)
            .filter(models.MonthlyMetric.company_id == company_id, models.MonthlyMetric.metric_month == m)
            .first()
        )
        if existing:
            continue
        revenue = Decimal(str(650000 + (5 - i) * 25000))
        expenses = Decimal(str(560000 + (5 - i) * 18000))
        burn = expenses - revenue
        metric = models.MonthlyMetric(
            id=uuid.uuid4(),
            company_id=company_id,
            metric_month=m,
            total_revenue=revenue,
            total_expenses=expenses,
            total_tax_liability=Decimal("0"),
            net_cash_flow=revenue - expenses,
            burn_rate=burn if burn > 0 else Decimal("0"),
            runway_months=Decimal("16.0"),
            ending_cash=Decimal("4200000"),
        )
        db.add(metric)


def upsert_ledger_entries(db, company_id):
    # Per-month category mix to prevent 0% cards.
    monthly_rows = [
        (models.LedgerCategory.REVENUE, models.LedgerEntryType.CREDIT, Decimal("850000"), "Revenue"),
        (models.LedgerCategory.PAYROLL, models.LedgerEntryType.DEBIT, Decimal("320000"), "Payroll"),
        (models.LedgerCategory.MARKETING, models.LedgerEntryType.DEBIT, Decimal("125000"), "Marketing"),
        (models.LedgerCategory.OFFICE_EXPENSE, models.LedgerEntryType.DEBIT, Decimal("80000"), "Office"),
        (models.LedgerCategory.HIRING, models.LedgerEntryType.DEBIT, Decimal("90000"), "Hiring"),
        (models.LedgerCategory.TECH_COST, models.LedgerEntryType.DEBIT, Decimal("95000"), "AWS"),
        (models.LedgerCategory.TECH_COST, models.LedgerEntryType.DEBIT, Decimal("47000"), "Licenses"),
        (models.LedgerCategory.TECH_COST, models.LedgerEntryType.DEBIT, Decimal("36000"), "SaaS"),
        (models.LedgerCategory.MISC, models.LedgerEntryType.DEBIT, Decimal("22000"), "Misc"),
    ]

    for i in range(2, -1, -1):
        m = month_start(i)
        tx_date = m + timedelta(days=10)
        for idx, (cat, etype, amt, label) in enumerate(monthly_rows):
            ref = f"SEED-OPS-V2-{m.strftime('%Y%m')}-{idx}"
            exists = db.query(models.FinancialLedgerEntry).filter(models.FinancialLedgerEntry.reference_id == ref).first()
            if exists:
                continue

            tags = {"seed": "seed_operational_v2"}
            if label == "AWS":
                tags.update({"cost_type": "aws_compute", "vendor": "aws"})
            elif label == "Licenses":
                tags.update({"cost_type": "licenses", "vendor": "atlassian"})
            elif label == "SaaS":
                tags.update({"cost_type": "saas_subscription", "vendor": "notion"})
            elif cat == models.LedgerCategory.HIRING:
                tags.update({"monthly_cost": 90000, "is_confirmed": False, "department": "engineering"})

            row = models.FinancialLedgerEntry(
                id=uuid.uuid4(),
                company_id=company_id,
                transaction_date=tx_date,
                amount=amt,
                currency="INR",
                amount_inr=amt,
                entry_type=etype,
                category=cat,
                product_tag=models.LedgerProductTag.SHARED,
                office_tag=models.LedgerOfficeTag.BENGALURU if cat == models.LedgerCategory.OFFICE_EXPENSE else models.LedgerOfficeTag.NA,
                source=models.LedgerSource.SANDBOX,
                reference_id=ref,
                reference_type="seed",
                description=f"Seeded {label} for {m.strftime('%Y-%m')}",
                entered_by_role=models.LedgerEnteredByRole.SYSTEM,
                is_recurring=cat in {
                    models.LedgerCategory.PAYROLL,
                    models.LedgerCategory.MARKETING,
                    models.LedgerCategory.OFFICE_EXPENSE,
                    models.LedgerCategory.TECH_COST,
                },
                tags=tags,
            )
            db.add(row)


def upsert_tax_inputs(db, company_id):
    # Ensure at least one active employee and payroll entries this quarter.
    emp = db.query(models.Employee).filter(models.Employee.company_id == company_id).first()
    if not emp:
        emp = models.Employee(
            id=uuid.uuid4(),
            company_id=company_id,
            employee_id="EMP-OPS-001",
            first_name="Riya",
            last_name="Sharma",
            email="riya.sharma@vireon.ai",
            hire_date=date.today() - timedelta(days=420),
            salary=Decimal("180000"),
            department="Engineering",
            status="active",
        )
        db.add(emp)
        db.flush()

    quarter_start_month = ((date.today().month - 1) // 3) * 3 + 1
    q_start = date(date.today().year, quarter_start_month, 1)
    for j in range(3):
        period_start = (q_start + timedelta(days=31 * j)).replace(day=1)
        period_end = (period_start + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        pay_date = min(period_end, period_start + timedelta(days=27))
        p_ref = f"SEED-OPS-V2-PAY-{period_start.strftime('%Y%m')}"
        exists_pay = (
            db.query(models.PayrollEntry)
            .filter(models.PayrollEntry.employee_id == emp.id, models.PayrollEntry.pay_period_start == period_start)
            .first()
        )
        if not exists_pay:
            gross = Decimal("180000")
            tax = Decimal("14500")
            net = gross - tax
            db.add(
                models.PayrollEntry(
                    id=uuid.uuid4(),
                    employee_id=emp.id,
                    pay_period_start=period_start,
                    pay_period_end=period_end,
                    gross_pay=gross,
                    federal_tax=tax,
                    state_tax=Decimal("0"),
                    social_security=Decimal("0"),
                    medicare=Decimal("0"),
                    other_deductions=Decimal("0"),
                    net_pay=net,
                    pay_date=pay_date,
                    status="processed",
                    department="engineering",
                )
            )

    # Ensure invoices in current quarter use the expected type string.
    for j in range(3):
        issue = (q_start + timedelta(days=31 * j)).replace(day=8)
        inv_num = f"INV-OPS-V2-{issue.strftime('%Y%m')}"
        exists_inv = db.query(models.Invoice).filter(models.Invoice.invoice_number == inv_num).first()
        if exists_inv:
            # Normalize type for old rows so tax summary can count it.
            exists_inv.type = "ACCOUNTS_RECEIVABLE"
            exists_inv.status = exists_inv.status or "PAID"
            continue

        sub = Decimal("420000")
        gst = (sub * Decimal("0.18")).quantize(Decimal("0.01"))
        total = sub + gst
        db.add(
            models.Invoice(
                id=uuid.uuid4(),
                company_id=company_id,
                invoice_number=inv_num,
                issue_date=issue,
                due_date=issue + timedelta(days=30),
                status="PAID",
                type="ACCOUNTS_RECEIVABLE",
                sub_total=sub,
                tax_amount=gst,
                total_amount=total,
                amount_paid=total,
                amount_due=Decimal("0"),
                currency="INR",
                memo="Seeded quarterly services invoice",
            )
        )


def ensure_recommendations(db, company_id):
    month = date.today().strftime("%Y-%m")
    exists = (
        db.query(models.RecommendationReport)
        .filter(models.RecommendationReport.company_id == company_id, models.RecommendationReport.month == month)
        .first()
    )
    if exists:
        return
    db.add(
        models.RecommendationReport(
            id=uuid.uuid4(),
            company_id=company_id,
            month=month,
            recommendations=[
                {"title": "Trim non-performing campaigns", "finding": "Marketing spend rose faster than attributable revenue.", "priority": "medium"},
                {"title": "Negotiate infra commitments", "finding": "AWS spend can be reduced with savings plans.", "priority": "medium"},
                {"title": "Sequence hiring by pipeline", "finding": "Stage hiring against quarterly conversion targets.", "priority": "high"},
            ],
            runway_at_generation=Decimal("14.5"),
            status=models.RecommendationStatus.ACTIVE,
        )
    )


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        company = ensure_company(db)
        upsert_monthly_metrics(db, company.id)
        upsert_ledger_entries(db, company.id)
        upsert_tax_inputs(db, company.id)
        ensure_recommendations(db, company.id)
        db.commit()

        # Ensure current quarter liability row exists/refreshes.
        today = date.today()
        quarter = (today.month - 1) // 3 + 1
        liability = create_quarterly_liability(db, company.id, today.year, quarter)
        # Keep one open liability so UI always shows due items and next due date.
        liability.paid_amount = Decimal("0")
        liability.remaining_balance = liability.total_liability
        liability.status = "pending"
        liability.payment_reference = None
        liability.last_payment_date = None
        db.commit()

        print("✅ Operational seed complete")
        print(f"   Company ID: {company.id}")
        print(f"   Quarter: {today.year} Q{quarter}")
    except Exception as exc:
        db.rollback()
        print(f"❌ Seed failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()