
from app.models.response_plan import ResponsePlan


def make_response_decision(
    response_plan: ResponsePlan,
    approved: bool,
) -> dict:
    """
    Determine which actions are authorized after human review.

    This function does not execute any production actions.
    """

    proposed_actions = [
        action.action
        for action in response_plan.immediate_actions
    ]

    if approved:
        return {
            "decision": (
                "Human approval received. The response plan "
                "is authorized to proceed."
            ),
            "status": "approved_for_execution",
            "approved": True,
            "rollback_authorized": (
                response_plan.rollback_recommended
            ),
            "authorized_actions": proposed_actions,
            "blocked_actions": [],
        }

    return {
        "decision": (
            "The response plan was rejected by the human "
            "operator. All proposed actions remain blocked."
        ),
        "status": "rejected_by_human",
        "approved": False,
        "rollback_authorized": False,
        "authorized_actions": [],
        "blocked_actions": proposed_actions,
    }
