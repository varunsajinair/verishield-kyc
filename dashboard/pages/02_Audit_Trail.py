import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from db_utils import load_all, load_stats

st.set_page_config(
    page_title="VeriShield — Audit Trail",
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
    <h1 style="margin:0;color:white;font-size:28px;">Audit Trail</h1>
    <p style="color:#64748b;margin:6px 0 0 0;font-size:13px;">
        All KYC verifications logged to PostgreSQL (Supabase)
    </p>
</div>
""", unsafe_allow_html=True)

stats = load_stats()
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Total Verifications", stats.get("total", 0))
with m2: st.metric("Approved", stats.get("approved", 0))
with m3: st.metric("Rejected", stats.get("rejected", 0))
with m4: st.metric("Under Review", stats.get("review", 0))

st.divider()

st.markdown("### Filter")
col1, col2 = st.columns(2)
with col1:
    result_filter = st.selectbox("Overall Result", ["All", "APPROVED", "REJECTED", "REVIEW"])
with col2:
    face_filter = st.selectbox("Face Result", ["All", "AUTHENTIC", "SUSPICIOUS", "DEEPFAKE"])

df = load_all()

if df.empty:
    st.info("No verifications yet — run one from the KYC Verification page.")
else:
    if result_filter != "All":
        df = df[df['overall_result'] == result_filter]
    if face_filter != "All":
        df = df[df['face_result'] == face_filter]

    st.markdown(f"### Showing {len(df)} Verifications")

    for _, row in df.iterrows():
        result = row.get('overall_result', 'UNKNOWN')
        color = '#059669' if result == 'APPROVED' else '#dc2626' if result == 'REJECTED' else '#f97316'
        icon = '✅' if result == 'APPROVED' else '❌' if result == 'REJECTED' else '⚠️'

        face_res = row.get('face_result', 'N/A')
        match_res = row.get('match_result', 'N/A')

        face_color = '#dc2626' if face_res == 'DEEPFAKE' else '#f97316' if face_res == 'SUSPICIOUS' else '#059669'

        st.markdown(f"""
        <div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:10px;
                    padding:14px 18px;margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <span style="color:white;font-weight:bold;">{icon} {row.get('verification_id', 'N/A')}</span>
                <span style="color:#64748b;font-size:12px;">{str(row.get('timestamp', ''))[:19]}</span>
                <span style="color:{face_color};font-size:12px;">Face: {face_res} ({row.get('face_confidence', 0):.0%})</span>
                <span style="color:#a78bfa;font-size:12px;">Match: {match_res} ({row.get('match_score', 0):.0%})</span>
                <span style="color:#64748b;font-size:12px;">{row.get('processing_time_ms', 0):.0f}ms</span>
                <span style="background:{color};color:white;padding:3px 12px;
                             border-radius:12px;font-size:12px;font-weight:bold;">{result}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.markdown("### Analytics")

    col1, col2 = st.columns(2)

    with col1:
        result_counts = df['overall_result'].value_counts()
        fig = go.Figure(go.Pie(
            labels=result_counts.index.tolist(),
            values=result_counts.values.tolist(),
            hole=0.4,
            marker=dict(colors=['#059669', '#dc2626', '#f97316'])
        ))
        fig.update_layout(
            title=dict(text="Results Distribution", font=dict(color='white')),
            paper_bgcolor='#0f172a',
            font=dict(color='white'),
            legend=dict(bgcolor='#0f172a', font=dict(color='white')),
            height=300, margin=dict(t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        if 'overall_risk_score' in df.columns:
            fig2 = go.Figure(go.Histogram(
                x=df['overall_risk_score'],
                nbinsx=20,
                marker_color='#185FA5'
            ))
            fig2.update_layout(
                title=dict(text="Risk Score Distribution", font=dict(color='white')),
                paper_bgcolor='#0f172a',
                plot_bgcolor='#0f172a',
                font=dict(color='white'),
                xaxis=dict(gridcolor='#1e3a5f', color='white'),
                yaxis=dict(gridcolor='#1e3a5f', color='white'),
                height=300, margin=dict(t=40, b=20)
            )
            st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    st.markdown("### Export")
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="kyc_audit_trail.csv",
        mime="text/csv"
    )