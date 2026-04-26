from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch
import uuid

from fastapi.testclient import TestClient

import models
from database import SessionLocal
from main import app


client = TestClient(app)


def _seed_company() -> str:
    db = SessionLocal()
    try:
        company = models.Company(
            name=f"Plaid Co {uuid.uuid4().hex[:8]}",
            stage="seed",
            initial_cash=Decimal("100000.00"),
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        return str(company.id)
    finally:
        db.close()


@patch("api.routers.banking.plaid_service.get_transactions")
@patch("api.routers.banking.plaid_service.get_accounts")
def test_plaid_sync_transactions_ingests_rows(mock_get_accounts, mock_get_transactions):
    company_id = _seed_company()

    mock_get_accounts.return_value = [
        {
            "account_id": "acc_1",
            "name": "Checking",
            "official_name": "Primary Checking",
            "mask": "1234",
            "subtype": "checking",
            "balances": {"iso_currency_code": "USD"},
        }
    ]
    mock_get_transactions.return_value = [
        {
            "account_id": "acc_1",
            "date": (date.today() - timedelta(days=1)).isoformat(),
            "name": "AWS Monthly Bill",
            "merchant_name": "Amazon Web Services",
            "amount": 1499.5,
        }
    ]

    response = client.post(
        "/api/v1/banking/plaid/sync-transactions",
        json={
            "company_id": company_id,
            "access_token": "access-sandbox-123",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["accounts_discovered"] == 1
    assert payload["transactions_fetched"] == 1
    assert payload["transactions_inserted"] == 1
