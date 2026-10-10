
import pytest

from app.models.response_plan import ResponsePlan, ResponseAction
from app.agents.response_decision_agent import make_response_decision


@pytest.fixture
def sample_plan():
    return ResponsePlan(
        incident_id="INC-TEST-001",
        immediate_actions=[
            ResponseAction(
                action="Inspect application logs",
                owner_role="SRE",
                priority="high",
                rationale="Identify the root cause",
                requires_approval=False,
            ),
            ResponseAction(
                action="Rollback production deployment",
                owner_role="DevOps",
                priority="immediate",
                rationale="Restore the previous stable version",
                requires_approval=True,
            ),
        ],
        communication_actions=[],
        escalation_actions=[],
        rollback_recommended=True,
        rollback_reason="Recent deployment may have caused the outage",
        customer_impact_message="We are investigating the issue.",
        success_criteria=["Service restored"],
        risk_notes=["Rollback requires human approval"],
        plan_confidence=0.9,
    )


def test_approved_plan(sample_plan):
    result = make_response_decision(sample_plan, approved=True)

    assert result["approved"] is True
    assert result["status"] == "approved_for_execution"
    assert result["rollback_authorized"] is True
    assert len(result["authorized_actions"]) == 2
    assert result["blocked_actions"] == []


def test_rejected_plan(sample_plan):
    result = make_response_decision(sample_plan, approved=False)

    assert result["approved"] is False
    assert result["status"] == "rejected_by_human"
    assert result["rollback_authorized"] is False
    assert result["authorized_actions"] == []

    assert len(result["blocked_actions"]) == 2
    assert "Rollback production deployment" in result["blocked_actions"]


def test_rejection_blocks_sensitive_actions(sample_plan):
    result = make_response_decision(sample_plan, approved=False)

    assert "Rollback production deployment" not in result["authorized_actions"]
    assert result["rollback_authorized"] is False
