from typing import List

from pydantic import BaseModel

from app.models.incident import Severity


class TriageResult(BaseModel):
    severity: Severity

    impact_summary: str

    affected_areas: List[str]

    escalation_required: bool

    escalation_reason: str

    recommended_next_steps: List[str]

    confidence: float