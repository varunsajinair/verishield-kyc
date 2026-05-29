import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import numpy as np

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

def load_model():
    model = models.efficientnet_b4(pretrained=True)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, 2)
    model.eval()
    return model

_model = None

def get_model():
    global _model
    if _model is None:
        _model = load_model()
    return _model

def predict_face(image: Image.Image) -> dict:
    try:
        model = get_model()
        tensor = transform(image).unsqueeze(0)

        with torch.no_grad():
            outputs = model(tensor)
            probs = torch.softmax(outputs, dim=1)
            deepfake_prob = float(probs[0][1])
            real_prob = float(probs[0][0])

        # Additional heuristics
        img_array = np.array(image)
        texture_score = detect_texture_artifacts(img_array)
        frequency_score = detect_frequency_artifacts(img_array)

        # Combined deepfake score
        combined_score = (deepfake_prob * 0.5 + texture_score * 0.3 + frequency_score * 0.2)

        # Liveness score (inverse of deepfake)
        liveness_score = round(1.0 - combined_score, 4)

        if combined_score > 0.65:
            result = "DEEPFAKE"
            alert_level = "CRITICAL" if combined_score > 0.85 else "HIGH RISK"
        elif combined_score > 0.4:
            result = "SUSPICIOUS"
            alert_level = "MEDIUM RISK"
        else:
            result = "AUTHENTIC"
            alert_level = "LOW RISK"

        return {
            "result": result,
            "confidence": round(combined_score if result != "AUTHENTIC" else real_prob, 4),
            "deepfake_probability": round(combined_score, 4),
            "real_probability": round(1 - combined_score, 4),
            "liveness_score": liveness_score,
            "risk_score": round(combined_score, 4),
            "alert_level": alert_level,
            "texture_score": round(texture_score, 4),
            "frequency_score": round(frequency_score, 4)
        }

    except Exception as e:
        print(f"Face model error: {e}")
        return {
            "result": "ERROR",
            "confidence": 0.0,
            "deepfake_probability": 0.0,
            "real_probability": 0.0,
            "liveness_score": 0.0,
            "risk_score": 0.0,
            "alert_level": "UNKNOWN",
            "texture_score": 0.0,
            "frequency_score": 0.0
        }

def detect_texture_artifacts(img_array: np.ndarray) -> float:
    """Detect unnatural texture patterns common in GAN-generated faces"""
    import cv2
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY).astype(np.float32)

    # Local Binary Pattern-like texture analysis
    kernel = np.array([[-1,-1,-1],[-1,8,-1],[-1,-1,-1]], dtype=np.float32)
    filtered = cv2.filter2D(gray, -1, kernel)
    texture_var = np.var(filtered)

    # Normalize
    texture_score = 1.0 - min(texture_var / 10000, 1.0)
    return float(texture_score)

def detect_frequency_artifacts(img_array: np.ndarray) -> float:
    """Detect frequency domain artifacts from GAN upsampling"""
    import cv2
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY).astype(np.float32)

    # FFT analysis
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    magnitude = np.abs(fshift)

    # Check for periodic patterns in high frequency
    h, w = magnitude.shape
    center_h, center_w = h // 2, w // 2
    high_freq = magnitude.copy()
    high_freq[center_h-20:center_h+20, center_w-20:center_w+20] = 0

    high_freq_energy = np.sum(high_freq) / (np.sum(magnitude) + 1e-6)
    frequency_score = min(high_freq_energy * 2, 1.0)

    return float(frequency_score)