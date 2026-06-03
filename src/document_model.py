from PIL import Image
import numpy as np
import cv2
import io
import os

def check_face_presence(img_array: np.ndarray) -> tuple:
    """Check if document contains a face photo"""
    try:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        return len(faces) > 0, len(faces)
    except:
        return False, 0

def check_image_quality(img_array: np.ndarray) -> float:
    """Check if image is clear enough to be a valid document"""
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    # Higher variance = sharper image
    quality_score = min(laplacian_var / 500.0, 1.0)
    return float(quality_score)

def check_text_density(img_array: np.ndarray) -> float:
    """Check if document has sufficient text regions"""
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    # Use edge detection to find text-like regions
    edges = cv2.Canny(gray, 50, 150)
    text_density = np.sum(edges > 0) / edges.size
    return float(text_density)

def check_aspect_ratio(image: Image.Image) -> float:
    """Check if image has valid ID document aspect ratio"""
    w, h = image.size
    ratio = w / h if h > 0 else 0

    # Standard ID ratios: credit card 1.586, passport 0.707, driving license ~1.4
    valid_ratios = [1.586, 0.707, 1.4, 1.0]
    min_diff = min(abs(ratio - r) for r in valid_ratios)

    # Score: closer to standard ratio = more likely a real document
    ratio_score = max(0, 1.0 - min_diff / 1.0)
    return float(ratio_score)

def check_metadata(image: Image.Image) -> dict:
    """Check image metadata for camera authenticity"""
    try:
        exif = image._getexif()
        if exif is None:
            return {'has_exif': False, 'is_camera': False}

        # Camera make/model tags
        make_tag = 271
        model_tag = 272
        software_tag = 305

        has_camera = make_tag in exif or model_tag in exif
        software = str(exif.get(software_tag, '')).lower()
        editing_software = ['photoshop', 'gimp', 'paint', 'pixlr', 'canva']
        is_edited = any(s in software for s in editing_software)

        return {
            'has_exif': True,
            'is_camera': has_camera,
            'is_edited': is_edited
        }
    except:
        return {'has_exif': False, 'is_camera': False, 'is_edited': False}

def check_resolution(image: Image.Image) -> float:
    """Check if resolution is sufficient for a valid document"""
    w, h = image.size
    total_pixels = w * h
    # Minimum 100K pixels for a readable document
    resolution_score = min(total_pixels / 500000, 1.0)
    return float(resolution_score)

def predict_document(image: Image.Image) -> dict:
    try:
        img_array = np.array(image.convert('RGB'))
        img_resized = cv2.resize(img_array, (512, 512))

        # Run all checks
        has_face, face_count = check_face_presence(img_resized)
        quality_score = check_image_quality(img_resized)
        text_density = check_text_density(img_resized)
        ratio_score = check_aspect_ratio(image)
        metadata = check_metadata(image)
        resolution_score = check_resolution(image)

        # Build findings and risk score
        findings = []
        risk_score = 0.0

        # Quality check
        if quality_score < 0.3:
            findings.append(f"⚠️ Low image quality — document may be blurry ({quality_score:.0%})")
            risk_score += 0.25
        else:
            findings.append(f"✅ Image quality acceptable ({quality_score:.0%})")

        # Face check
        if has_face:
            findings.append(f"✅ Face photo detected ({face_count} face(s) found)")
        else:
            findings.append("⚠️ No face photo detected — may not be a valid ID document")
            risk_score += 0.20

        # Text density
        if text_density > 0.05:
            findings.append(f"✅ Text regions detected ({text_density:.0%} density)")
        else:
            findings.append("⚠️ Insufficient text — document may be invalid")
            risk_score += 0.15

        # Aspect ratio
        if ratio_score > 0.5:
            findings.append(f"✅ Aspect ratio matches standard ID format")
        else:
            findings.append("⚠️ Non-standard dimensions — may not be an ID document")
            risk_score += 0.15

        # Resolution
        if resolution_score > 0.3:
            findings.append(f"✅ Resolution sufficient for verification")
        else:
            findings.append("⚠️ Low resolution — document may be invalid")
            risk_score += 0.10

        # Metadata
        if metadata.get('is_edited'):
            findings.append("🚨 Editing software detected in metadata — document may be tampered")
            risk_score += 0.40
        elif metadata.get('is_camera'):
            findings.append("✅ Camera metadata present — likely original photo")
        elif not metadata.get('has_exif'):
            findings.append("⚠️ No camera metadata — could be screenshot or digital copy")
            risk_score += 0.15

        risk_score = min(risk_score, 1.0)

        # Determine result
        if risk_score > 0.55:
            result = "SUSPICIOUS"
            alert_level = "HIGH RISK"
        elif risk_score > 0.30:
            result = "SUSPICIOUS"
            alert_level = "MEDIUM RISK"
        else:
            result = "AUTHENTIC"
            alert_level = "LOW RISK"

        return {
            "result": result,
            "confidence": round(1 - risk_score, 4),
            "forgery_probability": round(risk_score, 4),
            "real_probability": round(1 - risk_score, 4),
            "risk_score": round(risk_score, 4),
            "alert_level": alert_level,
            "tampered_regions": findings,
            "face_detected": has_face,
            "face_count": face_count,
            "quality_score": round(quality_score, 4),
            "text_density": round(text_density, 4),
            "ratio_score": round(ratio_score, 4),
            "resolution_score": round(resolution_score, 4)
        }

    except Exception as e:
        print(f"Document model error: {e}")
        return {
            "result": "ERROR",
            "confidence": 0.0,
            "forgery_probability": 0.0,
            "real_probability": 0.0,
            "risk_score": 0.0,
            "alert_level": "UNKNOWN",
            "tampered_regions": [f"Processing error: {str(e)}"],
            "face_detected": False,
            "face_count": 0,
            "quality_score": 0.0,
            "text_density": 0.0,
            "ratio_score": 0.0,
            "resolution_score": 0.0
        }