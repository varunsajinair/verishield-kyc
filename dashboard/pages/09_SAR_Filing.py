import streamlit as st
import random
from datetime import datetime, timedelta
from fpdf import FPDF
import io
from db_utils import load_all, load_stats

st.set_page_config(
    page_title="VeriShield - SAR Filing",
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
    <h1 style="margin:0;color:white;font-size:28px;">SAR Filing</h1>
    <p style="color:#64748b;margin:6px 0 0 0;font-size:13px;">
        Generate Suspicious Activity Reports for flagged KYC verifications
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

tab1, tab2 = st.tabs(["Generate SAR Report", "Red Flag Reference"])

with tab1:
    st.markdown("#### SAR Report Generator")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("**Institution Details**")
        institution = st.text_input("Reporting Institution", value="VeriShield Financial Services")
        branch = st.text_input("Branch/Department", value="Digital Onboarding - KYC Division")
        officer_name = st.text_input("Compliance Officer Name", value="")
        officer_title = st.text_input("Officer Title", value="Compliance Officer")
        filing_date = st.date_input("Filing Date", value=datetime.now())

        st.markdown("**Subject Details**")
        subject_name = st.text_input("Subject Full Name", value="John Doe")
        subject_id = st.text_input("Subject Account/ID", value=f"SUBJ{random.randint(10000,99999)}")
        subject_dob = st.text_input("Subject Date of Birth", value="1990-01-15")
        subject_nationality = st.text_input("Subject Nationality", value="Unknown")

    with col2:
        st.markdown("**Suspicious Activity Details**")
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
            value="High-confidence deepfake detected. Face liveness check failed.",
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
        pdf.cell(190, 8, 'Deepfake Identity Fraud - KYC Verification', 0, 1, 'C')
        pdf.set_font('Arial', '', 9)
        pdf.set_xy(10, 30)
        pdf.cell(190, 8, f"SAR ID: {data['sar_id']} | Filed: {data['filing_date']} | CONFIDENTIAL", 0, 1, 'C')

        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)

        # Alert banner
        pdf.set_fill_color(124, 58, 237)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(190, 10, f'FLAGGED: {data["activity_type"].upper()}', 0, 1, 'C', True)
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
            ('Compliance Officer', data['officer_name'] or 'N/A'),
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
        pdf.cell(190, 8, 'SECTION 4: NARRATIVE', 0, 1, 'L', True)
        pdf.set_font('Arial', '', 10)
        pdf.ln(2)
        narrative = (
            f"On {data['filing_date']}, VeriShield AI KYC verification system flagged subject "
            f"{data['subject_name']} (ID: {data['subject_id']}) during onboarding. "
            f"Activity type: {data['activity_type']}. "
            f"Deepfake probability: {data['deepfake_prob']:.0%}. "
            f"Overall risk score: {data['overall_risk']:.0%}. "
            f"Detection method: {data['detection_method']}. "
            f"Notes: {data['additional_notes']}"
        )
        pdf.multi_cell(190, 6, narrative)

        pdf.ln(4)

        # Footer
        pdf.set_fill_color(13, 27, 46)
        pdf.rect(0, 267, 210, 30, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', '', 8)
        pdf.set_xy(10, 272)
        pdf.cell(190, 6, 'VeriShield AI | Suspicious Activity Report', 0, 1, 'C')
        pdf.set_xy(10, 280)
        pdf.cell(190, 6, f'SAR ID: {data["sar_id"]} | CONFIDENTIAL', 0, 1, 'C')

        output = pdf.output(dest='S')
        if isinstance(output, str):
            return output.encode('latin-1')
        return bytes(output)

    if st.button("Generate SAR Report", type="primary", use_container_width=True):
        sar_data = {
            'sar_id': f"SAR-{random.randint(100000,999999)}",
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
            <p style="color:#7c3aed;font-size:22px;font-weight:bold;margin:0;">SAR GENERATED</p>
            <p style="color:#64748b;margin:8px 0 0 0;font-size:13px;">
                SAR ID: {sar_data['sar_id']} &nbsp;|&nbsp;
                Deepfake: {deepfake_prob:.0%} &nbsp;|&nbsp;
                Risk: {overall_risk:.0%}
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            label="Download SAR PDF",
            data=pdf_bytes,
            file_name=f"SAR_{sar_data['sar_id']}.pdf",
            mime="application/pdf"
        )

with tab2:
    st.markdown("#### Red Flag Indicators")
    st.markdown("<p style='color:#64748b;font-size:13px;'>Common signals that warrant a SAR filing during KYC</p>", unsafe_allow_html=True)

    red_flags = [
        ("Deepfake Face Detected", "AI model flagged high deepfake probability during liveness check"),
        ("Face Mismatch", "Face on submitted ID does not match the selfie"),
        ("Multiple Failed Attempts", "Same identity submitted multiple times with variations"),
        ("Technical Evasion", "Unusual patterns in submission timing or repeated API retries"),
        ("Geographic Mismatch", "Device location inconsistent with document issuing country"),
    ]

    for label, description in red_flags:
        st.markdown(f"""
        <div style="background:#0f172a;border-left:3px solid #dc2626;
                    padding:10px 16px;margin-bottom:6px;border-radius:0 8px 8px 0;">
            <p style="color:white;font-weight:600;margin:0;font-size:13px;">{label}</p>
            <p style="color:#64748b;font-size:12px;margin:2px 0 0 0;">{description}</p>
        </div>
        """, unsafe_allow_html=True)