from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch
import uuid

from fastapi.testclient import TestClient

import models
from database import SessionLocal
from main import app


client = TestClient(app)


def _seed_company_for_forecast_and_docs():
    db = SessionLocal()
    try:
        company = models.Company(
            name=f"Partial Features Co {uuid.uuid4().hex[:8]}",
            stage="seed",
            initial_cash=Decimal("250000.00"),
        )
        db.add(company)
        db.flush()

        # Seed ledger for forecasting endpoints.
        for i in range(1, 8):
            month_date = (date.today().replace(day=1) - timedelta(days=30 * (8 - i))).replace(day=1)
            db.add(
                models.FinancialLedgerEntry(
                    company_id=company.id,
                    transaction_date=month_date,
                    amount=Decimal("10000.00"),
                    currency="INR",
                    amount_inr=Decimal("10000.00"),
                    entry_type=models.LedgerEntryType.DEBIT,
                    category=models.LedgerCategory.TECH_COST,
                    description=f"Burn {i}",
                    source=models.LedgerSource.MANUAL_FINANCE,
                    entered_by_role=models.LedgerEnteredByRole.FINANCE,
                )
            )
            db.add(
                models.FinancialLedgerEntry(
                    company_id=company.id,
                    transaction_date=month_date,
                    amount=Decimal("7000.00"),
                    currency="INR",
                    amount_inr=Decimal("7000.00"),
                    entry_type=models.LedgerEntryType.CREDIT,
                    category=models.LedgerCategory.REVENUE,
                    description=f"Revenue {i}",
                    source=models.LedgerSource.MANUAL_FINANCE,
                    entered_by_role=models.LedgerEnteredByRole.FINANCE,
                )
            )

            db.add(
                models.MonthlyMetric(
                    company_id=company.id,
                    metric_month=month_date,
                    total_revenue=Decimal("7000.00"),
                    total_expenses=Decimal("10000.00"),
                    ending_cash=Decimal(str(250000 - i * 3000)),
                    burn_rate=Decimal("3000.00"),
                    runway_months=Decimal("12.0"),
                )
            )

        doc = models.Document(
            company_id=company.id,
            file_name="vendor_invoice.pdf",
            file_type="application/pdf",
            status="processed",
            ocr_text="Tax Invoice\nBill To Example Corp\nTotal 12,500",
            extracted_data={},
            structured_data={},
        )
        db.add(doc)
        db.commit()
        return str(company.id), str(doc.id)
    finally:
        db.close()


def test_live_fx_sync_endpoint_uses_provider_payload():
    with patch("api.routers.fx.fetch_live_inr_rates") as mock_fetch:
        mock_fetch.return_value = {
            "INR": Decimal("1"),
            "USD": Decimal("82.5"),
            "EUR": Decimal("89.1"),
        }
        response = client.post("/api/v1/fx/sync-live", json={"currencies": ["USD", "EUR"]})
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["source"] in {"live_provider", "fallback_defaults"}
        assert "USD" in payload["rates"]


def test_forecast_ensemble_and_monitoring_endpoints():
    company_id, _ = _seed_company_for_forecast_and_docs()

    ensemble = client.get(f"/api/v1/forecast/ensemble/{company_id}")
    assert ensemble.status_code == 200
    ep = ensemble.json()
    assert "runway_months" in ep
    assert "weights" in ep

    retrain = client.post(f"/api/v1/forecast/retrain/{company_id}")
    assert retrain.status_code == 200
    rp = retrain.json()
    assert rp["success"] is True
    assert "monitoring" in rp

    monitor = client.get(f"/api/v1/forecast/monitor/{company_id}")
    assert monitor.status_code == 200
    mp = monitor.json()
    assert "mape_cash" in mp


def test_document_classification_and_workflow_actions():
    _, document_id = _seed_company_for_forecast_and_docs()

    classify = client.post(f"/api/v1/documents/{document_id}/classify")
    assert classify.status_code == 200
    assert classify.json()["success"] is True

    approve = client.post(
        f"/api/v1/documents/{document_id}/workflow",
        json={"action": "approve", "note": "Reviewed and accepted"},
    )
    assert approve.status_code == 200
    assert approve.json()["success"] is True
