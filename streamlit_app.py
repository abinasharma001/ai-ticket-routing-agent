from __future__ import annotations

import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/predict"
ANALYZE_IMAGE_URL = "http://127.0.0.1:8000/analyze-image"

st.set_page_config(page_title="Ticket Routing Agent", page_icon="🎫", layout="centered")
st.title("AI Powered Intelligent Ticket Routing & Resolution Agent")
st.write("Submit a ticket and get a predicted category, department, confidence, resolution, and escalation flag.")

st.write("### Text Input")
title = st.text_input("Ticket title", placeholder="VPN connection drops for remote users")
description = st.text_area("Ticket description", placeholder="Remote staff lose VPN access every few minutes during work hours.")

st.write("### Image Input (Optional)")
uploaded_file = st.file_uploader("Upload screenshot", type=["png", "jpg", "jpeg"])

if st.button("Predict"):
    response = None
    try:
        if uploaded_file is not None:
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
            response = requests.post(ANALYZE_IMAGE_URL, files=files, timeout=30)
        else:
            if not title.strip() or not description.strip():
                st.error("Please enter both a title and a description, or upload an image.")
                st.stop()
            text_payload = f"{title}\n{description}"
            response = requests.post(API_URL, json={"text": text_payload}, timeout=30)
            
        response.raise_for_status()
        result = response.json()

        st.subheader("Prediction Result")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Category", result.get("category", ""))
        with col2:
            st.metric("Department", result.get("department", ""))
        with col3:
            st.metric("Confidence", f"{result.get('confidence', 0.0):.2f}")
            
        st.write("**Suggested Resolution**")
        st.success(result.get("resolution", "No resolution found"))
        
        if result.get("extracted_text"):
            st.write("**Extracted Text from Image**")
            st.info(result.get("extracted_text"))

        st.write("### Similar Tickets")
        similar_tickets = result.get("similar_tickets", [])
        if similar_tickets:
            for ticket in similar_tickets:
                with st.expander(f"[{ticket.get('score', 0.0):.2f}] {ticket.get('title', 'Unknown')} (ID: {ticket.get('id', 'N/A')})"):
                    st.write(f"**Resolution:** {ticket.get('resolution', 'N/A')}")
        else:
            st.write("No similar tickets found.")
            
    except requests.RequestException as exc:
        st.error(f"API request failed: {exc}")
