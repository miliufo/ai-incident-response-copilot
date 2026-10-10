import json

from app.core.llm import get_llm, MODEL_NAME
from app.models.incident import Incident
from app.models.triage import TriageResult
from app.models.investigation import InvestigationResult
from app.models.response_plan import ResponsePlan


def create_response_plan(
    incident: Incident,
    triage: TriageResult,
    investigation: InvestigationResult,
) -> ResponsePlan:

    client = get_llm()

    # Use the model's example structure instead of embedding the full
    # Pydantic JSON Schema. This reduces the chance that the LLM returns
    # the schema itself instead of an actual response plan.
    response_example = {
        "incident_id": incident.incident_id,
        "immediate_actions": [
            {
                "action": "Describe the action",
                "owner_role": "SRE",
                "priority": "immediate",
                "rationale": "Explain why this action is appropriate",
                "requires_approval": False,
            }
        ],
        "communication_actions": [
            "Describe an internal or external communication action"
        ],
        "escalation_actions": [
            "Describe an escalation action"
        ],
        "rollback_recommended": False,
        "rollback_reason": "Explain whether rollback is appropriate",
        "customer_impact_message": (
            "A concise customer-safe status message"
        ),
        "success_criteria": [
            "Describe a measurable recovery criterion"
        ],
        "risk_notes": [
            "Describe an operational risk"
        ],
        "plan_confidence": 0.8,
    }

    prompt = f"""
You are a senior Site Reliability Engineer (SRE) and Incident Commander.

Create a safe and practical response plan for this production incident.

INCIDENT:
{incident.model_dump_json(indent=2)}

TRIAGE RESULT:
{triage.model_dump_json(indent=2)}

INVESTIGATION RESULT:
{investigation.model_dump_json(indent=2)}

Your responsibilities:

1. Recommend immediate mitigation and diagnostic actions.
2. Assign an appropriate owner role to every action.
3. Prioritize actions.
4. Identify communication actions.
5. Identify escalation actions.
6. Decide whether rollback should be recommended.
7. Define measurable success criteria.
8. Identify operational risks.
9. Produce a concise customer-impact message.
10. Provide a plan confidence score between 0 and 1.

SAFETY RULES:

- Do NOT execute any action.
- You are creating recommendations only.
- Destructive or production-changing actions must require human approval.
- Rollbacks must require human approval.
- Database changes must require human approval.
- Infrastructure changes must require human approval.
- Do not claim an unverified hypothesis is the confirmed root cause.
- Do not invent evidence.
- Prefer reversible actions before irreversible actions.
- If evidence is insufficient, recommend investigation instead of guessing.
- The customer message must not expose sensitive internal details.

IMPORTANT OUTPUT RULES:

- Return ONLY one valid JSON object.
- Do NOT return JSON Schema.
- Do NOT return "$defs", "properties", "required", or schema metadata.
- Do NOT wrap the JSON in Markdown or code fences.
- Include ALL fields shown in the example below.
- Do not omit fields.
- "priority" must be one of:
  "immediate", "high", "medium", "low".
- "requires_approval" must be a JSON boolean.
- "rollback_recommended" must be a JSON boolean.
- "plan_confidence" must be a number from 0 to 1.

Use this exact JSON structure:

{json.dumps(response_example, indent=2)}
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    raw_result = response.choices[0].message.content

    if not raw_result:
        raise ValueError(
            "Response planning agent returned an empty response."
        )

    data = json.loads(raw_result)

    # Guard against the model accidentally returning JSON Schema
    # instead of an actual response-plan instance.
    if (
        "$defs" in data
        or "properties" in data
        or data.get("title") == "ResponsePlan"
    ):
        raise ValueError(
            "Response planning agent returned a JSON schema "
            "instead of a response plan."
        )

    # ---------------------------------------------------------
    # Defensive normalization
    # ---------------------------------------------------------
    # LLMs can occasionally omit fields even when explicitly
    # instructed not to. These safe defaults prevent an incomplete
    # model response from crashing the whole incident workflow.
    #
    # setdefault() does NOT overwrite valid AI-generated values.
    # It only fills a field when that field is missing.
    # ---------------------------------------------------------

    data.setdefault(
        "incident_id",
        incident.incident_id,
    )

    data.setdefault(
        "immediate_actions",
        [],
    )

    data.setdefault(
        "communication_actions",
        [
            (
                "Notify the incident response team and relevant "
                "stakeholders."
            ),
            (
                "Provide regular status updates until service "
                "recovery."
            ),
        ],
    )

    data.setdefault(
        "escalation_actions",
        [
            (
                "Escalate to the responsible engineering lead "
                "if the incident persists."
            )
        ],
    )

    data.setdefault(
        "rollback_recommended",
        False,
    )

    data.setdefault(
        "rollback_reason",
        (
            "Rollback should only be performed after confirming "
            "that a recent deployment is likely related to the "
            "incident."
        ),
    )

    data.setdefault(
        "customer_impact_message",
        (
            "We are investigating a service disruption affecting "
            "some customer requests and are working to restore "
            "normal service."
        ),
    )

    data.setdefault(
        "success_criteria",
        [
            "Service health returns to normal.",
            "Error rate returns to an acceptable level.",
            "Latency returns to the expected operating range.",
        ],
    )

    data.setdefault(
        "risk_notes",
        [
            (
                "Production-changing actions may introduce "
                "additional risk and require human review."
            )
        ],
    )

    data.setdefault(
        "plan_confidence",
        0.5,
    )

    # Final validation guarantees that downstream components receive
    # a correctly structured ResponsePlan object.
    return ResponsePlan.model_validate(data)