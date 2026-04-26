from datetime import date
from decimal import Decimal
from unittest import mock

import models
from agent import tools as agent_tools


def _seed_company(db_session):
    company = models.Company(name="FM Co", stage="seed", initial_cash=Decimal("100000"))
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


def test_finance_manager_budget_and_close_tools(db_session):
    company = _seed_company(db_session)
    company_id = company.id  # Capture ID before any tool calls

    with mock.patch("agent.tools._get_db", return_value=db_session):
        budget_result = agent_tools.manage_budget.invoke(
            {"month": "2026-03", "category": "marketing", "amount": 12000.0}
        )
        assert budget_result["success"] is True

        close_result = agent_tools.create_period_close.invoke(
            {"period": "2026-03", "company_id": company_id}
        )
        assert close_result["period"] == "2026-03"
        assert "readiness_score" in close_result


def test_finance_manager_reconciliation_and_consolidation_tools(db_session):
    parent = _seed_company(db_session)
    sub = models.Company(name="FM Sub", stage="seed", initial_cash=Decimal("50000"))
    db_session.add(sub)
    db_session.commit()
    parent_id = parent.id
    sub_id = sub.id

    db_session.add(
        models.MonthlyMetric(
            company_id=parent_id,
            metric_month=date.today().replace(day=1),
            total_revenue=Decimal("10000"),
            total_expenses=Decimal("8000"),
            ending_cash=Decimal("75000"),
        )
    )
    db_session.add(
        models.MonthlyMetric(
            company_id=sub_id,
            metric_month=date.today().replace(day=1),
            total_revenue=Decimal("7000"),
            total_expenses=Decimal("6000"),
            ending_cash=Decimal("42000"),
        )
    )
    db_session.commit()

    with mock.patch("agent.tools._get_db", return_value=db_session):
        recon = agent_tools.run_reconciliation.invoke({"period": "2026-03", "company_id": parent_id})
        assert recon["period"] == "2026-03"

        cons = agent_tools.get_consolidated_view.invoke({"entity_ids": [parent_id, sub_id]})
        assert "balance_sheet" in cons
        assert "pnl" in cons
