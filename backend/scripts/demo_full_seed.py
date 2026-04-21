#!/usr/bin/env python3
"""
Vireon competition demo seed.
Creates Orchard Analytics Inc. with 12 months of realistic SaaS financials.
Idempotent — safe to run multiple times.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from datetime import date, timedelta
from decimal import Decimal

from database import SessionLocal
from models import (
    Company, Account, Contact, Invoice, Expense, MonthlyMetric, Anomaly,
    FinancialLedgerEntry,
    LedgerEntryType, LedgerCategory, LedgerProductTag,
    LedgerOfficeTag, LedgerSource, LedgerEnteredByRole,
)

COMPANY_NAME = "Orchard Analytics Inc."
USD_TO_INR = Decimal("83.00")

# ── Revenue trajectory (Apr 2025 – Mar 2026) ─────────────────────────────────
MONTHLY_REVENUE = [42000, 45200, 48600, 52100, 46800, 57400, 59800, 62100, 63500, 65200, 66800, 68400]
# Month 5 (Aug 2025) dips because Acme Corp churns — this is anomaly #4

# ── Expense buckets ───────────────────────────────────────────────────────────
AWS_COSTS     = [12000, 12200, 12400, 12600, 12800, 13000, 13200, 18245, 13400, 13600, 17800, 13800]
# Month 8 (Nov 2025) AWS spikes to $18,245 — anomaly #1
# Month 11 (Feb 2026) OpenAI unbudgeted spike to $17,800 — anomaly #6

PAYROLL_COSTS = [85000, 85000, 85000, 85000, 89250, 93713, 98398, 103318, 103318, 103318, 103318, 103318]
# 5%/month growth in months 5-8 (Aug–Nov 2025) — anomaly #2

OFFICE_COSTS  = [8500] * 12
SALES_COSTS   = [22000, 22000, 23500, 23500, 24000, 24000, 24500, 24500, 25000, 25000, 25500, 25500]


def _date(month_offset: int) -> date:
    """Apr 2025 + offset months."""
    y, m = 2025, 4
    m += month_offset
    while m > 12:
        m -= 12
        y += 1
    return date(y, m, 1)


def seed():
    db = SessionLocal()
    try:
        # ── Idempotency: remove existing demo company ─────────────────────────
        existing = db.query(Company).filter(Company.name == COMPANY_NAME).first()
        if existing:
            cid = existing.id
            db.query(FinancialLedgerEntry).filter(FinancialLedgerEntry.company_id == cid).delete()
            db.query(MonthlyMetric).filter(MonthlyMetric.company_id == cid).delete()
            db.query(Anomaly).filter(Anomaly.company_id == cid).delete()
            db.query(Expense).filter(Expense.company_id == cid).delete()
            # Delete invoices with safe remote_id matching
            db.query(Invoice).filter(Invoice.company_id == cid).delete()
            db.query(Account).filter(Account.company_id == cid).delete()
            db.query(Contact).filter(Contact.company_id == cid).delete()
            db.delete(existing)
            db.commit()
            print("  Cleared previous demo data.")

        # ── Company ───────────────────────────────────────────────────────────
        company = Company(
            name=COMPANY_NAME,
            industry="B2B SaaS / FinTech Analytics",
            stage="Series A",
            initial_cash=Decimal("2840000.00"),
            founding_date=date(2022, 3, 1),
            effective_tax_rate=Decimal("0.2100"),
            notification_contacts=["cfo@orchardanalytics.com"],
            alert_thresholds={"critical_months": 3, "warning_months": 6},
        )
        db.add(company)
        db.flush()
        cid = company.id
        print(f"  Created company: {COMPANY_NAME} (id={cid})")

        # ── Chart of Accounts ─────────────────────────────────────────────────
        accounts = {
            "cash":    Account(remote_id=f"demo_acc_cash_{cid}", company_id=cid, name="Chase Business Checking", classification="ASSET", type="BANK", current_balance=Decimal("2840000.00"), currency="USD"),
            "ar":      Account(remote_id=f"demo_acc_ar_{cid}",   company_id=cid, name="Accounts Receivable",   classification="ASSET", type="ACCOUNTS_RECEIVABLE", current_balance=Decimal("93100.00"), currency="USD"),
            "revenue": Account(remote_id=f"demo_acc_rev_{cid}",  company_id=cid, name="SaaS Subscription Revenue", classification="REVENUE", type="OTHER_INCOME", current_balance=Decimal("0"), currency="USD"),
            "aws":     Account(remote_id=f"demo_acc_aws_{cid}",  company_id=cid, name="AWS Cloud Infrastructure",  classification="EXPENSE", type="OTHER_EXPENSE", current_balance=Decimal("0"), currency="USD"),
            "payroll": Account(remote_id=f"demo_acc_pay_{cid}",  company_id=cid, name="Payroll & Benefits",        classification="EXPENSE", type="OTHER_EXPENSE", current_balance=Decimal("0"), currency="USD"),
            "office":  Account(remote_id=f"demo_acc_off_{cid}",  company_id=cid, name="Office & Rent (WeWork)",    classification="EXPENSE", type="OTHER_EXPENSE", current_balance=Decimal("0"), currency="USD"),
            "sales":   Account(remote_id=f"demo_acc_sal_{cid}",  company_id=cid, name="Sales & Marketing",         classification="EXPENSE", type="OTHER_EXPENSE", current_balance=Decimal("0"), currency="USD"),
        }
        for acc in accounts.values():
            db.add(acc)
        db.flush()

        # ── Contacts (Customers) ──────────────────────────────────────────────
        customer_data = [
            ("Meridian Bank",   "vendors@meridianbank.com",  "Net 30", "INV-2026-041", 41000, 0,     "OPEN",          date(2026,4,18), date(2026,5,18)),
            ("Acme Corp",       "ap@acmecorp.com",           "Net 45", "INV-2026-042", 18500, 18500, "PAID",          date(2026,4, 1), date(2026,5, 1)),
            ("Nexus Ventures",  "finance@nexusvc.com",       "Net 30", "INV-2026-043", 7200,  0,     "OVERDUE",       date(2026,3,21), date(2026,4,20)),
            ("Bloom Health",    "billing@bloomhealth.io",    "Net 30", "INV-2026-044", 4800,  0,     "OPEN",          date(2026,4,10), date(2026,5,10)),
            ("Vertex Systems",  "accounts@vertexsys.com",    "Net 60", "INV-2026-045", 22000, 11000, "PARTIALLY_PAID",date(2026,4,12), date(2026,6,11)),
            ("Skyline Retail",  "ap@skylineretail.com",      "Net 30", "INV-2026-046", 3600,  0,     "OPEN",          date(2026,4,15), date(2026,5,15)),
            ("Orion Logistics", "finance@orionlog.com",      "Net 30", "INV-2026-047", 2100,  0,     "DRAFT",         date(2026,4,20), date(2026,5,20)),
        ]
        contacts = {}
        inv_num = 41
        for (name, email, terms, inv_no, total, paid, status, issue_dt, due_dt) in customer_data:
            c = Contact(
                remote_id=f"demo_cust_{name.lower().replace(' ', '_')}_{cid}",
                company_id=cid,
                name=name,
                type="CUSTOMER",
                email=email,
                payment_terms=terms,
                currency="USD",
            )
            db.add(c)
            db.flush()
            contacts[name] = c

            balance = Decimal(str(total - paid))
            inv = Invoice(
                remote_id=f"demo_{inv_no}_{cid}",
                company_id=cid,
                invoice_number=inv_no,
                contact_id=c.id,
                issue_date=issue_dt,
                due_date=due_dt,
                payment_date=issue_dt + timedelta(days=5) if status == "PAID" else None,
                status=status,
                type="ACCOUNTS_RECEIVABLE",
                sub_total=Decimal(str(total)),
                tax_amount=Decimal("0"),
                total_amount=Decimal(str(total)),
                amount_paid=Decimal(str(paid)),
                amount_due=balance,
                currency="USD",
                memo=f"SaaS subscription — {name}",
            )
            db.add(inv)
            inv_num += 1

        # ── Contacts (Vendors) ────────────────────────────────────────────────
        vendor_data = [
            ("Amazon Web Services", "aws-billing@amazon.com"),
            ("Salesforce",          "billing@salesforce.com"),
            ("WeWork",              "billing@wework.com"),
            ("Rippling",            "billing@rippling.com"),
            ("OpenAI",              "billing@openai.com"),
        ]
        vendors = {}
        for (name, email) in vendor_data:
            v = Contact(
                remote_id=f"demo_vend_{name.lower().replace(' ', '_')}_{cid}",
                company_id=cid,
                name=name,
                type="VENDOR",
                email=email,
                currency="USD",
            )
            db.add(v)
            db.flush()
            vendors[name] = v

        # ── 12 months of Ledger Entries + Monthly Metrics ─────────────────────
        cash_balance = Decimal("2840000.00")

        for i in range(12):
            mo_date = _date(i)
            rev  = Decimal(str(MONTHLY_REVENUE[i]))
            aws  = Decimal(str(AWS_COSTS[i]))
            pay  = Decimal(str(PAYROLL_COSTS[i]))
            off  = Decimal(str(OFFICE_COSTS[i]))
            sls  = Decimal(str(SALES_COSTS[i]))
            total_exp = aws + pay + off + sls
            net_flow  = rev - total_exp
            cash_balance += net_flow

            # Revenue entry
            db.add(FinancialLedgerEntry(
                company_id=cid, transaction_date=mo_date,
                amount=rev, currency="USD", amount_inr=rev * USD_TO_INR,
                entry_type=LedgerEntryType.CREDIT, category=LedgerCategory.REVENUE,
                product_tag=LedgerProductTag.ORCHARD, office_tag=LedgerOfficeTag.NA,
                source=LedgerSource.SANDBOX, description=f"SaaS subscription revenue — {mo_date.strftime('%b %Y')}",
                entered_by_role=LedgerEnteredByRole.FINANCE, is_recurring=True,
            ))

            # AWS expense
            db.add(FinancialLedgerEntry(
                company_id=cid, transaction_date=mo_date,
                amount=aws, currency="USD", amount_inr=aws * USD_TO_INR,
                entry_type=LedgerEntryType.DEBIT, category=LedgerCategory.TECH_COST,
                product_tag=LedgerProductTag.SHARED, office_tag=LedgerOfficeTag.NA,
                source=LedgerSource.AWS_BILLING, description=f"AWS infrastructure — {mo_date.strftime('%b %Y')}",
                entered_by_role=LedgerEnteredByRole.CTO, is_recurring=True,
                reference_id=f"aws-{mo_date.isoformat()}",
            ))

            # Payroll expense
            db.add(FinancialLedgerEntry(
                company_id=cid, transaction_date=mo_date,
                amount=pay, currency="USD", amount_inr=pay * USD_TO_INR,
                entry_type=LedgerEntryType.DEBIT, category=LedgerCategory.PAYROLL,
                product_tag=LedgerProductTag.SHARED, office_tag=LedgerOfficeTag.NA,
                source=LedgerSource.SANDBOX, description=f"Payroll & benefits — {mo_date.strftime('%b %Y')}",
                entered_by_role=LedgerEnteredByRole.FINANCE, is_recurring=True,
            ))

            # Office expense
            db.add(FinancialLedgerEntry(
                company_id=cid, transaction_date=mo_date,
                amount=off, currency="USD", amount_inr=off * USD_TO_INR,
                entry_type=LedgerEntryType.DEBIT, category=LedgerCategory.OFFICE_EXPENSE,
                product_tag=LedgerProductTag.SHARED, office_tag=LedgerOfficeTag.NA,
                source=LedgerSource.SANDBOX, description=f"WeWork office rent — {mo_date.strftime('%b %Y')}",
                entered_by_role=LedgerEnteredByRole.FINANCE, is_recurring=True,
            ))

            # Sales & marketing expense
            db.add(FinancialLedgerEntry(
                company_id=cid, transaction_date=mo_date,
                amount=sls, currency="USD", amount_inr=sls * USD_TO_INR,
                entry_type=LedgerEntryType.DEBIT, category=LedgerCategory.MARKETING,
                product_tag=LedgerProductTag.ORCHARD, office_tag=LedgerOfficeTag.NA,
                source=LedgerSource.SANDBOX, description=f"Sales & marketing — {mo_date.strftime('%b %Y')}",
                entered_by_role=LedgerEnteredByRole.CSO, is_recurring=True,
            ))

            # Monthly metric snapshot
            runway = float(cash_balance) / float(total_exp) if total_exp > 0 else 0
            db.add(MonthlyMetric(
                company_id=cid,
                metric_month=mo_date,
                total_revenue=rev,
                total_expenses=total_exp,
                total_tax_liability=rev * Decimal("0.21"),
                net_cash_flow=net_flow,
                burn_rate=total_exp,
                runway_months=Decimal(str(round(runway, 2))),
                ending_cash=cash_balance,
            ))

        # ── Duplicate transaction anomaly (anomaly #3) ───────────────────────
        dup_date = date(2026, 1, 15)
        for _ in range(2):
            db.add(FinancialLedgerEntry(
                company_id=cid, transaction_date=dup_date,
                amount=Decimal("1200"), currency="USD", amount_inr=Decimal("1200") * USD_TO_INR,
                entry_type=LedgerEntryType.DEBIT, category=LedgerCategory.TECH_COST,
                product_tag=LedgerProductTag.SHARED, office_tag=LedgerOfficeTag.NA,
                source=LedgerSource.SANDBOX, description="Rippling payroll platform — Jan 2026",
                entered_by_role=LedgerEnteredByRole.FINANCE, is_recurring=False,
                reference_id="rippling-jan-2026-dup",
            ))

        # ── Anomaly Records (pre-seeded for dashboard) ────────────────────────
        anomaly_records = [
            Anomaly(
                remote_id=f"demo_anom_1_{cid}", company_id=cid,
                anomaly_date=date(2025, 11, 1), severity="critical", type="vendor_spike",
                description="AWS infrastructure cost spike: $18,245 vs expected $12,100 (+50.6%). Possible untagged EC2 instances.",
                expected_value=Decimal("12100"), actual_value=Decimal("18245"), status="open",
            ),
            Anomaly(
                remote_id=f"demo_anom_2_{cid}", company_id=cid,
                anomaly_date=date(2025, 10, 1), severity="warning", type="payroll_drift",
                description="Payroll cost growing 5%/month for 4 consecutive months ($85K → $103K). No corresponding headcount approval logged.",
                expected_value=Decimal("85000"), actual_value=Decimal("103318"), status="open",
            ),
            Anomaly(
                remote_id=f"demo_anom_3_{cid}", company_id=cid,
                anomaly_date=date(2026, 1, 15), severity="warning", type="duplicate_transaction",
                description="Duplicate transaction detected: Rippling $1,200 charged twice on 2026-01-15.",
                expected_value=Decimal("1200"), actual_value=Decimal("2400"), status="open",
            ),
            Anomaly(
                remote_id=f"demo_anom_4_{cid}", company_id=cid,
                anomaly_date=date(2025, 8, 1), severity="warning", type="customer_churn",
                description="Acme Corp MRR dropped from $18,500 to $8,000 in Aug 2025. Possible partial cancellation.",
                expected_value=Decimal("18500"), actual_value=Decimal("8000"), status="resolved",
            ),
            Anomaly(
                remote_id=f"demo_anom_5_{cid}", company_id=cid,
                anomaly_date=date(2026, 1, 1), severity="warning", type="late_payment",
                description="Vertex Systems invoice INV-2026-045 ($22,000) is 67 days past due. Payment terms: Net 60.",
                expected_value=Decimal("22000"), actual_value=Decimal("11000"), status="open",
            ),
            Anomaly(
                remote_id=f"demo_anom_6_{cid}", company_id=cid,
                anomaly_date=date(2026, 2, 1), severity="warning", type="new_vendor_spike",
                description="Unbudgeted vendor payment: OpenAI API $4,500 in Feb 2026. No PO or approval on file.",
                expected_value=Decimal("0"), actual_value=Decimal("4500"), status="open",
            ),
            Anomaly(
                remote_id=f"demo_anom_7_{cid}", company_id=cid,
                anomaly_date=date(2026, 3, 1), severity="info", type="bank_reconciliation_gap",
                description="3 bank transactions in Mar 2026 remain unmatched in GL. Total unreconciled: $2,340.",
                expected_value=Decimal("0"), actual_value=Decimal("2340"), status="open",
            ),
        ]
        for anom in anomaly_records:
            db.add(anom)

        db.commit()
        print(f"  ✅  Demo seed complete: 12 months data, 7 invoices, 7 anomalies, 17 contacts")
        print(f"  Company ID: {cid}")

    except Exception as e:
        db.rollback()
        print(f"  ❌  Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding Vireon demo data...")
    seed()
    print("Done.")
