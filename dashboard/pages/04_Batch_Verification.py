import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="VeriShield — Batch Verification",
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
    <h1 style="margin:0;color:white;font-size:28px;">Batch Deepfake Detection</h1>
    <p style="color:#64748b;margin:6px 0 0 0;font-size:13px;">
        Upload multiple face photos for bulk deepfake screening
    </p>
</div>
""", unsafe_allow_html=True)

API_URL = st.secrets.get("API_URL", "https://verishield-kyc-production.up.railway.app")

uploaded_faces = st.file_uploader(
    "Upload Face Photos",
    type=['jpg', 'jpeg', 'png'],
    accept_multiple_files=True,
    key="batch_faces"
)

if uploaded_faces:
    st.markdown(f"**{len(uploaded_faces)} photos uploaded**")

    if st.button("Run Batch Deepfake Check", type="primary", use_container_width=True):
        results = []
        progress = st.progress(0)
        status = st.empty()

        for i, face in enumerate(uploaded_faces):
            status.markdown(f"<p style='color:#64748b;'>Processing {face.name}...</p>", unsafe_allow_html=True)
            try:
                face.seek(0)
                files = {'file': (face.name, face.read(), 'image/jpeg')}
                response = requests.post(f"{API_URL}/verify-face", files=files, timeout=120)
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

        st.markdown("### Results")

        authentic = sum(1 for r in results if r['result'] == 'AUTHENTIC')
        deepfakes = sum(1 for r in results if r['result'] == 'DEEPFAKE')
        suspicious = sum(1 for r in results if r['result'] == 'SUSPICIOUS')

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Total Processed", len(results))
        with c2: st.metric("Authentic", authentic)
        with c3: st.metric("Deepfakes", deepfakes)
        with c4: st.metric("Suspicious", suspicious)

        st.divider()

        for r in results:
            color = '#059669' if r['result'] == 'AUTHENTIC' else '#dc2626' if r['result'] == 'DEEPFAKE' else '#f97316'
            icon = '✅' if r['result'] == 'AUTHENTIC' else '❌' if r['result'] == 'DEEPFAKE' else '⚠️'

            st.markdown(f"""
            <div style="background:#0f172a;border:1px solid {color};border-radius:8px;
                        padding:12px 16px;margin-bottom:6px;">
                <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;">
                    <span style="color:white;font-weight:bold;">{icon} {r['filename']}</span>
                    <span style="color:{color};font-weight:bold;">{r['result']}</span>
                    <span style="color:#cbd5e1;font-size:12px;">Deepfake prob: {r['deepfake_probability']}</span>
                    <span style="color:#cbd5e1;font-size:12px;">Liveness: {r['liveness_score']}</span>
                    <span style="color:#f97316;font-size:12px;">{r['alert_level']}</span>
                    <span style="color:#64748b;font-size:12px;">{r['processing_ms']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        df_results = pd.DataFrame(results)
        csv = df_results.to_csv(index=False)
        st.download_button(
            "Download Results CSV",
            data=csv,
            file_name="batch_deepfake_results.csv",
            mime="text/csv"
        )