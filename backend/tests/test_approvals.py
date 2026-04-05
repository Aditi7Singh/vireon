from decimal import Decimal

import models
from services.workflow_approval_service import WorkflowApprovalService


def test_workflow_template_and_request_actions(db_session):
    company = models.Company(name="Approval Co", stage="seed", initial_cash=Decimal("100000"))
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)

    service = WorkflowApprovalService(db_session)
    workflow = service.create_workflow_template(
        company.id,
        "Finance Spend Approval",
        [
            {"step_order": 1, "approver_role": "manager", "min_amount": 0, "max_amount": 5000},
            {"step_order": 2, "approver_role": "director", "min_amount": 5000, "max_amount": None},
        ],
    )
    assert workflow.name == "Finance Spend Approval"

    req = service.submit_request(workflow.id, company.id, 3000, "finance_user")
    assert req.status == "pending"

    action = service.take_action(req.id, "approve", "u1", "manager", "ok")
    assert action["success"] is True
    assert action["status"] in {"pending", "approved"}
