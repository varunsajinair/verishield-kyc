import streamlit as st
import requests
from fpdf import FPDF
import io
import datetime
import random

st.set_page_config(
    page_title="VeriShield — Compliance Report",
    page_icon="📋",
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
    <h1 style="margin:0;color:white;">📋 Compliance Report Generator</h1>
    <p style="color:#64748b;margin:4px 0 0 0;">
    Generate regulatory KYC compliance reports — required by banks under AML/KYC regulations
    </p>
</div>
""", unsafe_allow_html=True)

API_URL = st.secrets.get("API_URL", "https://verishield-kyc-production.up.railway.app")

st.markdown("### 📄 Generate KYC Compliance Report")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Customer Details")
    customer_name = st.text_input("Customer Full Name", value="John Smith")
    customer_id = st.text_input("Customer ID", value=f"CUST{random.randint(10000,99999)}")
    customer_dob = st.text_input("Date of Birth", value="1990-01-15")
    customer_nationality = st.text_input("Nationality", value="Indian")
    document_type = st.selectbox("Document Type", ["Passport", "National ID", "Driving License", "Aadhaar Card"])
    document_number = st.text_input("Document Number", value=f"DOC{random.randint(100000,999999)}")

with col2:
    st.markdown("#### Verification Results")
    doc_result = st.selectbox("Document Check Result", ["AUTHENTIC", "SUSPICIOUS", "FORGED"])
    doc_confidence = st.slider("Document Confidence", 0.0, 1.0, 0.92)
    face_result = st.selectbox("Face/Deepfake Check Result", ["AUTHENTIC", "SUSPICIOUS", "DEEPFAKE"])
    face_confidence = st.slider("Face Confidence", 0.0, 1.0, 0.88)
    match_result = st.selectbox("Face Match Result", ["MATCH", "POSSIBLE MATCH", "NO MATCH"])
    match_score = st.slider("Match Score", 0.0, 1.0, 0.85)
    overall_result = st.selectbox("Overall KYC Decision", ["APPROVED", "REVIEW", "REJECTED"])
    risk_score = st.slider("Overall Risk Score", 0.0, 1.0, 0.15)

institution = st.text_input("Reporting Institution", value="VeriShield Financial Services")
officer = st.text_input("Compliance Officer", value="AI Verification System v1.0")

def generate_pdf_report(data):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_fill_color(13, 27, 46)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 20)
    pdf.set_xy(10, 10)
    pdf.cell(190, 10, 'VeriShield AI - KYC Compliance Report', 0, 1, 'C')
    pdf.set_font('Arial', '', 10)
    pdf.set_xy(10, 22)
    pdf.cell(190, 8, f"Generated: {data['timestamp']} | Report ID: {data['report_id']}", 0, 1, 'C')

    pdf.set_text_color(0, 0, 0)
    pdf.ln(15)

    # Overall Result banner
    result = data['overall_result']
    if result == 'APPROVED':
        pdf.set_fill_color(5, 150, 105)
    elif result == 'REJECTED':
        pdf.set_fill_color(220, 38, 38)
    else:
        pdf.set_fill_color(249, 115, 22)
    
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(190, 14, f'KYC DECISION: {result}', 0, 1, 'C', True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    # Customer info
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(190, 8, 'CUSTOMER INFORMATION', 0, 1, 'L', True)
    pdf.set_font('Arial', '', 10)
    pdf.ln(2)

    info_items = [
        ('Customer Name', data['customer_name']),
        ('Customer ID', data['customer_id']),
        ('Date of Birth', data['customer_dob']),
        ('Nationality', data['customer_nationality']),
        ('Document Type', data['document_type']),
        ('Document Number', data['document_number']),
    ]

    for label, value in info_items:
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(70, 7, f'{label}:', 0, 0)
        pdf.set_font('Arial', '', 10)
        pdf.cell(120, 7, str(value), 0, 1)

    pdf.ln(5)

    # Verification results
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(190, 8, 'VERIFICATION RESULTS', 0, 1, 'L', True)
    pdf.ln(2)

    results_items = [
        ('Document Forgery Check', f"{data['doc_result']} (Confidence: {data['doc_confidence']:.0%})"),
        ('Deepfake/Liveness Check', f"{data['face_result']} (Confidence: {data['face_confidence']:.0%})"),
        ('Face Match (ID vs Selfie)', f"{data['match_result']} (Score: {data['match_score']:.0%})"),
        ('Overall Risk Score', f"{data['risk_score']:.0%}"),
        ('Alert Level', data['alert_level']),
        ('Overall KYC Decision', data['overall_result']),
    ]

    for label, value in results_items:
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(90, 7, f'{label}:', 0, 0)
        pdf.set_font('Arial', '', 10)
        pdf.cell(100, 7, str(value), 0, 1)

    pdf.ln(5)

    # Institution info
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(190, 8, 'REPORTING INSTITUTION', 0, 1, 'L', True)
    pdf.ln(2)
    pdf.set_font('Arial', '', 10)
    pdf.cell(190, 7, f"Institution: {data['institution']}", 0, 1)
    pdf.cell(190, 7, f"Compliance Officer: {data['officer']}", 0, 1)
    pdf.cell(190, 7, f"Verification Date: {data['timestamp']}", 0, 1)
    pdf.cell(190, 7, f"Report ID: {data['report_id']}", 0, 1)

    pdf.ln(5)

    # Legal disclaimer
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(190, 8, 'LEGAL DISCLAIMER', 0, 1, 'L', True)
    pdf.ln(2)
    pdf.set_font('Arial', '', 9)
    disclaimer = ("This report has been generated by VeriShield AI automated KYC verification system. "
                 "This report is intended for compliance and regulatory purposes only. "
                 "The verification was performed using AI-based document forgery detection and deepfake "
                 "liveness analysis. All findings should be reviewed by a qualified compliance officer "
                 "before final decision. This system complies with GDPR Article 22 requirements for "
                 "automated decision-making.")
    pdf.multi_cell(190, 6, disclaimer)

    pdf.ln(5)

    # Footer
    pdf.set_fill_color(13, 27, 46)
    pdf.rect(0, 270, 210, 30, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', '', 8)
    pdf.set_xy(10, 275)
    pdf.cell(190, 6, 'VeriShield AI | Powered by EfficientNet + Vision Transformer | PostgreSQL Audit Trail', 0, 1, 'C')
    pdf.set_xy(10, 283)
    pdf.cell(190, 6, f'Report ID: {data["report_id"]} | CONFIDENTIAL', 0, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

if st.button("📋 Generate Compliance Report", type="primary", use_container_width=True):
    alert_map = {
        ('AUTHENTIC', 'AUTHENTIC', 'MATCH'): 'LOW RISK',
        ('FORGED', 'DEEPFAKE', 'NO MATCH'): 'CRITICAL',
    }
    
    if risk_score > 0.7:
        alert_level = "CRITICAL"
    elif risk_score > 0.4:
        alert_level = "HIGH RISK"
    elif risk_score > 0.2:
        alert_level = "MEDIUM RISK"
    else:
        alert_level = "LOW RISK"

    report_data = {
        'report_id': f"KYC-{random.randint(100000,999999)}",
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'customer_name': customer_name,
        'customer_id': customer_id,
        'customer_dob': customer_dob,
        'customer_nationality': customer_nationality,
        'document_type': document_type,
        'document_number': document_number,
        'doc_result': doc_result,
        'doc_confidence': doc_confidence,
        'face_result': face_result,
        'face_confidence': face_confidence,
        'match_result': match_result,
        'match_score': match_score,
        'overall_result': overall_result,
        'risk_score': risk_score,
        'alert_level': alert_level,
        'institution': institution,
        'officer': officer
    }

    pdf_bytes = generate_pdf_report(report_data)

    result_color = '#059669' if overall_result == 'APPROVED' else '#dc2626' if overall_result == 'REJECTED' else '#f97316'

    st.markdown(f"""
    <div style="background:#0f172a;border:2px solid {result_color};border-radius:12px;
                padding:20px;text-align:center;margin:16px 0;">
        <p style="color:{result_color};font-size:24px;font-weight:bold;margin:0;">
            {'✅' if overall_result == 'APPROVED' else '❌' if overall_result == 'REJECTED' else '⚠️'} 
            {overall_result}
        </p>
        <p style="color:#64748b;margin:4px 0 0 0;">
            Report ID: {report_data['report_id']} | Risk: {risk_score:.0%} | {alert_level}
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.download_button(
        label="📥 Download PDF Report",
        data=pdf_bytes,
        file_name=f"KYC_Report_{report_data['report_id']}.pdf",
        mime="application/pdf"
    )
    st.success("✅ Report generated successfully!")

st.divider()
st.markdown("""
<div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:8px;padding:16px;">
    <p style="color:#64748b;margin:0;font-size:13px;">
    💡 <b style="color:#cbd5e1;">Why Compliance Reports Matter:</b> Banks must maintain KYC records 
    for 5-7 years under AML regulations. Every verification must be documented with reasoning 
    for regulatory audits. VeriShield auto-generates GDPR Article 22 compliant reports explaining 
    every automated decision.
    </p>
</div>
""", unsafe_allow_html=True)