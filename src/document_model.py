import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import numpy as np
import os

# Use a pretrained EfficientNet as document forgery detector
# Fine-tuned behavior simulated with domain-specific rules + model confidence

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# Load pretrained EfficientNet-B0 as backbone
def load_model():
    model = models.efficientnet_b0(pretrained=True)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, 2)
    model.eval()
    return model

_model = None

def get_model():
    global _model
    if _model is None:
        _model = load_model()
    return _model

def predict_document(image: Image.Image) -> dict:
    try:
        model = get_model()
        tensor = transform(image).unsqueeze(0)
        
        with torch.no_grad():
            outputs = model(tensor)
            probs = torch.softmax(outputs, dim=1)
            forgery_prob = float(probs[0][1])
            real_prob = float(probs[0][0])
        
        # Domain-specific heuristics for document analysis
        img_array = np.array(image)
        
        # Check for noise patterns (forgery artifacts)
        noise_score = detect_noise_artifacts(img_array)
        
        # Check for edge inconsistencies
        edge_score = detect_edge_inconsistencies(img_array)
        
        # Combined score
        combined_score = (forgery_prob * 0.5 + noise_score * 0.3 + edge_score * 0.2)
        
        if combined_score > 0.6:
            result = "FORGED"
            alert_level = "CRITICAL" if combined_score > 0.8 else "HIGH RISK"
        elif combined_score > 0.35:
            result = "SUSPICIOUS"
            alert_level = "MEDIUM RISK"
        else:
            result = "AUTHENTIC"
            alert_level = "LOW RISK"
        
        # Identify tampered regions
        tampered_regions = []
        if noise_score > 0.5:
            tampered_regions.append("High noise artifacts detected")
        if edge_score > 0.5:
            tampered_regions.append("Edge inconsistencies detected")
        if forgery_prob > 0.5:
            tampered_regions.append("Model detected manipulation patterns")
        if not tampered_regions:
            tampered_regions.append("No tampering detected")
        
        return {
            "result": result,
            "confidence": round(combined_score if result != "AUTHENTIC" else real_prob, 4),
            "forgery_probability": round(combined_score, 4),
            "real_probability": round(1 - combined_score, 4),
            "risk_score": round(combined_score, 4),
            "alert_level": alert_level,
            "tampered_regions": tampered_regions,
            "noise_score": round(noise_score, 4),
            "edge_score": round(edge_score, 4)
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
            "tampered_regions": ["Processing error"],
            "noise_score": 0.0,
            "edge_score": 0.0
        }

def detect_noise_artifacts(img_array: np.ndarray) -> float:
    """Detect unusual noise patterns that indicate image manipulation"""
    import cv2
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY).astype(np.float32)
    
    # Laplacian noise detection
    laplacian = cv2.Laplacian(gray, cv2.CV_32F)
    noise_var = np.var(laplacian)
    
    # Normalize to 0-1 (high variance = more noise = more suspicious)
    noise_score = min(noise_var / 5000, 1.0)
    return float(noise_score)

def detect_edge_inconsistencies(img_array: np.ndarray) -> float:
    """Detect edge inconsistencies that indicate copy-paste or splicing"""
    import cv2
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Canny edge detection
    edges = cv2.Canny(gray, 100, 200)
    
    # Check edge density in different regions
    h, w = edges.shape
    regions = [
        edges[:h//2, :w//2],
        edges[:h//2, w//2:],
        edges[h//2:, :w//2],
        edges[h//2:, w//2:]
    ]
    
    densities = [np.mean(r) for r in regions]
    
    # High variance between regions = inconsistency
    inconsistency = np.std(densities) / (np.mean(densities) + 1e-6)
    edge_score = min(inconsistency / 2.0, 1.0)
    
    return float(edge_score)