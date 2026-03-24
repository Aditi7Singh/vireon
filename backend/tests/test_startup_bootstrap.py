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
    assert "credential_readiness" in payload
    assert "connector_conflict_policy" in payload


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


def test_connector_conflict_policy_roundtrip():
    get_res = client.get("/api/v1/system/connectors/conflict-policy")
    assert get_res.status_code == 200
    assert "policy" in get_res.json()

    put_res = client.put(
        "/api/v1/system/connectors/conflict-policy",
        json={"merge": "manual_review", "plaid": "latest_timestamp_wins"},
    )
    assert put_res.status_code == 200
    put_payload = put_res.json()
    assert put_payload["success"] is True
    assert put_payload["policy"]["merge"] == "manual_review"
    assert put_payload["policy"]["plaid"] == "latest_timestamp_wins"
