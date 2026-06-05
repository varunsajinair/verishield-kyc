import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from db_utils import load_all, load_stats

st.set_page_config(
    page_title="VeriShield — Analytics",
    page_icon="🛡️",
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
    <h1 style="margin:0;color:white;font-size:28px;">Analytics</h1>
    <p style="color:#64748b;margin:6px 0 0 0;font-size:13px;">
        Aggregated stats from all KYC verifications
    </p>
</div>
""", unsafe_allow_html=True)

stats = load_stats()
df = load_all()

m1, m2, m3, m4, m5 = st.columns(5)
with m1: st.metric("Total Verifications", stats.get("total", 0))
with m2: st.metric("Approval Rate", f"{stats.get('approved', 0) / max(stats.get('total', 1), 1):.0%}")
with m3: st.metric("Rejection Rate", f"{stats.get('rejected', 0) / max(stats.get('total', 1), 1):.0%}")
with m4: st.metric("Review Rate", f"{stats.get('review', 0) / max(stats.get('total', 1), 1):.0%}")
with m5:
    if not df.empty and 'processing_time_ms' in df.columns:
        st.metric("Avg Processing", f"{df['processing_time_ms'].mean():.0f}ms")
    else:
        st.metric("Avg Processing", "N/A")

st.divider()

if df.empty:
    st.info("No data yet — run some KYC verifications first.")
else:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Overall Results")
        result_counts = df['overall_result'].value_counts()
        fig = go.Figure(go.Pie(
            labels=result_counts.index.tolist(),
            values=result_counts.values.tolist(),
            hole=0.45,
            marker=dict(colors=['#059669', '#dc2626', '#f97316', '#185FA5'])
        ))
        fig.update_layout(
            paper_bgcolor='#0f172a',
            font=dict(color='white'),
            legend=dict(bgcolor='#0f172a', font=dict(color='white')),
            height=320, margin=dict(t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Deepfake Detection Results")
        face_counts = df['face_result'].value_counts()
        fig2 = go.Figure(go.Bar(
            x=face_counts.index.tolist(),
            y=face_counts.values.tolist(),
            marker_color=['#059669' if x == 'AUTHENTIC' else '#dc2626' if x == 'DEEPFAKE' else '#f97316' for x in face_counts.index],
            text=face_counts.values.tolist(),
            textposition='outside',
            textfont=dict(color='white')
        ))
        fig2.update_layout(
            paper_bgcolor='#0f172a',
            plot_bgcolor='#0f172a',
            font=dict(color='white'),
            xaxis=dict(gridcolor='#1e3a5f', color='white'),
            yaxis=dict(gridcolor='#1e3a5f', color='white'),
            height=320, margin=dict(t=20, b=20)
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Risk Score by Result")
        if 'overall_risk_score' in df.columns:
            fig3 = go.Figure()
            for result, color in [('APPROVED', '#059669'), ('REJECTED', '#dc2626'), ('REVIEW', '#f97316')]:
                subset = df[df['overall_result'] == result]['overall_risk_score']
                if not subset.empty:
                    fig3.add_trace(go.Box(
                        y=subset,
                        name=result,
                        marker_color=color
                    ))
            fig3.update_layout(
                paper_bgcolor='#0f172a',
                plot_bgcolor='#0f172a',
                font=dict(color='white'),
                xaxis=dict(gridcolor='#1e3a5f', color='white'),
                yaxis=dict(gridcolor='#1e3a5f', color='white', title='Risk Score'),
                height=320, margin=dict(t=20, b=20)
            )
            st.plotly_chart(fig3, use_container_width=True)

    with col2:
        st.markdown("#### Face Match Distribution")
        if 'match_result' in df.columns:
            match_counts = df['match_result'].value_counts()
            fig4 = go.Figure(go.Pie(
                labels=match_counts.index.tolist(),
                values=match_counts.values.tolist(),
                hole=0.4,
                marker=dict(colors=['#059669', '#f97316', '#dc2626'])
            ))
            fig4.update_layout(
                paper_bgcolor='#0f172a',
                font=dict(color='white'),
                legend=dict(bgcolor='#0f172a', font=dict(color='white')),
                height=320, margin=dict(t=20, b=20)
            )
            st.plotly_chart(fig4, use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Processing Time Distribution")
        if 'processing_time_ms' in df.columns:
            fig5 = go.Figure(go.Histogram(
                x=df['processing_time_ms'],
                nbinsx=20,
                marker_color='#185FA5'
            ))
            fig5.update_layout(
                paper_bgcolor='#0f172a',
                plot_bgcolor='#0f172a',
                font=dict(color='white'),
                xaxis=dict(gridcolor='#1e3a5f', color='white', title='Time (ms)'),
                yaxis=dict(gridcolor='#1e3a5f', color='white', title='Count'),
                height=320, margin=dict(t=20, b=20)
            )
            st.plotly_chart(fig5, use_container_width=True)

    with col2:
        st.markdown("#### Alert Level Distribution")
        if 'alert_level' in df.columns:
            alert_counts = df['alert_level'].value_counts()
            colors_map = {
                'CRITICAL': '#7c3aed',
                'HIGH RISK': '#dc2626',
                'MEDIUM RISK': '#f97316',
                'LOW RISK': '#059669'
            }
            fig6 = go.Figure(go.Bar(
                x=alert_counts.index.tolist(),
                y=alert_counts.values.tolist(),
                marker_color=[colors_map.get(x, '#185FA5') for x in alert_counts.index],
                text=alert_counts.values.tolist(),
                textposition='outside',
                textfont=dict(color='white')
            ))
            fig6.update_layout(
                paper_bgcolor='#0f172a',
                plot_bgcolor='#0f172a',
                font=dict(color='white'),
                xaxis=dict(gridcolor='#1e3a5f', color='white'),
                yaxis=dict(gridcolor='#1e3a5f', color='white'),
                height=320, margin=dict(t=20, b=20)
            )
            st.plotly_chart(fig6, use_container_width=True)