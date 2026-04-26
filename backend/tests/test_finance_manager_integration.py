from datetime import date
from decimal import Decimal
import uuid

import models
from services.close_service import CloseService
from services.consolidation_service import ConsolidationService
from services import planning as planning_service


def test_finance_manager_budget_cycle(db_session):
    company = models.Company(name="FM Int", stage="seed", initial_cash=Decimal("200000"))
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)

    budget = planning_service.create_budget(db_session, company.id, "2026-03", {"marketing": 10000, "payroll": 50000})
    submit = planning_service.submit_for_approval(db_session, budget.id)
    approve = planning_service.approve_budget(db_session, budget.id, uuid.uuid4())
    utilization = planning_service.track_budget_utilization(db_session, company.id, "2026-03")

    assert submit["success"] is True
    assert approve["success"] is True
    assert utilization["success"] is True


def test_finance_manager_close_cycle(db_session):
    company = models.Company(name="FM Close Int", stage="seed", initial_cash=Decimal("150000"))
    db_session.add(company)
    db_session.flush()
    db_session.add(
        models.MonthlyMetric(
            company_id=company.id,
            metric_month=date.today().replace(day=1),
            total_revenue=Decimal("30000"),
            total_expenses=Decimal("24000"),
            ending_cash=Decimal("145000"),
        )
    )
    db_session.commit()

    svc = CloseService(db_session)
    readiness = svc.validate_close_readiness(company.id, "2026-03")
    accruals = svc.calculate_accruals(company.id, "2026-03")
    lock = svc.lock_period(company.id, "2026-03", uuid.uuid4())

    assert readiness["period"] == "2026-03"
    assert "accruals" in accruals
    assert lock["status"] == "locked"


def test_finance_manager_consolidation_cycle(db_session):
    parent = models.Company(name="Parent Int", stage="seed", initial_cash=Decimal("220000"))
    sub = models.Company(name="Sub Int", stage="seed", initial_cash=Decimal("70000"))
    db_session.add_all([parent, sub])
    db_session.flush()
    for company, rev, exp, cash in [(parent, 50000, 40000, 200000), (sub, 20000, 18000, 60000)]:
        db_session.add(
            models.MonthlyMetric(
                company_id=company.id,
                metric_month=date.today().replace(day=1),
                total_revenue=Decimal(str(rev)),
                total_expenses=Decimal(str(exp)),
                ending_cash=Decimal(str(cash)),
            )
        )
    db_session.commit()

    svc = ConsolidationService(db_session)
    svc.add_subsidiary(parent.id, sub.id)
    bs = svc.generate_consolidated_balance_sheet([parent.id, sub.id], "2026-03")
    pnl = svc.generate_consolidated_pnl([parent.id, sub.id], "2026-03")

    assert bs["company_count"] >= 2
    assert pnl["company_count"] >= 2
