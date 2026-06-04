import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from db_utils import load_all, load_stats

st.set_page_config(
    page_title="VeriShield — Risk Dashboard",
    page_icon="⚠️",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #0a0e1a; }
    .main .block-container { padding-top: 1rem; }
    hr { border-color: #1e3a5f !important; }
    p, label, .stMarkdown { color: #cbd5e1 !important; }
    h1, h2, h3 { color: white !important; }
    div[data-testid="stMetricValue"] { color: white !important; }
    div[data-testid="stMetricLabel"] { color: #94a3b8 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background:linear-gradient(135deg,#0d1b2e,#1a2744);border-radius:16px;
     padding:24px 32px;margin-bottom:24px;border:1px solid #1e3a5f;">
    <h1 style="margin:0;color:white;">⚠️ Risk Scoring Dashboard</h1>
    <p style="color:#64748b;margin:4px 0 0 0;">
    Combined risk scores across deepfake and face match checks — real-time threat intelligence
    </p>
</div>
""", unsafe_allow_html=True)

stats = load_stats()
df = load_all()

m1, m2, m3, m4, m5 = st.columns(5)
with m1: st.metric("Total Verifications", stats.get("total", 0))
with m2: st.metric("🚨 Critical Risk", len(df[df['alert_level'] == 'CRITICAL']) if not df.empty else 0)
with m3: st.metric("⚠️ High Risk", len(df[df['alert_level'] == 'HIGH RISK']) if not df.empty else 0)
with m4: st.metric("🟡 Medium Risk", len(df[df['alert_level'] == 'MEDIUM RISK']) if not df.empty else 0)
with m5: st.metric("✅ Low Risk", len(df[df['alert_level'] == 'LOW RISK']) if not df.empty else 0)

st.divider()

if df.empty:
    st.info("No real verification data yet — showing simulated risk data for demo!")
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        'verification_id': [f'VER{i:04d}' for i in range(n)],
        'face_confidence': np.random.beta(2, 5, n),
        'match_score': np.random.beta(5, 2, n),
        'overall_risk_score': np.random.beta(2, 5, n),
        'face_result': np.random.choice(['AUTHENTIC', 'AUTHENTIC', 'AUTHENTIC', 'SUSPICIOUS', 'DEEPFAKE'], n),
        'overall_result': np.random.choice(['APPROVED', 'APPROVED', 'APPROVED', 'REVIEW', 'REJECTED'], n),
        'alert_level': np.random.choice(['LOW RISK', 'LOW RISK', 'MEDIUM RISK', 'HIGH RISK', 'CRITICAL'], n),
        'processing_time_ms': np.random.normal(800, 200, n)
    })

# Overall Risk Gauge
st.markdown("### 🎯 Overall Platform Risk Score")

avg_risk = df['overall_risk_score'].mean() if 'overall_risk_score' in df.columns else 0.25
risk_pct = avg_risk * 100

fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=risk_pct,
    domain={'x': [0, 1], 'y': [0, 1]},
    title={'text': "Platform Risk Score", 'font': {'color': 'white', 'size': 16}},
    delta={'reference': 30, 'increasing': {'color': '#dc2626'}, 'decreasing': {'color': '#059669'}},
    gauge={
        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': 'white', 'tickfont': {'color': 'white'}},
        'bar': {'color': '#dc2626' if risk_pct > 60 else '#f97316' if risk_pct > 30 else '#059669'},
        'bgcolor': '#0f172a',
        'borderwidth': 2,
        'bordercolor': '#1e3a5f',
        'steps': [
            {'range': [0, 30], 'color': 'rgba(5,150,105,0.2)'},
            {'range': [30, 60], 'color': 'rgba(249,115,22,0.2)'},
            {'range': [60, 100], 'color': 'rgba(220,38,38,0.2)'}
        ],
        'threshold': {
            'line': {'color': 'white', 'width': 4},
            'thickness': 0.75,
            'value': 60
        }
    }
))
fig_gauge.update_layout(
    paper_bgcolor='#0f172a',
    font=dict(color='white'),
    height=300,
    margin=dict(t=40, b=20)
)
st.plotly_chart(fig_gauge, use_container_width=True)

st.divider()

# Risk breakdown — only deepfake and match
st.markdown("### 📊 Risk Breakdown by Component")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🧬 Deepfake Risk")
    face_risk = df['face_confidence'].mean() if 'face_confidence' in df.columns else 0.15
    fig_face = go.Figure(go.Indicator(
        mode="gauge+number",
        value=face_risk * 100,
        title={'text': "Deepfake Risk", 'font': {'color': 'white', 'size': 12}},
        gauge={
            'axis': {'range': [0, 100], 'tickfont': {'color': 'white'}},
            'bar': {'color': '#dc2626' if face_risk > 0.6 else '#f97316' if face_risk > 0.3 else '#059669'},
            'bgcolor': '#0f172a',
            'steps': [
                {'range': [0, 30], 'color': 'rgba(5,150,105,0.2)'},
                {'range': [30, 60], 'color': 'rgba(249,115,22,0.2)'},
                {'range': [60, 100], 'color': 'rgba(220,38,38,0.2)'}
            ]
        }
    ))
    fig_face.update_layout(paper_bgcolor='#0f172a', font=dict(color='white'), height=250, margin=dict(t=40, b=0))
    st.plotly_chart(fig_face, use_container_width=True)

with col2:
    st.markdown("#### 🔍 Face Match Risk")
    match_risk = 1 - df['match_score'].mean() if 'match_score' in df.columns else 0.1
    fig_match = go.Figure(go.Indicator(
        mode="gauge+number",
        value=match_risk * 100,
        title={'text': "Face Mismatch Risk", 'font': {'color': 'white', 'size': 12}},
        gauge={
            'axis': {'range': [0, 100], 'tickfont': {'color': 'white'}},
            'bar': {'color': '#dc2626' if match_risk > 0.6 else '#f97316' if match_risk > 0.3 else '#059669'},
            'bgcolor': '#0f172a',
            'steps': [
                {'range': [0, 30], 'color': 'rgba(5,150,105,0.2)'},
                {'range': [30, 60], 'color': 'rgba(249,115,22,0.2)'},
                {'range': [60, 100], 'color': 'rgba(220,38,38,0.2)'}
            ]
        }
    ))
    fig_match.update_layout(paper_bgcolor='#0f172a', font=dict(color='white'), height=250, margin=dict(t=40, b=0))
    st.plotly_chart(fig_match, use_container_width=True)

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🚨 Alert Level Distribution")
    alert_counts = df['alert_level'].value_counts()
    colors_map = {
        'CRITICAL': '#7c3aed',
        'HIGH RISK': '#dc2626',
        'MEDIUM RISK': '#f97316',
        'LOW RISK': '#059669'
    }
    fig_alert = go.Figure(go.Bar(
        x=alert_counts.index.tolist(),
        y=alert_counts.values.tolist(),
        marker_color=[colors_map.get(x, '#185FA5') for x in alert_counts.index],
        text=alert_counts.values.tolist(),
        textposition='outside',
        textfont=dict(color='white')
    ))
    fig_alert.update_layout(
        paper_bgcolor='#0f172a', plot_bgcolor='#0f172a',
        font=dict(color='white'),
        xaxis=dict(gridcolor='#1e3a5f', color='white'),
        yaxis=dict(gridcolor='#1e3a5f', color='white'),
        height=300, margin=dict(t=20, b=20)
    )
    st.plotly_chart(fig_alert, use_container_width=True)

with col2:
    st.markdown("#### 📈 Risk Score Distribution")
    fig_hist = go.Figure(go.Histogram(
        x=df['overall_risk_score'] if 'overall_risk_score' in df.columns else [],
        nbinsx=20,
        marker_color='#185FA5'
    ))
    fig_hist.update_layout(
        paper_bgcolor='#0f172a', plot_bgcolor='#0f172a',
        font=dict(color='white'),
        xaxis=dict(gridcolor='#1e3a5f', color='white', title='Risk Score'),
        yaxis=dict(gridcolor='#1e3a5f', color='white', title='Count'),
        height=300, margin=dict(t=20, b=20)
    )
    st.plotly_chart(fig_hist, use_container_width=True)

st.divider()

st.markdown("### 🚨 High Risk Verifications")
high_risk = df[df['alert_level'].isin(['CRITICAL', 'HIGH RISK'])] if 'alert_level' in df.columns else pd.DataFrame()

if not high_risk.empty:
    for _, row in high_risk.head(10).iterrows():
        alert = row.get('alert_level', 'N/A')
        color = '#7c3aed' if alert == 'CRITICAL' else '#dc2626'
        st.markdown(f"""
        <div style="background:#0f172a;border-left:4px solid {color};
                    padding:12px 16px;margin-bottom:6px;border-radius:0 8px 8px 0;">
            <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;">
                <span style="color:white;font-weight:bold;">🚨 {row.get('verification_id', 'N/A')}</span>
                <span style="color:{color};font-weight:bold;">{alert}</span>
                <span style="color:#a78bfa;">Face: {row.get('face_result', 'N/A')}</span>
                <span style="color:#fbbf24;">Match: {row.get('match_result', 'N/A')}</span>
                <span style="color:#cbd5e1;">Risk: {row.get('overall_risk_score', 0):.2%}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.success("✅ No high risk verifications detected!")

st.divider()
st.markdown("""
<div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:8px;padding:16px;">
    <p style="color:#64748b;margin:0;font-size:13px;">
    💡 <b style="color:#cbd5e1;">Risk Scoring:</b> VeriShield combines deepfake probability and 
    face match score into a unified risk score. Scores above 0.6 trigger automatic rejection. 
    Scores between 0.3-0.6 go to manual review. Below 0.3 are auto-approved — same logic used by 
    Onfido, Jumio, and Sumsub in production.
    </p>
</div>
""", unsafe_allow_html=True)