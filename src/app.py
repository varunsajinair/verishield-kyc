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

from src.document_model import predict_document
from src.face_model import predict_face
from src.face_match import match_faces
from src.database import log_verification

load_dotenv()

app = FastAPI(
    title="VeriShield AI",
    description="KYC Document Forgery & Deepfake Identity Detector",
    version="1.0.0"
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
        "version": "1.0.0",
        "description": "KYC Document Forgery & Deepfake Identity Detector"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "models": ["ViT-Document", "EfficientNet-Face"],
        "database": "PostgreSQL (Supabase)"
    }

@app.post("/verify-document")
async def verify_document(file: UploadFile = File(...)):
    start_time = time.time()
    
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    result = predict_document(image)
    processing_time = (time.time() - start_time) * 1000
    
    return {
        "verification_id": str(uuid.uuid4())[:8],
        "type": "document",
        "result": result["result"],
        "confidence": result["confidence"],
        "tampered_regions": result["tampered_regions"],
        "risk_score": result["risk_score"],
        "alert_level": result["alert_level"],
        "processing_time_ms": round(processing_time, 2)
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
    
    # Run all three checks
    doc_result = predict_document(doc_image)
    face_result = predict_face(selfie_image)
    match_result = match_faces(doc_image, selfie_image)
    
    # Calculate overall risk
    risk_scores = [
        doc_result["risk_score"],
        face_result["risk_score"],
        1.0 - match_result["similarity_score"]
    ]
    overall_risk = np.mean(risk_scores)
    
    if overall_risk > 0.7:
        overall_result = "REJECTED"
        alert_level = "CRITICAL"
    elif overall_risk > 0.4:
        overall_result = "REVIEW"
        alert_level = "HIGH RISK"
    else:
        overall_result = "APPROVED"
        alert_level = "LOW RISK"
    
    processing_time = (time.time() - start_time) * 1000
    
    # Log to Supabase
    log_verification({
        "verification_id": verification_id,
        "document_result": doc_result["result"],
        "document_confidence": doc_result["confidence"],
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
        "document_check": {
            "result": doc_result["result"],
            "confidence": doc_result["confidence"],
            "risk_score": doc_result["risk_score"]
        },
        "face_check": {
            "result": face_result["result"],
            "confidence": face_result["confidence"],
            "deepfake_probability": face_result["deepfake_probability"]
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