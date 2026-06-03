from PIL import Image
import numpy as np
import cv2
import torch
from transformers import CLIPProcessor, CLIPModel

# Load CLIP model — zero shot document classifier
_clip_model = None
_clip_processor = None

def get_clip():
    global _clip_model, _clip_processor
    if _clip_model is None:
        print("Loading CLIP model...")
        _clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        _clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        _clip_model.eval()
        print("✅ CLIP model loaded!")
    return _clip_model, _clip_processor

def classify_document_clip(image: Image.Image) -> dict:
    """
    Zero-shot document classification using CLIP.
    No training needed — uses OpenAI's pretrained vision-language model.
    """
    model, processor = get_clip()

    # Text descriptions for classification
    text_labels = [
        "a passport or identity document with text and photo",
        "a national ID card or driving license",
        "a random photo or selfie of a person",
        "a landscape or nature photo",
        "a screenshot or digital image",
        "a document with official text and stamps",
    ]

    inputs = processor(
        text=text_labels,
        images=image,
        return_tensors="pt",
        padding=True
    )

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits_per_image
        probs = logits.softmax(dim=1)[0]

    results = {label: float(prob) for label, prob in zip(text_labels, probs)}

    # Document probability = passport + ID card + official document
    doc_prob = (
        float(probs[0]) +  # passport
        float(probs[1]) +  # ID card
        float(probs[5])    # official document
    )

    # Non-document probability
    non_doc_prob = (
        float(probs[2]) +  # random photo
        float(probs[3]) +  # landscape
        float(probs[4])    # screenshot
    )

    return {
        'document_probability': min(doc_prob, 1.0),
        'non_document_probability': min(non_doc_prob, 1.0),
        'top_label': max(results, key=results.get),
        'scores': results
    }

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

def predict_document(image: Image.Image) -> dict:
    try:
        img_array = np.array(image.convert('RGB'))
        img_resized = cv2.resize(img_array, (512, 512))

        # CLIP zero-shot classification
        clip_result = classify_document_clip(image)
        doc_prob = clip_result['document_probability']
        non_doc_prob = clip_result['non_document_probability']
        top_label = clip_result['top_label']

        # Supporting checks
        has_face, face_count = check_face_presence(img_resized)
        quality_score = check_image_quality(img_resized)
        text_density = check_text_density(img_resized)
        resolution_score = check_resolution(image)

        # Final risk score — CLIP is primary signal
        risk_score = 0.0
        findings = []

        # CLIP document check — most important
        if doc_prob > 0.5:
            findings.append(f"✅ CLIP: Image classified as identity document ({doc_prob:.0%} confidence)")
        elif doc_prob > 0.25:
            findings.append(f"⚠️ CLIP: Uncertain if identity document ({doc_prob:.0%} confidence)")
            risk_score += 0.3
        else:
            findings.append(f"🚨 CLIP: Not an identity document ({non_doc_prob:.0%} non-document confidence)")
            risk_score += 0.55

        # Supporting checks
        if has_face:
            findings.append(f"✅ Face photo detected ({face_count} face(s))")
        else:
            findings.append("⚠️ No face photo detected")
            risk_score += 0.15

        if quality_score > 0.3:
            findings.append(f"✅ Image quality acceptable ({quality_score:.0%})")
        else:
            findings.append(f"⚠️ Low image quality ({quality_score:.0%})")
            risk_score += 0.10

        if text_density > 0.05:
            findings.append(f"✅ Text regions detected ({text_density:.0%} density)")
        else:
            findings.append("⚠️ Low text density")
            risk_score += 0.10

        if resolution_score > 0.2:
            findings.append(f"✅ Resolution sufficient")
        else:
            findings.append("⚠️ Low resolution")
            risk_score += 0.10

        risk_score = min(risk_score, 1.0)

        if risk_score > 0.5:
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
            "clip_doc_probability": round(doc_prob, 4),
            "top_label": top_label,
            "face_detected": has_face,
            "quality_score": round(quality_score, 4),
            "text_density": round(text_density, 4),
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
            "quality_score": 0.0,
            "text_density": 0.0,
        }