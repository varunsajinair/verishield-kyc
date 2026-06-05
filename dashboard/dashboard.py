import streamlit as st
import requests
import pandas as pd
from db_utils import load_stats, load_recent

st.set_page_config(
    page_title="VeriShield AI",
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
     padding:32px;margin-bottom:24px;border:1px solid #1e3a5f;">
    <h1 style="margin:0;color:white;font-size:32px;">🛡️ VeriShield AI</h1>
    <p style="color:#94a3b8;margin:8px 0 0 0;font-size:15px;">
        KYC Deepfake Identity Detection
    </p>
    <p style="color:#475569;margin:6px 0 0 0;font-size:12px;">
        EfficientNet-B0 &nbsp;·&nbsp; 140K face dataset &nbsp;·&nbsp; PostgreSQL audit log
    </p>
</div>
""", unsafe_allow_html=True)

API_URL = st.secrets.get("API_URL", "https://verishield-kyc-production.up.railway.app")

try:
    health = requests.get(f"{API_URL}/health", timeout=5).json()
    api_status = "🟢 Online"
except:
    api_status = "🔴 Offline"

stats = load_stats()

m1, m2, m3, m4, m5 = st.columns(5)
with m1: st.metric("API Status", api_status)
with m2: st.metric("Total Verifications", stats.get("total", 0))
with m3: st.metric("Approved", stats.get("approved", 0))
with m4: st.metric("Rejected", stats.get("rejected", 0))
with m5: st.metric("Under Review", stats.get("review", 0))

st.divider()

st.markdown("### What this does")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("""
    <div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:12px;padding:20px;">
        <p style="color:white;font-weight:600;margin:0 0 6px 0;font-size:14px;">Deepfake Detection</p>
        <p style="color:#64748b;font-size:12px;margin:0;line-height:1.6;">
            EfficientNet-B0 trained on 140K real/fake faces. Flags synthetic faces at inference.
        </p>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:12px;padding:20px;">
        <p style="color:white;font-weight:600;margin:0 0 6px 0;font-size:14px;">Face Matching</p>
        <p style="color:#64748b;font-size:12px;margin:0;line-height:1.6;">
            Compares ID photo against live selfie using cosine similarity on face embeddings.
        </p>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:12px;padding:20px;">
        <p style="color:white;font-weight:600;margin:0 0 6px 0;font-size:14px;">GradCAM Heatmaps</p>
        <p style="color:#64748b;font-size:12px;margin:0;line-height:1.6;">
            Shows which facial regions drove the model's decision — useful for manual review.
        </p>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown("""
    <div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:12px;padding:20px;">
        <p style="color:white;font-weight:600;margin:0 0 6px 0;font-size:14px;">Audit Trail</p>
        <p style="color:#64748b;font-size:12px;margin:0;line-height:1.6;">
            Every verification logged to Supabase PostgreSQL with timestamp and result.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

st.markdown("### Recent Verifications")

df = load_recent()

if not df.empty:
    for _, row in df.iterrows():
        result = row.get('overall_result', 'UNKNOWN')
        color = '#059669' if result == 'APPROVED' else '#dc2626' if result == 'REJECTED' else '#f97316'
        icon = '✅' if result == 'APPROVED' else '❌' if result == 'REJECTED' else '⚠️'

        st.markdown(f"""
        <div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:8px;
                    padding:12px 16px;margin-bottom:6px;">
            <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;">
                <span style="color:white;font-size:13px;">{icon} {row.get('verification_id', 'N/A')}</span>
                <span style="color:#64748b;font-size:12px;">{str(row.get('timestamp', ''))[:19]}</span>
                <span style="color:#a78bfa;font-size:12px;">Face: {row.get('face_result', 'N/A')}</span>
                <span style="color:#fbbf24;font-size:12px;">Match: {row.get('match_result', 'N/A')}</span>
                <span style="background:{color};color:white;padding:2px 10px;
                             border-radius:12px;font-size:11px;">{result}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No verifications yet — run one from the KYC Verification page.")
