import streamlit as st
import random
from datetime import datetime, timedelta
from fpdf import FPDF
import io
from db_utils import load_all, load_stats

st.set_page_config(
    page_title="VeriShield - SAR Filing",
    page_icon="🏛️",
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
    <h1 style="margin:0;color:white;">🏛️ FinCEN SAR Filing</h1>
    <p style="color:#64748b;margin:4px 0 0 0;">
    Suspicious Activity Report generator for deepfake KYC fraud - FIN-2024-DEEPFAKEFRAUD compliant
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background:#0f172a;border:1px solid #7c3aed;border-radius:8px;padding:12px 16px;margin-bottom:16px;">
    <p style="color:#cbd5e1;margin:0;font-size:13px;">
    💡 <b style="color:white;">Legal Requirement:</b> FinCEN Alert FIN-2024-DEEPFAKEFRAUD requires all 
    financial institutions to file SARs using the keyword <b>FIN-2024-DEEPFAKEFRAUD</b> when deepfake 
    media is detected during KYC onboarding. Non-compliance can result in fines up to $1M per violation.
    </p>
</div>
""", unsafe_allow_html=True)

stats = load_stats()
df = load_all()

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Total Verifications", stats.get("total", 0))
with m2: st.metric("Deepfakes Detected", len(df[df['face_result'] == 'DEEPFAKE']) if not df.empty else 0)
with m3: st.metric("Rejected", stats.get("rejected", 0))
with m4: st.metric("SARs Required", len(df[df['overall_result'] == 'REJECTED']) if not df.empty else 0)

st.divider()

tab1, tab2 = st.tabs(["📋 Generate SAR Report", "📚 SAR Reference Guide"])

with tab1:
    st.markdown("### 📋 FinCEN SAR Report Generator")
    st.markdown("<p style='color:#64748b;'>Generate FIN-2024-DEEPFAKEFRAUD compliant SAR reports</p>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### Institution Details")
        institution = st.text_input("Reporting Institution", value="VeriShield Financial Services")
        branch = st.text_input("Branch/Department", value="Digital Onboarding - KYC Division")
        officer_name = st.text_input("Compliance Officer Name", value="AI Compliance System v2.0")
        officer_title = st.text_input("Officer Title", value="Chief Compliance Officer")
        filing_date = st.date_input("Filing Date", value=datetime.now())

        st.markdown("#### Subject Details")
        subject_name = st.text_input("Subject Full Name", value="John Doe")
        subject_id = st.text_input("Subject Account/ID", value=f"SUBJ{random.randint(10000,99999)}")
        subject_dob = st.text_input("Subject Date of Birth", value="1990-01-15")
        subject_nationality = st.text_input("Subject Nationality", value="Unknown")

    with col2:
        st.markdown("#### Suspicious Activity Details")
        activity_type = st.selectbox("Primary Activity Type", [
            "Deepfake Identity Fraud",
            "Synthetic Identity",
            "Identity Impersonation",
            "Face Spoofing Attack",
            "Multiple Activity Types"
        ])

        detection_method = st.selectbox("Detection Method", [
            "AI Deepfake Detection (EfficientNet-B0)",
            "Face Match Failure",
            "Combined AI Analysis"
        ])

        deepfake_prob = st.slider("Deepfake Probability", 0.0, 1.0, 0.89)
        overall_risk = st.slider("Overall Risk Score", 0.0, 1.0, 0.85)
        verification_id = st.text_input("Verification ID", value=f"VER-{random.randint(100000,999999)}")

        additional_notes = st.text_area(
            "Additional Notes",
            value="AI system detected high-confidence deepfake manipulation. Face liveness check failed.",
            height=100
        )

    def generate_sar_pdf(data):
        pdf = FPDF()
        pdf.add_page()

        # Header
        pdf.set_fill_color(13, 27, 46)
        pdf.rect(0, 0, 210, 45, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 16)
        pdf.set_xy(10, 8)
        pdf.cell(190, 10, 'SUSPICIOUS ACTIVITY REPORT (SAR)', 0, 1, 'C')
        pdf.set_font('Arial', 'B', 11)
        pdf.set_xy(10, 20)
        pdf.cell(190, 8, 'FinCEN Form 111 | FIN-2024-DEEPFAKEFRAUD', 0, 1, 'C')
        pdf.set_font('Arial', '', 9)
        pdf.set_xy(10, 30)
        pdf.cell(190, 8, f"SAR ID: {data['sar_id']} | Filed: {data['filing_date']} | CONFIDENTIAL", 0, 1, 'C')

        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)

        # Alert banner
        pdf.set_fill_color(124, 58, 237)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(190, 10, f'DEEPFAKE IDENTITY FRAUD DETECTED - {data["activity_type"].upper()}', 0, 1, 'C', True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)

        # Section 1 - Institution
        pdf.set_font('Arial', 'B', 11)
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(190, 8, 'SECTION 1: REPORTING INSTITUTION', 0, 1, 'L', True)
        pdf.set_font('Arial', '', 10)
        pdf.ln(2)
        fields = [
            ('Institution Name', data['institution']),
            ('Branch/Department', data['branch']),
            ('Compliance Officer', data['officer_name']),
            ('Officer Title', data['officer_title']),
            ('Filing Date', str(data['filing_date'])),
        ]
        for label, value in fields:
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(70, 7, f'{label}:', 0, 0)
            pdf.set_font('Arial', '', 10)
            pdf.cell(120, 7, str(value), 0, 1)

        pdf.ln(4)

        # Section 2 - Subject
        pdf.set_font('Arial', 'B', 11)
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(190, 8, 'SECTION 2: SUBJECT INFORMATION', 0, 1, 'L', True)
        pdf.set_font('Arial', '', 10)
        pdf.ln(2)
        subject_fields = [
            ('Full Name', data['subject_name']),
            ('Account/ID', data['subject_id']),
            ('Date of Birth', data['subject_dob']),
            ('Nationality', data['subject_nationality']),
        ]
        for label, value in subject_fields:
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(70, 7, f'{label}:', 0, 0)
            pdf.set_font('Arial', '', 10)
            pdf.cell(120, 7, str(value), 0, 1)

        pdf.ln(4)

        # Section 3 - Suspicious Activity
        pdf.set_font('Arial', 'B', 11)
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(190, 8, 'SECTION 3: SUSPICIOUS ACTIVITY', 0, 1, 'L', True)
        pdf.set_font('Arial', '', 10)
        pdf.ln(2)
        activity_fields = [
            ('Activity Type', data['activity_type']),
            ('Detection Method', data['detection_method']),
            ('Deepfake Probability', f"{data['deepfake_prob']:.0%}"),
            ('Overall Risk Score', f"{data['overall_risk']:.0%}"),
            ('Verification ID', data['verification_id']),
            ('FinCEN Keyword', 'FIN-2024-DEEPFAKEFRAUD'),
        ]
        for label, value in activity_fields:
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(70, 7, f'{label}:', 0, 0)
            pdf.set_font('Arial', '', 10)
            pdf.cell(120, 7, str(value), 0, 1)

        pdf.ln(4)

        # Section 4 - Narrative
        pdf.set_font('Arial', 'B', 11)
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(190, 8, 'SECTION 4: NARRATIVE DESCRIPTION', 0, 1, 'L', True)
        pdf.set_font('Arial', '', 10)
        pdf.ln(2)
        narrative = (
            f"On {data['filing_date']}, VeriShield AI automated KYC verification system detected "
            f"suspicious activity during customer onboarding for subject {data['subject_name']} "
            f"(ID: {data['subject_id']}). The AI system flagged this verification as {data['activity_type']} "
            f"with a deepfake probability of {data['deepfake_prob']:.0%} and overall risk score of "
            f"{data['overall_risk']:.0%}. Detection method: {data['detection_method']}. "
            f"This report is filed in accordance with FinCEN Alert FIN-2024-DEEPFAKEFRAUD. "
            f"Additional notes: {data['additional_notes']}"
        )
        pdf.multi_cell(190, 6, narrative)

        pdf.ln(4)

        # Footer
        pdf.set_fill_color(13, 27, 46)
        pdf.rect(0, 267, 210, 30, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', '', 8)
        pdf.set_xy(10, 272)
        pdf.cell(190, 6, 'VeriShield AI | FIN-2024-DEEPFAKEFRAUD Compliant SAR Report', 0, 1, 'C')
        pdf.set_xy(10, 280)
        pdf.cell(190, 6, f'SAR ID: {data["sar_id"]} | CONFIDENTIAL', 0, 1, 'C')

        output = pdf.output(dest='S')
        if isinstance(output, str):
            return output.encode('latin-1')
        return bytes(output)

    if st.button("🏛️ Generate FinCEN SAR Report", type="primary", use_container_width=True):
        sar_data = {
            'sar_id': f"SAR-DEEPFAKE-{random.randint(100000,999999)}",
            'filing_date': filing_date,
            'institution': institution,
            'branch': branch,
            'officer_name': officer_name,
            'officer_title': officer_title,
            'subject_name': subject_name,
            'subject_id': subject_id,
            'subject_dob': subject_dob,
            'subject_nationality': subject_nationality,
            'activity_type': activity_type,
            'detection_method': detection_method,
            'deepfake_prob': deepfake_prob,
            'overall_risk': overall_risk,
            'verification_id': verification_id,
            'additional_notes': additional_notes
        }

        pdf_bytes = generate_sar_pdf(sar_data)

        st.markdown(f"""
        <div style="background:#0f172a;border:2px solid #7c3aed;border-radius:12px;
                    padding:20px;text-align:center;margin:16px 0;">
            <p style="color:#7c3aed;font-size:22px;font-weight:bold;margin:0;">
                🏛️ SAR REPORT GENERATED
            </p>
            <p style="color:#64748b;margin:8px 0 0 0;">
                SAR ID: {sar_data['sar_id']} |
                Deepfake Prob: {deepfake_prob:.0%} |
                Overall Risk: {overall_risk:.0%}
            </p>
            <p style="color:#94a3b8;font-size:12px;margin:4px 0 0 0;">
                FIN-2024-DEEPFAKEFRAUD compliant | Ready for FinCEN submission
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            label="📥 Download SAR PDF",
            data=pdf_bytes,
            file_name=f"SAR_{sar_data['sar_id']}.pdf",
            mime="application/pdf"
        )
        st.success("✅ SAR Report generated successfully!")

with tab2:
    st.markdown("### 📚 SAR Reference Guide")

    st.markdown("""
    <div style="background:#0f172a;border:1px solid #7c3aed;border-radius:12px;padding:20px;margin-bottom:12px;">
        <p style="color:#7c3aed;font-weight:bold;font-size:16px;margin:0 0 8px 0;">🏛️ FinCEN Alert FIN-2024-DEEPFAKEFRAUD</p>
        <p style="color:#94a3b8;font-size:13px;margin:0 0 8px 0;">
        Issued by the Financial Crimes Enforcement Network requiring all financial institutions
        to identify and report deepfake-related fraud in KYC processes.
        </p>
        <p style="color:#cbd5e1;font-size:12px;margin:0;">
        <b>Key Requirements:</b> Use keyword "FIN-2024-DEEPFAKEFRAUD" in SAR filings |
        File within 30 days of detection | Preserve all AI detection evidence
        </p>
    </div>
    """, unsafe_allow_html=True)

    red_flags = [
        ("🤖 Deepfake Face", "AI-generated or manipulated face detected during liveness check"),
        ("🔍 Face Mismatch", "Face on ID document does not match submitted selfie"),
        ("⚡ Technical Issues", "Customer reports repeated technical problems during verification"),
        ("🌍 Geographic Mismatch", "Device location does not match document issuing country"),
        ("🔄 Multiple Attempts", "Same identity submitted multiple times with variations"),
    ]

    st.markdown("#### 🚩 Red Flag Indicators")
    for icon_label, description in red_flags:
        st.markdown(f"""
        <div style="background:#0f172a;border-left:3px solid #dc2626;
                    padding:10px 16px;margin-bottom:6px;border-radius:0 8px 8px 0;">
            <p style="color:white;font-weight:bold;margin:0;">{icon_label}</p>
            <p style="color:#64748b;font-size:12px;margin:2px 0 0 0;">{description}</p>
        </div>
        """, unsafe_allow_html=True)

st.divider()
st.markdown("""
<div style="background:#0f172a;border:1px solid #7c3aed;border-radius:8px;padding:16px;">
    <p style="color:#64748b;margin:0;font-size:13px;">
    💡 <b style="color:white;">Why SAR Filing Matters:</b> FinCEN FIN-2024-DEEPFAKEFRAUD mandates 
    banks to file SARs when deepfakes are detected in KYC. Fines for non-compliance reach $1M per 
    violation. VeriShield automates SAR generation reducing compliance costs significantly.
    </p>
</div>
""", unsafe_allow_html=True)