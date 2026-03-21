from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_startup_health_endpoint_returns_readiness_payload():
    response = client.get("/api/v1/system/startup-health")
    assert response.status_code == 200
    payload = response.json()

    assert "status" in payload
    assert "checks" in payload
    assert "table_readiness" in payload
    assert "issues" in payload
    assert "actions" in payload

    checks = payload["checks"]
    assert "companies" in checks
    assert "monthly_metrics" in checks
    assert "exchange_rates" in checks


def test_fx_default_sync_and_convert():
    sync_res = client.post("/api/v1/fx/sync-default")
    assert sync_res.status_code == 200

    convert_res = client.post(
        "/api/v1/fx/convert",
        json={"amount": 100, "base_currency": "USD", "target_currency": "INR"},
    )
    assert convert_res.status_code == 200
    payload = convert_res.json()
    assert payload["currency"] == "INR"
    assert payload["converted_amount"] > 0
