from datetime import date, timedelta
from decimal import Decimal
import uuid
from unittest import mock

import models
from agent import tools as agent_tools


def _seed_operational_company(db_session):
    company = models.Company(name="FO Int", stage="seed", initial_cash=Decimal("100000"))
    db_session.add(company)
    db_session.flush()

    invoices = [
        models.Invoice(
            remote_id=f"ap-{uuid.uuid4()}",
            company_id=company.id,
            invoice_number=f"AP-{uuid.uuid4().hex[:8]}",
            issue_date=date.today() - timedelta(days=12),
            due_date=date.today() + timedelta(days=4),
            status="OPEN",
            type="ACCOUNTS_PAYABLE",
            sub_total=Decimal("2500"),
            tax_amount=Decimal("0"),
            total_amount=Decimal("2500"),
            amount_paid=Decimal("0"),
            amount_due=Decimal("2500"),
            currency="USD",
        ),
        models.Invoice(
            remote_id=f"ar-{uuid.uuid4()}",
            company_id=company.id,
            invoice_number=f"AR-{uuid.uuid4().hex[:8]}",
            issue_date=date.today() - timedelta(days=25),
            due_date=date.today() - timedelta(days=3),
            status="OPEN",
            type="ACCOUNTS_RECEIVABLE",
            sub_total=Decimal("4000"),
            tax_amount=Decimal("0"),
            total_amount=Decimal("4000"),
            amount_paid=Decimal("0"),
            amount_due=Decimal("4000"),
            currency="USD",
        ),
    ]
    db_session.add_all(invoices)
    db_session.add(
        models.MonthlyMetric(
            company_id=company.id,
            metric_month=date.today().replace(day=1),
            total_revenue=Decimal("30000"),
            total_expenses=Decimal("21000"),
            ending_cash=Decimal("92000"),
        )
    )
    db_session.commit()
    return company, invoices


def test_finance_agent_invoice_batch_and_payment_optimization(db_session):
    company, invoices = _seed_operational_company(db_session)
    company_id = company.id  # Capture ID before any tool commits

    # Mock _get_db to return test session for tool execution
    with mock.patch("agent.tools._get_db", return_value=db_session):
        batch = agent_tools.process_invoice_batch.invoke({"invoice_ids": [invoices[0].id], "action": "submit"})
        assert batch["processed"] == 1
        
        optimize = agent_tools.optimize_vendor_payments.invoke({"company_id": company_id, "timing": "early_discounts"})
        assert "recommendations" in optimize


def test_finance_agent_collections_workflow_execution(db_session):
    company, _ = _seed_operational_company(db_session)
    company_id = company.id  # Capture ID before any tool calls
    
    with mock.patch("agent.tools._get_db", return_value=db_session):
        collections = agent_tools.run_collections_workflow.invoke({"company_id": company_id, "strategy": "tiered"})
        assert "overdue_count" in collections
        assert "next_actions" in collections
