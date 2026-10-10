
from typing import TypedDict, Optional

from app.models.incident import Incident
from app.models.triage import TriageResult
from app.models.investigation import InvestigationResult
from app.models.response_plan import ResponsePlan


class IncidentState(TypedDict):
    incident: Incident

    triage: Optional[TriageResult]
    investigation: Optional[InvestigationResult]
    response_plan: Optional[ResponsePlan]

    approval_required: bool
    approved: bool
    final_status: str

    # Final response decision
    decision: Optional[str]
    approval_record: Optional["HumanApprovalRecord"]

class HumanApprovalRecord(TypedDict):
    incident_id: str
    plan_fingerprint: str
    reviewer_id: str
    decision: str
    reviewed_at: str
