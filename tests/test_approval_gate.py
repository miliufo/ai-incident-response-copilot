
from app.graph.incident_graph import approval_gate_node


def test_approval_required():
    state = {
        "approval_required": True,
        "approved": False,
        "final_status": "response_plan_completed",
    }

    result = approval_gate_node(state)

    assert result["approved"] is False
    assert result["final_status"] == "awaiting_human_approval"
    assert result["decision"] is None


def test_approval_not_required():
    state = {
        "approval_required": False,
        "approved": False,
        "final_status": "response_plan_completed",
    }

    result = approval_gate_node(state)

    assert result["approved"] is False
    assert result["final_status"] == "ready_for_decision"
    assert result["decision"] is None
