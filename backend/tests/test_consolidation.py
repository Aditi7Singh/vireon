from datetime import date
from decimal import Decimal

import models
from services.consolidation_service import ConsolidationService


def _seed_company(db_session, name: str, revenue: int, expenses: int, cash: int):
    company = models.Company(name=name, stage="seed", initial_cash=Decimal(str(cash)))
    db_session.add(company)
    db_session.flush()
    db_session.add(
        models.MonthlyMetric(
            company_id=company.id,
            metric_month=date.today().replace(day=1),
            total_revenue=Decimal(str(revenue)),
            total_expenses=Decimal(str(expenses)),
            ending_cash=Decimal(str(cash)),
        )
    )
    db_session.commit()
    db_session.refresh(company)
    return company


def test_consolidation_service_core_methods(db_session):
    parent = _seed_company(db_session, "Parent", 20000, 14000, 90000)
    sub = _seed_company(db_session, "Sub", 12000, 9000, 45000)

    service = ConsolidationService(db_session)
    rel = service.add_subsidiary(parent.id, sub.id)
    assert rel["success"] is True

    bs = service.generate_consolidated_balance_sheet([parent.id, sub.id], "2026-03")
    assert bs["assets"] > 0

    pnl = service.generate_consolidated_pnl([parent.id, sub.id], "2026-03")
    assert "net_income" in pnl

    translated = service.translate_to_base_currency({"parent:USD": 100.0, "sub:EUR": 50.0}, "INR")
    assert translated["target_currency"] == "INR"
