import json

from app.core.llm import get_llm, MODEL_NAME
from app.models.incident import Incident
from app.models.triage import TriageResult
from app.models.investigation import InvestigationResult


def investigate_incident(
    incident: Incident,
    triage: TriageResult
) -> InvestigationResult:

    client = get_llm()

    prompt = f"""
You are a senior Site Reliability Engineer (SRE)
and production incident investigator.

Investigate the following production incident.

INCIDENT:
{incident.model_dump_json(indent=2)}

TRIAGE RESULT:
{triage.model_dump_json(indent=2)}

Your responsibilities:

1. Summarize the incident.
2. Generate plausible root-cause hypotheses.
3. Rank hypotheses by likelihood.
4. Identify evidence supporting each hypothesis.
5. Specify evidence that engineers should collect.
6. Recommend practical diagnostic actions.
7. Identify missing information.
8. Assign an investigation priority.

IMPORTANT RULES:

- Never claim a root cause is confirmed without evidence.
- Never invent logs, metrics, deployments, alerts,
  infrastructure events, or monitoring results.
- Clearly distinguish facts from hypotheses.
- Supporting evidence must come from the provided incident
  or triage information.
- If evidence is unavailable, list it as missing information.
- Confidence values must be between 0 and 1.

Return ONLY valid JSON matching this schema:

{json.dumps(InvestigationResult.model_json_schema(), indent=2)}
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
            "Investigation agent returned an empty response."
        )

    data = json.loads(raw_result)

    return InvestigationResult.model_validate(data)