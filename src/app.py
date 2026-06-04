from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import uuid
import time
import os
from datetime import datetime
from PIL import Image
import io
import numpy as np
from dotenv import load_dotenv

from src.face_model import predict_face
from src.face_match import match_faces
from src.database import log_verification

load_dotenv()

app = FastAPI(
    title="VeriShield AI",
    description="KYC Deepfake Identity Detector",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
def root():
    return {
        "name": "VeriShield AI",
        "version": "2.0.0",
        "description": "KYC Deepfake Identity Detector"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "models": ["EfficientNet-Deepfake"],
        "database": "PostgreSQL (Supabase)"
    }

@app.post("/verify-face")
async def verify_face(file: UploadFile = File(...)):
    start_time = time.time()
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    result = predict_face(image)
    processing_time = (time.time() - start_time) * 1000

    return {
        "verification_id": str(uuid.uuid4())[:8],
        "type": "face",
        "result": result["result"],
        "confidence": result["confidence"],
        "deepfake_probability": result["deepfake_probability"],
        "liveness_score": result["liveness_score"],
        "alert_level": result["alert_level"],
        "processing_time_ms": round(processing_time, 2)
    }

@app.post("/kyc-complete")
async def kyc_complete(
    document: UploadFile = File(...),
    selfie: UploadFile = File(...)
):
    start_time = time.time()
    verification_id = str(uuid.uuid4())[:12]

    try:
        doc_contents = await document.read()
        doc_image = Image.open(io.BytesIO(doc_contents)).convert("RGB")

        selfie_contents = await selfie.read()
        selfie_image = Image.open(io.BytesIO(selfie_contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image files")

    # Run face check on selfie + face match
    face_result = predict_face(selfie_image)
    match_result = match_faces(doc_image, selfie_image)

    face_is_real = face_result["result"] == "AUTHENTIC"
    face_is_suspicious = face_result["result"] == "SUSPICIOUS"
    face_is_deepfake = face_result["result"] == "DEEPFAKE"

    match_is_good = match_result["result"] == "MATCH"
    match_is_possible = match_result["result"] == "POSSIBLE MATCH"
    match_is_bad = match_result["result"] == "NO MATCH"

    # KYC Decision Logic:
    # APPROVED = face matches document (real or deepfake warning)
    # REJECTED = deepfake detected OR face does not match
    # REVIEW = possible match

    if face_is_deepfake:
        # Deepfake always rejected regardless of match
        overall_result = "REJECTED"
        alert_level = "CRITICAL"
        overall_risk = 0.95
    elif match_is_bad:
        # No face match = rejected
        overall_result = "REJECTED"
        alert_level = "HIGH RISK"
        overall_risk = 0.85
    elif match_is_good and face_is_real:
        # Perfect — real face + match
        overall_result = "APPROVED"
        alert_level = "LOW RISK"
        overall_risk = 0.05
    elif match_is_good and face_is_suspicious:
        # Face matches but suspicious — needs review
        overall_result = "REVIEW"
        alert_level = "MEDIUM RISK"
        overall_risk = 0.45
    elif match_is_possible and face_is_real:
        # Real face but uncertain match — review
        overall_result = "REVIEW"
        alert_level = "MEDIUM RISK"
        overall_risk = 0.40
    elif match_is_possible and face_is_suspicious:
        # Suspicious face + uncertain match — high risk review
        overall_result = "REVIEW"
        alert_level = "HIGH RISK"
        overall_risk = 0.65
    else:
        overall_result = "REVIEW"
        alert_level = "MEDIUM RISK"
        overall_risk = 0.50

    processing_time = (time.time() - start_time) * 1000

    log_verification({
        "verification_id": verification_id,
        "document_result": "N/A",
        "document_confidence": 0.0,
        "face_result": face_result["result"],
        "face_confidence": face_result["confidence"],
        "match_result": match_result["result"],
        "match_score": match_result["similarity_score"],
        "overall_result": overall_result,
        "overall_risk_score": overall_risk,
        "alert_level": alert_level,
        "processing_time_ms": processing_time
    })

    return {
        "verification_id": verification_id,
        "timestamp": datetime.now().isoformat(),
        "face_check": {
            "result": face_result["result"],
            "confidence": face_result["confidence"],
            "deepfake_probability": face_result["deepfake_probability"],
            "liveness_score": face_result["liveness_score"]
        },
        "match_check": {
            "result": match_result["result"],
            "similarity_score": match_result["similarity_score"]
        },
        "overall_result": overall_result,
        "overall_risk_score": round(float(overall_risk), 4),
        "alert_level": alert_level,
        "processing_time_ms": round(processing_time, 2)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)