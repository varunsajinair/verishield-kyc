from PIL import Image
import numpy as np
import cv2
import io
import os

def check_face_presence(img_array: np.ndarray) -> tuple:
    try:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        return len(faces) > 0, len(faces)
    except:
        return False, 0

def check_image_quality(img_array: np.ndarray) -> float:
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return float(min(laplacian_var / 500.0, 1.0))

def check_text_density(img_array: np.ndarray) -> float:
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    return float(np.sum(edges > 0) / edges.size)

def check_resolution(image: Image.Image) -> float:
    w, h = image.size
    return float(min(w * h / 500000, 1.0))

def check_aspect_ratio(image: Image.Image) -> float:
    w, h = image.size
    ratio = w / h if h > 0 else 0
    valid_ratios = [1.586, 0.707, 1.4, 1.35, 1.0]
    min_diff = min(abs(ratio - r) for r in valid_ratios)
    return float(max(0, 1.0 - min_diff))

def check_color_distribution(img_array: np.ndarray) -> dict:
    """
    ID documents have specific color patterns:
    - Usually light background (white/cream/blue)
    - High contrast between text and background
    - Specific color temperature
    """
    # Check if background is predominantly light colored
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    mean_brightness = np.mean(gray)
    contrast = np.std(gray)

    # ID documents: bright background (>100) and good contrast (>30)
    is_light_bg = mean_brightness > 100
    has_contrast = contrast > 30

    return {
        'is_light_bg': is_light_bg,
        'has_contrast': has_contrast,
        'brightness': float(mean_brightness),
        'contrast': float(contrast)
    }

def check_mrz_region(img_array: np.ndarray) -> float:
    """
    Check for MRZ (Machine Readable Zone) at bottom of document.
    Passports and ID cards have MRZ with specific pattern.
    """
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape

    # MRZ is at bottom 20% of document
    bottom_region = gray[int(h*0.75):, :]

    # MRZ has high density of characters — high edge density
    edges = cv2.Canny(bottom_region, 50, 150)
    mrz_density = np.sum(edges > 0) / edges.size

    # Check for horizontal lines pattern (MRZ rows)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    horizontal_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel)
    line_score = np.sum(horizontal_lines > 0) / horizontal_lines.size

    mrz_score = min((mrz_density * 2 + line_score * 5), 1.0)
    return float(mrz_score)

def check_metadata(image: Image.Image) -> dict:
    try:
        exif = image._getexif()
        if exif is None:
            return {'has_exif': False, 'is_camera': False, 'is_edited': False}
        software_tag = 305
        make_tag = 271
        has_camera = make_tag in exif
        software = str(exif.get(software_tag, '')).lower()
        editing_sw = ['photoshop', 'gimp', 'paint', 'pixlr', 'canva', 'lightroom']
        is_edited = any(s in software for s in editing_sw)
        return {'has_exif': True, 'is_camera': has_camera, 'is_edited': is_edited}
    except:
        return {'has_exif': False, 'is_camera': False, 'is_edited': False}

def predict_document(image: Image.Image) -> dict:
    try:
        img_array = np.array(image.convert('RGB'))
        img_resized = cv2.resize(img_array, (512, 512))

        # Run all checks
        has_face, face_count = check_face_presence(img_resized)
        quality_score = check_image_quality(img_resized)
        text_density = check_text_density(img_resized)
        resolution_score = check_resolution(image)
        ratio_score = check_aspect_ratio(image)
        color_info = check_color_distribution(img_resized)
        mrz_score = check_mrz_region(img_resized)
        metadata = check_metadata(image)

        risk_score = 0.0
        findings = []

        # Face check — ID must have face
        if has_face:
            findings.append(f"✅ Face photo detected ({face_count} face(s) found)")
        else:
            findings.append("⚠️ No face photo detected — may not be a valid ID")
            risk_score += 0.25

        # Quality check
        if quality_score > 0.3:
            findings.append(f"✅ Image quality acceptable ({quality_score:.0%})")
        else:
            findings.append(f"⚠️ Low image quality — document may be blurry")
            risk_score += 0.15

        # Text density
        if text_density > 0.05:
            findings.append(f"✅ Text regions detected ({text_density:.0%} density)")
        else:
            findings.append("⚠️ Insufficient text for a valid ID document")
            risk_score += 0.20

        # Aspect ratio
        if ratio_score > 0.4:
            findings.append(f"✅ Aspect ratio matches standard ID format")
        else:
            findings.append("⚠️ Non-standard dimensions — may not be an ID")
            risk_score += 0.15

        # Color/background
        if color_info['is_light_bg'] and color_info['has_contrast']:
            findings.append(f"✅ Document color profile normal")
        else:
            findings.append("⚠️ Unusual color profile for an ID document")
            risk_score += 0.10

        # MRZ check
        if mrz_score > 0.1:
            findings.append(f"✅ Machine Readable Zone (MRZ) detected")
        else:
            findings.append("ℹ️ No MRZ detected — may be non-standard document")

        # Resolution
        if resolution_score > 0.2:
            findings.append(f"✅ Resolution sufficient for verification")
        else:
            findings.append("⚠️ Low resolution — document may be invalid")
            risk_score += 0.10

        # Metadata
        if metadata.get('is_edited'):
            findings.append("🚨 Editing software detected in metadata!")
            risk_score += 0.40
        elif metadata.get('is_camera'):
            findings.append("✅ Camera metadata present — likely original photo")
        elif not metadata.get('has_exif'):
            findings.append("⚠️ No camera metadata — could be screenshot")
            risk_score += 0.10

        risk_score = min(risk_score, 1.0)

        if risk_score > 0.55:
            result = "INVALID"
            alert_level = "HIGH RISK"
        elif risk_score > 0.25:
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
            "mrz_score": round(mrz_score, 4),
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
            "mrz_score": 0.0,
            "ratio_score": 0.0,
            "resolution_score": 0.0
        }