import streamlit as st
import pandas as pd
import requests
import io
import time
from PIL import Image
import zipfile
import os
import tempfile

st.set_page_config(
    page_title="VeriShield — Batch Verification",
    page_icon="📦",
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
    <h1 style="margin:0;color:white;">📦 Batch KYC Verification</h1>
    <p style="color:#64748b;margin:4px 0 0 0;">
    Upload multiple documents or faces at once for bulk screening
    </p>
</div>
""", unsafe_allow_html=True)

API_URL = st.secrets.get("API_URL", "https://verishield-kyc-production.up.railway.app")

tab1, tab2 = st.tabs(["📄 Batch Document Check", "🧬 Batch Face Check"])

with tab1:
    st.markdown("### 📄 Batch Document Forgery Detection")
    st.markdown("<p style='color:#64748b;'>Upload multiple ID documents — system will check each one for forgery</p>", unsafe_allow_html=True)

    uploaded_docs = st.file_uploader(
        "Upload Multiple Documents",
        type=['jpg', 'jpeg', 'png'],
        accept_multiple_files=True,
        key="batch_docs"
    )

    if uploaded_docs:
        st.markdown(f"**{len(uploaded_docs)} documents uploaded**")

        if st.button("🔍 Run Batch Document Check", type="primary", use_container_width=True):
            results = []
            progress = st.progress(0)
            status = st.empty()

            for i, doc in enumerate(uploaded_docs):
                status.markdown(f"<p style='color:#64748b;'>Processing {doc.name}...</p>", unsafe_allow_html=True)
                try:
                    doc.seek(0)
                    files = {'file': (doc.name, doc.read(), 'image/jpeg')}
                    response = requests.post(f"{API_URL}/verify-document", files=files, timeout=60)
                    result = response.json()
                    results.append({
                        'filename': doc.name,
                        'result': result.get('result', 'ERROR'),
                        'confidence': f"{result.get('confidence', 0):.2%}",
                        'risk_score': f"{result.get('risk_score', 0):.2%}",
                        'alert_level': result.get('alert_level', 'N/A'),
                        'findings': ', '.join(result.get('tampered_regions', []))
                    })
                except Exception as e:
                    results.append({
                        'filename': doc.name,
                        'result': 'ERROR',
                        'confidence': '0%',
                        'risk_score': '0%',
                        'alert_level': 'ERROR',
                        'findings': str(e)
                    })
                progress.progress((i + 1) / len(uploaded_docs))

            status.empty()
            progress.empty()

            st.markdown("### 📊 Batch Results")

            approved = sum(1 for r in results if r['result'] == 'AUTHENTIC')
            flagged = sum(1 for r in results if r['result'] in ['FORGED', 'SUSPICIOUS'])

            c1, c2, c3 = st.columns(3)
            with c1: st.metric("Total Processed", len(results))
            with c2: st.metric("✅ Authentic", approved)
            with c3: st.metric("🚨 Flagged", flagged)

            st.divider()

            for r in results:
                color = '#059669' if r['result'] == 'AUTHENTIC' else '#dc2626' if r['result'] == 'FORGED' else '#f97316'
                icon = '✅' if r['result'] == 'AUTHENTIC' else '❌' if r['result'] == 'FORGED' else '⚠️'

                st.markdown(f"""
                <div style="background:#0f172a;border:1px solid {color};border-radius:8px;
                            padding:12px 16px;margin-bottom:6px;">
                    <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;">
                        <span style="color:white;font-weight:bold;">{icon} {r['filename']}</span>
                        <span style="color:{color};font-weight:bold;">{r['result']}</span>
                        <span style="color:#cbd5e1;font-size:12px;">Confidence: {r['confidence']}</span>
                        <span style="color:#cbd5e1;font-size:12px;">Risk: {r['risk_score']}</span>
                        <span style="color:#f97316;font-size:12px;">{r['alert_level']}</span>
                    </div>
                    <p style="color:#64748b;font-size:11px;margin:4px 0 0 0;">{r['findings']}</p>
                </div>
                """, unsafe_allow_html=True)

            # Download results
            df_results = pd.DataFrame(results)
            csv = df_results.to_csv(index=False)
            st.download_button(
                "📥 Download Results CSV",
                data=csv,
                file_name="batch_document_results.csv",
                mime="text/csv"
            )

with tab2:
    st.markdown("### 🧬 Batch Deepfake Detection")
    st.markdown("<p style='color:#64748b;'>Upload multiple face photos — system will check each for deepfakes</p>", unsafe_allow_html=True)

    uploaded_faces = st.file_uploader(
        "Upload Multiple Face Photos",
        type=['jpg', 'jpeg', 'png'],
        accept_multiple_files=True,
        key="batch_faces"
    )

    if uploaded_faces:
        st.markdown(f"**{len(uploaded_faces)} photos uploaded**")

        if st.button("🧬 Run Batch Face Check", type="primary", use_container_width=True):
            results = []
            progress = st.progress(0)
            status = st.empty()

            for i, face in enumerate(uploaded_faces):
                status.markdown(f"<p style='color:#64748b;'>Processing {face.name}...</p>", unsafe_allow_html=True)
                try:
                    face.seek(0)
                    files = {'file': (face.name, face.read(), 'image/jpeg')}
                    response = requests.post(f"{API_URL}/verify-face", files=files, timeout=60)
                    result = response.json()
                    results.append({
                        'filename': face.name,
                        'result': result.get('result', 'ERROR'),
                        'deepfake_probability': f"{result.get('deepfake_probability', 0):.2%}",
                        'liveness_score': f"{result.get('liveness_score', 0):.2%}",
                        'alert_level': result.get('alert_level', 'N/A'),
                        'processing_ms': f"{result.get('processing_time_ms', 0):.0f}ms"
                    })
                except Exception as e:
                    results.append({
                        'filename': face.name,
                        'result': 'ERROR',
                        'deepfake_probability': '0%',
                        'liveness_score': '0%',
                        'alert_level': 'ERROR',
                        'processing_ms': '0ms'
                    })
                progress.progress((i + 1) / len(uploaded_faces))

            status.empty()
            progress.empty()

            st.markdown("### 📊 Batch Results")

            authentic = sum(1 for r in results if r['result'] == 'AUTHENTIC')
            deepfakes = sum(1 for r in results if r['result'] == 'DEEPFAKE')
            suspicious = sum(1 for r in results if r['result'] == 'SUSPICIOUS')

            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Total Processed", len(results))
            with c2: st.metric("✅ Authentic", authentic)
            with c3: st.metric("🤖 Deepfakes", deepfakes)
            with c4: st.metric("⚠️ Suspicious", suspicious)

            st.divider()

            for r in results:
                color = '#059669' if r['result'] == 'AUTHENTIC' else '#dc2626' if r['result'] == 'DEEPFAKE' else '#f97316'
                icon = '✅' if r['result'] == 'AUTHENTIC' else '🤖' if r['result'] == 'DEEPFAKE' else '⚠️'

                st.markdown(f"""
                <div style="background:#0f172a;border:1px solid {color};border-radius:8px;
                            padding:12px 16px;margin-bottom:6px;">
                    <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;">
                        <span style="color:white;font-weight:bold;">{icon} {r['filename']}</span>
                        <span style="color:{color};font-weight:bold;">{r['result']}</span>
                        <span style="color:#cbd5e1;font-size:12px;">Deepfake Prob: {r['deepfake_probability']}</span>
                        <span style="color:#cbd5e1;font-size:12px;">Liveness: {r['liveness_score']}</span>
                        <span style="color:#f97316;font-size:12px;">{r['alert_level']}</span>
                        <span style="color:#64748b;font-size:12px;">{r['processing_ms']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            df_results = pd.DataFrame(results)
            csv = df_results.to_csv(index=False)
            st.download_button(
                "📥 Download Results CSV",
                data=csv,
                file_name="batch_face_results.csv",
                mime="text/csv"
            )

st.divider()
st.markdown("""
<div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:8px;padding:16px;">
    <p style="color:#64748b;margin:0;font-size:13px;">
    💡 <b style="color:#cbd5e1;">Batch Processing:</b> Banks process thousands of KYC verifications daily.
    VeriShield's batch mode allows compliance teams to screen multiple documents simultaneously,
    with results exportable to CSV for regulatory reporting.
    </p>
</div>
""", unsafe_allow_html=True)