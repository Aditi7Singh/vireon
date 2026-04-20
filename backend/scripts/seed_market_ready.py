#!/usr/bin/env python3
"""
Market-Ready Comprehensive Seed Script for Vireon
Creates realistic startup data: vendors, customers, AR/AP invoices, POs,
employees, fixed assets, customer cohorts, health scores, anomalies, and GL entries.

Idempotent: safe to run multiple times — uses reference IDs to skip existing records.
Company profile: Orchard Analytics Inc. — B2B SaaS / FinTech — Series A
"""

from __future__ import annotations

import uuid
import hashlib
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
import sys

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from database import SessionLocal, Base, engine
import models


# ─── Helpers ─────────────────────────────────────────────────────────────────

def d(offset_months: int, day: int = 1) -> date:
    """Return a date N months before today."""
    today = date.today()
    y, m = today.year, today.month - offset_months
    while m <= 0:
        m += 12
        y -= 1
    return date(y, m, min(day, 28))


def mk_id() -> uuid.UUID:
    return uuid.uuid4()


def skip_if(db, model, **kwargs) -> bool:
    return db.query(model).filter_by(**kwargs).first() is not None


# ─── Company ─────────────────────────────────────────────────────────────────

def ensure_company(db):
    company = db.query(models.Company).order_by(models.Company.created_at).first()
    if company:
        # Update to match our market-ready profile
        company.name = "Orchard Analytics Inc."
        company.industry = "B2B SaaS / FinTech"
        company.stage = "series_a"
        company.initial_cash = Decimal("2840000")
        db.flush()
        return company
    company = models.Company(
        id=mk_id(),
        name="Orchard Analytics Inc.",
        industry="B2B SaaS / FinTech",
        stage="series_a",
        initial_cash=Decimal("2840000"),
        founding_date=date(2023, 1, 15),
        effective_tax_rate=Decimal("0.2500"),
        notification_contacts={
            "ceo": "aditi@orchardanalytics.com",
            "finance": ["finance@orchardanalytics.com"],
        },
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


# ─── Vendors ─────────────────────────────────────────────────────────────────

VENDORS = [
    {"ref": "VENDOR-AWS",         "name": "Amazon Web Services",     "email": "aws-billing@amazon.com",      "phone": "+1-800-379-7441", "terms": "Net 30",    "category": "Infrastructure"},
    {"ref": "VENDOR-SALESFORCE",  "name": "Salesforce",               "email": "billing@salesforce.com",      "phone": "+1-800-667-6389", "terms": "Net 30",    "category": "CRM / SaaS"},
    {"ref": "VENDOR-COOLEY",      "name": "Cooley LLP",               "email": "billing@cooley.com",          "phone": "+1-650-843-5000", "terms": "Net 15",    "category": "Legal"},
    {"ref": "VENDOR-WEWORK",      "name": "WeWork",                   "email": "enterprise@wework.com",       "phone": "+1-646-389-3922", "terms": "Net 1",     "category": "Office Space"},
    {"ref": "VENDOR-DATADOG",     "name": "Datadog",                  "email": "billing@datadoghq.com",       "phone": "+1-866-329-4466", "terms": "Net 30",    "category": "Monitoring"},
    {"ref": "VENDOR-GREENHOUSE",  "name": "Greenhouse Software",      "email": "billing@greenhouse.io",       "phone": "+1-646-677-7060", "terms": "Net 30",    "category": "HR / ATS"},
    {"ref": "VENDOR-RIPPLING",    "name": "Rippling",                 "email": "billing@rippling.com",        "phone": "+1-415-854-0048", "terms": "Auto",      "category": "HR / Payroll"},
    {"ref": "VENDOR-STRIPE",      "name": "Stripe Inc.",              "email": "billing@stripe.com",          "phone": "+1-888-228-7434", "terms": "Net 30",    "category": "Payment Processing"},
    {"ref": "VENDOR-OPENAI",      "name": "OpenAI",                   "email": "billing@openai.com",          "phone": "+1-415-000-0000", "terms": "Net 30",    "category": "AI / ML"},
    {"ref": "VENDOR-NOTION",      "name": "Notion Labs",              "email": "billing@notion.so",           "phone": "+1-888-888-2946", "terms": "Auto",      "category": "Productivity"},
]

def seed_vendors(db, company_id) -> dict:
    """Returns {ref: contact_id}"""
    vendor_ids = {}
    for v in VENDORS:
        existing = db.query(models.Contact).filter_by(remote_id=v["ref"]).first()
        if existing:
            vendor_ids[v["ref"]] = existing.id
            continue
        contact = models.Contact(
            id=mk_id(),
            remote_id=v["ref"],
            company_id=company_id,
            name=v["name"],
            type="VENDOR",
            email=v["email"],
            phone=v["phone"],
            payment_terms=v["terms"],
            currency="USD",
            status="active",
            billing_address={"city": "San Francisco", "state": "CA", "country": "US"},
        )
        db.add(contact)
        db.flush()
        vendor_ids[v["ref"]] = contact.id
    return vendor_ids


# ─── Customers ───────────────────────────────────────────────────────────────

CUSTOMERS = [
    {"ref": "CUST-MERIDIAN",  "name": "Meridian Bank",      "email": "ap@meridianbank.com",     "phone": "+1-212-555-0101", "terms": "Net 15", "industry": "Financial Services", "plan": "Enterprise"},
    {"ref": "CUST-ACME",      "name": "Acme Corp",           "email": "ap@acmecorp.com",         "phone": "+1-415-555-0102", "terms": "Net 30", "industry": "Manufacturing",       "plan": "Enterprise"},
    {"ref": "CUST-NEXUS",     "name": "Nexus Ventures",      "email": "finance@nexusvc.com",     "phone": "+1-650-555-0103", "terms": "Net 30", "industry": "Finance / PE",        "plan": "Growth"},
    {"ref": "CUST-BLOOM",     "name": "Bloom Health",        "email": "billing@bloomhealth.io",  "phone": "+1-512-555-0104", "terms": "Net 30", "industry": "Healthcare",          "plan": "Growth"},
    {"ref": "CUST-VERTEX",    "name": "Vertex Systems",      "email": "accounts@vertexsys.com",  "phone": "+1-408-555-0105", "terms": "Net 15", "industry": "Technology",          "plan": "Enterprise"},
    {"ref": "CUST-SKYLINE",   "name": "Skyline Retail",      "email": "ap@skylineretail.com",    "phone": "+1-303-555-0106", "terms": "Net 60", "industry": "Retail",              "plan": "Starter"},
    {"ref": "CUST-ORION",     "name": "Orion Logistics",     "email": "finance@orionlog.com",    "phone": "+1-972-555-0107", "terms": "Net 30", "industry": "Logistics",           "plan": "Growth"},
    {"ref": "CUST-DELTA",     "name": "DeltaStream",         "email": "billing@deltastream.io",  "phone": "+1-206-555-0108", "terms": "Net 60", "industry": "Media",               "plan": "Starter"},
]

def seed_customers(db, company_id) -> dict:
    customer_ids = {}
    for c in CUSTOMERS:
        existing = db.query(models.Contact).filter_by(remote_id=c["ref"]).first()
        if existing:
            customer_ids[c["ref"]] = existing.id
            continue
        contact = models.Contact(
            id=mk_id(),
            remote_id=c["ref"],
            company_id=company_id,
            name=c["name"],
            type="CUSTOMER",
            email=c["email"],
            phone=c["phone"],
            payment_terms=c["terms"],
            currency="USD",
            status="active",
        )
        db.add(contact)
        db.flush()
        customer_ids[c["ref"]] = contact.id
    return customer_ids


# ─── AR Invoices ─────────────────────────────────────────────────────────────

def seed_ar_invoices(db, company_id, customer_ids):
    invoices = [
        {"num": "INV-2026-041", "cust": "CUST-MERIDIAN", "issue": d(0, 1),  "due": d(0, 1)+timedelta(30),  "amt": Decimal("18500"), "paid": Decimal("18500"), "status": "PAID",    "memo": "Analytics Platform — Enterprise License Q2"},
        {"num": "INV-2026-042", "cust": "CUST-NEXUS",    "issue": d(0, 5),  "due": d(0, 5)+timedelta(30),  "amt": Decimal("7200"),  "paid": Decimal("0"),     "status": "OVERDUE", "memo": "Professional Services — April"},
        {"num": "INV-2026-043", "cust": "CUST-BLOOM",    "issue": d(0, 10), "due": d(0, 10)+timedelta(30), "amt": Decimal("4800"),  "paid": Decimal("0"),     "status": "OPEN",    "memo": "SaaS Subscription — Growth Plan"},
        {"num": "INV-2026-044", "cust": "CUST-VERTEX",   "issue": d(0, 12), "due": d(0, 12)+timedelta(30), "amt": Decimal("22000"), "paid": Decimal("11000"), "status": "PARTIALLY_PAID", "memo": "Implementation Services Phase 2"},
        {"num": "INV-2026-045", "cust": "CUST-SKYLINE",  "issue": d(0, 15), "due": d(0, 15)+timedelta(30), "amt": Decimal("3600"),  "paid": Decimal("0"),     "status": "OPEN",    "memo": "Monthly Reporting Module — May"},
        {"num": "INV-2026-046", "cust": "CUST-MERIDIAN", "issue": d(0, 18), "due": d(0, 18)+timedelta(30), "amt": Decimal("41000"), "paid": Decimal("0"),     "status": "OPEN",    "memo": "Enterprise Analytics — Annual Renewal"},
        {"num": "INV-2026-047", "cust": "CUST-ORION",    "issue": d(0, 20), "due": d(0, 20)+timedelta(30), "amt": Decimal("2100"),  "paid": Decimal("0"),     "status": "DRAFT",   "memo": "Custom Dashboard Development"},
        # Prior month invoices
        {"num": "INV-2026-038", "cust": "CUST-ACME",     "issue": d(1, 1),  "due": d(1, 1)+timedelta(30),  "amt": Decimal("18500"), "paid": Decimal("18500"), "status": "PAID",    "memo": "Enterprise License Q1"},
        {"num": "INV-2026-039", "cust": "CUST-VERTEX",   "issue": d(1, 5),  "due": d(1, 5)+timedelta(30),  "amt": Decimal("11000"), "paid": Decimal("11000"), "status": "PAID",    "memo": "Enterprise License Q1"},
        {"num": "INV-2026-040", "cust": "CUST-BLOOM",    "issue": d(1, 10), "due": d(1, 10)+timedelta(30), "amt": Decimal("4800"),  "paid": Decimal("4800"),  "status": "PAID",    "memo": "Growth Plan Q1"},
        {"num": "INV-2026-035", "cust": "CUST-DELTA",    "issue": d(2, 1),  "due": d(2, 1)+timedelta(60),  "amt": Decimal("960"),   "paid": Decimal("0"),     "status": "OVERDUE", "memo": "Starter Plan — Feb"},
        {"num": "INV-2026-036", "cust": "CUST-ORION",    "issue": d(2, 5),  "due": d(2, 5)+timedelta(30),  "amt": Decimal("3200"),  "paid": Decimal("3200"),  "status": "PAID",    "memo": "Growth Plan Feb"},
    ]
    for inv in invoices:
        if skip_if(db, models.Invoice, invoice_number=inv["num"]):
            continue
        cid = customer_ids.get(inv["cust"])
        tax = (inv["amt"] * Decimal("0.0")).quantize(Decimal("0.01"))
        db.add(models.Invoice(
            id=mk_id(),
            remote_id=f"MR-{inv['num']}",
            company_id=company_id,
            invoice_number=inv["num"],
            contact_id=cid,
            issue_date=inv["issue"],
            due_date=inv["due"],
            status=inv["status"],
            type="ACCOUNTS_RECEIVABLE",
            sub_total=inv["amt"],
            tax_amount=tax,
            total_amount=inv["amt"] + tax,
            amount_paid=inv["paid"],
            amount_due=inv["amt"] - inv["paid"],
            currency="USD",
            memo=inv["memo"],
            payment_date=inv["issue"] + timedelta(15) if inv["paid"] > 0 else None,
        ))


# ─── AP Bills ────────────────────────────────────────────────────────────────

def seed_ap_bills(db, company_id, vendor_ids):
    bills = [
        {"num": "BILL-2026-087", "vendor": "VENDOR-AWS",        "issue": d(0, 1),  "due": d(0, 1)+timedelta(30),  "amt": Decimal("14200"), "paid": Decimal("14200"), "status": "PAID",    "memo": "AWS Infrastructure — April"},
        {"num": "BILL-2026-088", "vendor": "VENDOR-STRIPE",      "issue": d(0, 3),  "due": d(0, 3)+timedelta(15),  "amt": Decimal("1840"),  "paid": Decimal("1840"),  "status": "PAID",    "memo": "Stripe Payment Processing Fees — April"},
        {"num": "BILL-2026-089", "vendor": "VENDOR-SALESFORCE",  "issue": d(0, 5),  "due": d(0, 5)+timedelta(30),  "amt": Decimal("8400"),  "paid": Decimal("0"),     "status": "OPEN",    "memo": "Salesforce Enterprise License — Q2"},
        {"num": "BILL-2026-090", "vendor": "VENDOR-COOLEY",      "issue": d(0, 8),  "due": d(0, 8)+timedelta(15),  "amt": Decimal("22500"), "paid": Decimal("0"),     "status": "OVERDUE", "memo": "Legal Services — Series A Diligence"},
        {"num": "BILL-2026-091", "vendor": "VENDOR-GREENHOUSE",  "issue": d(0, 10), "due": d(0, 10)+timedelta(30), "amt": Decimal("3600"),  "paid": Decimal("0"),     "status": "OPEN",    "memo": "Greenhouse ATS — Q2 License"},
        {"num": "BILL-2026-092", "vendor": "VENDOR-WEWORK",      "issue": d(0, 1),  "due": d(0, 1)+timedelta(1),   "amt": Decimal("9800"),  "paid": Decimal("9800"),  "status": "PAID",    "memo": "Office Rent — April 2026"},
        {"num": "BILL-2026-093", "vendor": "VENDOR-DATADOG",     "issue": d(0, 15), "due": d(0, 15)+timedelta(30), "amt": Decimal("2100"),  "paid": Decimal("0"),     "status": "OPEN",    "memo": "Datadog Monitoring — April"},
        {"num": "BILL-2026-094", "vendor": "VENDOR-NOTION",      "issue": d(0, 18), "due": d(0, 18)+timedelta(30), "amt": Decimal("480"),   "paid": Decimal("0"),     "status": "OPEN",    "memo": "Notion Team Plan — April"},
        # Prior month
        {"num": "BILL-2026-080", "vendor": "VENDOR-AWS",        "issue": d(1, 1),  "due": d(1, 1)+timedelta(30),  "amt": Decimal("13400"), "paid": Decimal("13400"), "status": "PAID",    "memo": "AWS — March"},
        {"num": "BILL-2026-081", "vendor": "VENDOR-WEWORK",      "issue": d(1, 1),  "due": d(1, 1)+timedelta(1),   "amt": Decimal("9800"),  "paid": Decimal("9800"),  "status": "PAID",    "memo": "WeWork — March"},
        {"num": "BILL-2026-082", "vendor": "VENDOR-RIPPLING",    "issue": d(1, 1),  "due": d(1, 1)+timedelta(1),   "amt": Decimal("4200"),  "paid": Decimal("4200"),  "status": "PAID",    "memo": "Rippling HRIS — March"},
    ]
    for b in bills:
        if skip_if(db, models.Invoice, invoice_number=b["num"]):
            continue
        vid = vendor_ids.get(b["vendor"])
        db.add(models.Invoice(
            id=mk_id(),
            remote_id=f"MR-{b['num']}",
            company_id=company_id,
            invoice_number=b["num"],
            contact_id=vid,
            issue_date=b["issue"],
            due_date=b["due"],
            status=b["status"],
            type="ACCOUNTS_PAYABLE",
            sub_total=b["amt"],
            tax_amount=Decimal("0"),
            total_amount=b["amt"],
            amount_paid=b["paid"],
            amount_due=b["amt"] - b["paid"],
            currency="USD",
            memo=b["memo"],
            payment_date=b["issue"] + timedelta(5) if b["paid"] > 0 else None,
        ))


# ─── Purchase Orders ─────────────────────────────────────────────────────────

def seed_purchase_orders(db, company_id, vendor_ids):
    pos = [
        {
            "num": "PO-2026-042", "vendor": "VENDOR-AWS",       "requested_by": "Aditi Singh",    "dept": "Engineering",
            "issue": d(0, 1), "delivery": d(0, 1)+timedelta(30), "amt": Decimal("14200"), "status": models.POStatus.RECEIVED,
            "approved_by": "Aditi Singh",
            "lines": [
                ("EC2 Reserved Instances — 1yr", Decimal("4"), Decimal("2800")),
                ("S3 Storage + Data Transfer", Decimal("1"), Decimal("3400")),
            ]
        },
        {
            "num": "PO-2026-043", "vendor": "VENDOR-GREENHOUSE", "requested_by": "Priya K.",       "dept": "People",
            "issue": d(0, 5), "delivery": d(0, 5)+timedelta(35), "amt": Decimal("8400"),  "status": models.POStatus.APPROVED,
            "approved_by": "Aditi Singh",
            "lines": [("ATS Annual License — 20 seats", Decimal("20"), Decimal("420"))]
        },
        {
            "num": "PO-2026-044", "vendor": "VENDOR-OPENAI",    "requested_by": "Dev Team Lead",  "dept": "Engineering",
            "issue": d(0, 8), "delivery": d(0, 8)+timedelta(20), "amt": Decimal("3600"),  "status": models.POStatus.SUBMITTED,
            "lines": [("GPT-4o API Credits — Monthly top-up", Decimal("1"), Decimal("3600"))]
        },
        {
            "num": "PO-2026-045", "vendor": "VENDOR-COOLEY",    "requested_by": "Aditi Singh",    "dept": "Finance",
            "issue": d(0, 12), "delivery": d(0, 12)+timedelta(18), "amt": Decimal("22500"), "status": models.POStatus.PARTIALLY_RECEIVED,
            "approved_by": "Aditi Singh",
            "lines": [("Series A Legal Services — Phase 1", Decimal("1"), Decimal("22500"))]
        },
        {
            "num": "PO-2026-046", "vendor": "VENDOR-SALESFORCE", "requested_by": "Priya K.",      "dept": "Sales",
            "issue": d(0, 18), "delivery": d(0, 18)+timedelta(30), "amt": Decimal("8400"), "status": models.POStatus.SUBMITTED,
            "lines": [("Sales Cloud — Enterprise 15 seats Q2", Decimal("15"), Decimal("560"))]
        },
    ]
    for po in pos:
        if skip_if(db, models.PurchaseOrder, po_number=po["num"]):
            continue
        vid = vendor_ids.get(po["vendor"])
        po_obj = models.PurchaseOrder(
            id=mk_id(),
            company_id=company_id,
            po_number=po["num"],
            vendor_id=vid,
            po_date=po["issue"],
            expected_delivery_date=po["delivery"],
            total_amount=po["amt"],
            currency="USD",
            status=po["status"],
            requested_by=po["requested_by"],
            approved_by=po.get("approved_by"),
            approved_at=datetime.utcnow() if po.get("approved_by") else None,
            department=po["dept"],
        )
        db.add(po_obj)
        db.flush()

        for desc, qty, unit in po["lines"]:
            db.add(models.POLineItem(
                id=mk_id(),
                po_id=po_obj.id,
                description=desc,
                quantity=qty,
                unit_price=unit,
                total_price=qty * unit,
                quantity_received=qty if po["status"] == models.POStatus.RECEIVED else Decimal("0"),
            ))


# ─── Employees ───────────────────────────────────────────────────────────────

EMPLOYEES = [
    ("EMP-MR-001", "Aditi",    "Singh",     "aditi@orchardanalytics.com",    date(2023, 1, 15), Decimal("180000"), "CEO",                      "leadership"),
    ("EMP-MR-002", "Rahul",    "Mehta",     "rahul@orchardanalytics.com",    date(2023, 1, 15), Decimal("170000"), "CTO",                      "engineering"),
    ("EMP-MR-003", "Priya",    "K.",        "priya@orchardanalytics.com",    date(2023, 6, 1),  Decimal("150000"), "VP Sales",                 "sales"),
    ("EMP-MR-004", "Dev",      "Team Lead", "devlead@orchardanalytics.com",  date(2023, 8, 15), Decimal("145000"), "Senior Engineer",          "engineering"),
    ("EMP-MR-005", "Arjun",    "Sharma",    "arjun@orchardanalytics.com",    date(2024, 1, 10), Decimal("130000"), "Backend Engineer",         "engineering"),
    ("EMP-MR-006", "Meera",    "Iyer",      "meera@orchardanalytics.com",    date(2024, 1, 15), Decimal("120000"), "Frontend Engineer",        "engineering"),
    ("EMP-MR-007", "Karan",    "Malhotra",  "karan@orchardanalytics.com",    date(2024, 3, 1),  Decimal("120000"), "Marketing Manager",        "marketing"),
    ("EMP-MR-008", "Sanya",    "Kapoor",    "sanya@orchardanalytics.com",    date(2024, 3, 15), Decimal("130000"), "Product Manager",          "product"),
    ("EMP-MR-009", "Vikram",   "Nair",      "vikram@orchardanalytics.com",   date(2024, 6, 1),  Decimal("135000"), "Data Scientist",           "engineering"),
    ("EMP-MR-010", "Anjali",   "Patel",     "anjali@orchardanalytics.com",   date(2024, 9, 1),  Decimal("95000"),  "Customer Success Manager", "sales"),
    ("EMP-MR-011", "Rohit",    "Verma",     "rohit@orchardanalytics.com",    date(2025, 1, 15), Decimal("110000"), "Account Executive",        "sales"),
    ("EMP-MR-012", "Tanvi",    "Shah",      "tanvi@orchardanalytics.com",    date(2025, 3, 1),  Decimal("125000"), "Finance Manager",          "finance"),
]

def seed_employees(db, company_id) -> list:
    emp_ids = []
    for emp_id_str, first, last, email, hire, salary, title, dept in EMPLOYEES:
        existing = db.query(models.Employee).filter_by(employee_id=emp_id_str).first()
        if existing:
            emp_ids.append(existing)
            continue
        emp = models.Employee(
            id=mk_id(),
            company_id=company_id,
            employee_id=emp_id_str,
            first_name=first,
            last_name=last,
            email=email,
            hire_date=hire,
            salary=salary,
            job_title=title,
            department=dept,
            status="active",
        )
        db.add(emp)
        db.flush()
        emp_ids.append(emp)
    return emp_ids


def seed_payroll(db, employees):
    """Create 3 months of payroll entries for all employees."""
    for emp in employees:
        for mo in range(3, 0, -1):
            period_start = d(mo, 1)
            period_end = d(mo - 1, 1) - timedelta(days=1)
            if skip_if(db, models.PayrollEntry, employee_id=emp.id, pay_period_start=period_start):
                continue
            gross = emp.salary / 12
            federal_tax = gross * Decimal("0.12")
            ss = gross * Decimal("0.062")
            medicare = gross * Decimal("0.0145")
            state_tax = gross * Decimal("0.05")
            net = gross - federal_tax - ss - medicare - state_tax
            db.add(models.PayrollEntry(
                id=mk_id(),
                employee_id=emp.id,
                pay_period_start=period_start,
                pay_period_end=period_end,
                gross_pay=gross.quantize(Decimal("0.01")),
                federal_tax=federal_tax.quantize(Decimal("0.01")),
                state_tax=state_tax.quantize(Decimal("0.01")),
                social_security=ss.quantize(Decimal("0.01")),
                medicare=medicare.quantize(Decimal("0.01")),
                other_deductions=Decimal("0"),
                net_pay=net.quantize(Decimal("0.01")),
                pay_date=period_end,
                status="processed",
                department=emp.department,
            ))


# ─── Fixed Assets ─────────────────────────────────────────────────────────────

ASSETS = [
    ("ASSET-MR-001", "MacBook Pro Fleet (10 units)",   "Computer Equipment", date(2023, 2, 1),  Decimal("35000"), Decimal("0"), 3, Decimal("9722.22")),
    ("ASSET-MR-002", "Office Furniture & Fixtures",     "Furniture",          date(2023, 3, 15), Decimal("22000"), Decimal("2000"), 7, Decimal("2857.14")),
    ("ASSET-MR-003", "Development Server Cluster",      "Computer Equipment", date(2023, 6, 1),  Decimal("48000"), Decimal("0"), 3, Decimal("13333.33")),
    ("ASSET-MR-004", "Audio/Video Conference Equipment","Office Equipment",   date(2024, 1, 10), Decimal("8500"),  Decimal("500"), 5, Decimal("1600")),
    ("ASSET-MR-005", "Security & Access Systems",       "Security Equipment", date(2024, 3, 1),  Decimal("5200"),  Decimal("200"), 5, Decimal("1000")),
]

def seed_fixed_assets(db, company_id):
    for serial, name, cat, purchase_date, cost, salvage, life, accum_dep in ASSETS:
        if skip_if(db, models.FixedAsset, serial_number=serial, company_id=company_id):
            continue
        months_held = max(0, (date.today().year - purchase_date.year) * 12 + (date.today().month - purchase_date.month))
        annual_dep = (cost - salvage) / life
        accum = min(annual_dep * Decimal(months_held) / 12, cost - salvage)
        book = cost - accum
        asset = models.FixedAsset(
            id=mk_id(),
            company_id=company_id,
            asset_name=name,
            asset_category=cat,
            purchase_date=purchase_date,
            purchase_cost=cost,
            salvage_value=salvage,
            useful_life_years=life,
            depreciation_method="straight_line",
            accumulated_depreciation=accum.quantize(Decimal("0.01")),
            book_value=book.quantize(Decimal("0.01")),
            serial_number=serial,
            status="active",
        )
        db.add(asset)


# ─── Customer Health Scores ───────────────────────────────────────────────────

HEALTH_DATA = {
    "CUST-MERIDIAN": (88, "healthy",  Decimal("85"), Decimal("90"), Decimal("8"),   Decimal("0"),     date(2026, 4, 1),  0, 0),
    "CUST-ACME":     (72, "healthy",  Decimal("78"), Decimal("70"), Decimal("22"),  Decimal("0"),     date(2026, 4, 1),  1, 0),
    "CUST-NEXUS":    (31, "at_risk",  Decimal("35"), Decimal("28"), Decimal("69"),  Decimal("57600"), date(2026, 3, 28), 3, 1),
    "CUST-BLOOM":    (68, "healthy",  Decimal("72"), Decimal("65"), Decimal("28"),  Decimal("0"),     date(2026, 4, 18), 0, 0),
    "CUST-VERTEX":   (92, "healthy",  Decimal("95"), Decimal("88"), Decimal("5"),   Decimal("0"),     date(2026, 4, 20), 0, 0),
    "CUST-SKYLINE":  (28, "at_risk",  Decimal("22"), Decimal("34"), Decimal("78"),  Decimal("14400"), date(2026, 3, 10), 4, 2),
    "CUST-ORION":    (65, "healthy",  Decimal("68"), Decimal("62"), Decimal("32"),  Decimal("0"),     date(2026, 4, 17), 1, 0),
    "CUST-DELTA":    (12, "churned",  Decimal("10"), Decimal("14"), Decimal("95"),  Decimal("9600"),  date(2026, 2, 1),  5, 3),
}

def seed_customer_health(db, company_id, customer_ids):
    for ref, (score, status_str, pay_score, rev_score, churn_prob, arr_risk, last_pay, late_cnt, dispute_cnt) in HEALTH_DATA.items():
        cid = customer_ids.get(ref)
        if not cid:
            continue
        existing = db.query(models.CustomerHealthScore).filter_by(company_id=company_id, customer_id=cid).first()
        if existing:
            existing.score = Decimal(str(score))
            existing.churn_probability = churn_prob
            existing.calculated_at = datetime.utcnow()
            continue
        status_enum = models.CustomerHealthStatus.HEALTHY if status_str == "healthy" else (
            models.CustomerHealthStatus.AT_RISK if status_str == "at_risk" else models.CustomerHealthStatus.CHURNED
        )
        db.add(models.CustomerHealthScore(
            id=mk_id(),
            company_id=company_id,
            customer_id=cid,
            score=Decimal(str(score)),
            status=status_enum,
            payment_behavior_score=pay_score,
            revenue_trend_score=rev_score,
            churn_probability=churn_prob,
            arr_at_risk=arr_risk,
            late_payment_count=late_cnt,
            dispute_count=dispute_cnt,
            last_payment_date=last_pay,
            calculated_at=datetime.utcnow(),
        ))


# ─── Customer Cohorts (SaaS Metrics) ─────────────────────────────────────────

def seed_customer_cohorts(db, company_id):
    cohorts = [
        ("Q1 2025", "Q1 2025", date(2025, 1, 1), 4, Decimal("45000"),  Decimal("540000"),  Decimal("0.045"), Decimal("48000"), Decimal("4200"), Decimal("114"), Decimal("72"), Decimal("11.4")),
        ("Q2 2025", "Q2 2025", date(2025, 4, 1), 5, Decimal("54500"),  Decimal("654000"),  Decimal("0.038"), Decimal("52000"), Decimal("4800"), Decimal("112"), Decimal("74"), Decimal("10.8")),
        ("Q3 2025", "Q3 2025", date(2025, 7, 1), 6, Decimal("65800"),  Decimal("789600"),  Decimal("0.031"), Decimal("58000"), Decimal("5100"), Decimal("115"), Decimal("78"), Decimal("11.4")),
        ("Q4 2025", "Q4 2025", date(2025, 10, 1), 7, Decimal("89400"),  Decimal("1072800"), Decimal("0.024"), Decimal("64000"), Decimal("4600"), Decimal("118"), Decimal("82"), Decimal("13.9")),
        ("Q1 2026", "Q1 2026", date(2026, 1, 1), 8, Decimal("108200"), Decimal("1298400"), Decimal("0.018"), Decimal("71000"), Decimal("4900"), Decimal("120"), Decimal("85"), Decimal("14.5")),
    ]
    for name, val, acq_date, cnt, mrr, arr, churn, ltv, cac, nrr, gm, payback in cohorts:
        ref = f"MR-COHORT-{val.replace(' ', '-')}"
        if db.query(models.CustomerCohort).filter_by(cohort_name=name, company_id=company_id).first():
            continue
        db.add(models.CustomerCohort(
            id=mk_id(),
            company_id=company_id,
            cohort_name=name,
            cohort_type="acquisition_quarter",
            cohort_value=val,
            customer_acquired_date=acq_date,
            customer_count=cnt,
            mrr_total=mrr,
            arr_total=arr,
            churn_rate=churn,
            ltv_estimate=ltv,
            cac_estimate=cac,
            nrr=nrr,
            gross_margin_pct=gm,
            payback_months=payback,
            health_score=Decimal("8.2"),
        ))


# ─── Budget ───────────────────────────────────────────────────────────────────

def seed_budget(db, company_id):
    existing_budget = db.query(models.Budget).filter_by(company_id=company_id, name="FY 2026 Annual Budget").first()
    if not existing_budget:
        budget = models.Budget(
            id=mk_id(),
            company_id=company_id,
            name="FY 2026 Annual Budget",
            fiscal_year=2026,
            status="active",
        )
        db.add(budget)
        db.flush()

        budget_lines = [
            ("Revenue — SaaS Subscriptions", Decimal("120000")),
            ("Revenue — Professional Services", Decimal("25000")),
            ("COGS — Hosting & Infrastructure", Decimal("18000")),
            ("COGS — Support Staff", Decimal("14000")),
            ("Salaries & Benefits — Engineering", Decimal("75000")),
            ("Salaries & Benefits — Sales & Marketing", Decimal("45000")),
            ("Salaries & Benefits — G&A", Decimal("28000")),
            ("Marketing & Demand Gen", Decimal("22000")),
            ("Office & Facilities", Decimal("12000")),
            ("Legal & Compliance", Decimal("8000")),
            ("R&D & Tools", Decimal("15000")),
        ]
        for cat, monthly in budget_lines:
            db.add(models.BudgetLine(
                id=mk_id(),
                budget_id=budget.id,
                category=cat,
                monthly_amount=monthly,
            ))


# ─── Anomalies ────────────────────────────────────────────────────────────────

def seed_anomalies(db, company_id):
    anomalies = [
        {
            "remote_id": "ANOM-MR-001",
            "date": d(0, 8),
            "severity": "high",
            "type": "duplicate_invoice",
            "description": "Potential duplicate bill from Cooley LLP: BILL-2026-090 ($22,500) matches pattern of BILL-2026-075 from 45 days ago (same vendor, similar amount, same description).",
            "expected": Decimal("0"),
            "actual": Decimal("22500"),
            "status": "open",
        },
        {
            "remote_id": "ANOM-MR-002",
            "date": d(0, 12),
            "severity": "medium",
            "type": "spending_spike",
            "description": "AWS spend increased 28% month-over-month ($11,100 → $14,200) without corresponding engineering headcount increase. Possible over-provisioning or cost leak.",
            "expected": Decimal("11100"),
            "actual": Decimal("14200"),
            "status": "open",
        },
        {
            "remote_id": "ANOM-MR-003",
            "date": d(1, 5),
            "severity": "low",
            "type": "late_payment",
            "description": "Nexus Ventures invoice INV-2026-042 ($7,200) is now 15 days past due. Historical payment average was 42 days DSO — this is trending 2x slower.",
            "expected": Decimal("7200"),
            "actual": Decimal("0"),
            "status": "open",
        },
        {
            "remote_id": "ANOM-MR-004",
            "date": d(2, 15),
            "severity": "medium",
            "type": "revenue_drop",
            "description": "DeltaStream subscription revenue dropped 33% — no payment received for 78 days. Churn risk is 95%. Consider proactive win-back campaign.",
            "expected": Decimal("1200"),
            "actual": Decimal("0"),
            "status": "acknowledged",
        },
    ]
    for a in anomalies:
        if skip_if(db, models.Anomaly, remote_id=a["remote_id"]):
            continue
        db.add(models.Anomaly(
            id=mk_id(),
            remote_id=a["remote_id"],
            company_id=company_id,
            anomaly_date=a["date"],
            severity=a["severity"],
            type=a["type"],
            description=a["description"],
            expected_value=a["expected"],
            actual_value=a["actual"],
            status=a["status"],
        ))


# ─── Comprehensive Monthly Metrics ────────────────────────────────────────────

def seed_monthly_metrics(db, company_id):
    """12 months of realistic growth metrics."""
    metrics = [
        # (offset_months, revenue, expenses, cash)
        (11, Decimal("38000"),  Decimal("290000"), Decimal("4200000")),
        (10, Decimal("42500"),  Decimal("310000"), Decimal("4050000")),
        (9,  Decimal("47000"),  Decimal("328000"), Decimal("3880000")),
        (8,  Decimal("52000"),  Decimal("345000"), Decimal("3690000")),
        (7,  Decimal("58000"),  Decimal("362000"), Decimal("3488000")),
        (6,  Decimal("65000"),  Decimal("380000"), Decimal("3273000")),
        (5,  Decimal("73000"),  Decimal("395000"), Decimal("3051000")),
        (4,  Decimal("82000"),  Decimal("412000"), Decimal("4800000")),  # Series A close
        (3,  Decimal("89400"),  Decimal("438000"), Decimal("4451000")),
        (2,  Decimal("96200"),  Decimal("455000"), Decimal("4092000")),
        (1,  Decimal("102400"), Decimal("468000"), Decimal("3726000")),
        (0,  Decimal("108200"), Decimal("481000"), Decimal("3353000")),
    ]
    for offset, revenue, expenses, cash in metrics:
        m = d(offset, 1)
        if skip_if(db, models.MonthlyMetric, company_id=company_id, metric_month=m):
            continue
        burn = max(Decimal("0"), expenses - revenue)
        runway = cash / burn if burn > 0 else Decimal("99")
        db.add(models.MonthlyMetric(
            id=mk_id(),
            company_id=company_id,
            metric_month=m,
            total_revenue=revenue,
            total_expenses=expenses,
            total_tax_liability=Decimal("0"),
            net_cash_flow=revenue - expenses,
            burn_rate=burn,
            runway_months=runway.quantize(Decimal("0.1")),
            ending_cash=cash,
        ))


# ─── General Ledger Entries ───────────────────────────────────────────────────

def seed_gl_entries(db, company_id):
    """Comprehensive 6-month GL entries for all accounts."""
    gl_entries = []

    for offset in range(5, -1, -1):
        m = d(offset, 1)

        # Revenue entries
        for acc, name, amt, dept, tag in [
            (models.GLAccountCode.SUBSCRIPTION_REVENUE, "SaaS Subscription Revenue", Decimal("85000") + Decimal("4000") * (5 - offset), models.Department.SALES, models.LedgerProductTag.ORCHARD),
            (models.GLAccountCode.SERVICE_REVENUE, "Professional Services Revenue", Decimal("15000") + Decimal("1000") * (5 - offset), models.Department.SALES, models.LedgerProductTag.SHARED),
        ]:
            ref = f"GL-MR-REV-{acc.value}-{m.strftime('%Y%m')}"
            gl_entries.append((acc, name, m + timedelta(1), Decimal("0"), amt, f"Revenue recognition — {name} {m.strftime('%b %Y')}", dept, tag, ref))

        # COGS entries
        for acc, name, amt, dept in [
            (models.GLAccountCode.TECH_COST_AWS, "AWS Infrastructure COGS", Decimal("12000") + Decimal("400") * (5 - offset), models.Department.ENGINEERING),
            (models.GLAccountCode.TECH_COST_SAAS, "Third-Party API Costs", Decimal("3000") + Decimal("100") * (5 - offset), models.Department.ENGINEERING),
        ]:
            ref = f"GL-MR-COGS-{acc.value}-{m.strftime('%Y%m')}"
            gl_entries.append((acc, name, m + timedelta(5), amt, Decimal("0"), f"COGS — {name} {m.strftime('%b %Y')}", dept, models.LedgerProductTag.SHARED, ref))

        # OpEx entries
        for acc, name, amt, dept in [
            (models.GLAccountCode.PAYROLL_EXPENSE, "Salaries & Benefits", Decimal("186000"), models.Department.ENGINEERING),
            (models.GLAccountCode.MARKETING_EXPENSE, "Sales & Marketing", Decimal("68000"), models.Department.MARKETING),
            (models.GLAccountCode.OFFICE_EXPENSE, "Office & Facilities", Decimal("14200"), models.Department.OPERATIONS),
            (models.GLAccountCode.MISC, "Legal & Professional Fees", Decimal("22500"), models.Department.FINANCE),
        ]:
            ref = f"GL-MR-OPEX-{acc.value}-{m.strftime('%Y%m')}"
            gl_entries.append((acc, name, m + timedelta(10), amt, Decimal("0"), f"OpEx — {name} {m.strftime('%b %Y')}", dept, models.LedgerProductTag.SHARED, ref))

    for acc, name, tx_date, debit, credit, desc, dept, tag, ref in gl_entries:
        if db.query(models.GeneralLedger).filter_by(reference_id=ref).first():
            continue
        db.add(models.GeneralLedger(
            id=mk_id(),
            company_id=company_id,
            account_code=acc,
            account_name=name,
            transaction_date=tx_date,
            debit_amount=debit,
            credit_amount=credit,
            description=desc,
            department=dept,
            product_tag=tag,
            source_type="seed",
            reference_id=ref,
        ))


# ─── Bank Feed & Transactions ─────────────────────────────────────────────────

def seed_bank_data(db, company_id):
    feed_ref = "BANKFEED-MR-SVB-001"
    feed = db.query(models.BankFeed).filter_by(account_number_last4="8821", company_id=company_id).first()
    if not feed:
        feed = models.BankFeed(
            id=mk_id(),
            company_id=company_id,
            bank_name="Silicon Valley Bank",
            account_name="Orchard Analytics — Operating",
            account_type="checking",
            account_number_last4="8821",
            currency="USD",
            status="active",
            last_synced_at=datetime.utcnow(),
        )
        db.add(feed)
        db.flush()

    transactions = [
        (d(0, 2),  Decimal("18500"),  "Meridian Bank payment",       "Revenue",     False),
        (d(0, 4),  Decimal("-14200"), "AWS payment",                  "Software",    True),
        (d(0, 5),  Decimal("-9800"),  "WeWork rent",                  "Office",      False),
        (d(0, 8),  Decimal("-1840"),  "Stripe fee debit",             "Software",    True),
        (d(0, 10), Decimal("11000"),  "Vertex Systems payment",       "Revenue",     False),
        (d(0, 12), Decimal("-4200"),  "Rippling payroll debit",       "Payroll",     False),
        (d(0, 14), Decimal("-2100"),  "Datadog subscription",         "Software",    True),
        (d(0, 15), Decimal("4800"),   "Bloom Health payment",         "Revenue",     False),
        (d(0, 17), Decimal("-8400"),  "Salesforce renewal",           "Software",    True),
        (d(0, 19), Decimal("-186000"),"Payroll — April run",          "Payroll",     False),
    ]
    for tx_date, amount, desc, cat, is_saas in transactions:
        if db.query(models.BankingTransaction).filter_by(
            feed_id=feed.id, transaction_date=tx_date, description=desc
        ).first():
            continue
        db.add(models.BankingTransaction(
            id=mk_id(),
            feed_id=feed.id,
            transaction_date=tx_date,
            amount=amount,
            description=desc,
            merchant_name=desc.split(" ")[0],
            category=cat,
            is_saas=is_saas,
        ))


# ─── Contracts ───────────────────────────────────────────────────────────────

def seed_contracts(db, company_id, customer_ids):
    contracts_data = [
        ("CUST-MERIDIAN", "CTR-MR-001", "Meridian Bank Enterprise Agreement", "active", date(2026, 1, 15), date(2027, 1, 14), Decimal("150000")),
        ("CUST-ACME",     "CTR-MR-002", "Acme Corp Enterprise License",       "active", date(2024, 6, 1),  date(2026, 6, 1),  Decimal("98400")),
        ("CUST-VERTEX",   "CTR-MR-003", "Vertex Systems MSA + SOW",           "active", date(2023, 11, 15), date(2026, 11, 14), Decimal("132000")),
        ("CUST-NEXUS",    "CTR-MR-004", "Nexus Ventures Growth Plan",         "active", date(2025, 1, 10), date(2026, 7, 10),  Decimal("57600")),
        ("CUST-ORION",    "CTR-MR-005", "Orion Logistics SaaS MSA",           "active", date(2025, 2, 1),  date(2026, 8, 1),   Decimal("38400")),
    ]
    for cust_ref, contract_num, title, status, start, end, arr in contracts_data:
        if db.query(models.Contract).filter_by(contract_number=contract_num).first():
            continue
        cid = customer_ids.get(cust_ref)
        db.add(models.Contract(
            id=mk_id(),
            company_id=company_id,
            contact_id=cid,
            contract_number=contract_num,
            title=title,
            status=status,
            start_date=start,
            end_date=end,
            total_value=arr,
            currency="USD",
            contract_type="customer",
            auto_renewal=True,
        ))


# ─── Main ─────────────────────────────────────────────────────────────────────

def run():
    print("🌱 Starting Market-Ready seed script...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        print("  → Company profile...")
        company = ensure_company(db)
        cid = company.id
        db.commit()

        print("  → Vendors...")
        vendor_ids = seed_vendors(db, cid)
        db.commit()

        print("  → Customers...")
        customer_ids = seed_customers(db, cid)
        db.commit()

        print("  → AR Invoices...")
        seed_ar_invoices(db, cid, customer_ids)
        db.commit()

        print("  → AP Bills...")
        seed_ap_bills(db, cid, vendor_ids)
        db.commit()

        print("  → Purchase Orders...")
        seed_purchase_orders(db, cid, vendor_ids)
        db.commit()

        print("  → Employees...")
        employees = seed_employees(db, cid)
        db.commit()

        print("  → Payroll entries...")
        seed_payroll(db, employees)
        db.commit()

        print("  → Fixed Assets...")
        seed_fixed_assets(db, cid)
        db.commit()

        print("  → Customer Health Scores...")
        seed_customer_health(db, cid, customer_ids)
        db.commit()

        print("  → Customer Cohorts (SaaS Metrics)...")
        seed_customer_cohorts(db, cid)
        db.commit()

        print("  → Budget...")
        seed_budget(db, cid)
        db.commit()

        print("  → Anomalies...")
        seed_anomalies(db, cid)
        db.commit()

        print("  → Monthly Metrics (12 months)...")
        seed_monthly_metrics(db, cid)
        db.commit()

        print("  → General Ledger entries...")
        seed_gl_entries(db, cid)
        db.commit()

        print("  → Bank Feed & Transactions...")
        seed_bank_data(db, cid)
        db.commit()

        print("  → Contracts...")
        seed_contracts(db, cid, customer_ids)
        db.commit()

        print()
        print(f"✅ Market-Ready seed complete!")
        print(f"   Company: {company.name}")
        print(f"   ID: {company.id}")
        print(f"   Vendors: {len(VENDORS)}")
        print(f"   Customers: {len(CUSTOMERS)}")
        print(f"   Employees: {len(EMPLOYEES)}")
        print()
        print("   Run the existing seed scripts too:")
        print("   → python scripts/seed_active_company_operational_data.py")

    except Exception as exc:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"❌ Seed failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
