from datetime import date
from decimal import Decimal
import uuid

import models
from services.audit_service import AuditService


def test_audit_log_query_and_report(db_session):
    company = models.Company(name="Audit Co", stage="seed", initial_cash=Decimal("100000"))
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)

    service = AuditService(db_session)
    entity_id = uuid.uuid4()
    event = service.log_entity_change(
        entity_type="budget",
        entity_id=entity_id,
        old={"amount": 1000},
        new={"amount": 1200},
        user_id=uuid.uuid4(),
        company_id=company.id,
        event_type="configuration_change",
    )
    assert event.immutable_hash

    rows = service.query_audit_trail("budget", entity_id, date.today(), date.today())
    assert len(rows) >= 1

    period = date.today().strftime("%Y-%m")
    report = service.generate_audit_report(company.id, period, "all")
    assert report["company_id"] == str(company.id)
    assert "event_count" in report
