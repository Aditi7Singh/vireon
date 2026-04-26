from datetime import date, timedelta
from decimal import Decimal
import uuid

from fastapi.testclient import TestClient

import models
from database import SessionLocal
from main import app


client = TestClient(app)


def _seed_company_with_metrics_and_invoices():
    db = SessionLocal()
    try:
        company = models.Company(
            name=f"QA Co {uuid.uuid4().hex[:8]}",
            stage="seed",
            initial_cash=Decimal("500000.00"),
        )
        db.add(company)
        db.flush()

        latest_month = date.today().replace(day=1)
        prev_month = (latest_month - timedelta(days=1)).replace(day=1)

        db.add(
            models.MonthlyMetric(
                company_id=company.id,
                metric_month=prev_month,
                total_revenue=Decimal("120000.00"),
                total_expenses=Decimal("180000.00"),
                ending_cash=Decimal("650000.00"),
                burn_rate=Decimal("60000.00"),
                runway_months=Decimal("10.83"),
            )
        )
        db.add(
            models.MonthlyMetric(
                company_id=company.id,
                metric_month=latest_month,
                total_revenue=Decimal("90000.00"),
                total_expenses=Decimal("170000.00"),
                ending_cash=Decimal("500000.00"),
                burn_rate=Decimal("80000.00"),
                runway_months=Decimal("6.25"),
            )
        )

        db.add(
            models.Invoice(
                remote_id=f"ar-{uuid.uuid4()}",
                company_id=company.id,
                invoice_number=f"AR-{uuid.uuid4().hex[:10]}",
                issue_date=date.today() - timedelta(days=45),
                due_date=date.today() - timedelta(days=10),
                status="OPEN",
                type="ACCOUNTS_RECEIVABLE",
                sub_total=Decimal("10000.00"),
                tax_amount=Decimal("0.00"),
                total_amount=Decimal("10000.00"),
                amount_paid=Decimal("0.00"),
                amount_due=Decimal("10000.00"),
                currency="USD",
            )
        )
        db.add(
            models.Invoice(
                remote_id=f"ap-{uuid.uuid4()}",
                company_id=company.id,
                invoice_number=f"AP-{uuid.uuid4().hex[:10]}",
                issue_date=date.today() - timedelta(days=20),
                due_date=date.today() + timedelta(days=7),
                status="OPEN",
                type="ACCOUNTS_PAYABLE",
                sub_total=Decimal("3000.00"),
                tax_amount=Decimal("0.00"),
                total_amount=Decimal("3000.00"),
                amount_paid=Decimal("0.00"),
                amount_due=Decimal("3000.00"),
                currency="USD",
            )
        )

        db.commit()
        return str(company.id)
    finally:
        db.close()


def test_revenue_endpoint_is_deterministic_not_placeholder():
    company_id = _seed_company_with_metrics_and_invoices()

    response = client.get(f"/api/v1/revenue/{company_id}")
    assert response.status_code == 200
    payload = response.json()

    assert payload["mrr"] == 90000.0
    assert payload["arr"] == 1080000.0
    assert payload["growth_pct"] == -25.0
    assert payload["churn_rate"] == 25.0
    assert payload["nrr"] == 75.0


def test_cash_balance_and_aging_are_invoice_driven():
    company_id = _seed_company_with_metrics_and_invoices()

    cash_res = client.get(f"/api/v1/cash-balance/{company_id}")
    assert cash_res.status_code == 200
    cash_payload = cash_res.json()

    assert cash_payload["cash"] == 500000.0
    assert cash_payload["ar"] == 10000.0
    assert cash_payload["ap"] == 3000.0
    assert cash_payload["net_cash"] == 507000.0

    aging_res = client.get(f"/api/v1/collections/aging/{company_id}")
    assert aging_res.status_code == 200
    aging = aging_res.json()

    assert aging["ar"]["total_open"] == 10000.0
    assert aging["ap"]["total_open"] == 3000.0
    assert len(aging["overdue_receivables"]) >= 1
