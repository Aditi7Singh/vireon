"""Test new finance API endpoints"""
import uuid
from decimal import Decimal

import models


def test_close_endpoints(client, db_session):
    """Test close router endpoints"""
    company = models.Company(name="Close Co", stage="seed", initial_cash=Decimal("150000"))
    db_session.add(company)
    db_session.commit()
    
    response = client.post(
        "/close/validate",
        json={"company_id": str(company.id), "period": "2026-03"}
    )
    assert response.status_code in (200, 201)


def test_approvals_endpoints(client, db_session):
    """Test approvals router endpoints"""
    company = models.Company(name="Approvals Co", stage="seed", initial_cash=Decimal("100000"))
    db_session.add(company)
    db_session.commit()
    
    response = client.post(
        "/approvals/workflows",
        json={
            "company_id": str(company.id),
            "name": "Test Workflow",
            "entity_type": "PurchaseOrder",
            "steps": [
                {
                    "step_order": 1,
                    "approver_role": "Manager",
                    "min_amount": "0",
                    "max_amount": "10000",
                }
            ]
        }
    )
    assert response.status_code in (200, 201)


def test_planning_budget_endpoints(client, db_session):
    """Test enhanced planning router budget endpoints"""
    company = models.Company(name="Planning Co", stage="seed", initial_cash=Decimal("100000"))
    db_session.add(company)
    db_session.commit()
    
    response = client.post(
        "/planning/budgets",
        json={
            "company_id": str(company.id),
            "period": "2026-Q1",
            "budgets": {
                "marketing": 5000.0,
                "operations": 3000.0,
            }
        }
    )
    assert response.status_code in (200, 201)


def test_agent_finance_chat_endpoint(client, db_session):
    """Test new finance agent chat endpoints"""
    company = models.Company(name="Agent Co", stage="seed", initial_cash=Decimal("100000"))
    db_session.add(company)
    db_session.commit()
    
    response = client.post(
        "/agent/finance/chat",
        json={
            "message": "What are my current invoices?",
            "session_id": str(uuid.uuid4()),
            "company_id": str(company.id),
        }
    )
    assert response.status_code in (200, 201)
    
    response = client.post(
        "/agent/finance-manager/chat",
        json={
            "message": "Can you validate the close for March?",
            "session_id": str(uuid.uuid4()),
            "company_id": str(company.id),
        }
    )
    assert response.status_code in (200, 201)
