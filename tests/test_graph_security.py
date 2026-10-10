
import pytest

from app.graph.incident_graph import (
    approval_gate_node,
    route_after_approval,
    response_decision_node,
)
from app.models.response_plan import ResponsePlan, ResponseAction


@pytest.fixture
def sensitive_plan():
    return ResponsePlan(
        incident_id="INC-SECURITY-001",
        immediate_actions=[
            ResponseAction(
                action="Inspect application logs",
                owner_role="SRE",
                priority="high",
                rationale="Investigate the incident",
                requires_approval=False,
            ),
            ResponseAction(
                action="Rollback production deployment",
                owner_role="DevOps",
                priority="immediate",
                rationale="Restore previous stable release",
                requires_approval=True,
            ),
        ],
        communication_actions=[],
        escalation_actions=[],
        rollback_recommended=True,
        rollback_reason="Recent deployment caused failures",
        customer_impact_message="Incident under investigation",
        success_criteria=["Service restored"],
        risk_notes=["Rollback requires human approval"],
        plan_confidence=0.9,
    )


# TEST 1: Sensitive plans must wait for human approval.

def test_sensitive_plan_waits_for_human():
    state = {
        "approval_required": True,
        "approved": False,
    }

    result = approval_gate_node(state)

    assert result["approved"] is False
    assert result["final_status"] == "awaiting_human_approval"


# TEST 2: Sensitive plans must stop at the approval gate.

def test_sensitive_plan_cannot_bypass_gate():
    state = {
        "approval_required": True,
        "approved": False,
    }

    assert route_after_approval(state) == "end"


# TEST 3: Non-sensitive plans can proceed to decision.

def test_non_sensitive_plan_routes_to_decision():
    state = {
        "approval_required": False,
        "approved": False,
    }

    assert route_after_approval(state) == "response_decision"


# TEST 4: Missing response plan must raise an error.

def test_decision_node_rejects_unapproved_sensitive_plan():
    state = {
        "approval_required": True,
        "approved": False,
        "response_plan": None,
    }

    with pytest.raises(ValueError, match="Response plan is missing"):
        response_decision_node(state)


# TEST 5: Missing plan must never be auto-authorized.

def test_sensitive_plan_cannot_be_auto_authorized():
    state = {
        "approval_required": True,
        "approved": False,
        "response_plan": None,
    }

    try:
        result = response_decision_node(state)
    except ValueError:
        return

    assert result["approved"] is False
    assert result["final_status"] == "awaiting_human_approval"
    assert result.get("decision") is None


# TEST 6: A real sensitive plan must not be authorized
# without human approval.

def test_real_sensitive_plan_requires_approval(sensitive_plan):
    state = {
        "approval_required": True,
        "approved": False,
        "response_plan": sensitive_plan,
    }

    result = response_decision_node(state)

    assert result["approved"] is False
    assert result["final_status"] == "awaiting_human_approval"
    assert result.get("decision") is None


# TEST 7: A sensitive plan must not authorize rollback
# before human approval.

def test_rollback_blocked_without_approval(sensitive_plan):
    state = {
        "approval_required": True,
        "approved": False,
        "response_plan": sensitive_plan,
    }

    result = response_decision_node(state)

    assert result["approved"] is False
    assert result.get("final_status") != "approved_for_execution"

    decision = result.get("decision") or {}

    assert decision.get("rollback_authorized", False) is False
    assert decision.get("authorized_actions", []) == []


# TEST 8: Approval gate must block a sensitive plan.

def test_approval_gate_blocks_real_sensitive_plan(sensitive_plan):
    state = {
        "approval_required": True,
        "approved": False,
        "response_plan": sensitive_plan,
    }

    gate_result = approval_gate_node(state)

    assert gate_result["approved"] is False
    assert gate_result["final_status"] == "awaiting_human_approval"

    next_state = {**state, **gate_result}

    assert route_after_approval(next_state) == "end"
