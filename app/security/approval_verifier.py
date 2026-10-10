
import hashlib
import json
from datetime import datetime, timezone

from app.graph.state import HumanApprovalRecord


def create_plan_fingerprint(response_plan) -> str:
    """Create a deterministic fingerprint of a response plan."""
    if hasattr(response_plan, "model_dump"):
        data = response_plan.model_dump(mode="json")
    else:
        raise TypeError("Expected a Pydantic response plan.")

    serialized = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


def verify_human_approval(
    record: HumanApprovalRecord,
    response_plan,
    incident_id: str,
) -> bool:
    """Check approval metadata against the current response plan."""
    if not record or not isinstance(record, dict):
        return False

    if record.get("decision") != "approved":
        return False

    if record.get("incident_id") != incident_id:
        return False

    if record.get("plan_fingerprint") != create_plan_fingerprint(
        response_plan
    ):
        return False

    if not record.get("reviewer_id"):
        return False

    try:
        reviewed_at = datetime.fromisoformat(
            record["reviewed_at"]
        )
    except (KeyError, TypeError, ValueError):
        return False

    if reviewed_at.tzinfo is None:
        return False

    if reviewed_at > datetime.now(timezone.utc):
        return False

    return True
