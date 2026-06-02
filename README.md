<div align="center">

# 🛡️ VeriShield AI

### KYC Document Forgery & Deepfake Identity Detection Platform

[![Python](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red?style=for-the-badge&logo=streamlit)](https://streamlit.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-29B5E8?style=for-the-badge&logo=postgresql)](https://supabase.com)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker)](https://docker.com)
[![Railway](https://img.shields.io/badge/Railway-Deployed-0B0D0E?style=for-the-badge&logo=railway)](https://railway.app)

**Trained on 140,000 Real/Fake Faces | EfficientNet-B0 | 98.65% Accuracy | Real-time KYC**

[🚀 Live Demo](https://verishield-kyc-varunsajinair.streamlit.app) • [📡 API Docs](https://verishield-kyc-production.up.railway.app/docs) • [📊 Dashboard](https://verishield-kyc-varunsajinair.streamlit.app)

</div>

---

## 🎯 What is VeriShield?

VeriShield is a **production-grade KYC (Know Your Customer) verification platform** that detects document forgery and deepfake identity fraud. Banks and fintechs are legally required to perform KYC verification — VeriShield automates this using state-of-the-art computer vision models.

> 💡 Deepfake attacks grew 2,000% in 3 years. The FBI recorded $16.6B in internet crime losses in 2024. VeriShield addresses both document forgery and deepfake identity fraud in a single platform.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      VeriShield AI                           │
├──────────────────────┬──────────────────────────────────────┤
│   MODEL HEAD 1       │         MODEL HEAD 2                  │
│   EfficientNet-B0    │     EfficientNet-B0 (Face)            │
│   Document Forgery   │     Deepfake Detection                │
│   Detection          │     Trained on 140K faces             │
│   Noise + Edge       │     98.65% Accuracy                   │
│   Analysis           │                                       │
├──────────────────────┴──────────────────────────────────────┤
│                    FastAPI Backend (Railway)                  │
│         /verify-document  /verify-face  /kyc-complete        │
├─────────────────────────────────────────────────────────────┤
│              PostgreSQL Audit Trail (Supabase)               │
│         Every verification logged with full metadata         │
├─────────────────────────────────────────────────────────────┤
│              Streamlit Dashboard (6 Pages)                   │
│  KYC Portal │ Audit Trail │ Analytics │ Batch │ Reports │ Models │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

| Feature | Description | Tech |
|---------|-------------|------|
| 🪪 **Full KYC Verification** | Document + face + match check in one API call | FastAPI |
| 📄 **Document Forgery Detection** | Noise artifacts + edge inconsistency + model scoring | EfficientNet + OpenCV |
| 🧬 **Deepfake Detection** | Texture + frequency analysis + trained classifier | EfficientNet-B0 |
| 🔍 **Face Matching** | ID photo vs selfie similarity scoring | OpenCV histogram |
| 📋 **Audit Trail** | Every verification logged permanently | PostgreSQL (Supabase) |
| 📦 **Batch Processing** | Screen multiple documents/faces at once | FastAPI + Streamlit |
| 📊 **Analytics Dashboard** | Real-time charts from verification data | Plotly |
| 📋 **Compliance Reports** | Auto-generate GDPR Article 22 PDF reports | FPDF2 |
| 🧠 **Model Performance** | EfficientNet vs ResNet vs VGG comparison | Plotly |
| 🐳 **Docker** | Fully containerized with docker-compose | Docker |

---

## 🚀 Quick Start

### Option 1 — Docker
```bash
git clone https://github.com/varunsajinair/verishield-kyc
cd verishield-kyc
cp .env.example .env
# Fill in your credentials
docker-compose up
```

### Option 2 — Local Setup
```bash
git clone https://github.com/varunsajinair/verishield-kyc
cd verishield-kyc

pip install -r requirements.txt

# Terminal 1 — Run API
uvicorn src.app:app --reload --port 8000

# Terminal 2 — Run Dashboard
cd dashboard
streamlit run dashboard.py
```

---

## 🧠 Model Performance

| Model | Accuracy | F1 Score | AUC-ROC | Inference |
|-------|----------|----------|---------|-----------|
| **EfficientNet-B0 (VeriShield)** ⭐ | **98.65%** | **98.0%** | **99.1%** | 650ms |
| ResNet-50 | 94.2% | 92.9% | 96.3% | 450ms |
| VGG-16 | 91.5% | 89.9% | 94.1% | 820ms |
| MobileNet-V2 | 89.3% | 88.0% | 92.5% | 280ms |

> Trained on **140,000 real and AI-generated faces** from the IEEE Real vs Fake dataset.

---

## 📡 API Reference

**Base URL:** `https://verishield-kyc-production.up.railway.app`

### POST `/verify-document`
```bash
curl -X POST "https://verishield-kyc-production.up.railway.app/verify-document" \
  -F "file=@id_card.jpg"
```

**Response:**
```json
{
  "verification_id": "a1b2c3d4",
  "result": "AUTHENTIC",
  "confidence": 0.92,
  "risk_score": 0.08,
  "alert_level": "LOW RISK",
  "tampered_regions": ["No tampering detected"],
  "processing_time_ms": 1200
}
```

### POST `/verify-face`
```bash
curl -X POST "https://verishield-kyc-production.up.railway.app/verify-face" \
  -F "file=@selfie.jpg"
```

### POST `/kyc-complete`
```bash
curl -X POST "https://verishield-kyc-production.up.railway.app/kyc-complete" \
  -F "document=@id_card.jpg" \
  -F "selfie=@selfie.jpg"
```

### GET `/health`
```json
{
  "status": "healthy",
  "models": ["ViT-Document", "EfficientNet-Face"],
  "database": "PostgreSQL (Supabase)"
}
```

---

## 🏦 Real-World Impact

- Banks must perform KYC under **AML/BSA regulations**
- FinCEN issued **FIN-2024-DEEPFAKEFRAUD** requiring banks to detect deepfakes in KYC
- Deepfake attacks grew **2,000%** in 3 years
- VeriShield automates document forgery + deepfake detection + compliance reporting

---

## 🗂️ Project Structure

```
verishield-kyc/
├── src/
│   ├── app.py                  ← FastAPI application
│   ├── document_model.py       ← Document forgery detection
│   ├── face_model.py           ← Deepfake detection
│   ├── face_match.py           ← Face similarity matching
│   └── database.py             ← PostgreSQL logging
├── dashboard/
│   ├── dashboard.py            ← Main Streamlit app
│   ├── db_utils.py             ← Database utilities
│   ├── .streamlit/
│   │   ├── config.toml         ← Dark theme config
│   │   └── secrets.toml        ← Local secrets (gitignored)
│   └── pages/
│       ├── 01_KYC_Verification.py
│       ├── 02_Audit_Trail.py
│       ├── 03_Analytics.py
│       ├── 04_Batch_Verification.py
│       ├── 05_Compliance_Report.py
│       └── 06_Model_Performance.py
├── models/                     ← Trained model files
├── screenshots/                ← Dashboard screenshots
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── Procfile
```

---

## 🔧 Environment Variables

```env
DB_HOST=your_supabase_host
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password
```

---

## 🌐 Deployment

| Service | Platform | URL |
|---------|----------|-----|
| FastAPI Backend | Railway | https://verishield-kyc-production.up.railway.app |
| Streamlit Dashboard | Streamlit Cloud | https://verishield-kyc-varunsajinair.streamlit.app |
| Audit Database | Supabase PostgreSQL | kyc_verifications table |

---

## 💼 Resume Line

> Built VeriShield — production-grade KYC identity verification platform using EfficientNet-B0 trained on 140K real/fake faces (98.65% accuracy). Features real-time document forgery detection, deepfake liveness analysis, face matching, PostgreSQL audit trail, batch processing, GDPR-compliant PDF compliance reports, and model performance dashboard. Deployed on Railway + Streamlit Cloud with Supabase as audit database. Containerized with Docker.

---

## 🙏 Acknowledgements

- 140K Real and Fake Faces Dataset (Kaggle/IEEE)
- EfficientNet architecture (Google Brain)
- Streamlit for dashboard framework
- Supabase for PostgreSQL hosting
- Railway for API deployment

---

<div align="center">

**Built with ❤️ by Varun Sajinair**

⭐ Star this repo if you found it useful!

</div>