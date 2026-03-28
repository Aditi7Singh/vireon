from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_liveness_endpoint_returns_alive():
    response = client.get("/health/live")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "alive"
    assert payload["service"] == "vireon-backend"


def test_readiness_endpoint_returns_dependency_report():
    response = client.get("/health/ready")
    # Readiness may be 503 depending on dependency configuration; both are valid
    assert response.status_code in (200, 503)
    payload = response.json()

    assert "ready" in payload
    assert "checks" in payload
    assert "database" in payload["checks"]
    assert "redis" in payload["checks"]
