from datetime import date, timedelta
from decimal import Decimal
import uuid

from fastapi.testclient import TestClient

import models
from database import SessionLocal
from main import app


client = TestClient(app)


def _seed_company_with_financials() -> str:
    db = SessionLocal()
    try:
        company = models.Company(
            name=f"Ops Co {uuid.uuid4().hex[:8]}",
            stage="seed",
            initial_cash=Decimal("300000.00"),
        )
        db.add(company)
        db.flush()

        vendor = models.Contact(
            remote_id=f"vendor-{uuid.uuid4()}",
            company_id=company.id,
            name="Cloud Vendor",
            type="VENDOR",
            email="vendor@example.com",
            status="active",
            currency="USD",
        )
        db.add(vendor)
        db.flush()

        month_a = (date.today().replace(day=1) - timedelta(days=40)).replace(day=1)
        month_b = date.today().replace(day=1)

        db.add(
            models.MonthlyMetric(
                company_id=company.id,
                metric_month=month_a,
                total_revenue=Decimal("70000"),
                total_expenses=Decimal("90000"),
                ending_cash=Decimal("320000"),
                burn_rate=Decimal("20000"),
                runway_months=Decimal("16"),
            )
        )
        db.add(
            models.MonthlyMetric(
                company_id=company.id,
                metric_month=month_b,
                total_revenue=Decimal("80000"),
                total_expenses=Decimal("95000"),
                ending_cash=Decimal("300000"),
                burn_rate=Decimal("15000"),
                runway_months=Decimal("20"),
            )
        )

        db.add(
            models.Invoice(
                remote_id=f"ar-{uuid.uuid4()}",
                company_id=company.id,
                invoice_number=f"AR-{uuid.uuid4().hex[:8]}",
                issue_date=date.today() - timedelta(days=25),
                due_date=date.today() - timedelta(days=3),
                status="OPEN",
                type="ACCOUNTS_RECEIVABLE",
                sub_total=Decimal("12000"),
                tax_amount=Decimal("0"),
                total_amount=Decimal("12000"),
                amount_paid=Decimal("0"),
                amount_due=Decimal("12000"),
                currency="USD",
            )
        )
        db.add(
            models.Invoice(
                remote_id=f"ap-{uuid.uuid4()}",
                company_id=company.id,
                contact_id=vendor.id,
                invoice_number=f"AP-{uuid.uuid4().hex[:8]}",
                issue_date=date.today() - timedelta(days=30),
                due_date=date.today() - timedelta(days=5),
                payment_date=date.today() - timedelta(days=1),
                status="PAID",
                type="ACCOUNTS_PAYABLE",
                sub_total=Decimal("5000"),
                tax_amount=Decimal("0"),
                total_amount=Decimal("5000"),
                amount_paid=Decimal("5000"),
                amount_due=Decimal("0"),
                currency="USD",
            )
        )

        db.add(
            models.FinancialLedgerEntry(
                company_id=company.id,
                transaction_date=date.today() - timedelta(days=3),
                amount=Decimal("2500"),
                currency="INR",
                amount_inr=Decimal("2500"),
                entry_type=models.LedgerEntryType.DEBIT,
                category=models.LedgerCategory.NON_TECH_COST,
                description="Ops spend",
                source=models.LedgerSource.MANUAL_FINANCE,
                entered_by_role=models.LedgerEnteredByRole.FINANCE,
            )
        )

        db.add(
            models.Forecast(
                company_id=company.id,
                forecast_date=(date.today().replace(day=1) + timedelta(days=31)).replace(day=1),
                mrr_predicted=Decimal("85000"),
                cash_predicted=Decimal("285000"),
                confidence_lower=Decimal("250000"),
                confidence_upper=Decimal("310000"),
            )
        )

        db.commit()
        return str(company.id)
    finally:
        db.close()


def test_remaining_work_endpoints_return_valid_payloads():
    company_id = _seed_company_with_financials()

    comparative = client.get(f"/api/v1/metrics/comparative/{company_id}")
    assert comparative.status_code == 200
    assert "metrics" in comparative.json()

    vendors = client.get(f"/api/v1/vendors/performance/{company_id}")
    assert vendors.status_code == 200
    assert vendors.json()["count"] >= 1

    cashflow = client.get(f"/api/v1/cash-flow/forecast/{company_id}")
    assert cashflow.status_code == 200
    assert "forecast" in cashflow.json()

    wc = client.get(f"/api/v1/working-capital/optimize/{company_id}")
    assert wc.status_code == 200
    assert "recommendations" in wc.json()

    credit = client.get(f"/api/v1/credit/risk/{company_id}")
    assert credit.status_code == 200
    assert "score" in credit.json()


def test_custom_report_builder_and_warehouse_export():
    company_id = _seed_company_with_financials()

    report = client.post(
        "/api/v1/reports/custom/build",
        json={
            "company_id": company_id,
            "sections": ["scorecard", "collections", "runway"],
        },
    )
    assert report.status_code == 200
    assert "data" in report.json()

    export = client.post(
        "/api/v1/reports/export/warehouse",
        json={
            "company_id": company_id,
            "provider": "bigquery",
            "dataset": "finance",
            "table": "ledger",
        },
    )
    assert export.status_code == 200
    payload = export.json()
    assert payload["success"] is True
    assert payload["provider"] == "bigquery"
