import pytest
from fastapi.testclient import TestClient
from datetime import date
from decimal import Decimal

import models
from analytics import metrics

def test_math_engine_metrics():
    revenue = 50000.0
    expenses = 60000.0
    cash = 200000.0
    
    net_burn = metrics.calculate_net_burn(revenue, expenses)
    assert net_burn == 10000.0
    
    runway = metrics.calculate_runway(cash, net_burn)
    assert runway == 20.0
    
    arr = metrics.calculate_arr(revenue)
    assert arr == 600000.0

def test_get_financial_summary_not_found(client: TestClient):
    # Register and get token
    client.post("/users/", json={"username": "testuser", "email": "test@test.com", "password": "password"})
    token_resp = client.post("/token", data={"username": "testuser", "password": "password"})
    token = token_resp.json()["access_token"]
    
    import uuid
    dummy_company_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"/metrics/financials/{dummy_company_id}", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "No financial metrics found for this company"
