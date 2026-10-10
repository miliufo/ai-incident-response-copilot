from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class IncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"


class Incident(BaseModel):
    incident_id: str = Field(..., description="Unique incident identifier")

    title: str
    description: str

    service: str
    environment: str = "production"

    symptoms: List[str] = Field(default_factory=list)

    severity: Severity = Severity.UNKNOWN
    status: IncidentStatus = IncidentStatus.OPEN

    reported_at: datetime = Field(default_factory=datetime.utcnow)

    reporter: Optional[str] = None
    error_message: Optional[str] = None