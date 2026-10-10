
from app.graph.state import IncidentState, HumanApprovalRecord
from app.agents.response_decision_agent import make_response_decision
from app.security.approval_verifier import verify_human_approval


def _requires_human_approval(response_plan) -> bool:
    return (
        response_plan.rollback_recommended
        or any(
            action.requires_approval
            for action in response_plan.immediate_actions
        )
    )


def approve_response_plan(
    state: IncidentState,
    approval_record: HumanApprovalRecord | None = None,
) -> dict:
    """
    Approve a response plan only after verifying
    a matching human approval record.
    """
    response_plan = state.get("response_plan")

    if response_plan is None:
        raise ValueError("Response plan is missing.")

    incident_id = response_plan.incident_id

    if _requires_human_approval(response_plan):
        if not verify_human_approval(
            record=approval_record,
            response_plan=response_plan,
            incident_id=incident_id,
        ):
            return {
                "approved": False,
                "final_status": "awaiting_human_approval",
                "response_decision": None,
                "error": "Valid human approval record is required.",
            }

    decision = make_response_decision(
        response_plan=response_plan,
        approved=True,
    )

    return {
        "approved": True,
        "final_status": "approved_by_human",
        "response_decision": decision,
    }


def reject_response_plan(state: IncidentState) -> dict:
    """
    Reject a response plan and block its actions.
    """
    response_plan = state.get("response_plan")

    if response_plan is None:
        raise ValueError("Response plan is missing.")

    decision = make_response_decision(
        response_plan=response_plan,
        approved=False,
    )

    return {
        "approved": False,
        "final_status": "rejected_by_human",
        "response_decision": decision,
    }
