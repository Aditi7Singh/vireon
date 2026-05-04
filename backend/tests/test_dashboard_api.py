from fastapi.testclient import TestClient
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import database
import models
from main import app


client = TestClient(app)


def _create_user_token(username: str, role: str) -> str:
    create_res = client.post(
        "/api/v1/users/",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "password123",
            "role": role,
        },
    )
    assert create_res.status_code == 200, create_res.text

    token_res = client.post(
        "/api/v1/token",
        data={"username": username, "password": "password123"},
    )
    assert token_res.status_code == 200, token_res.text
    token = token_res.json().get("access_token")
    assert token
    return token


def _get_default_company_id() -> str:
    res = client.get("/api/v1/system/startup-health")
    assert res.status_code == 200
    payload = res.json()
    cid = payload.get("default_company_id")
    assert cid
    return cid


def test_dashboard_core_endpoints_return_success():
    company_id = _get_default_company_id()

    burn_summary = client.get(f"/api/v1/burn/summary/{company_id}?month=2026-03")
    assert burn_summary.status_code == 200

    burn_expenses = client.get(f"/api/v1/burn/expenses/{company_id}?month=2026-03")
    assert burn_expenses.status_code == 200

    metrics_history = client.get(f"/api/v1/metrics/history/{company_id}?months=6")
    assert metrics_history.status_code == 200


def test_finance_and_export_endpoints():
    company_id = _get_default_company_id()

    finance_token = _create_user_token("finance-pending-user", "FINANCE")

    pending = client.get(
        f"/api/v1/inputs/pending-review?company_id={company_id}",
        headers={"Authorization": f"Bearer {finance_token}"},
    )
    assert pending.status_code == 200

    csv_export = client.get(f"/api/v1/reports/export/ledger/csv?company_id={company_id}")
    assert csv_export.status_code == 200
    assert "text/csv" in csv_export.headers.get("content-type", "")

    pdf_export = client.get(f"/api/v1/reports/export/summary/pdf?company_id={company_id}")
    assert pdf_export.status_code == 200
    assert "application/pdf" in pdf_export.headers.get("content-type", "")


def test_role_gated_dashboard_actions_accept_jwt_role():
    company_id = _get_default_company_id()

    cto_token = _create_user_token("cto-gated-user", "CTO")
    finance_token = _create_user_token("finance-gated-user", "FINANCE")

    tech_cost = client.post(
        "/api/v1/inputs/tech-cost",
        json={
            "company_id": company_id,
            "cost_type": "saas_tool",
            "product_tag": "ai_lab",
            "amount_inr": 18000,
            "billing_period": "2026-04",
            "vendor_name": "Anthropic Claude",
            "description": "Claude subscription April 2026",
            "is_recurring": True,
        },
        headers={"Authorization": f"Bearer {cto_token}"},
    )
    assert tech_cost.status_code == 200, tech_cost.text

    pending = client.get(
        f"/api/v1/inputs/pending-review?company_id={company_id}",
        headers={"Authorization": f"Bearer {finance_token}"},
    )
    assert pending.status_code == 200, pending.text


def test_group_consolidated_pl_applies_intercompany_elimination():
    company_id = _get_default_company_id()

    db = database.SessionLocal()
    try:
        # Insert an intercompany-tagged credit entry and verify elimination toggle.
        db.add(
            models.FinancialLedgerEntry(
                id=uuid4(),
                company_id=UUID(company_id),
                transaction_date=date.today(),
                amount=Decimal("1000.00"),
                currency="INR",
                amount_inr=Decimal("1000.00"),
                entry_type=models.LedgerEntryType.CREDIT,
                category=models.LedgerCategory.REVENUE,
                product_tag=models.LedgerProductTag.SHARED,
                office_tag=models.LedgerOfficeTag.NA,
                source=models.LedgerSource.SANDBOX,
                description="Intercompany services recharge",
                entered_by_role=models.LedgerEnteredByRole.FINANCE,
                tags={"intercompany": True, "intercompany_counterparty_company_id": "demo-counterparty"},
            )
        )
        db.commit()
    finally:
        db.close()

    with_elimination = client.get(
        f"/api/v1/reports/pl/consolidated-group?company_ids={company_id}&apply_eliminations=true"
    )
    without_elimination = client.get(
        f"/api/v1/reports/pl/consolidated-group?company_ids={company_id}&apply_eliminations=false"
    )

    assert with_elimination.status_code == 200
    assert without_elimination.status_code == 200

    with_payload = with_elimination.json()
    without_payload = without_elimination.json()

    assert with_payload["eliminations_applied"] is True
    assert with_payload["eliminated_entries"] >= 1
    assert without_payload["eliminations_applied"] is False
    assert without_payload["consolidated_revenue_inr"] >= with_payload["consolidated_revenue_inr"]
