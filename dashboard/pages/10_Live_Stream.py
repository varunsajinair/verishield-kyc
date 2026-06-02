import streamlit as st
import requests
import random
import time
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="VeriShield — Live KYC Stream",
    page_icon="⚡",
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
    <h1 style="margin:0;color:white;">⚡ Live KYC Stream</h1>
    <p style="color:#64748b;margin:4px 0 0 0;">
    Real-time simulation of KYC verifications — as they would appear in a bank's onboarding system
    </p>
</div>
""", unsafe_allow_html=True)

API_URL = st.secrets.get("API_URL", "https://verishield-kyc-production.up.railway.app")

# Session state
if 'stream_running' not in st.session_state:
    st.session_state.stream_running = False
if 'stream_history' not in st.session_state:
    st.session_state.stream_history = []
if 'stream_stats' not in st.session_state:
    st.session_state.stream_stats = {'total': 0, 'approved': 0, 'rejected': 0, 'review': 0, 'deepfakes': 0, 'forgeries': 0}

# Controls
col1, col2, col3 = st.columns(3)
with col1:
    start_btn = st.button("▶️ Start Stream", type="primary", use_container_width=True)
with col2:
    stop_btn = st.button("⏹️ Stop Stream", use_container_width=True)
with col3:
    clear_btn = st.button("🗑️ Clear History", use_container_width=True)

if start_btn:
    st.session_state.stream_running = True
if stop_btn:
    st.session_state.stream_running = False
if clear_btn:
    st.session_state.stream_history = []
    st.session_state.stream_stats = {'total': 0, 'approved': 0, 'rejected': 0, 'review': 0, 'deepfakes': 0, 'forgeries': 0}

st.divider()

# Live stats
m1, m2, m3, m4, m5, m6 = st.columns(6)
with m1: st.metric("Total", st.session_state.stream_stats['total'])
with m2: st.metric("✅ Approved", st.session_state.stream_stats['approved'])
with m3: st.metric("❌ Rejected", st.session_state.stream_stats['rejected'])
with m4: st.metric("⚠️ Review", st.session_state.stream_stats['review'])
with m5: st.metric("🤖 Deepfakes", st.session_state.stream_stats['deepfakes'])
with m6: st.metric("📄 Forgeries", st.session_state.stream_stats['forgeries'])

st.divider()

# Stream area
stream_placeholder = st.empty()
status_placeholder = st.empty()

def generate_simulated_verification():
    """Generate a simulated KYC verification result"""
    names = ["Rahul Sharma", "Priya Patel", "Arjun Singh", "Deepa Nair", "Mohammed Ali",
             "Sarah Johnson", "Chen Wei", "Maria Garcia", "Ahmed Hassan", "Emma Wilson"]
    
    doc_results = ['AUTHENTIC', 'AUTHENTIC', 'AUTHENTIC', 'AUTHENTIC', 'SUSPICIOUS', 'FORGED']
    face_results = ['AUTHENTIC', 'AUTHENTIC', 'AUTHENTIC', 'AUTHENTIC', 'SUSPICIOUS', 'DEEPFAKE']
    match_results = ['MATCH', 'MATCH', 'MATCH', 'POSSIBLE MATCH', 'NO MATCH']
    
    doc_result = random.choice(doc_results)
    face_result = random.choice(face_results)
    match_result = random.choice(match_results)
    
    # Calculate overall risk
    risk_score = 0.1
    if doc_result == 'FORGED': risk_score += 0.4
    elif doc_result == 'SUSPICIOUS': risk_score += 0.2
    if face_result == 'DEEPFAKE': risk_score += 0.4
    elif face_result == 'SUSPICIOUS': risk_score += 0.2
    if match_result == 'NO MATCH': risk_score += 0.2
    elif match_result == 'POSSIBLE MATCH': risk_score += 0.1
    risk_score = min(risk_score + random.uniform(-0.05, 0.05), 1.0)

    if risk_score > 0.7:
        overall = 'REJECTED'
        alert = 'CRITICAL'
    elif risk_score > 0.4:
        overall = 'REVIEW'
        alert = 'HIGH RISK'
    elif risk_score > 0.2:
        overall = 'REVIEW'
        alert = 'MEDIUM RISK'
    else:
        overall = 'APPROVED'
        alert = 'LOW RISK'

    return {
        'verification_id': f"KYC-{random.randint(100000,999999)}",
        'name': random.choice(names),
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'doc_result': doc_result,
        'face_result': face_result,
        'match_result': match_result,
        'overall': overall,
        'alert': alert,
        'risk_score': round(risk_score, 3),
        'processing_ms': random.randint(400, 1200)
    }

def render_stream():
    history = st.session_state.stream_history[-15:][::-1]
    
    with stream_placeholder.container():
        st.markdown("### 🔴 Live Verification Feed")
        if not history:
            st.info("Click ▶️ Start Stream to begin!")
            return
            
        for item in history:
            overall = item['overall']
            color = '#059669' if overall == 'APPROVED' else '#dc2626' if overall == 'REJECTED' else '#f97316'
            icon = '✅' if overall == 'APPROVED' else '❌' if overall == 'REJECTED' else '⚠️'
            
            doc_color = '#dc2626' if item['doc_result'] == 'FORGED' else '#f97316' if item['doc_result'] == 'SUSPICIOUS' else '#059669'
            face_color = '#dc2626' if item['face_result'] == 'DEEPFAKE' else '#f97316' if item['face_result'] == 'SUSPICIOUS' else '#059669'

            st.markdown(f"""
            <div style="background:#0f172a;border-left:4px solid {color};
                        padding:10px 16px;margin-bottom:4px;border-radius:0 8px 8px 0;
                        display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;">
                <span style="color:white;font-weight:bold;font-size:13px;">{icon} {item['verification_id']}</span>
                <span style="color:#94a3b8;font-size:12px;">👤 {item['name']}</span>
                <span style="color:#64748b;font-size:12px;">🕐 {item['timestamp']}</span>
                <span style="color:{doc_color};font-size:12px;">📄 {item['doc_result']}</span>
                <span style="color:{face_color};font-size:12px;">🧬 {item['face_result']}</span>
                <span style="color:#a78bfa;font-size:12px;">🔍 {item['match_result']}</span>
                <span style="color:#fbbf24;font-size:12px;">Risk: {item['risk_score']:.0%}</span>
                <span style="color:#64748b;font-size:12px;">⚡ {item['processing_ms']}ms</span>
                <span style="background:{color};color:white;padding:1px 8px;
                             border-radius:10px;font-size:11px;font-weight:bold;">{overall}</span>
            </div>
            """, unsafe_allow_html=True)

# Main stream loop
render_stream()

if st.session_state.stream_running:
    status_placeholder.markdown("<p style='color:#059669;'>🔴 Stream is LIVE — generating verifications...</p>", unsafe_allow_html=True)
    
    # Generate one verification
    verification = generate_simulated_verification()
    st.session_state.stream_history.append(verification)
    
    # Update stats
    st.session_state.stream_stats['total'] += 1
    if verification['overall'] == 'APPROVED':
        st.session_state.stream_stats['approved'] += 1
    elif verification['overall'] == 'REJECTED':
        st.session_state.stream_stats['rejected'] += 1
    else:
        st.session_state.stream_stats['review'] += 1
    if verification['face_result'] == 'DEEPFAKE':
        st.session_state.stream_stats['deepfakes'] += 1
    if verification['doc_result'] == 'FORGED':
        st.session_state.stream_stats['forgeries'] += 1

    time.sleep(2)
    st.rerun()
else:
    status_placeholder.markdown("<p style='color:#64748b;'>⏸️ Stream paused — click Start to begin</p>", unsafe_allow_html=True)

st.divider()
st.markdown("""
<div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:8px;padding:16px;">
    <p style="color:#64748b;margin:0;font-size:13px;">
    💡 <b style="color:#cbd5e1;">Live KYC Stream:</b> In production, this feed would show real customer 
    onboarding verifications in real-time. Banks process thousands of KYC verifications daily — 
    compliance teams monitor this feed to catch fraud patterns as they emerge.
    </p>
</div>
""", unsafe_allow_html=True)