from datetime import date, timedelta
from decimal import Decimal
import uuid
from unittest import mock

import models
from agent import tools as agent_tools


def _seed_company_with_invoices(db_session):
    company = models.Company(name="FO Co", stage="seed", initial_cash=Decimal("80000"))
    db_session.add(company)
    db_session.flush()

    ap_invoice = models.Invoice(
        remote_id=f"ap-{uuid.uuid4()}",
        company_id=company.id,
        invoice_number=f"AP-{uuid.uuid4().hex[:8]}",
        issue_date=date.today() - timedelta(days=10),
        due_date=date.today() + timedelta(days=5),
        status="OPEN",
        type="ACCOUNTS_PAYABLE",
        sub_total=Decimal("3000"),
        tax_amount=Decimal("0"),
        total_amount=Decimal("3000"),
        amount_paid=Decimal("0"),
        amount_due=Decimal("3000"),
        currency="USD",
    )
    ar_invoice = models.Invoice(
        remote_id=f"ar-{uuid.uuid4()}",
        company_id=company.id,
        invoice_number=f"AR-{uuid.uuid4().hex[:8]}",
        issue_date=date.today() - timedelta(days=20),
        due_date=date.today() - timedelta(days=2),
        status="OPEN",
        type="ACCOUNTS_RECEIVABLE",
        sub_total=Decimal("4500"),
        tax_amount=Decimal("0"),
        total_amount=Decimal("4500"),
        amount_paid=Decimal("0"),
        amount_due=Decimal("4500"),
        currency="USD",
    )
    db_session.add_all([ap_invoice, ar_invoice])
    db_session.commit()
    return company, ap_invoice, ar_invoice


def test_finance_agent_invoice_and_payment_tools(db_session):
    company, ap_invoice, _ = _seed_company_with_invoices(db_session)
    company_id = company.id  # Capture ID before any tool commits

    # Mock _get_db to return test session for tool execution
    with mock.patch("agent.tools._get_db", return_value=db_session):
        batch_result = agent_tools.process_invoice_batch.invoke(
            {"invoice_ids": [ap_invoice.id], "action": "mark_paid"}
        )
        assert batch_result["processed"] == 1

        payment_result = agent_tools.schedule_payments.invoke({"payment_run_id": uuid.uuid4()})
        assert "scheduled_count" in payment_result

        optimize_result = agent_tools.optimize_vendor_payments.invoke(
            {"company_id": company_id, "timing": "cash_preserve"}
        )
        assert "recommendations" in optimize_result


def test_finance_agent_collections_and_tax_tools(db_session):
    company, _, _ = _seed_company_with_invoices(db_session)
    company_id = company.id  # Capture ID before any tool calls
    
    db_session.add(
        models.MonthlyMetric(
            company_id=company_id,
            metric_month=date.today().replace(day=1),
            total_revenue=Decimal("20000"),
            total_expenses=Decimal("15000"),
            ending_cash=Decimal("60000"),
        )
    )
    db_session.commit()

    with mock.patch("agent.tools._get_db", return_value=db_session):
        collections = agent_tools.run_collections_workflow.invoke(
            {"company_id": company_id, "strategy": "assertive"}
        )
        assert "overdue_count" in collections

        tax_data = agent_tools.prepare_tax_filing_data.invoke(
            {"tax_period": "2026-Q1", "company_id": company_id}
        )
        assert tax_data["status"] == "prepared"
