
import pytest

from app.models.response_plan import ResponsePlan, ResponseAction
from app.services.approval_service import (
    approve_response_plan,
    reject_response_plan,
)


@pytest.fixture
def sample_state():
    """Create a sensitive response plan for testing."""

    plan = ResponsePlan(
        incident_id="INC-APPROVAL-001",
        immediate_actions=[
            ResponseAction(
                action="Rollback production deployment",
                owner_role="DevOps",
                priority="immediate",
                rationale="Restore previous stable version",
                requires_approval=True,
            ),
        ],
        communication_actions=[],
        escalation_actions=[],
        rollback_recommended=True,
        rollback_reason="Potential deployment regression",
        customer_impact_message="Incident under investigation",
        success_criteria=["Service restored"],
        risk_notes=["Rollback requires human approval"],
        plan_confidence=0.9,
    )

    return {
        "response_plan": plan,
        "approval_required": True,
        "approved": False,
    }


def test_sensitive_plan_requires_verified_approval(sample_state):
    """
    Sensitive plans must not be approved without
    a verified human approval record.
    """

    result = approve_response_plan(sample_state)

    assert result["approved"] is False
    assert result["final_status"] == "awaiting_human_approval"
    assert result["response_decision"] is None
    assert result["error"] == "Valid human approval record is required."


def test_invalid_approval_record_is_rejected(sample_state):
    """An invalid approval record must not authorize actions."""

    invalid_record = {
        "incident_id": "WRONG-INCIDENT",
        "plan_fingerprint": "invalid-fingerprint",
        "reviewer_id": "reviewer-001",
        "decision": "approved",
        "reviewed_at": "2026-01-01T12:00:00+00:00",
    }

    result = approve_response_plan(
        sample_state,
        approval_record=invalid_record,
    )

    assert result["approved"] is False
    assert result["final_status"] == "awaiting_human_approval"
    assert result["response_decision"] is None


def test_reject_response_plan(sample_state):
    """Rejecting a plan must block its actions."""

    result = reject_response_plan(sample_state)

    assert result["approved"] is False
    assert result["final_status"] == "rejected_by_human"
    assert result["response_decision"]["approved"] is False
    assert result["response_decision"]["rollback_authorized"] is False
    assert result["response_decision"]["authorized_actions"] == []


def test_approval_requires_response_plan():
    """Approval must fail when no response plan exists."""

    state = {
        "response_plan": None,
        "approval_required": True,
        "approved": False,
    }

    with pytest.raises(
        ValueError,
        match="Response plan is missing",
    ):
        approve_response_plan(state)


def test_rejection_requires_response_plan():
    """Rejection must fail when no response plan exists."""

    state = {
        "response_plan": None,
        "approval_required": True,
        "approved": False,
    }

    with pytest.raises(
        ValueError,
        match="Response plan is missing",
    ):
        reject_response_plan(state)


def test_non_sensitive_plan_does_not_require_approval():
    """
    Non-sensitive plans can proceed automatically
    according to the current service policy.
    """

    plan = ResponsePlan(
        incident_id="INC-SAFE-001",
        immediate_actions=[
            ResponseAction(
                action="Inspect application logs",
                owner_role="SRE",
                priority="high",
                rationale="Investigate the root cause",
                requires_approval=False,
            ),
        ],
        communication_actions=[],
        escalation_actions=[],
        rollback_recommended=False,
        rollback_reason="No rollback required",
        customer_impact_message="Investigation ongoing",
        success_criteria=["Root cause identified"],
        risk_notes=[],
        plan_confidence=0.9,
    )

    state = {
        "response_plan": plan,
        "approval_required": False,
        "approved": False,
    }

    result = approve_response_plan(state)

    assert result["approved"] is True
    assert result["final_status"] == "approved_by_human"
    assert result["response_decision"]["approved"] is True


from datetime import datetime, timezone

from app.security.approval_verifier import create_plan_fingerprint


def test_valid_human_approval_is_accepted(sample_state):
    """
    A matching human approval record should
    authorize the exact response plan.
    """
    plan = sample_state["response_plan"]

    approval_record = {
        "incident_id": plan.incident_id,
        "plan_fingerprint": create_plan_fingerprint(plan),
        "reviewer_id": "security-reviewer-001",
        "decision": "approved",
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }

    result = approve_response_plan(
        sample_state,
        approval_record=approval_record,
    )

    assert result["approved"] is True
    assert result["final_status"] == "approved_by_human"
    assert result["response_decision"]["approved"] is True
    assert result["response_decision"]["rollback_authorized"] is True
