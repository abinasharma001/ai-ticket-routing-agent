from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

# ✅ USE LIVE BACKEND
API_URL = os.getenv(
    "API_URL",
    "https://dependable-learning-production.up.railway.app/predict"
)

st.set_page_config(
    page_title="AI Ticket Routing & Resolution Dashboard",
    page_icon="🚀",
    layout="wide",
)

# -----------------------------
# UI STYLING (UNCHANGED 🔥)
# -----------------------------

st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at 20% 20%, #1e3a8a 0%, #0f172a 45%, #020617 100%);
    color: #e2e8f0;
}
.main-title {
    font-size: 2.2rem;
    font-weight: 800;
    text-align: center;
}
.section-card {
    background: rgba(15, 23, 42, 0.8);
    border-radius: 16px;
    padding: 1rem;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER
# -----------------------------

st.markdown('<div class="main-title">🚀 AI Ticket Routing Dashboard</div>', unsafe_allow_html=True)

# -----------------------------
# INPUT
# -----------------------------

with st.container():
    st.markdown('<div class="section-card">', unsafe_allow_html=True)

    title = st.text_input("Ticket Title")
    description = st.text_area("Ticket Description", height=150)

    submitted = st.button("Analyze Ticket")

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# FUNCTIONS
# -----------------------------

def confidence_style(confidence: float):
    if confidence > 0.75:
        return "green", "High"
    elif confidence > 0.5:
        return "orange", "Medium"
    return "red", "Low"

def safe_float(value: Any):
    try:
        return float(value)
    except:
        return 0.0

# -----------------------------
# API CALL
# -----------------------------

if submitted:
    if not title.strip() or not description.strip():
        st.warning("Please enter both title and description")
    else:
        with st.spinner("Analyzing ticket..."):

            try:
                # ✅ FIX: Combine title + description
                combined_text = f"{title} {description}"

                response = requests.post(
                    API_URL,
                    json={"text": combined_text},   # 🔥 FIXED
                    timeout=30,
                )

                response.raise_for_status()
                result = response.json()

                confidence = safe_float(result.get("confidence", 0.0))
                color, level = confidence_style(confidence)

                # -----------------------------
                # RESULTS
                # -----------------------------

                st.markdown('<div class="section-card">', unsafe_allow_html=True)

                st.success("✅ Analysis Complete")

                st.write(f"### 📂 Category: {result.get('category')}")
                st.write(f"### 🏢 Department: {result.get('department')}")
                st.write(f"### 📊 Confidence: {confidence * 100:.0f}% ({level})")

                st.progress(min(max(confidence, 0.0), 1.0))

                st.markdown("</div>", unsafe_allow_html=True)

            except requests.RequestException as e:
                st.error("❌ Backend API not reachable")
                st.caption(str(e))

            except Exception as e:
                st.error("❌ Something went wrong")
                st.caption(str(e))

# -----------------------------
# FOOTER
# -----------------------------

st.markdown("---")
st.caption("Built with ❤️ using FastAPI + Streamlit")