from __future__ import annotations

import os
from typing import Any
from datetime import datetime
from collections import Counter

import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ✅ USE LIVE BACKEND
API_URL = os.getenv(
    "API_URL",
    "https://dependable-learning-production.up.railway.app/predict"
)

# ============================================
# PAGE CONFIGURATION
# ============================================

st.set_page_config(
    page_title="AI Ticket Routing & Resolution Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================
# GLASSMORPHISM STYLING & ANIMATIONS
# ============================================

st.markdown("""
<style>
    /* Root styling */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        color: #f1f5f9;
    }
    
    html, body {
        margin: 0;
        padding: 0;
    }
    
    /* Main container */
    .main {
        padding: 2rem 1rem;
    }
    
    /* Hero section */
    .hero-container {
        text-align: center;
        margin-bottom: 3rem;
        animation: fadeInDown 0.6s ease-out;
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 900;
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        padding: 0;
        letter-spacing: -1px;
    }
    
    .hero-subtitle {
        font-size: 1.15rem;
        color: #cbd5e1;
        margin-top: 0.75rem;
        font-weight: 300;
        letter-spacing: 0.5px;
    }
    
    .hero-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        display: inline-block;
        animation: bounce 2s infinite;
    }
    
    /* Glassmorphism card */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 20px;
        padding: 2rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        margin-bottom: 2rem;
        transition: all 0.3s ease;
        animation: fadeIn 0.8s ease-out;
    }
    
    .glass-card:hover {
        background: rgba(30, 41, 59, 0.85);
        border-color: rgba(148, 163, 184, 0.3);
        box-shadow: 0 12px 40px rgba(59, 130, 246, 0.15);
        transform: translateY(-2px);
    }
    
    /* Input card */
    .input-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(100, 165, 250, 0.2);
        border-radius: 20px;
        padding: 2.5rem;
        backdrop-filter: blur(15px);
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1), 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .input-card:focus-within {
        border-color: rgba(100, 165, 250, 0.5);
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1), 0 0 30px rgba(100, 165, 250, 0.2);
    }
    
    /* Result cards */
    .result-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 16px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
        animation: slideInUp 0.6s ease-out;
    }
    
    .result-card:hover {
        background: rgba(30, 41, 59, 0.8);
        border-color: rgba(148, 163, 184, 0.3);
        box-shadow: 0 12px 40px rgba(59, 130, 246, 0.15);
        transform: translateY(-4px);
    }
    
    .result-card-icon {
        font-size: 2.5rem;
        margin-bottom: 0.75rem;
    }
    
    .result-card-label {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    
    .result-card-value {
        font-size: 1.5rem;
        color: #f1f5f9;
        font-weight: 700;
    }
    
    /* Confidence card with progress bar */
    .confidence-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 16px;
        padding: 2rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        animation: slideInUp 0.7s ease-out;
    }
    
    .confidence-label {
        font-size: 0.9rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    .confidence-value {
        font-size: 3rem;
        font-weight: 900;
        margin-bottom: 1rem;
    }
    
    .confidence-value.high {
        color: #10b981;
    }
    
    .confidence-value.medium {
        color: #f59e0b;
    }
    
    .confidence-value.low {
        color: #ef4444;
    }
    
    .confidence-bar {
        height: 8px;
        background: rgba(148, 163, 184, 0.2);
        border-radius: 10px;
        overflow: hidden;
        margin-bottom: 1rem;
    }
    
    .confidence-fill {
        height: 100%;
        background: linear-gradient(90deg, #10b981 0%, #f59e0b 50%, #ef4444 100%);
        border-radius: 10px;
        animation: growBar 0.8s ease-out;
    }
    
    .confidence-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .confidence-badge.high {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .confidence-badge.medium {
        background: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    
    .confidence-badge.low {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        padding: 1rem 2rem !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        box-shadow: 0 8px 15px rgba(59, 130, 246, 0.3) !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%) !important;
        box-shadow: 0 12px 25px rgba(59, 130, 246, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(15, 23, 42, 0.5) !important;
        border: 1px solid rgba(100, 165, 250, 0.2) !important;
        color: #f1f5f9 !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        background: rgba(15, 23, 42, 0.8) !important;
        border-color: rgba(100, 165, 250, 0.5) !important;
        box-shadow: 0 0 15px rgba(100, 165, 250, 0.2) !important;
    }
    
    /* Spinner animation */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .spinner {
        display: inline-block;
        width: 40px;
        height: 40px;
        border: 4px solid rgba(100, 165, 250, 0.2);
        border-top: 4px solid #60a5fa;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        margin: 0 auto;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    
    @keyframes growBar {
        from {
            width: 0;
        }
        to {
            width: 100%;
        }
    }
    
    /* Typography */
    h1, h2, h3 {
        margin-top: 0;
        margin-bottom: 1rem;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2.5rem;
        }
        
        .glass-card {
            padding: 1.5rem;
        }
        
        .input-card {
            padding: 1.5rem;
        }
    }
    
    /* KPI Cards */
    .kpi-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 16px;
        padding: 1.75rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
        animation: slideInUp 0.6s ease-out;
        text-align: center;
    }
    
    .kpi-card:hover {
        background: rgba(30, 41, 59, 0.8);
        border-color: rgba(148, 163, 184, 0.3);
        box-shadow: 0 12px 40px rgba(59, 130, 246, 0.15);
        transform: translateY(-4px);
    }
    
    .kpi-icon {
        font-size: 2rem;
        margin-bottom: 0.75rem;
        display: inline-block;
    }
    
    .kpi-label {
        font-size: 0.75rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    
    .kpi-value {
        font-size: 2.25rem;
        color: #f1f5f9;
        font-weight: 900;
        margin-bottom: 0.5rem;
    }
    
    .kpi-subtitle {
        font-size: 0.85rem;
        color: #cbd5e1;
        font-weight: 400;
    }
    
    /* Chart container */
    .chart-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 16px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        margin-bottom: 2rem;
    }
    
    .chart-title {
        font-size: 1.25rem;
        color: #f1f5f9;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    /* Table styling */
    .stDataFrame {
        background: rgba(30, 41, 59, 0.6) !important;
        border-radius: 12px !important;
    }
    
    .stDataFrame th {
        background: rgba(59, 130, 246, 0.1) !important;
        color: #60a5fa !important;
        font-weight: 700 !important;
    }
    
    .stDataFrame td {
        color: #cbd5e1 !important;
    }
    
    /* Sidebar nav button */
    .nav-button {
        display: inline-block;
        padding: 0.75rem 1.5rem;
        margin: 0.25rem;
        border-radius: 8px;
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.3);
        color: #60a5fa;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .nav-button:hover {
        background: rgba(59, 130, 246, 0.2);
        border-color: rgba(59, 130, 246, 0.6);
    }
    
    .nav-button.active {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        border-color: transparent;
    }
    
    /* Loading state for plotly */
    .plotly-graph-div {
        background: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# UTILITY FUNCTIONS
# ============================================

def confidence_style(confidence: float) -> tuple[str, str, str]:
    """
    Determine confidence level styling and category.
    
    Args:
        confidence: Float between 0 and 1
        
    Returns:
        Tuple of (color, level, emoji)
    """
    if confidence > 0.75:
        return "high", "High Confidence", "🎯"
    elif confidence > 0.5:
        return "medium", "Medium Confidence", "⚡"
    return "low", "Low Confidence", "⚠️"

def safe_float(value: Any) -> float:
    """Safely convert value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def render_hero_section():
    """Render the centered hero header with title and subtitle."""
    st.markdown("""
    <div class="hero-container">
        <div class="hero-icon">🚀</div>
        <h1 class="hero-title">AI Ticket Routing</h1>
        <p class="hero-subtitle">Intelligent classification & department routing powered by machine learning</p>
    </div>
    """, unsafe_allow_html=True)

def render_input_section() -> tuple[str, str, bool]:
    """Render the input card and return form data."""
    st.markdown('<div class="glass-card input-card">', unsafe_allow_html=True)
    
    st.markdown("##### 📝 Submit Ticket")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        title = st.text_input(
            "Ticket Title",
            placeholder="Enter a brief ticket title...",
            label_visibility="collapsed"
        )
    
    with col2:
        pass  # For alignment
    
    description = st.text_area(
        "Ticket Description",
        placeholder="Describe the issue in detail...",
        height=120,
        label_visibility="collapsed"
    )
    
    submitted = st.button("🔍 Analyze Ticket", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    return title, description, submitted

def render_loading_spinner():
    """Render animated loading spinner."""
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center;">
            <div class="spinner"></div>
            <p style="color: #94a3b8; margin-top: 1rem; font-size: 1.1rem;">Analyzing ticket...</p>
        </div>
        """, unsafe_allow_html=True)

def render_result_card(icon: str, label: str, value: str):
    """
    Render a single result card.
    
    Args:
        icon: Emoji icon
        label: Field label
        value: Field value
    """
    st.markdown(f"""
    <div class="result-card">
        <div class="result-card-icon">{icon}</div>
        <div class="result-card-label">{label}</div>
        <div class="result-card-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def render_confidence_card(confidence: float):
    """
    Render the confidence card with progress bar and color coding.
    
    Args:
        confidence: Confidence score between 0 and 1
    """
    color_class, level, emoji = confidence_style(confidence)
    percentage = min(max(confidence * 100, 0), 100)
    
    st.markdown(f"""
    <div class="confidence-card">
        <div class="confidence-label">Classification Confidence</div>
        <div class="confidence-value {color_class}">{percentage:.1f}%</div>
        <div class="confidence-bar">
            <div class="confidence-fill" style="width: {percentage}%;"></div>
        </div>
        <span class="confidence-badge {color_class}">{emoji} {level}</span>
    </div>
    """, unsafe_allow_html=True)

def render_results_section(result: dict):
    """
    Render the complete results section with all cards.
    
    Args:
        result: Dictionary with API response data
    """
    st.markdown('<div style="margin-top: 2rem;">', unsafe_allow_html=True)
    
    # Success message
    st.success("✅ Analysis Complete", icon="✅")
    
    # Create columns for result cards
    col1, col2, col3 = st.columns(3)
    
    category = result.get('category', 'Unknown')
    department = result.get('department', 'Unknown')
    confidence = safe_float(result.get('confidence', 0.0))
    
    with col1:
        render_result_card("📂", "Category", category)
    
    with col2:
        render_result_card("🏢", "Department", department)
    
    with col3:
        render_confidence_card(confidence)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# ANALYTICS FUNCTIONS
# ============================================

def add_to_history(title: str, description: str, result: dict):
    """
    Add a prediction to the history.
    
    Args:
        title: Ticket title
        description: Ticket description
        result: API response
    """
    entry = {
        "timestamp": datetime.now(),
        "input_text": f"{title} {description}",
        "category": result.get('category', 'Unknown'),
        "department": result.get('department', 'Unknown'),
        "confidence": safe_float(result.get('confidence', 0.0))
    }
    st.session_state.prediction_history.append(entry)

def get_kpi_stats() -> dict:
    """Calculate KPI statistics from prediction history."""
    if not st.session_state.prediction_history:
        return {
            "total": 0,
            "avg_confidence": 0.0,
            "most_frequent_category": "N/A"
        }
    
    history = st.session_state.prediction_history
    categories = [h["category"] for h in history]
    confidences = [h["confidence"] for h in history]
    
    most_common = Counter(categories).most_common(1)
    
    return {
        "total": len(history),
        "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
        "most_frequent_category": most_common[0][0] if most_common else "N/A"
    }

def render_kpi_cards():
    """Render KPI statistics cards."""
    stats = get_kpi_stats()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">📊</div>
            <div class="kpi-label">Total Tickets</div>
            <div class="kpi-value">{stats['total']}</div>
            <div class="kpi-subtitle">Analyzed predictions</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">💯</div>
            <div class="kpi-label">Avg Confidence</div>
            <div class="kpi-value">{stats['avg_confidence'] * 100:.1f}%</div>
            <div class="kpi-subtitle">Classification accuracy</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">🏷️</div>
            <div class="kpi-label">Top Category</div>
            <div class="kpi-value">{stats['most_frequent_category']}</div>
            <div class="kpi-subtitle">Most frequent</div>
        </div>
        """, unsafe_allow_html=True)

def render_category_distribution():
    """Render category distribution bar chart."""
    if not st.session_state.prediction_history:
        st.info("No data available yet. Make some predictions to see analytics.")
        return
    
    history = st.session_state.prediction_history
    categories = [h["category"] for h in history]
    category_counts = Counter(categories)
    
    df = pd.DataFrame({
        "Category": list(category_counts.keys()),
        "Count": list(category_counts.values())
    }).sort_values("Count", ascending=False)
    
    fig = px.bar(
        df,
        x="Category",
        y="Count",
        title="Ticket Category Distribution",
        labels={"Count": "Number of Tickets"},
        color="Count",
        color_continuous_scale="Blues"
    )
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f1f5f9"),
        title_font_size=20,
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_department_distribution():
    """Render department distribution pie chart."""
    if not st.session_state.prediction_history:
        return
    
    history = st.session_state.prediction_history
    departments = [h["department"] for h in history]
    dept_counts = Counter(departments)
    
    fig = px.pie(
        names=list(dept_counts.keys()),
        values=list(dept_counts.values()),
        title="Ticket Distribution by Department"
    )
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f1f5f9"),
        title_font_size=20,
        legend=dict(font=dict(size=12))
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_confidence_timeline():
    """Render confidence score timeline."""
    if not st.session_state.prediction_history:
        return
    
    history = st.session_state.prediction_history
    df = pd.DataFrame(history)
    df["Index"] = range(1, len(df) + 1)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df["Index"],
        y=df["confidence"] * 100,
        mode="lines+markers",
        name="Confidence %",
        line=dict(color="#60a5fa", width=3),
        marker=dict(size=8),
        fill="tozeroy",
        fillcolor="rgba(96, 165, 250, 0.1)"
    ))
    
    fig.add_hline(
        y=75,
        line_dash="dash",
        line_color="rgba(16, 185, 129, 0.5)",
        annotation_text="High Confidence (75%)",
        annotation_position="right"
    )
    
    fig.update_layout(
        title="Prediction Confidence Over Time",
        xaxis_title="Prediction Number",
        yaxis_title="Confidence (%)",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f1f5f9"),
        title_font_size=20,
        hovermode="x unified",
        yaxis=dict(range=[0, 100])
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_recent_predictions():
    """Render table of recent predictions."""
    if not st.session_state.prediction_history:
        st.info("No predictions yet. Submit tickets to see history.")
        return
    
    history = st.session_state.prediction_history
    df = pd.DataFrame(history)
    
    # Show last 10 predictions, newest first
    df = df.iloc[-10:].iloc[::-1].reset_index(drop=True)
    
    # Format columns
    df["Timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df["Confidence"] = (df["confidence"] * 100).round(1).astype(str) + "%"
    df["Input"] = df["input_text"].str[:50] + "..."
    
    display_df = df[["Timestamp", "Category", "Department", "Confidence", "Input"]]
    
    st.markdown("### Recent Predictions (Last 10)")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

def render_analytics_page():
    """Render the complete analytics dashboard."""
    # Header
    st.markdown("""
    <div class="hero-container">
        <div class="hero-icon">📊</div>
        <h1 class="hero-title">Analytics Dashboard</h1>
        <p class="hero-subtitle">Insights from your ticket prediction history</p>
    </div>
    """, unsafe_allow_html=True)
    
    # KPI Cards
    st.markdown("### Key Performance Indicators")
    render_kpi_cards()
    
    st.markdown("---")
    
    # Charts Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Category Distribution")
        render_category_distribution()
    
    with col2:
        st.markdown("### Department Distribution")
        render_department_distribution()
    
    st.markdown("---")
    
    # Timeline
    st.markdown("### Confidence Score Timeline")
    render_confidence_timeline()
    
    st.markdown("---")
    
    # Recent Predictions Table
    render_recent_predictions()
    
    st.markdown("---")
    
    # Clear History Button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🗑️ Clear All History", use_container_width=True, key="clear_history"):
            st.session_state.prediction_history = []
            st.success("✅ Prediction history cleared!")
            st.rerun()

# ============================================
# MAIN APPLICATION
# ============================================

def main():
    """Main application entry point."""
    # Initialize session state
    if "api_result" not in st.session_state:
        st.session_state.api_result = None
    if "api_error" not in st.session_state:
        st.session_state.api_error = None
    if "prediction_history" not in st.session_state:
        st.session_state.prediction_history = []
    if "current_page" not in st.session_state:
        st.session_state.current_page = "prediction"
    
    # Sidebar Navigation
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="color: #60a5fa; letter-spacing: 1px;">🚀 Navigation</h2>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎯 Prediction", use_container_width=True, key="nav_prediction"):
                st.session_state.current_page = "prediction"
                st.rerun()
        
        with col2:
            if st.button("📊 Analytics", use_container_width=True, key="nav_analytics"):
                st.session_state.current_page = "analytics"
                st.rerun()
        
        st.markdown("---")
        
        # History stats in sidebar
        st.markdown("### 📈 History Stats")
        stats = get_kpi_stats()
        st.metric("Total Predictions", stats['total'])
        st.metric("Avg Confidence", f"{stats['avg_confidence'] * 100:.1f}%")
        st.metric("Top Category", stats['most_frequent_category'])
    
    # Page Routing
    if st.session_state.current_page == "prediction":
        render_prediction_page()
    elif st.session_state.current_page == "analytics":
        render_analytics_page()

def render_prediction_page():
    """Render the main prediction/ticket routing page."""
    render_hero_section()
    
    title, description, submitted = render_input_section()
    
    if submitted:
        if not title.strip() or not description.strip():
            st.warning("⚠️ Please enter both ticket title and description")
        else:
            # Show loading spinner
            render_loading_spinner()
            
            try:
                combined_text = f"{title} {description}"
                
                response = requests.post(
                    API_URL,
                    json={"text": combined_text},
                    timeout=30,
                )
                
                response.raise_for_status()
                result = response.json()
                st.session_state.api_result = result
                st.session_state.api_error = None
                
                # Add to history
                add_to_history(title, description, result)
                
                st.rerun()
                
            except requests.exceptions.Timeout:
                st.session_state.api_error = ("timeout", "⏱️ Request timeout - API is taking too long to respond")
                st.rerun()
            
            except requests.exceptions.ConnectionError:
                st.session_state.api_error = ("connection", "❌ Cannot connect to API")
                st.rerun()
            
            except requests.exceptions.RequestException as e:
                st.session_state.api_error = ("request", f"❌ API Error: {str(e)}")
                st.rerun()
            
            except Exception as e:
                st.session_state.api_error = ("unknown", f"❌ Unexpected Error: {str(e)}")
                st.rerun()
    
    # Display results or errors
    if st.session_state.api_result:
        render_results_section(st.session_state.api_result)
        
        # Add clear button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔄 New Prediction", use_container_width=True, key="new_prediction"):
                st.session_state.api_result = None
                st.session_state.api_error = None
                st.rerun()
    
    elif st.session_state.api_error:
        error_type, error_msg = st.session_state.api_error
        st.error(error_msg)
        
        if error_type == "timeout":
            st.caption("Please try again or contact support")
        elif error_type == "connection":
            st.caption("Backend service is currently unavailable")
        else:
            st.caption("Error details have been logged")
        
        # Add retry button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔄 Try Again", use_container_width=True, key="try_again"):
                st.session_state.api_result = None
                st.session_state.api_error = None
                st.rerun()

if __name__ == "__main__":
    main()