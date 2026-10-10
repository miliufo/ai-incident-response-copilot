from typing import List

from pydantic import BaseModel, Field


class RootCauseHypothesis(BaseModel):
    hypothesis: str
    supporting_evidence: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class InvestigationResult(BaseModel):
    incident_summary: str

    hypotheses: List[RootCauseHypothesis]

    evidence_to_collect: List[str]

    diagnostic_actions: List[str]

    missing_information: List[str]

    investigation_priority: str