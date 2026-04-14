from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000/predict")

st.set_page_config(
    page_title="AI Ticket Routing & Resolution Dashboard",
    page_icon="🚀",
    layout="wide",
)

st.markdown(
    """
    <style>
        .stApp {
            background: radial-gradient(circle at 20% 20%, #1e3a8a 0%, #0f172a 45%, #020617 100%);
            color: #e2e8f0;
            font-family: "Inter", "Segoe UI", sans-serif;
        }

        div[data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at 20% 20%, #1e3a8a 0%, #0f172a 45%, #020617 100%);
        }

        .dashboard-header {
            text-align: center;
            padding: 1.25rem 1rem 1.75rem 1rem;
        }

        .main-title {
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: 0.01em;
            color: #f8fafc;
            margin-bottom: 0.35rem;
        }

        .subtitle {
            color: #cbd5e1;
            font-size: 1.02rem;
            line-height: 1.55;
            margin-bottom: 0.2rem;
        }

        .section-card {
            background: linear-gradient(145deg, rgba(15, 23, 42, 0.88), rgba(15, 23, 42, 0.72));
            border: 1px solid rgba(148, 163, 184, 0.20);
            border-radius: 20px;
            padding: 1.2rem 1.2rem;
            margin-bottom: 1.15rem;
            box-shadow: 0 10px 30px rgba(2, 6, 23, 0.45);
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        }

        .section-card:hover {
            transform: scale(1.01);
            box-shadow: 0 16px 34px rgba(2, 6, 23, 0.55);
            border-color: rgba(96, 165, 250, 0.50);
        }

        .result-fade {
            animation: fadeInUp 0.45s ease-in-out;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(8px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .ticket-card {
            background: rgba(15, 23, 42, 0.50);
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 14px;
            padding: 0.75rem 0.9rem;
            margin-bottom: 0.65rem;
        }

        .ticket-title {
            color: #f1f5f9;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }

        .ticket-meta {
            color: #cbd5e1;
            font-size: 0.92rem;
            line-height: 1.4;
        }

        .status-good { color: #22c55e; font-weight: 700; }
        .status-medium { color: #facc15; font-weight: 700; }
        .status-low { color: #ef4444; font-weight: 700; }

        .stButton > button {
            width: 100%;
            border: 0;
            border-radius: 12px;
            padding: 0.65rem 1.1rem;
            font-weight: 700;
            color: #e2e8f0;
            background: linear-gradient(90deg, #2563eb, #1d4ed8, #1e40af);
            box-shadow: 0 8px 18px rgba(37, 99, 235, 0.35);
            transition: transform 0.16s ease, box-shadow 0.16s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 12px 20px rgba(37, 99, 235, 0.45);
        }

        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div {
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, 0.35);
            background: rgba(15, 23, 42, 0.70);
        }

        hr.dashboard-divider {
            border: 0;
            border-top: 1px solid rgba(148, 163, 184, 0.22);
            margin: 0.6rem 0 1rem 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="dashboard-header">', unsafe_allow_html=True)
st.markdown('<div class="main-title">🚀 AI Ticket Routing & Resolution Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Smart AI system to classify, route, and resolve IT support tickets</div>',
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)


def confidence_style(confidence: float) -> tuple[str, str, str]:
    if confidence > 0.75:
        return "status-good", "green", "High"
    if confidence > 0.50:
        return "status-medium", "orange", "Medium"
    return "status-low", "red", "Low"


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


with st.container():
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🧠 Ticket Input")
    st.markdown('<hr class="dashboard-divider" />', unsafe_allow_html=True)
    with st.form("ticket_form", clear_on_submit=False):
        title = st.text_input("Ticket Title", placeholder="VPN connection drops for remote users")

        description = st.text_area(
            "Ticket Description",
            placeholder="Remote staff lose VPN access every few minutes during work hours.",
            height=180,
        )

        submitted = st.form_submit_button("Analyze Ticket", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

if submitted:
    if not title.strip() or not description.strip():
        st.error("Please enter both a ticket title and a ticket description.")
    else:
        try:
            response = requests.post(
                API_URL,
                json={"title": title, "description": description},
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            confidence = safe_float(result.get("confidence", 0.0))
            confidence_class, confidence_color, confidence_level = confidence_style(confidence)
            similar_tickets = result.get("similar_tickets", []) or []
            reason = str(result.get("reason", ""))

            st.markdown('<div class="section-card result-fade">', unsafe_allow_html=True)
            st.subheader("📊 Analysis Results")
            st.markdown('<hr class="dashboard-divider" />', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🎯 Predicted Category", result.get("category", "-"))
            with col2:
                st.metric("🏢 Assigned Department", result.get("department", "-"))
            with col3:
                st.metric("🧪 Confidence", f"{confidence * 100:.0f}%")

            st.markdown("### 📊 Confidence Score")
            st.progress(min(max(confidence, 0.0), 1.0))
            st.markdown(
                f'<span class="{confidence_class}">Confidence: {confidence * 100:.0f}% ({confidence_level})</span>',
                unsafe_allow_html=True,
            )
            st.caption("Green = good confidence, Yellow = medium confidence, Red = low confidence")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="section-card result-fade">', unsafe_allow_html=True)
            st.subheader("💡 Suggested Resolution")
            st.markdown('<hr class="dashboard-divider" />', unsafe_allow_html=True)
            st.success(result.get("resolution", "No resolution returned."))
            if reason:
                st.caption(f"Reason: {reason}")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="section-card result-fade">', unsafe_allow_html=True)
            st.subheader("🚨 Escalation Status")
            st.markdown('<hr class="dashboard-divider" />', unsafe_allow_html=True)
            escalation = bool(result.get("escalation", False))
            if escalation:
                st.error("🚨 Escalation Required")
            else:
                st.success("✅ No Escalation Required")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="section-card result-fade">', unsafe_allow_html=True)
            st.subheader("📚 Similar Tickets")
            st.markdown('<hr class="dashboard-divider" />', unsafe_allow_html=True)
            if similar_tickets:
                for item in similar_tickets:
                    if isinstance(item, dict):
                        ticket_text = item.get("ticket_text") or item.get("title") or "Similar ticket"
                        resolution = item.get("resolution", "")
                        similarity = safe_float(item.get("similarity", 0.0))
                        st.markdown('<div class="ticket-card">', unsafe_allow_html=True)
                        st.markdown(f'<div class="ticket-title">{ticket_text}</div>', unsafe_allow_html=True)
                        st.markdown(
                            f'<div class="ticket-meta">Similarity: {similarity * 100:.0f}%<br/>Suggested resolution: {resolution}</div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="ticket-card">', unsafe_allow_html=True)
                        st.markdown(f'<div class="ticket-meta">{item}</div>', unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("No similar tickets were returned by the backend for this request.")
            st.markdown("</div>", unsafe_allow_html=True)
        except requests.RequestException as exc:
            st.error(
                "Unable to reach the API at http://localhost:8000/predict. "
                "Make sure the backend is running, then try again."
            )
            st.caption(str(exc))
