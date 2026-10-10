from typing import List, Literal
from pydantic import BaseModel, Field


class ResponseAction(BaseModel):
    action: str
    owner_role: str
    priority: Literal["immediate", "high", "medium", "low"]
    rationale: str
    requires_approval: bool = False


class ResponsePlan(BaseModel):
    incident_id: str

    immediate_actions: List[ResponseAction]

    communication_actions: List[str]

    escalation_actions: List[str]

    rollback_recommended: bool

    rollback_reason: str

    customer_impact_message: str

    success_criteria: List[str]

    risk_notes: List[str]

    plan_confidence: float = Field(
        ge=0.0,
        le=1.0
    )