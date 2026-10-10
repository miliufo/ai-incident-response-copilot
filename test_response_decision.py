
from app.models.response_plan import ResponsePlan, ResponseAction
from app.services.approval_service import (
    approve_response_plan,
    reject_response_plan,
)


# -------------------------------------------------
# 1. Create a sample incident response plan
# -------------------------------------------------

response_plan = ResponsePlan(
    incident_id="INC-001",
    immediate_actions=[
        ResponseAction(
            action="Analyze application logs",
            owner_role="SRE",
            priority="immediate",
            rationale="Identify the cause of HTTP 500 errors.",
            requires_approval=False,
        ),
        ResponseAction(
            action="Rollback checkout-api deployment",
            owner_role="DevOps",
            priority="high",
            rationale="Restore the previous stable version.",
            requires_approval=True,
        ),
    ],
    communication_actions=[
        "Notify the incident response team."
    ],
    escalation_actions=[
        "Escalate to the engineering lead."
    ],
    rollback_recommended=True,
    rollback_reason="Recent deployment may have caused the outage.",
    customer_impact_message="We are investigating checkout issues.",
    success_criteria=[
        "HTTP 500 errors return to normal.",
        "Checkout service is restored.",
    ],
    risk_notes=[
        "Rollback may temporarily interrupt service."
    ],
    plan_confidence=0.85,
)


# -------------------------------------------------
# 2. Prepare workflow state
# -------------------------------------------------

state = {
    "response_plan": response_plan,
    "approval_required": True,
    "approved": False,
    "final_status": "awaiting_human_approval",
}


# -------------------------------------------------
# 3. Test human approval
# -------------------------------------------------

print("\n========== APPROVE TEST ==========")

approved_result = approve_response_plan(state)

print("Approved:", approved_result["approved"])
print("Status:", approved_result["final_status"])

approved_decision = approved_result["response_decision"]

print("Decision:", approved_decision["decision"])
print("Rollback authorized:", approved_decision["rollback_authorized"])
print("Authorized actions:", approved_decision["authorized_actions"])
print("Blocked actions:", approved_decision["blocked_actions"])


# -------------------------------------------------
# 4. Test human rejection
# -------------------------------------------------

print("\n========== REJECT TEST ==========")

rejected_result = reject_response_plan(state)

print("Approved:", rejected_result["approved"])
print("Status:", rejected_result["final_status"])

rejected_decision = rejected_result["response_decision"]

print("Decision:", rejected_decision["decision"])
print("Rollback authorized:", rejected_decision["rollback_authorized"])
print("Authorized actions:", rejected_decision["authorized_actions"])
print("Blocked actions:", rejected_decision["blocked_actions"])


# -------------------------------------------------
# 5. Verify safety requirements
# -------------------------------------------------

assert approved_decision["approved"] is True
assert approved_decision["rollback_authorized"] is True

assert rejected_decision["approved"] is False
assert rejected_decision["rollback_authorized"] is False
assert rejected_decision["authorized_actions"] == []

print("\nALL HUMAN APPROVAL TESTS PASSED")
