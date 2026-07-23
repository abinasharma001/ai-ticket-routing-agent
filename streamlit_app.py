from __future__ import annotations

import requests
import pandas as pd
import plotly.express as px
import streamlit as st

from app.utils.pdf_gen import generate_solution_pdf


BASE_URL = "http://127.0.0.1:8001"
API_URL = f"{BASE_URL}/predict"
ANALYZE_IMAGE_URL = f"{BASE_URL}/analyze-image"
ESCALATE_URL = f"{BASE_URL}/escalate"
HISTORY_URL = f"{BASE_URL}/history"


st.set_page_config(page_title="Ticket Routing Agent", page_icon="🎫", layout="wide")


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1.1rem;
                padding-bottom: 2rem;
                max-width: 1180px;
            }
            .hero-shell {
                padding: 1.1rem 1.25rem;
                border-radius: 1.2rem;
                background: linear-gradient(135deg, rgba(15,23,42,0.98), rgba(30,41,59,0.92));
                color: #f8fafc;
                margin-bottom: 1rem;
                border: 1px solid rgba(148,163,184,0.24);
            }
            .hero-shell h1 {
                margin: 0;
                font-size: 2rem;
                line-height: 1.1;
            }
            .hero-shell p {
                margin: 0.4rem 0 0;
                color: #cbd5e1;
            }
            .result-card {
                border: 1px solid rgba(148,163,184,0.18);
                border-radius: 1rem;
                padding: 1rem;
                background: rgba(15,23,42,0.02);
            }
            .confidence-chip {
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
                padding: 0.35rem 0.65rem;
                border-radius: 999px;
                font-weight: 700;
                font-size: 0.9rem;
            }
            .confidence-green { background: rgba(16,185,129,0.14); color: #065f46; }
            .confidence-yellow { background: rgba(245,158,11,0.16); color: #92400e; }
            .confidence-red { background: rgba(239,68,68,0.14); color: #991b1b; }
            .similarity-badge {
                display: inline-block;
                margin-top: 0.35rem;
                padding: 0.25rem 0.55rem;
                border-radius: 999px;
                background: rgba(59,130,246,0.12);
                color: #1d4ed8;
                font-weight: 700;
                font-size: 0.85rem;
            }
            div[data-testid="stMetric"] {
                border: 1px solid rgba(148,163,184,0.16);
                border-radius: 0.9rem;
                padding: 0.7rem 0.8rem;
                background: rgba(255,255,255,0.02);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _format_percentage(value: float) -> str:
    return f"{max(0.0, min(1.0, value)) * 100:.0f}%"


def _confidence_class(confidence: float) -> str:
    if confidence >= 0.8:
        return "confidence-green"
    if confidence >= 0.6:
        return "confidence-yellow"
    return "confidence-red"


def _safe_error_message(response: requests.Response | None, fallback: str) -> str:
    if response is None:
        return fallback
    try:
        payload = response.json()
    except ValueError:
        return fallback
    if isinstance(payload, dict):
        return str(payload.get("detail") or fallback)
    return fallback


def _render_issue_summary(result: dict[str, object]) -> None:
    confidence = float(result.get("confidence", 0.0) or 0.0)
    st.markdown(
        f'<div class="confidence-chip {_confidence_class(confidence)}">Confidence: {_format_percentage(confidence)}</div>',
        unsafe_allow_html=True,
    )

    metrics = st.columns(3)
    with metrics[0]:
        st.metric("Category", result.get("category", ""))
    with metrics[1]:
        st.metric("Department", result.get("department", ""))
    with metrics[2]:
        st.metric("Processing Time", f"{float(result.get('processing_ms', 0.0) or 0.0):.0f} ms")

    st.progress(int(max(0.0, min(1.0, confidence)) * 100))
    st.markdown("### Suggested Solution")
    st.success(result.get("solution", "No solution found."))


def _render_similar_tickets(similar_tickets: list[dict[str, object]]) -> None:
    st.markdown("### Similar Issues Found")
    if not similar_tickets:
        st.info("No highly similar historical ticket found.")
        return

    for ticket in similar_tickets:
        similarity = float(ticket.get("score", 0.0) or 0.0)
        similarity_percent = _format_percentage(similarity)
        with st.expander(f"Ticket {ticket.get('id', 'N/A')} · Similarity: {similarity_percent}", expanded=False):
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            card_cols = st.columns(2)
            with card_cols[0]:
                st.write(f"**Ticket ID:** {ticket.get('id', 'N/A')}")
                st.write(f"**Category:** {ticket.get('category', 'N/A')}")
                st.write(f"**Department:** {ticket.get('department', 'N/A')}")
            with card_cols[1]:
                st.markdown(f'<span class="similarity-badge">Similarity: {similarity_percent}</span>', unsafe_allow_html=True)
                st.write(f"**Problem:** {ticket.get('title') or ticket.get('ticket_text', 'N/A')}")
            st.write(f"**Suggested Solution:** {ticket.get('resolution', 'N/A')}")
            st.markdown("</div>", unsafe_allow_html=True)


def _render_history_analytics(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No ticket history has been recorded yet.")
        return

    df = df.copy()
    df["timestamp"] = pd.to_datetime(df.get("timestamp"), errors="coerce")
    df["confidence"] = pd.to_numeric(df.get("confidence"), errors="coerce").fillna(0.0)
    if "processing_ms" not in df.columns:
        df["processing_ms"] = pd.NA
    df["processing_ms"] = pd.to_numeric(df.get("processing_ms"), errors="coerce")

    total_tickets = int(len(df))
    average_confidence = float(df["confidence"].mean()) if total_tickets else 0.0
    average_processing_ms = float(df["processing_ms"].mean()) if df["processing_ms"].notna().any() else 0.0
    category_count = int(df["category"].nunique()) if "category" in df.columns else 0
    department_count = int(df["department"].nunique()) if "department" in df.columns else 0

    summary_cols = st.columns(4)
    summary_cols[0].metric("Total Tickets", f"{total_tickets}")
    summary_cols[1].metric("Average Confidence", _format_percentage(average_confidence))
    summary_cols[2].metric("Avg Processing Time", f"{average_processing_ms:.0f} ms")
    summary_cols[3].metric("Distinct Categories", f"{category_count} / {department_count}")

    chart_cols = st.columns(2)

    with chart_cols[0]:
        st.markdown("#### Tickets by Category")
        category_counts = df["category"].fillna("Unknown").value_counts().reset_index()
        category_counts.columns = ["Category", "Count"]
        st.plotly_chart(px.bar(category_counts, x="Category", y="Count", text="Count"), width="stretch")

        st.markdown("#### Daily Ticket Trend")
        daily_trend = df.dropna(subset=["timestamp"]).copy()
        if not daily_trend.empty:
            daily_trend["date"] = daily_trend["timestamp"].dt.date
            trend_series = daily_trend.groupby("date").size().reset_index(name="Tickets")
            st.plotly_chart(px.line(trend_series, x="date", y="Tickets", markers=True), width="stretch")
        else:
            st.info("Not enough timestamp data for a daily trend yet.")

    with chart_cols[1]:
        st.markdown("#### Tickets by Department")
        department_counts = df["department"].fillna("Unknown").value_counts().reset_index()
        department_counts.columns = ["Department", "Count"]
        st.plotly_chart(px.bar(department_counts, x="Department", y="Count", text="Count"), width="stretch")

        st.markdown("#### Confidence Distribution")
        confidence_bins = pd.cut(df["confidence"].fillna(0.0), bins=[0, 0.5, 0.7, 0.85, 1.0], include_lowest=True)
        confidence_distribution = confidence_bins.value_counts().sort_index().reset_index()
        confidence_distribution.columns = ["Range", "Count"]
        st.plotly_chart(px.pie(confidence_distribution, names="Range", values="Count", hole=0.45), width="stretch")

    recurring_issues = (
        df["input_text"].fillna("").str.split("\n").str[0].value_counts().head(5)
        if "input_text" in df.columns
        else pd.Series(dtype=int)
    )

    st.markdown("#### Top Recurring Issues")
    if not recurring_issues.empty:
        recurring_df = recurring_issues.reset_index()
        recurring_df.columns = ["Issue", "Count"]
        st.plotly_chart(px.bar(recurring_df, x="Issue", y="Count", text="Count"), width="stretch")
    else:
        st.info("No recurring issues detected yet.")

    st.markdown("#### Ticket History")
    display_df = df.copy()
    for column in ["id", "timestamp", "input_text", "category", "department", "confidence", "processing_ms"]:
        if column not in display_df.columns:
            display_df[column] = None
    st.dataframe(display_df[["id", "timestamp", "input_text", "category", "department", "confidence", "processing_ms"]], width="stretch")


_inject_styles()
st.markdown(
    """
    <div class="hero-shell">
        <h1>AI Powered Intelligent Ticket Routing & Resolution Agent</h1>
        <p>Route tickets, inspect OCR text, retrieve similar incidents, escalate when needed, and review historical analytics.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2 = st.tabs(["Support Agent", "Analytics Dashboard"])

with tab1:
    st.write("Submit a ticket and get a predicted category, department, confidence, and suggested solution.")

    with st.form("prediction_form", clear_on_submit=False):
        left_col, right_col = st.columns([1.2, 1])
        with left_col:
            st.markdown("### Text Input")
            title = st.text_input("Ticket title", placeholder="VPN connection drops for remote users")
            description = st.text_area(
                "Ticket description",
                placeholder="Remote staff lose VPN access every few minutes during work hours.",
                height=140,
            )

        with right_col:
            st.markdown("### Image Input (Optional)")
            uploaded_file = st.file_uploader(
                "Upload screenshot",
                type=["png", "jpg", "jpeg"],
                help="PNG or JPG only. Keep screenshots under 5 MB.",
            )
            if uploaded_file is not None:
                st.image(uploaded_file, caption="Uploaded image preview", use_container_width=True)

        submitted = st.form_submit_button("Predict")

    if submitted:
        response = None
        text_payload = f"{title}\n{description}".strip()

        try:
            if uploaded_file is not None:
                file_bytes = uploaded_file.getvalue()
                if len(file_bytes) > 5 * 1024 * 1024:
                    st.error("Please upload an image smaller than 5 MB.")
                    st.stop()
                if not uploaded_file.type or not uploaded_file.type.startswith("image/"):
                    st.error("Only image files are allowed for OCR analysis.")
                    st.stop()
                files = {"file": (uploaded_file.name, file_bytes, uploaded_file.type)}
                with st.spinner("Analyzing screenshot and extracting text..."):
                    response = requests.post(ANALYZE_IMAGE_URL, files=files, timeout=30)
            else:
                if not title.strip() or not description.strip():
                    st.error("Please enter both a title and a description, or upload an image.")
                    st.stop()
                with st.spinner("Predicting ticket routing..."):
                    response = requests.post(API_URL, json={"text": text_payload}, timeout=30)

            if response is None:
                st.stop()

            if response.ok:
                result = response.json()
                result["input"] = result.get("extracted_text", text_payload)
                st.session_state["prediction_result"] = result
                st.session_state["issue_text"] = result.get("extracted_text", text_payload)
                st.toast("Prediction completed successfully.", icon="✅")
            else:
                st.session_state.pop("prediction_result", None)
                st.session_state.pop("issue_text", None)
                st.error(_safe_error_message(response, "The backend could not complete the request."))
                st.toast("Prediction failed.", icon="⚠️")
        except requests.RequestException:
            st.error("The API is temporarily unavailable. Please try again in a moment.")
            st.toast("Request failed.", icon="⚠️")

    if "prediction_result" in st.session_state:
        result = st.session_state["prediction_result"]
        issue_text = st.session_state.get("issue_text", result.get("input", ""))

        st.subheader("Prediction Result")
        _render_issue_summary(result)

        if result.get("extracted_text"):
            st.markdown("### Extracted Text from Image")
            st.info(result.get("extracted_text"))

        _render_similar_tickets(result.get("similar_tickets", []))

        st.write("---")
        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            pdf_buffer = generate_solution_pdf(result)
            st.download_button(
                label="Download Solution as PDF",
                data=pdf_buffer,
                file_name="ticket_resolution.pdf",
                mime="application/pdf",
                width="stretch",
            )

        with col_btn2:
            if st.button("Still not solved? Create Ticket", width="stretch"):
                with st.spinner("Escalating ticket and preparing email..."):
                    try:
                        esc_response = requests.post(
                            ESCALATE_URL,
                            json={
                                "issue": issue_text,
                                "category": result.get("category", ""),
                                "department": result.get("department", ""),
                            },
                            timeout=30,
                        )
                        if esc_response.ok:
                            st.success("Ticket escalated and email sent successfully!")
                            st.toast("Escalation sent.", icon="📨")
                        else:
                            st.error(_safe_error_message(esc_response, "Escalation failed."))
                            st.toast("Escalation failed.", icon="⚠️")
                    except requests.RequestException:
                        st.error("Escalation service is temporarily unavailable.")
                        st.toast("Escalation request failed.", icon="⚠️")

with tab2:
    st.write("### Analytics Dashboard")
    st.write("View the history of processed tickets.")

    if st.button("Refresh History", width="stretch"):
        st.rerun()

    try:
        hist_resp = requests.get(HISTORY_URL, timeout=10)
        hist_resp.raise_for_status()
        data = hist_resp.json()
        df = pd.DataFrame(data)
        _render_history_analytics(df)
    except requests.RequestException:
        st.error("Could not load history right now. Please try again later.")
    except Exception:
        st.error("Could not load history right now. Please try again later.")
