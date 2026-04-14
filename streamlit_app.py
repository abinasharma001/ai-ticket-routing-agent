from __future__ import annotations

import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/predict"

st.set_page_config(page_title="Ticket Routing Agent", page_icon="🎫", layout="centered")
st.title("AI Powered Intelligent Ticket Routing & Resolution Agent")
st.write("Submit a ticket and get a predicted category, department, confidence, resolution, and escalation flag.")

title = st.text_input("Ticket title", placeholder="VPN connection drops for remote users")
description = st.text_area("Ticket description", placeholder="Remote staff lose VPN access every few minutes during work hours.")

if st.button("Predict"):
    if not title.strip() or not description.strip():
        st.error("Please enter both a title and a description.")
    else:
        try:
            response = requests.post(API_URL, json={"title": title, "description": description}, timeout=30)
            response.raise_for_status()
            result = response.json()

            st.subheader("Prediction Result")
            st.metric("Category", result.get("category", ""))
            st.metric("Department", result.get("department", ""))
            st.metric("Confidence", f"{result.get('confidence', 0.0):.2f}")
            st.write("**Resolution**")
            st.success(result.get("resolution", ""))
            st.write(f"**Escalation:** {result.get('escalation', False)}")
        except requests.RequestException as exc:
            st.error(f"API request failed: {exc}")
