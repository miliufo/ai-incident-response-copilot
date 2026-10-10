
from datetime import datetime, timedelta, timezone

from app.models.response_plan import ResponsePlan, ResponseAction
from app.security.approval_verifier import (
    create_plan_fingerprint,
    verify_human_approval,
)


def make_test_plan():
    return ResponsePlan(
        incident_id="INC-SECURITY-001",
        immediate_actions=[
            ResponseAction(
                action="Rollback production deployment",
                owner_role="DevOps",
                priority="immediate",
                rationale="Restore previous stable version",
                requires_approval=True,
            )
        ],
        communication_actions=[],
        escalation_actions=[],
        rollback_recommended=True,
        rollback_reason="Deployment regression",
        customer_impact_message="Incident under investigation",
        success_criteria=["Service restored"],
        risk_notes=["Rollback requires approval"],
        plan_confidence=0.9,
    )


def make_approval_record(plan):
    return {
        "incident_id": plan.incident_id,
        "plan_fingerprint": create_plan_fingerprint(plan),
        "reviewer_id": "security-operator-001",
        "decision": "approved",
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }


def test_valid_approval():
    plan = make_test_plan()
    record = make_approval_record(plan)

    assert verify_human_approval(
        record, plan, plan.incident_id
    ) is True


def test_rejected_approval():
    plan = make_test_plan()
    record = make_approval_record(plan)
    record["decision"] = "rejected"

    assert verify_human_approval(
        record, plan, plan.incident_id
    ) is False


def test_wrong_incident():
    plan = make_test_plan()
    record = make_approval_record(plan)
    record["incident_id"] = "INC-OTHER-999"

    assert verify_human_approval(
        record, plan, plan.incident_id
    ) is False


def test_modified_response_plan():
    plan = make_test_plan()
    record = make_approval_record(plan)

    plan.immediate_actions[0].action = (
        "Delete production database"
    )

    assert verify_human_approval(
        record, plan, plan.incident_id
    ) is False


def test_missing_reviewer():
    plan = make_test_plan()
    record = make_approval_record(plan)
    record["reviewer_id"] = ""

    assert verify_human_approval(
        record, plan, plan.incident_id
    ) is False


def test_future_approval_timestamp():
    plan = make_test_plan()
    record = make_approval_record(plan)

    future_time = datetime.now(timezone.utc) + timedelta(days=1)
    record["reviewed_at"] = future_time.isoformat()

    assert verify_human_approval(
        record, plan, plan.incident_id
    ) is False


def test_missing_approval_record():
    plan = make_test_plan()

    assert verify_human_approval(
        None, plan, plan.incident_id
    ) is False
