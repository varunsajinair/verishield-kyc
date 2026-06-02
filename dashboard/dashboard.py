import streamlit as st
import requests
import pandas as pd
from db_utils import load_stats, load_recent

st.set_page_config(
    page_title="VeriShield AI — KYC Platform",
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
    <p style="color:#64748b;margin:8px 0 0 0;font-size:16px;">
    KYC Document Forgery & Deepfake Identity Detection Platform
    </p>
    <p style="color:#334155;margin:4px 0 0 0;font-size:13px;">
    Powered by Vision Transformer + EfficientNet-B4 | PostgreSQL Audit Trail
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

st.markdown("### 🚀 Platform Features")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("""
    <div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:12px;padding:20px;text-align:center;">
        <p style="font-size:32px;margin:0;">📄</p>
        <p style="color:white;font-weight:bold;margin:8px 0 4px 0;">Document Verification</p>
        <p style="color:#64748b;font-size:12px;margin:0;">ViT-based forgery detection with GradCAM visualization</p>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:12px;padding:20px;text-align:center;">
        <p style="font-size:32px;margin:0;">🧬</p>
        <p style="color:white;font-weight:bold;margin:8px 0 4px 0;">Deepfake Detection</p>
        <p style="color:#64748b;font-size:12px;margin:0;">EfficientNet-B4 liveness & deepfake analysis</p>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:12px;padding:20px;text-align:center;">
        <p style="font-size:32px;margin:0;">🔍</p>
        <p style="color:white;font-weight:bold;margin:8px 0 4px 0;">Face Matching</p>
        <p style="color:#64748b;font-size:12px;margin:0;">ID photo vs selfie similarity scoring</p>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown("""
    <div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:12px;padding:20px;text-align:center;">
        <p style="font-size:32px;margin:0;">📋</p>
        <p style="color:white;font-weight:bold;margin:8px 0 4px 0;">Audit Trail</p>
        <p style="color:#64748b;font-size:12px;margin:0;">Every verification logged in PostgreSQL</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

st.markdown("### 📊 Recent Verifications")

df = load_recent()

if not df.empty:
    for _, row in df.iterrows():
        result = row.get('overall_result', 'UNKNOWN')
        color = '#059669' if result == 'APPROVED' else '#dc2626' if result == 'REJECTED' else '#f97316'
        icon = '✅' if result == 'APPROVED' else '❌' if result == 'REJECTED' else '⚠️'

        st.markdown(f"""
        <div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:8px;
                    padding:12px 16px;margin-bottom:6px;display:flex;
                    justify-content:space-between;align-items:center;">
            <span style="color:white;font-size:13px;">{icon} {row.get('verification_id', 'N/A')}</span>
            <span style="color:#64748b;font-size:12px;">{str(row.get('timestamp', ''))[:19]}</span>
            <span style="color:#fbbf24;font-size:12px;">Doc: {row.get('document_result', 'N/A')}</span>
            <span style="color:#a78bfa;font-size:12px;">Face: {row.get('face_result', 'N/A')}</span>
            <span style="background:{color};color:white;padding:2px 10px;
                         border-radius:12px;font-size:11px;">{result}</span>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No verifications yet — go to KYC Verification to get started!")

st.divider()

st.markdown("""
<div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:8px;padding:16px;">
    <p style="color:#64748b;margin:0;font-size:13px;">
    💡 <b style="color:#cbd5e1;">VeriShield AI</b> — Banks are legally required to perform KYC (Know Your Customer) 
    verification under AML regulations. VeriShield automates document forgery detection and deepfake liveness 
    checks using state-of-the-art Vision Transformers and EfficientNet models.
    </p>
</div>
""", unsafe_allow_html=True)