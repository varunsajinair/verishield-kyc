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
    valid_ratios = [1.586, 0.707, 1.4, 1.35, 1.0, 1.5]
    min_diff = min(abs(ratio - r) for r in valid_ratios)
    return float(max(0, 1.0 - min_diff))

def check_metadata(image: Image.Image) -> dict:
    """
    Most reliable check — EXIF metadata tells exactly 
    what software created/edited the image
    """
    try:
        exif = image._getexif()
        
        if exif is None:
            # No EXIF at all — likely screenshot or web download
            return {
                'has_exif': False,
                'is_camera': False,
                'is_edited': False,
                'software': 'Unknown',
                'finding': '⚠️ No metadata found — could be screenshot or web image',
                'risk': 0.15
            }

        software_tag = 305  # Software
        make_tag = 271      # Camera Make
        model_tag = 272     # Camera Model

        software = str(exif.get(software_tag, '')).strip()
        camera_make = str(exif.get(make_tag, '')).strip()
        camera_model = str(exif.get(model_tag, '')).strip()

        # Known editing software
        editing_software = [
            'photoshop', 'gimp', 'paint', 'pixlr', 'canva',
            'lightroom', 'affinity', 'illustrator', 'inkscape',
            'snapseed', 'picsart', 'vsco', 'facetune',
            'microsoft photo', 'windows photo', 'paint.net',
            'corel', 'phixr', 'fotor', 'befunky'
        ]

        # Known camera manufacturers
        camera_makes = [
            'apple', 'samsung', 'google', 'huawei', 'xiaomi',
            'canon', 'nikon', 'sony', 'fujifilm', 'olympus',
            'panasonic', 'leica', 'hasselblad', 'oneplus',
            'motorola', 'lg', 'oppo', 'vivo', 'realme'
        ]

        software_lower = software.lower()
        make_lower = camera_make.lower()

        is_edited = any(s in software_lower for s in editing_software)
        is_camera = any(m in make_lower for m in camera_makes)

        if is_edited:
            return {
                'has_exif': True,
                'is_camera': False,
                'is_edited': True,
                'software': software,
                'finding': f'🚨 Edited with {software} — document may be tampered!',
                'risk': 0.65
            }
        elif is_camera:
            return {
                'has_exif': True,
                'is_camera': True,
                'is_edited': False,
                'software': f'{camera_make} {camera_model}',
                'finding': f'✅ Original photo from {camera_make} camera',
                'risk': 0.0
            }
        elif software:
            # Has software tag but not recognized
            return {
                'has_exif': True,
                'is_camera': False,
                'is_edited': False,
                'software': software,
                'finding': f'⚠️ Created by: {software}',
                'risk': 0.10
            }
        else:
            return {
                'has_exif': True,
                'is_camera': False,
                'is_edited': False,
                'software': 'Unknown',
                'finding': '⚠️ Metadata present but no software info',
                'risk': 0.10
            }

    except Exception as e:
        return {
            'has_exif': False,
            'is_camera': False,
            'is_edited': False,
            'software': 'Error',
            'finding': '⚠️ Could not read metadata',
            'risk': 0.10
        }

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
        metadata = check_metadata(image)

        risk_score = 0.0
        findings = []

        # METADATA — most reliable signal
        findings.append(metadata['finding'])
        risk_score += metadata['risk']

        # Face check
        if has_face:
            findings.append(f"✅ Face photo detected ({face_count} face(s) found)")
        else:
            findings.append("⚠️ No face photo detected — may not be a valid ID document")
            risk_score += 0.20

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
            risk_score += 0.15

        # Aspect ratio
        if ratio_score > 0.4:
            findings.append(f"✅ Aspect ratio matches standard ID format")
        else:
            findings.append("⚠️ Non-standard dimensions — may not be an ID")
            risk_score += 0.10

        # Resolution
        if resolution_score > 0.2:
            findings.append(f"✅ Resolution sufficient for verification")
        else:
            findings.append("⚠️ Low resolution")
            risk_score += 0.10

        risk_score = min(risk_score, 1.0)

        if risk_score > 0.55:
            result = "FORGED"
            alert_level = "CRITICAL" if risk_score > 0.75 else "HIGH RISK"
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
            "ratio_score": round(ratio_score, 4),
            "resolution_score": round(resolution_score, 4),
            "metadata_software": metadata.get('software', 'Unknown'),
            "is_edited": metadata.get('is_edited', False),
            "is_camera": metadata.get('is_camera', False)
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
            "resolution_score": 0.0,
            "metadata_software": "Error",
            "is_edited": False,
            "is_camera": False
        }