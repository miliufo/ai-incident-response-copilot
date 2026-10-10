
from langgraph.graph import StateGraph, START, END

from app.graph.state import IncidentState
from app.security.approval_verifier import verify_human_approval
from app.agents.triage_agent import triage_incident
from app.agents.investigation_agent import investigate_incident
from app.agents.response_planner_agent import create_response_plan
from app.agents.response_decision_agent import make_response_decision

from app.models.incident import Severity


# ============================================================
# SECURITY POLICY
# ============================================================

def requires_human_approval(state: IncidentState) -> bool:
    """
    Determine whether a response plan requires human approval.

    Never rely only on the approval_required state flag.
    Sensitive actions and rollback recommendations must
    independently trigger human approval.
    """

    plan = state.get("response_plan")
    triage = state.get("triage")

    approval_flag = bool(
        state.get("approval_required", False)
    )

    is_critical = (
        triage is not None
        and triage.severity == Severity.CRITICAL
    )

    if plan is None:
        return approval_flag or is_critical

    rollback_sensitive = bool(
        plan.rollback_recommended
    )

    action_sensitive = any(
        action.requires_approval
        for action in plan.immediate_actions
    )

    return (
        approval_flag
        or is_critical
        or rollback_sensitive
        or action_sensitive
    )


# ============================================================
# 1. TRIAGE NODE
# ============================================================

def triage_node(state: IncidentState):
    incident = state["incident"]

    result = triage_incident(incident)

    return {
        "triage": result,
        "final_status": "triage_completed",
    }


# ============================================================
# 2. INVESTIGATION NODE
# ============================================================

def investigation_node(state: IncidentState):
    incident = state["incident"]
    triage = state["triage"]

    if triage is None:
        raise ValueError("Triage result is missing.")

    result = investigate_incident(
        incident=incident,
        triage=triage,
    )

    return {
        "investigation": result,
        "final_status": "investigation_completed",
    }


# ============================================================
# 3. RESPONSE PLANNING NODE
# ============================================================

def response_planning_node(state: IncidentState):
    incident = state["incident"]
    triage = state["triage"]
    investigation = state["investigation"]

    if triage is None:
        raise ValueError("Triage result is missing.")

    if investigation is None:
        raise ValueError("Investigation result is missing.")

    plan = create_response_plan(
        incident=incident,
        triage=triage,
        investigation=investigation,
    )

    is_critical = (
        triage.severity == Severity.CRITICAL
    )

    rollback_requires_approval = bool(
        plan.rollback_recommended
    )

    action_requires_approval = any(
        action.requires_approval
        for action in plan.immediate_actions
    )

    approval_required = (
        is_critical
        or rollback_requires_approval
        or action_requires_approval
    )

    return {
        "response_plan": plan,
        "approval_required": approval_required,
        "approved": False,
        "decision": None,
        "final_status": "response_plan_completed",
    }


# ============================================================
# 4. HUMAN APPROVAL GATE
# ============================================================

def approval_gate_node(state: IncidentState):
    plan = state.get("response_plan")

    if plan is None:
        # Preserve compatibility with lightweight gate tests,
        # while failing closed when the workflow has no plan.
        if state.get("approval_required", False):
            return {
                "approval_required": True,
                "approved": False,
                "decision": None,
                "final_status": "awaiting_human_approval",
            }

        return {
            "approval_required": False,
            "approved": False,
            "decision": None,
            "final_status": "ready_for_decision",
        }

    approval_required = requires_human_approval(state)

    if approval_required:
        return {
            "approval_required": True,
            "approved": False,
            "decision": None,
            "final_status": "awaiting_human_approval",
        }

    return {
        "approval_required": False,
        "approved": False,
        "decision": None,
        "final_status": "ready_for_decision",
    }


# ============================================================
# 5. RESPONSE DECISION NODE
# ============================================================


def response_decision_node(state: IncidentState):
    response_plan = state.get("response_plan")

    if response_plan is None:
        raise ValueError("Response plan is missing.")

    approval_required = requires_human_approval(state)

    if not approval_required:
        actions = [
            action.action
            for action in response_plan.immediate_actions
        ]

        return {
            "approval_required": False,
            "approved": False,
            "decision": {
                "decision": (
                    "No human approval is required. "
                    "The non-sensitive response plan "
                    "is authorized to proceed."
                ),
                "status": "auto_authorized",
                "approved": False,
                "rollback_authorized": False,
                "authorized_actions": actions,
                "blocked_actions": [],
            },
            "final_status": "auto_authorized",
        }

    approval_record = state.get("approval_record")
    approved_flag = state.get("approved", False)

    # A boolean flag alone is never sufficient authorization.
    verified = False

    if approved_flag and approval_record is not None:
        verified = verify_human_approval(
            record=approval_record,
            response_plan=response_plan,
            incident_id=response_plan.incident_id,
        )

    if not verified:
        return {
            "approval_required": True,
            "approved": False,
            "decision": None,
            "final_status": "awaiting_human_approval",
        }

    decision = make_response_decision(
        response_plan=response_plan,
        approved=True,
    )

    return {
        "approval_required": True,
        "approved": True,
        "decision": decision,
        "final_status": decision["status"],
    }



# ============================================================
# 6. ROUTING LOGIC
# ============================================================

def route_after_approval(state: IncidentState):
    """
    Sensitive plans stop at the approval gate.

    Non-sensitive plans proceed to response_decision.
    """

    if requires_human_approval(state):
        return "end"

    return "response_decision"


# ============================================================
# 7. BUILD LANGGRAPH WORKFLOW
# ============================================================

builder = StateGraph(IncidentState)

builder.add_node(
    "triage",
    triage_node,
)

builder.add_node(
    "investigation",
    investigation_node,
)

builder.add_node(
    "response_planning",
    response_planning_node,
)

builder.add_node(
    "approval_gate",
    approval_gate_node,
)

builder.add_node(
    "response_decision",
    response_decision_node,
)


# ============================================================
# 8. WORKFLOW EDGES
# ============================================================

builder.add_edge(
    START,
    "triage",
)

builder.add_edge(
    "triage",
    "investigation",
)

builder.add_edge(
    "investigation",
    "response_planning",
)

builder.add_edge(
    "response_planning",
    "approval_gate",
)

builder.add_conditional_edges(
    "approval_gate",
    route_after_approval,
    {
        "end": END,
        "response_decision": "response_decision",
    },
)

builder.add_edge(
    "response_decision",
    END,
)


# ============================================================
# 9. COMPILE GRAPH
# ============================================================

incident_graph = builder.compile()
