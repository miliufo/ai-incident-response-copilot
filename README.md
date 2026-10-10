# 🚨 AI Incident Response Copilot

**A Multi-Agent AI System for Production Incident Triage, Investigation, Response Planning, and Human-in-the-Loop Approval**

An AI-powered incident management prototype built with **Python, LangGraph, Streamlit, and LLMs**. The system assists engineering and Site Reliability Engineering (SRE) teams in analyzing production incidents, investigating possible causes, generating structured response plans, and controlling sensitive remediation decisions through human approval.

## ✨ Key Features

- **Multi-Agent Architecture** — Dedicated agents for incident triage, investigation, response planning, and response decisions.
- **LangGraph Orchestration** — Stateful workflow with conditional routing and approval gates.
- **AI Incident Triage** — Assesses incident severity and helps prioritize response.
- **Investigation Agent** — Produces structured investigative findings and recommendations.
- **Response Planning Agent** — Generates remediation actions, rollback recommendations, escalation steps, and success criteria.
- **Human-in-the-Loop Approval** — Requires human authorization for sensitive response plans.
- **Approval Verification** — Checks reviewer identity metadata, incident ID, plan fingerprint, decision, and approval timestamp.
- **Security-Focused Design** — Blocks unauthorized sensitive actions and prevents approval bypasses covered by the test suite.
- **Interactive Streamlit Dashboard** — Supports incident submission, AI analysis, plan review, and approval or rejection.
- **Automated Testing** — 28 passing tests covering approval workflows, verification, routing, and response decisions.

## 🏗️ System Architecture

```text
Production Incident
        |
        v
  Triage Agent
        |
        v
Investigation Agent
        |
        v
Response Planning Agent
        |
        v
 Human Approval Gate
        |
        +---- Sensitive Response Plan
        |             |
        |             v
        |       Human Review
        |        /       \
        |    Approve    Reject
        |       |          |
        |       v          v
        |   Authorized   Blocked
        |
        +---- Non-Sensitive Response Plan
                      |
                      v
             Response Decision
                      |
                      v
              Auto-Authorized
```

The workflow is coordinated by LangGraph. Sensitive plans are stopped at the approval gate until an authorized human decision is processed.

## 🤖 AI Agents

| Agent | Responsibility |
|---|---|
| Triage Agent | Evaluates the reported incident and determines severity |
| Investigation Agent | Analyzes incident context and produces investigative findings |
| Response Planner Agent | Generates structured response and remediation plans |
| Response Decision Agent | Determines authorized and blocked actions |

## 🔐 Human Approval and Security

The application uses a human-in-the-loop design for sensitive remediation decisions.

Sensitive actions include actions explicitly marked as requiring approval and plans recommending rollback. Critical incidents also trigger the workflow's approval gate.

The approval verification layer checks:

- Approval decision is explicitly approved
- Approval record matches the incident
- Approval record matches the current response plan fingerprint
- Reviewer ID is present
- Approval timestamp is valid and not in the future

Invalid or missing approval records are rejected by the approval service.

**Security boundary:** This project demonstrates approval-policy enforcement in an application workflow. Reviewer ID entry is not equivalent to authenticated identity, and the application is not a production-grade authorization service without additional authentication, persistent audit records, and trusted execution controls.

## 🖥️ Streamlit Dashboard

The dashboard provides an interactive interface for:

1. Reporting production incidents
2. Running AI-powered incident analysis
3. Reviewing response plans and rollback recommendations
4. Approving or rejecting sensitive actions
5. Inspecting final response decisions
6. Viewing authorized and blocked actions

### Application Screenshot

Add a screenshot of the running dashboard to `assets/incident-response-dashboard.png`, then enable the following Markdown image reference:

`![AI Incident Response Copilot Dashboard](assets/incident-response-dashboard.png)`

## 📁 Project Structure

```text
ai-incident-response-copilot/
├── app/
│   ├── agents/
│   │   ├── triage_agent.py
│   │   ├── investigation_agent.py
│   │   ├── response_planner_agent.py
│   │   └── response_decision_agent.py
│   ├── core/
│   │   └── llm.py
│   ├── graph/
│   │   ├── incident_graph.py
│   │   └── state.py
│   ├── models/
│   │   ├── incident.py
│   │   ├── triage.py
│   │   ├── investigation.py
│   │   └── response_plan.py
│   ├── security/
│   │   └── approval_verifier.py
│   └── services/
│       └── approval_service.py
├── tests/
│   ├── test_approval_bypass.py
│   ├── test_approval_gate.py
│   ├── test_approval_service.py
│   ├── test_approval_verifier.py
│   ├── test_graph_security.py
│   └── test_response_decision.py
├── assets/
├── data/
├── streamlit_app.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 🚀 Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-incident-response-copilot.git
cd ai-incident-response-copilot
```

Replace `YOUR_USERNAME` with your GitHub username once the repository is published.

### 2. Create a Virtual Environment

Python 3.11 is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Never commit your actual API key.

### 5. Run the Application

```bash
streamlit run streamlit_app.py
```

Open the local URL displayed in your terminal, typically:

`http://localhost:8501`

## 🧪 Testing

Run the complete automated test suite:

```bash
python -m pytest tests/ -v
```

Latest local verification:

**28 tests passed — 0 failures**

The tests cover human approval requirements, approval record verification, rollback protection, workflow routing, and response decision logic.

Check Python syntax:

```bash
python -m compileall -q app streamlit_app.py
```

## 🛡️ Safety and Limitations

- The system generates response recommendations and authorization decisions; it does not automatically execute production-changing operations.
- AI-generated investigations and recommendations must be reviewed against real operational evidence.
- Approval metadata validation does not independently authenticate the reviewer.
- The system is a portfolio and demonstration project, not a replacement for production incident-management controls.
- Real-world deployment would require stronger identity management, durable approval storage, audit logging, and integration with trusted operational systems.

## 🛠️ Technology Stack

**Language:** Python 3.11

**AI and Orchestration:** LLMs, OpenAI-compatible API, LangGraph, LangChain Core

**Interface:** Streamlit

**Data Models:** Pydantic

**Testing:** Pytest

**Additional Dependencies:** FastAPI, Uvicorn, ChromaDB, Sentence Transformers, Pandas, Plotly, SQLAlchemy, HTTPX

## 🎯 Project Purpose

This project demonstrates practical AI engineering concepts:

- Multi-agent workflow design
- LLM-based incident analysis
- Stateful graph orchestration
- Human-in-the-loop decision making
- Approval-policy validation
- Defensive programming and automated security testing
- Interactive AI application development

The goal is to demonstrate how AI-assisted operational workflows can combine intelligent recommendations with explicit human control over sensitive actions.

## 📄 License

No license has been selected yet. A license file can be added before public distribution.