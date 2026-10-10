import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from app.models.incident import Incident
from app.models.triage import TriageResult

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)


def triage_incident(incident: Incident) -> TriageResult:
    prompt = f"""
You are a senior Site Reliability Engineer (SRE) and incident commander.

Analyze the following production incident.

INCIDENT:
{incident.model_dump_json(indent=2)}

Your responsibilities:
1. Determine incident severity.
2. Summarize the business and technical impact.
3. Identify affected areas.
4. Decide whether escalation is required.
5. Recommend immediate next steps.
6. Provide a confidence score between 0 and 1.

Severity rules:

CRITICAL:
- Complete production outage
- Major revenue-impacting service unavailable
- Severe security incident
- Large percentage of customers affected

HIGH:
- Major degradation
- Important functionality unavailable
- Significant customer impact

MEDIUM:
- Partial degradation
- Limited customer impact
- Workaround exists

LOW:
- Minor issue
- Little or no customer impact

Do not invent evidence that is not present in the incident.

Return ONLY valid JSON using exactly this structure:

{{
  "severity": "critical|high|medium|low|unknown",
  "impact_summary": "Short impact summary",
  "affected_areas": ["area 1", "area 2"],
  "escalation_required": true,
  "escalation_reason": "Reason for escalation decision",
  "recommended_next_steps": [
    "step 1",
    "step 2"
  ],
  "confidence": 0.90
}}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
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
        raise ValueError("Triage agent returned an empty response.")

    data = json.loads(raw_result)

    return TriageResult.model_validate(data)