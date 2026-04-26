from datetime import date
from decimal import Decimal
import uuid

import models
from services.close_service import CloseService


def _seed_close_company(db_session):
    company = models.Company(name="Close Co", stage="seed", initial_cash=Decimal("150000"))
    db_session.add(company)
    db_session.flush()
    db_session.add(
        models.MonthlyMetric(
            company_id=company.id,
            metric_month=date.today().replace(day=1),
            total_revenue=Decimal("50000"),
            total_expenses=Decimal("35000"),
            ending_cash=Decimal("145000"),
        )
    )
    db_session.commit()
    return company


def test_close_service_flow(db_session):
    company = _seed_close_company(db_session)
    service = CloseService(db_session)

    readiness = service.validate_close_readiness(company.id, "2026-03")
    assert readiness["period"] == "2026-03"

    accruals = service.calculate_accruals(company.id, "2026-03")
    assert "accruals" in accruals

    locked = service.lock_period(company.id, "2026-03", uuid.uuid4())
    assert locked["status"] == "locked"

    status = service.get_close_status(company.id)
    assert status["company_id"] == str(company.id)
