import streamlit as st

from datetime import datetime, timezone

from app.security.approval_verifier import create_plan_fingerprint
from app.agents.response_decision_agent import make_response_decision
from app.models.incident import Incident
from app.graph.incident_graph import incident_graph
from app.services.approval_service import (
    approve_response_plan,
    reject_response_plan,
)


st.set_page_config(
    page_title="AI Incident Response Copilot",
    page_icon="🚨",
    layout="wide",
)


# ---------------------------------------------------------
# Session State
# ---------------------------------------------------------

if "incident_result" not in st.session_state:
    st.session_state.incident_result = None

if "approval_decision" not in st.session_state:
    st.session_state.approval_decision = None


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.title("🚨 AI Incident Response Copilot")

st.caption(
    "Multi-agent incident triage, investigation, response planning "
    "and human-in-the-loop approval."
)

st.divider()


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:

    st.header("Incident Response System")

    st.markdown(
        """
**AI Workflow**

1. 🚨 Incident Intake
2. 🧠 Triage Agent
3. 🔍 Investigation Agent
4. 📋 Response Planner
5. 👤 Human Approval
6. ⚡ Response Decision
"""
    )

    st.divider()

    st.subheader("System Controls")

    if st.button("Clear Incident", use_container_width=True):
        st.session_state.incident_result = None
        st.session_state.approval_decision = None
        st.rerun()

    st.divider()

    st.caption(
        "AI-generated recommendations require human approval "
        "before sensitive remediation actions."
    )


# ---------------------------------------------------------
# Incident Form
# ---------------------------------------------------------

st.subheader("Report Production Incident")

with st.form("incident_form"):

    col1, col2 = st.columns(2)

    with col1:
        incident_id = st.text_input(
            "Incident ID",
            value="INC-001",
        )

        title = st.text_input(
            "Incident title",
            value="Checkout API failure",
        )

        service = st.text_input(
            "Affected service",
            value="checkout-api",
        )

    with col2:
        environment = st.selectbox(
            "Environment",
            ["production", "staging", "development"],
        )

        reporter = st.text_input(
            "Reporter",
            value="SRE Team",
        )

        symptoms_text = st.text_input(
            "Symptoms",
            value="HTTP 500 errors, High latency",
        )

    description = st.text_area(
        "Incident description",
        value=(
            "Customers cannot complete checkout in production. "
            "The checkout API is returning HTTP 500 errors "
            "and experiencing high latency."
        ),
        height=120,
    )

    submitted = st.form_submit_button(
        "🚀 Run AI Incident Analysis",
        use_container_width=True,
    )


# ---------------------------------------------------------
# Execute Multi-Agent Workflow
# ---------------------------------------------------------

if submitted:

    symptoms = [
        symptom.strip()
        for symptom in symptoms_text.split(",")
        if symptom.strip()
    ]

    incident = Incident(
        incident_id=incident_id,
        title=title,
        description=description,
        service=service,
        environment=environment,
        symptoms=symptoms,
        reporter=reporter or None,
    )

    initial_state = {
        "incident": incident,
        "triage": None,
        "investigation": None,
        "response_plan": None,
        "approval_required": False,
        "approved": False,
        "final_status": "new",
    }

    try:
        with st.spinner(
            "AI agents are triaging and investigating the incident..."
        ):
            result = incident_graph.invoke(initial_state)

        st.session_state.incident_result = result
        st.session_state.approval_decision = None

    except Exception as exc:
        st.error(f"Incident analysis failed: {exc}")


# ---------------------------------------------------------
# Results Dashboard
# ---------------------------------------------------------

result = st.session_state.incident_result

if result:

    incident = result["incident"]
    triage = result.get("triage")
    investigation = result.get("investigation")
    plan = result.get("response_plan")

    st.divider()

    st.subheader("Incident Command Center")

    # -----------------------------------------------------
    # Top Metrics
    # -----------------------------------------------------

    severity = (
        triage.severity.value.upper()
        if triage
        else "UNKNOWN"
    )

    confidence = (
        f"{triage.confidence * 100:.0f}%"
        if triage
        else "N/A"
    )

    status = result.get(
        "final_status",
        "unknown",
    ).replace("_", " ").title()

    rollback = (
        "Recommended"
        if plan and plan.rollback_recommended
        else "Not Recommended"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Severity",
        severity,
    )

    c2.metric(
        "AI Confidence",
        confidence,
    )

    c3.metric(
        "Workflow Status",
        status,
    )

    c4.metric(
        "Rollback",
        rollback,
    )

    st.divider()

    # -----------------------------------------------------
    # Triage
    # -----------------------------------------------------

    if triage:

        st.subheader("🧠 AI Triage")

        if triage.severity.value == "critical":
            st.error(
                f"CRITICAL INCIDENT — {triage.impact_summary}"
            )

        elif triage.severity.value == "high":
            st.warning(
                f"HIGH SEVERITY — {triage.impact_summary}"
            )

        else:
            st.info(triage.impact_summary)

        left, right = st.columns(2)

        with left:

            st.markdown("#### Affected Areas")

            for area in triage.affected_areas:
                st.write(f"• {area}")

        with right:

            st.markdown("#### Recommended Next Steps")

            for step in triage.recommended_next_steps:
                st.write(f"• {step}")

        if triage.escalation_required:

            st.warning(
                "Escalation required: "
                + triage.escalation_reason
            )

    # -----------------------------------------------------
    # Investigation
    # -----------------------------------------------------

    if investigation:

        st.divider()

        st.subheader("🔍 AI Investigation")

        st.write(investigation.incident_summary)

        st.markdown("#### Root Cause Hypotheses")

        for index, hypothesis in enumerate(
            investigation.hypotheses,
            start=1,
        ):

            with st.expander(
                f"{index}. {hypothesis.hypothesis} "
                f"— Confidence {hypothesis.confidence:.0%}"
            ):

                st.markdown("**Supporting evidence**")

                for evidence in hypothesis.supporting_evidence:
                    st.write(f"• {evidence}")

        col1, col2 = st.columns(2)

        with col1:

            st.markdown("#### Evidence to Collect")

            for evidence in investigation.evidence_to_collect:
                st.write(f"• {evidence}")

        with col2:

            st.markdown("#### Diagnostic Actions")

            for action in investigation.diagnostic_actions:
                st.write(f"• {action}")

        if investigation.missing_information:

            with st.expander("Missing Information"):

                for item in investigation.missing_information:
                    st.write(f"• {item}")

    # -----------------------------------------------------
    # Response Plan
    # -----------------------------------------------------

    if plan:

        st.divider()

        st.subheader("📋 AI Response Plan")

        st.markdown("#### Immediate Actions")

        for index, action in enumerate(
            plan.immediate_actions,
            start=1,
        ):

            approval_text = (
                "🔒 Approval required"
                if action.requires_approval
                else "No approval required"
            )

            with st.expander(
                f"{index}. {action.action}"
            ):

                st.write(
                    f"**Owner:** {action.owner_role}"
                )

                st.write(
                    f"**Priority:** {action.priority}"
                )

                st.write(
                    f"**Rationale:** {action.rationale}"
                )

                st.write(
                    f"**Control:** {approval_text}"
                )

        # -------------------------------------------------
        # Rollback
        # -------------------------------------------------

        if plan.rollback_recommended:

            st.warning(
                "↩️ **Rollback Recommended**\n\n"
                + plan.rollback_reason
            )

        # -------------------------------------------------
        # Communication
        # -------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            st.markdown("#### Communication Actions")

            for action in plan.communication_actions:
                st.write(f"• {action}")

        with col2:

            st.markdown("#### Escalation Actions")

            for action in plan.escalation_actions:
                st.write(f"• {action}")

        st.markdown("#### Customer Impact Message")

        st.info(plan.customer_impact_message)

        # -------------------------------------------------
        # Success Criteria / Risks
        # -------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            st.markdown("#### Success Criteria")

            for criterion in plan.success_criteria:
                st.write(f"✓ {criterion}")

        with col2:

            st.markdown("#### Risk Notes")

            for risk in plan.risk_notes:
                st.write(f"• {risk}")

        st.progress(
            plan.plan_confidence,
            text=(
                "Response Plan Confidence: "
                f"{plan.plan_confidence:.0%}"
            ),
        )

    # -----------------------------------------------------
    # Human Approval
    # -----------------------------------------------------

if isinstance(result, dict) and result.get("approval_required", False):

    st.divider()
    st.subheader("👤 Human Approval Required")

    st.warning(
        "This response plan contains sensitive actions. "
        "A human reviewer must approve or reject the plan."
    )

    reviewer_id = st.text_input(
        "Reviewer ID",
        placeholder="e.g. security-admin-01",
        key="reviewer_id",
    )

    approve_col, reject_col = st.columns(2)

    with approve_col:

        if st.button(
            "✅ Approve Response Plan",
            use_container_width=True,
            type="primary",
        ):

            if not reviewer_id.strip():
                st.error(
                    "Reviewer ID is required before approval."
                )

            else:
                approval_record = {
                    "incident_id": plan.incident_id,
                    "plan_fingerprint": create_plan_fingerprint(plan),
                    "reviewer_id": reviewer_id.strip(),
                    "decision": "approved",
                    "reviewed_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                }

                decision = approve_response_plan(
                    result,
                    approval_record=approval_record,
                )

                st.session_state.approval_decision = decision
                st.rerun()

    with reject_col:

        if st.button(
            "❌ Reject Response Plan",
            use_container_width=True,
        ):

            decision = reject_response_plan(result)

            st.session_state.approval_decision = decision
            st.rerun()

    # -----------------------------------------------------
    # Approval Result
    # -----------------------------------------------------
    # ---------------------------------------------------------
    # Final Response Decision
    # ---------------------------------------------------------

    decision = st.session_state.approval_decision

    if decision:

        st.divider()

        st.subheader("⚖️ Final Response Decision")

        approved = decision.get("approved", False)

        # Generate the final response decision
        final_decision = decision.get("response_decision")

        if final_decision is None:
            st.warning(
                decision.get(
                    "error",
                    "The response plan has not received valid approval."
                )
            )
            st.stop()

        # -----------------------------------------------------
        # Approval Status
        # -----------------------------------------------------

        if approved:

            st.success(
                "Human approval received. "
                "The response plan is authorized to proceed."
            )

        else:

            st.error(
                "Response plan rejected by human operator. "
                "Sensitive remediation actions remain blocked."
            )

        # -----------------------------------------------------
        # Decision Summary
        # -----------------------------------------------------

        st.markdown("### Decision Summary")

        st.write(final_decision.get("decision", ""))

        st.code(
            final_decision.get("status", "unknown"),
            language="text",
        )

        # -----------------------------------------------------
        # Authorization Metrics
        # -----------------------------------------------------

        col1, col2, col3 = st.columns(3)

        authorized_actions = final_decision.get(
            "authorized_actions", []
        )

        blocked_actions = final_decision.get(
            "blocked_actions", []
        )

        rollback_authorized = final_decision.get(
            "rollback_authorized", False
        )

        with col1:
            st.metric(
                "Authorized Actions",
                len(authorized_actions),
            )

        with col2:
            st.metric(
                "Blocked Actions",
                len(blocked_actions),
            )

        with col3:
            st.metric(
                "Rollback Authorized",
                "Yes" if rollback_authorized else "No",
            )

        # -----------------------------------------------------
        # Authorized Actions
        # -----------------------------------------------------

        st.markdown("### ✅ Authorized Actions")

        if authorized_actions:

            for action in authorized_actions:
                st.write(f"✅ {action}")

        else:

            st.info("No actions have been authorized.")

        # -----------------------------------------------------
        # Blocked Actions
        # -----------------------------------------------------

        st.markdown("### 🚫 Blocked Actions")

        if blocked_actions:

            for action in blocked_actions:
                st.write(f"🚫 {action}")

        else:

            st.info("No blocked actions.")

        # -----------------------------------------------------
        # Safety Notice
        # -----------------------------------------------------

        st.caption(
            "Safety notice: This dashboard authorizes or blocks "
            "proposed actions. It does not automatically execute "
            "production-changing operations."
        )
    # -----------------------------------------------------
    # Technical Details
    # -----------------------------------------------------

    with st.expander("⚙️ Agent Execution Details"):

        st.write(
            "**Incident ID:**",
            incident.incident_id,
        )

        st.write(
            "**Service:**",
            incident.service,
        )

        st.write(
            "**Environment:**",
            incident.environment,
        )

        st.write(
            "**Workflow status:**",
            result.get("final_status"),
        )

        st.write(
            "**Approval required:**",
            result.get("approval_required"),
        )

        if triage:
            st.markdown("##### Triage JSON")
            st.json(triage.model_dump(mode="json"))

        if investigation:
            st.markdown("##### Investigation JSON")
            st.json(
                investigation.model_dump(
                    mode="json"
                )
            )

        if plan:
            st.markdown("##### Response Plan JSON")
            st.json(
                plan.model_dump(
                    mode="json"
                )
            )