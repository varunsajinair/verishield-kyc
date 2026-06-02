import streamlit as st
import requests
import json
from PIL import Image
import io

st.set_page_config(
    page_title="VeriShield — KYC Verification",
    page_icon="🔍",
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
    <h1 style="margin:0;color:white;">🔍 KYC Verification Portal</h1>
    <p style="color:#64748b;margin:4px 0 0 0;">
    Upload an ID document and selfie for complete KYC verification — document forgery + deepfake detection + face match
    </p>
</div>
""", unsafe_allow_html=True)

API_URL = st.secrets.get("API_URL", "https://verishield-kyc-production.up.railway.app")

tab1, tab2, tab3 = st.tabs([
    "🪪 Full KYC Check",
    "📄 Document Only",
    "🧬 Face Only"
])

with tab1:
    st.markdown("### 🪪 Complete KYC Verification")
    st.markdown("<p style='color:#64748b;'>Upload both ID document and selfie for full verification</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📄 ID Document")
        doc_file = st.file_uploader(
            "Upload ID Card / Passport / Driving License",
            type=['jpg', 'jpeg', 'png'],
            key="doc_full"
        )
        if doc_file:
            st.image(doc_file, caption="Uploaded Document", use_column_width=True)

    with col2:
        st.markdown("#### 🤳 Selfie")
        selfie_file = st.file_uploader(
            "Upload Selfie Photo",
            type=['jpg', 'jpeg', 'png'],
            key="selfie_full"
        )
        if selfie_file:
            st.image(selfie_file, caption="Uploaded Selfie", use_column_width=True)

    if st.button("🔍 Run Full KYC Verification", use_container_width=True, type="primary"):
        if not doc_file or not selfie_file:
            st.error("Please upload both document and selfie!")
        else:
            with st.spinner("Running AI verification — document forgery check + deepfake detection + face match..."):
                try:
                    doc_file.seek(0)
                    selfie_file.seek(0)
                    files = {
                        'document': (doc_file.name, doc_file.read(), 'image/jpeg'),
                        'selfie': (selfie_file.name, selfie_file.read(), 'image/jpeg')
                    }
                    response = requests.post(
                        f"{API_URL}/kyc-complete",
                        files=files,
                        timeout=60
                    )
                    result = response.json()

                    overall = result.get('overall_result', 'UNKNOWN')
                    risk = result.get('overall_risk_score', 0)
                    alert = result.get('alert_level', 'UNKNOWN')

                    color = '#059669' if overall == 'APPROVED' else '#dc2626' if overall == 'REJECTED' else '#f97316'
                    icon = '✅' if overall == 'APPROVED' else '❌' if overall == 'REJECTED' else '⚠️'

                    st.markdown(f"""
                    <div style="background:#0f172a;border:3px solid {color};border-radius:16px;
                                padding:24px;text-align:center;margin:16px 0;">
                        <p style="font-size:48px;margin:0;">{icon}</p>
                        <p style="color:{color};font-size:28px;font-weight:bold;margin:8px 0;">
                            {overall}
                        </p>
                        <p style="color:#64748b;margin:0;">
                            Verification ID: {result.get('verification_id', 'N/A')} | 
                            Risk Score: {risk:.2%} | 
                            Alert: {alert}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    c1, c2, c3 = st.columns(3)

                    doc_check = result.get('document_check', {})
                    face_check = result.get('face_check', {})
                    match_check = result.get('match_check', {})

                    doc_color = '#dc2626' if doc_check.get('result') == 'FORGED' else '#f97316' if doc_check.get('result') == 'SUSPICIOUS' else '#059669'
                    face_color = '#dc2626' if face_check.get('result') == 'DEEPFAKE' else '#f97316' if face_check.get('result') == 'SUSPICIOUS' else '#059669'
                    match_color = '#dc2626' if match_check.get('result') == 'NO MATCH' else '#f97316' if match_check.get('result') == 'POSSIBLE MATCH' else '#059669'

                    with c1:
                        st.markdown(f"""
                        <div style="background:#0f172a;border:1px solid {doc_color};border-radius:12px;padding:16px;text-align:center;">
                            <p style="color:#94a3b8;font-size:11px;margin:0;">DOCUMENT CHECK</p>
                            <p style="color:{doc_color};font-size:18px;font-weight:bold;margin:8px 0;">{doc_check.get('result', 'N/A')}</p>
                            <p style="color:white;font-size:14px;margin:0;">Confidence: {doc_check.get('confidence', 0):.2%}</p>
                            <p style="color:#64748b;font-size:12px;margin:4px 0;">Risk: {doc_check.get('risk_score', 0):.2%}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with c2:
                        st.markdown(f"""
                        <div style="background:#0f172a;border:1px solid {face_color};border-radius:12px;padding:16px;text-align:center;">
                            <p style="color:#94a3b8;font-size:11px;margin:0;">DEEPFAKE CHECK</p>
                            <p style="color:{face_color};font-size:18px;font-weight:bold;margin:8px 0;">{face_check.get('result', 'N/A')}</p>
                            <p style="color:white;font-size:14px;margin:0;">Deepfake Prob: {face_check.get('deepfake_probability', 0):.2%}</p>
                            <p style="color:#64748b;font-size:12px;margin:4px 0;">Liveness: {(1-face_check.get('deepfake_probability', 0)):.2%}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with c3:
                        st.markdown(f"""
                        <div style="background:#0f172a;border:1px solid {match_color};border-radius:12px;padding:16px;text-align:center;">
                            <p style="color:#94a3b8;font-size:11px;margin:0;">FACE MATCH</p>
                            <p style="color:{match_color};font-size:18px;font-weight:bold;margin:8px 0;">{match_check.get('result', 'N/A')}</p>
                            <p style="color:white;font-size:14px;margin:0;">Similarity: {match_check.get('similarity_score', 0):.2%}</p>
                            <p style="color:#64748b;font-size:12px;margin:4px 0;">Processing: {result.get('processing_time_ms', 0):.0f}ms</p>
                        </div>
                        """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"API Error: {e}")

with tab2:
    st.markdown("### 📄 Document Forgery Detection Only")

    doc_only = st.file_uploader(
        "Upload ID Document",
        type=['jpg', 'jpeg', 'png'],
        key="doc_only"
    )

    if doc_only:
        st.image(doc_only, caption="Uploaded Document", width=400)

    if st.button("🔍 Analyze Document", use_container_width=True, type="primary"):
        if not doc_only:
            st.error("Please upload a document!")
        else:
            with st.spinner("Analyzing document for forgery..."):
                try:
                    doc_only.seek(0)
                    files = {'file': (doc_only.name, doc_only.read(), 'image/jpeg')}
                    response = requests.post(
                        f"{API_URL}/verify-document",
                        files=files,
                        timeout=60
                    )
                    result = response.json()

                    res = result.get('result', 'UNKNOWN')
                    color = '#dc2626' if res == 'FORGED' else '#f97316' if res == 'SUSPICIOUS' else '#059669'

                    st.markdown(f"""
                    <div style="background:#0f172a;border:2px solid {color};border-radius:12px;padding:20px;margin-top:16px;">
                        <p style="color:{color};font-size:22px;font-weight:bold;margin:0;">
                            {'❌ FORGED' if res == 'FORGED' else '⚠️ SUSPICIOUS' if res == 'SUSPICIOUS' else '✅ AUTHENTIC'}
                        </p>
                        <hr style="border-color:#1e3a5f;margin:12px 0;">
                        <p style="color:#cbd5e1;margin:4px 0;">Confidence: <b>{result.get('confidence', 0):.2%}</b></p>
                        <p style="color:#cbd5e1;margin:4px 0;">Risk Score: <b>{result.get('risk_score', 0):.2%}</b></p>
                        <p style="color:#cbd5e1;margin:4px 0;">Alert Level: <b>{result.get('alert_level', 'N/A')}</b></p>
                        <p style="color:#cbd5e1;margin:4px 0;">Processing: <b>{result.get('processing_time_ms', 0):.0f}ms</b></p>
                        <hr style="border-color:#1e3a5f;margin:12px 0;">
                        <p style="color:#94a3b8;font-size:12px;margin:4px 0;"><b>Findings:</b></p>
                        {''.join([f"<p style='color:#f97316;font-size:12px;margin:2px 0;'>• {r}</p>" for r in result.get('tampered_regions', [])])}
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"API Error: {e}")

with tab3:
    st.markdown("### 🧬 Deepfake Face Detection Only")

    face_only = st.file_uploader(
        "Upload Selfie / Face Photo",
        type=['jpg', 'jpeg', 'png'],
        key="face_only"
    )

    if face_only:
        st.image(face_only, caption="Uploaded Face", width=300)

    if st.button("🧬 Analyze Face", use_container_width=True, type="primary"):
        if not face_only:
            st.error("Please upload a face photo!")
        else:
            with st.spinner("Analyzing face for deepfake..."):
                try:
                    face_only.seek(0)
                    files = {'file': (face_only.name, face_only.read(), 'image/jpeg')}
                    response = requests.post(
                        f"{API_URL}/verify-face",
                        files=files,
                        timeout=60
                    )
                    result = response.json()

                    res = result.get('result', 'UNKNOWN')
                    color = '#dc2626' if res == 'DEEPFAKE' else '#f97316' if res == 'SUSPICIOUS' else '#059669'

                    st.markdown(f"""
                    <div style="background:#0f172a;border:2px solid {color};border-radius:12px;padding:20px;margin-top:16px;">
                        <p style="color:{color};font-size:22px;font-weight:bold;margin:0;">
                            {'🤖 DEEPFAKE DETECTED' if res == 'DEEPFAKE' else '⚠️ SUSPICIOUS' if res == 'SUSPICIOUS' else '✅ AUTHENTIC FACE'}
                        </p>
                        <hr style="border-color:#1e3a5f;margin:12px 0;">
                        <p style="color:#cbd5e1;margin:4px 0;">Deepfake Probability: <b>{result.get('deepfake_probability', 0):.2%}</b></p>
                        <p style="color:#cbd5e1;margin:4px 0;">Liveness Score: <b>{result.get('liveness_score', 0):.2%}</b></p>
                        <p style="color:#cbd5e1;margin:4px 0;">Confidence: <b>{result.get('confidence', 0):.2%}</b></p>
                        <p style="color:#cbd5e1;margin:4px 0;">Alert Level: <b>{result.get('alert_level', 'N/A')}</b></p>
                        <p style="color:#cbd5e1;margin:4px 0;">Processing: <b>{result.get('processing_time_ms', 0):.0f}ms</b></p>
                        <hr style="border-color:#1e3a5f;margin:12px 0;">
                        <p style="color:#94a3b8;font-size:12px;margin:4px 0;">Texture Score: {result.get('texture_score', 0):.4f} | Frequency Score: {result.get('frequency_score', 0):.4f}</p>
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"API Error: {e}")

st.divider()
st.markdown("""
<div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:8px;padding:16px;">
    <p style="color:#64748b;margin:0;font-size:13px;">
    💡 <b style="color:#cbd5e1;">How it works:</b> Document check uses EfficientNet + noise/edge analysis.
    Face check uses EfficientNet-B4 + texture/frequency analysis. Face match uses histogram correlation.
    All results logged to PostgreSQL for compliance audit trail.
    </p>
</div>
""", unsafe_allow_html=True)