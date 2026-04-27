from __future__ import annotations

import requests
import streamlit as st
import pandas as pd
from app.utils.pdf_gen import generate_solution_pdf

API_URL = "http://127.0.0.1:8000/predict"
ANALYZE_IMAGE_URL = "http://127.0.0.1:8000/analyze-image"
ESCALATE_URL = "http://127.0.0.1:8000/escalate"
HISTORY_URL = "http://127.0.0.1:8000/history"

st.set_page_config(page_title="Ticket Routing Agent", page_icon="🎫", layout="centered")
st.title("AI Powered Intelligent Ticket Routing & Resolution Agent")

tab1, tab2 = st.tabs(["Support Agent", "Analytics Dashboard"])

with tab1:
    st.write("Submit a ticket and get a predicted category, department, confidence, and suggested solution.")

    st.write("### Text Input")
    title = st.text_input("Ticket title", placeholder="VPN connection drops for remote users")
    description = st.text_area("Ticket description", placeholder="Remote staff lose VPN access every few minutes during work hours.")

    st.write("### Image Input (Optional)")
    uploaded_file = st.file_uploader("Upload screenshot", type=["png", "jpg", "jpeg"])

    if st.button("Predict"):
        response = None
        text_payload = f"{title}\n{description}"
        try:
            if uploaded_file is not None:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                response = requests.post(ANALYZE_IMAGE_URL, files=files, timeout=30)
            else:
                if not title.strip() or not description.strip():
                    st.error("Please enter both a title and a description, or upload an image.")
                    st.stop()
                response = requests.post(API_URL, json={"text": text_payload}, timeout=30)
                
            response.raise_for_status()
            result = response.json()
            
            # Save to session state so we can use buttons without losing data
            st.session_state['prediction_result'] = result
            result['input'] = text_payload  # for PDF generator
            st.session_state['issue_text'] = result.get("extracted_text", text_payload)
            
        except requests.RequestException as exc:
            st.error(f"API request failed: {exc}")

    # Display results from session state
    if 'prediction_result' in st.session_state:
        result = st.session_state['prediction_result']
        issue_text = st.session_state['issue_text']
        
        st.subheader("Prediction Result")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Category", result.get("category", ""))
        with col2:
            st.metric("Department", result.get("department", ""))
        with col3:
            st.metric("Confidence", f"{result.get('confidence', 0.0):.2f}")
            
        st.write("### Suggested Solution")
        st.success(result.get("solution", "No solution found"))
        
        if result.get("extracted_text"):
            st.write("**Extracted Text from Image**")
            st.info(result.get("extracted_text"))

        st.write("### Similar Issues Found")
        similar_tickets = result.get("similar_tickets", [])
        if similar_tickets:
            for ticket in similar_tickets:
                with st.expander(f"[{ticket.get('score', 0.0):.2f}] {ticket.get('title', 'Unknown')} (ID: {ticket.get('id', 'N/A')})"):
                    st.write(f"**Solution:** {ticket.get('resolution', 'N/A')}")
        else:
            st.write("No similar tickets found.")
            
        st.write("---")
        
        # Action Buttons
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            # Download PDF
            pdf_buffer = generate_solution_pdf(result)
            st.download_button(
                label="Download Solution as PDF",
                data=pdf_buffer,
                file_name="ticket_resolution.pdf",
                mime="application/pdf"
            )
            
        with col_btn2:
            if st.button("Still not solved? Create Ticket"):
                with st.spinner("Escalating..."):
                    try:
                        esc_response = requests.post(ESCALATE_URL, json={
                            "issue": issue_text,
                            "category": result.get("category", ""),
                            "department": result.get("department", "")
                        }, timeout=30)
                        
                        if esc_response.status_code == 503:
                            st.warning("SMTP credentials not configured. Cannot send email.")
                        else:
                            esc_response.raise_for_status()
                            st.success("Ticket escalated and email sent successfully!")
                    except Exception as e:
                        st.error(f"Escalation failed: {e}")

with tab2:
    st.write("### Analytics Dashboard")
    st.write("View the history of processed tickets.")
    
    if st.button("Refresh History"):
        pass # re-runs the page naturally
        
    try:
        hist_resp = requests.get(HISTORY_URL, timeout=10)
        hist_resp.raise_for_status()
        data = hist_resp.json()
        
        df = pd.DataFrame(data)
        
        # Ensure all columns exist and normalize them to prevent KeyError
        expected_columns = ["id", "timestamp", "input_text", "category", "department", "confidence"]
        for col in expected_columns:
            if col not in df.columns:
                df[col] = None
                
        # Reorder columns safely
        if not df.empty:
            df = df[expected_columns]
        
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Could not load history: {e}")
