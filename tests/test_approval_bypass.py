
from app.graph.incident_graph import approval_gate_node
from app.models.response_plan import ResponsePlan, ResponseAction


def test_rollback_cannot_bypass_approval():
    plan = ResponsePlan(
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
        rollback_reason="Potential deployment regression",
        customer_impact_message="Incident under investigation",
        success_criteria=["Service restored"],
        risk_notes=["Production rollback requires approval"],
        plan_confidence=0.9,
    )

    # Simulate an incorrectly modified workflow state.
    state = {
        "response_plan": plan,
        "approval_required": False,
        "approved": False,
    }

    result = approval_gate_node(state)

    # A sensitive plan must never bypass human approval.
    assert result["approved"] is False
    assert result["final_status"] == "awaiting_human_approval"
