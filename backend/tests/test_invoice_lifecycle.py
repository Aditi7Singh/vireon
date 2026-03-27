from datetime import date, timedelta
from decimal import Decimal
import uuid

from fastapi.testclient import TestClient

import models
from database import SessionLocal
from main import app


client = TestClient(app)


def _seed_company_with_ar_invoice():
    db = SessionLocal()
    try:
        company = models.Company(
            name=f"Invoice Co {uuid.uuid4().hex[:8]}",
            stage="seed",
            initial_cash=Decimal("100000.00"),
        )
        db.add(company)
        db.flush()

        contact = models.Contact(
            remote_id=f"contact-{uuid.uuid4()}",
            company_id=company.id,
            name="Test Customer",
            type="CUSTOMER",
            email="customer@example.com",
            status="active",
            currency="USD",
        )
        db.add(contact)
        db.flush()

        ar_invoice = models.Invoice(
            remote_id=f"ar-{uuid.uuid4()}",
            company_id=company.id,
            contact_id=contact.id,
            invoice_number=f"INV-{uuid.uuid4().hex[:8]}",
            issue_date=date.today() - timedelta(days=40),
            due_date=date.today() - timedelta(days=5),
            status="OPEN",
            type="ACCOUNTS_RECEIVABLE",
            sub_total=Decimal("1000.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("1000.00"),
            amount_paid=Decimal("0.00"),
            amount_due=Decimal("1000.00"),
            currency="USD",
        )
        db.add(ar_invoice)

        ap_invoice = models.Invoice(
            remote_id=f"ap-{uuid.uuid4()}",
            company_id=company.id,
            invoice_number=f"BILL-{uuid.uuid4().hex[:8]}",
            issue_date=date.today() - timedelta(days=10),
            due_date=date.today() + timedelta(days=10),
            status="OPEN",
            type="ACCOUNTS_PAYABLE",
            sub_total=Decimal("500.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("500.00"),
            amount_paid=Decimal("0.00"),
            amount_due=Decimal("500.00"),
            currency="USD",
        )
        db.add(ap_invoice)

        db.commit()
        return str(company.id), str(ar_invoice.id)
    finally:
        db.close()


def test_invoice_lifecycle_mark_paid_writeoff_and_metrics():
    company_id, invoice_id = _seed_company_with_ar_invoice()

    queue_res = client.get(f"/api/v1/invoices/queue/{company_id}")
    assert queue_res.status_code == 200
    queue_payload = queue_res.json()
    assert queue_payload["count"] >= 1

    dso_res = client.get(f"/api/v1/invoices/dso/{company_id}")
    assert dso_res.status_code == 200
    dso_payload = dso_res.json()
    assert "dso_days" in dso_payload
    assert dso_payload["open_ar"] >= 0

    mark_paid_res = client.post(
        f"/api/v1/invoices/{invoice_id}/mark-paid",
        json={"payment_amount": 400.0},
    )
    assert mark_paid_res.status_code == 200
    mark_payload = mark_paid_res.json()
    assert mark_payload["status"] == "PARTIALLY_PAID"
    assert mark_payload["amount_due"] == 600.0

    writeoff_res = client.post(
        f"/api/v1/invoices/{invoice_id}/write-off",
        json={"reason": "Uncollectible"},
    )
    assert writeoff_res.status_code == 200
    writeoff_payload = writeoff_res.json()
    assert writeoff_payload["status"] == "VOID"
    assert writeoff_payload["written_off_amount"] == 600.0
