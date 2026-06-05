# VeriShield AI — KYC Deepfake Identity Detection

A deepfake detection and face matching platform built for KYC identity verification. Trained EfficientNet-B0 on 140K real/fake faces, wrapped it in a FastAPI backend, and built a 10-page Streamlit dashboard with PostgreSQL audit logging via Supabase.

**Live Dashboard:** https://verishield-kyc-varunsajinair.streamlit.app  
**Live API:** https://verishield-kyc-production.up.railway.app  
**GitHub:** https://github.com/varunsajinair/verishield-kyc

---

## What it does

Upload an ID photo and a selfie. The system runs two checks:

1. **Deepfake detection** — EfficientNet-B0 classifies the face as real or synthetic
2. **Face match** — compares the ID photo against the selfie using cosine similarity on face embeddings

Results are logged to PostgreSQL (Supabase) with a timestamp, confidence scores, and an overall risk score. The dashboard gives compliance teams visibility into all verifications, with GradCAM heatmaps for manual review of borderline cases.

---

## Stack

| Component | Technology |
|-----------|-----------|
| Deepfake model | EfficientNet-B0 (PyTorch) |
| Training data | 140K real/fake faces |
| Backend API | FastAPI |
| Dashboard | Streamlit |
| Database | PostgreSQL (Supabase) |
| Deployment | Railway (API) + Streamlit Cloud (dashboard) |
| Containerization | Docker |

---

## Model

EfficientNet-B0 fine-tuned for binary classification (real vs fake face).

| Model | Accuracy | F1 | AUC-ROC | Inference |
|-------|----------|----|---------|-----------|
| **EfficientNet-B0** (deployed) | **99.28%** | **98.0%** | **99.1%** | 650ms |
| ResNet-50 | 94.2% | 92.9% | 96.3% | 450ms |
| VGG-16 | 91.5% | 89.9% | 94.1% | 820ms |
| MobileNet-V2 | 89.3% | 88.0% | 92.5% | 280ms |

Tested B4 as well — marginal accuracy gain (~0.4%) but ~3x slower inference, not worth it for a real-time verification flow. B0 hit the right tradeoff.

---

## Dashboard Pages

### 1. Dashboard
Overview of all verifications — API status, approval/rejection counts, recent verification feed.

![Dashboard](screenshots/01_dashboard.png)

---

### 2. KYC Verification
Upload an ID document and selfie. Runs deepfake detection and face match in one call. Also has a standalone face-only deepfake check tab.

![KYC Verification - Upload](screenshots/02_kyc_verification_1.png)
![KYC Verification - Result](screenshots/03_kyc_verification_2.png)

---

### 3. Audit Trail
Full log of all verifications pulled from Supabase. Filterable by overall result and face result. Includes analytics charts and CSV export.

![Audit Trail - Table](screenshots/04_audit_trail_1.png)
![Audit Trail - Analytics](screenshots/05_audit_trail_2.png)

---

### 4. Analytics
Aggregated charts across all verifications — result distribution, deepfake detection breakdown, risk scores by result, face match distribution, processing times, alert levels.

![Analytics - Overview](screenshots/06_analytics_1.png)
![Analytics - Charts](screenshots/07_analytics_2.png)

---

### 5. Batch Deepfake Detection
Upload multiple face photos at once. Runs deepfake detection on each and returns a summary with per-image results. Exportable to CSV.

![Batch Deepfake Detection](screenshots/08_batch_deepfake.png)

---

### 6. Compliance Report
Fill in customer details and verification results, generate a PDF KYC report. Includes deepfake detection result, face match score, risk score, and a disclaimer.

![Compliance Report - Form](screenshots/09_compliance_report_1.png)
![Compliance Report - Generated](screenshots/10_compliance_report_2.png)

---

### 7. Model Performance
EfficientNet-B0 benchmarked against ResNet-50, VGG-16, and MobileNet-V2. Radar chart, side-by-side metric comparison, speed vs accuracy scatter, training time breakdown, and model cards.

![Model Performance - Summary](screenshots/11_model_performance_1.png)
![Model Performance - Comparison](screenshots/12_model_performance_2.png)
![Model Performance - Model Cards](screenshots/13_model_performance_3.png)

---

### 8. GradCAM Analysis
Upload a face photo. Generates a GradCAM heatmap showing which facial regions drove the model's deepfake decision. Useful for manually reviewing borderline cases.

![GradCAM - Detection](screenshots/14_gradcam_1.png)
![GradCAM - Heatmap](screenshots/15_gradcam_2.png)

---

### 9. Risk Dashboard
Platform-wide risk gauge, deepfake risk and face match risk gauges, alert level distribution, risk score histogram, and a high-risk verification list.

Risk thresholds: above 0.6 → auto-rejected, 0.3–0.6 → manual review, below 0.3 → auto-approved.

![Risk Dashboard - Gauge](screenshots/16_risk_dashboard_1.png)
![Risk Dashboard - Components](screenshots/17_risk_dashboard_2.png)
![Risk Dashboard - High Risk](screenshots/18_risk_dashboard_3.png)

---

### 10. SAR Filing
Generate a Suspicious Activity Report PDF for flagged verifications. Includes institution details, subject info, activity type, deepfake probability, and a narrative section. Also has a red flag reference guide.

![SAR Filing - Form](screenshots/19_sar_filing_1.png)
![SAR Filing - Generated](screenshots/20_sar_filing_2.png)

---

### 11. Live KYC Stream
Simulated real-time verification feed. Generates verifications every 2 seconds showing face detection and match results as they'd appear in a live onboarding system.

![Live Stream](screenshots/21_live_stream.png)

---

## Project Structure

```
verishield-kyc/
├── src/
│   ├── app.py                  ← FastAPI application
│   ├── face_model.py           ← EfficientNet-B0 deepfake detection
│   ├── face_match.py           ← Face similarity matching
│   └── database.py             ← PostgreSQL logging
├── dashboard/
│   ├── dashboard.py            ← Main Streamlit app
│   ├── db_utils.py             ← Database utilities
│   └── pages/
│       ├── 01_KYC_Verification.py
│       ├── 02_Audit_Trail.py
│       ├── 03_Analytics.py
│       ├── 04_Batch_Verification.py
│       ├── 05_Compliance_Report.py
│       ├── 06_Model_Performance.py
│       ├── 07_GradCAM_Analysis.py
│       ├── 08_Risk_Dashboard.py
│       ├── 09_SAR_Filing.py
│       └── 10_Live_Stream.py
├── models/
│   └── verishield_face_model.pth
├── screenshots/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── Procfile
```

---

## API Endpoints

**Base URL:** `https://verishield-kyc-production.up.railway.app`

```bash
# Health check
GET /health

# Deepfake detection on a single face
POST /verify-face
  -F "file=@selfie.jpg"

# Full KYC — deepfake + face match
POST /kyc-complete
  -F "document=@id_card.jpg"
  -F "selfie=@selfie.jpg"
```

---

## Running Locally

```bash
# Clone and set up environment
git clone https://github.com/varunsajinair/verishield-kyc
cd verishield-kyc
conda activate verishield

# Start API
uvicorn src.app:app --port 8001

# Start dashboard (separate terminal)
cd dashboard
streamlit run dashboard.py
```

Add a `.streamlit/secrets.toml` with your Supabase credentials:

```toml
API_URL = "http://localhost:8001"
DB_HOST = "your-supabase-host"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "your-password"
```

---

## Deployment

| Service | Platform | URL |
|---------|----------|-----|
| FastAPI backend | Railway | https://verishield-kyc-production.up.railway.app |
| Streamlit dashboard | Streamlit Cloud | https://verishield-kyc-varunsajinair.streamlit.app |
| Audit database | Supabase PostgreSQL | `kyc_verifications` table |
