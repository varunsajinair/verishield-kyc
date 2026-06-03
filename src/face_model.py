import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import numpy as np
import os
import cv2

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def load_model():
    model = models.efficientnet_b0(weights='DEFAULT')
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, 2)
    model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'verishield_face_model.pth')
    if os.path.exists(model_path):
        checkpoint = torch.load(model_path, map_location='cpu')
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
            val_acc = checkpoint.get('val_acc', 0)
            fake_acc = checkpoint.get('fake_acc', 0)
            real_acc = checkpoint.get('real_acc', 0)
            print(f"✅ Loaded trained face model")
            print(f"   Val Acc: {val_acc:.2f}% | Fake Detection: {fake_acc:.2f}% | Real Detection: {real_acc:.2f}%")
        else:
            model.load_state_dict(checkpoint)
            print(f"✅ Loaded trained face model")
    else:
        print("⚠️ Trained model not found, using pretrained weights")
    model.eval()
    return model

_model = None

def get_model():
    global _model
    if _model is None:
        _model = load_model()
    return _model

def detect_gan_frequency_fingerprint(img_array: np.ndarray) -> float:
    """
    Detect GAN frequency fingerprints — StyleGAN leaves periodic artifacts
    in the frequency domain invisible to human eye but detectable via FFT.
    Based on research: 'Fourier-Based GAN Fingerprint Detection' (2024)
    """
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY).astype(np.float32)
    
    # Apply FFT
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    magnitude = np.log(np.abs(fshift) + 1)
    
    # Normalize
    magnitude = (magnitude - magnitude.min()) / (magnitude.max() - magnitude.min() + 1e-8)
    
    h, w = magnitude.shape
    center_h, center_w = h // 2, w // 2
    
    # GAN fingerprint: look for periodic patterns in mid-high frequency range
    # StyleGAN uses upsampling that creates grid-like artifacts
    mid_freq = magnitude[center_h-60:center_h+60, center_w-60:center_w+60]
    outer_freq = magnitude.copy()
    outer_freq[center_h-60:center_h+60, center_w-60:center_w+60] = 0
    
    # Check for periodic peaks (GAN artifact signature)
    mid_std = np.std(mid_freq)
    outer_mean = np.mean(outer_freq[outer_freq > 0])
    
    # Real images have smoother frequency distribution
    # GAN images have periodic spikes
    periodicity_score = float(np.std(outer_freq[outer_freq > 0]) / (outer_mean + 1e-8))
    
    # Normalize to 0-1
    gan_score = min(periodicity_score / 0.8, 1.0)
    
    return float(gan_score)

def detect_stylegan_checkerboard(img_array: np.ndarray) -> float:
    """
    Detect StyleGAN checkerboard artifacts from upsampling.
    StyleGAN uses nearest-neighbor upsampling which creates
    subtle checkerboard patterns in high frequency domain.
    """
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY).astype(np.float32)
    
    # High pass filter to isolate high frequency artifacts
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    high_freq = gray - blur
    
    # Check for regular periodic patterns (checkerboard)
    # Apply 2D autocorrelation
    normalized = high_freq / (np.std(high_freq) + 1e-8)
    
    # FFT of high frequency component
    f = np.fft.fft2(normalized)
    power = np.abs(f) ** 2
    power_shift = np.fft.fftshift(power)
    
    h, w = power_shift.shape
    center_h, center_w = h // 2, w // 2
    
    # Look for peaks at specific frequencies (GAN upsampling artifacts)
    region = power_shift[center_h-30:center_h+30, center_w-30:center_w+30]
    
    # Checkerboard score: high if periodic peaks exist
    sorted_vals = np.sort(region.flatten())[::-1]
    top_ratio = sorted_vals[:10].mean() / (sorted_vals[10:100].mean() + 1e-8)
    
    checkerboard_score = min((top_ratio - 1) / 10, 1.0)
    checkerboard_score = max(checkerboard_score, 0.0)
    
    return float(checkerboard_score)

def detect_texture_uniformity(img_array: np.ndarray) -> float:
    """
    GAN faces have unnaturally uniform skin texture.
    Real faces have natural micro-texture variations.
    """
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY).astype(np.float32)
    
    # Local standard deviation — real faces have more variation
    kernel_size = 15
    local_mean = cv2.blur(gray, (kernel_size, kernel_size))
    local_sq_mean = cv2.blur(gray**2, (kernel_size, kernel_size))
    local_std = np.sqrt(np.maximum(local_sq_mean - local_mean**2, 0))
    
    # Focus on face region (center)
    h, w = local_std.shape
    face_region = local_std[h//4:3*h//4, w//4:3*w//4]
    
    # GAN faces have lower std variation (too smooth)
    uniformity = 1.0 - min(np.std(face_region) / 30.0, 1.0)
    
    return float(uniformity)

def predict_face(image: Image.Image) -> dict:
    try:
        model = get_model()
        tensor = transform(image).unsqueeze(0)

        with torch.no_grad():
            outputs = model(tensor)
            probs = torch.softmax(outputs, dim=1)
            fake_prob = float(probs[0][0])
            real_prob = float(probs[0][1])

        img_array = np.array(image.resize((224, 224)))

        # Frequency domain GAN fingerprint detection
        gan_freq_score = detect_gan_frequency_fingerprint(img_array)
        checkerboard_score = detect_stylegan_checkerboard(img_array)
        texture_uniformity = detect_texture_uniformity(img_array)

        # Weighted ensemble:
        # Model is best for trained deepfakes
        # Frequency analysis is best for StyleGAN/GAN-generated faces
        combined_score = (
            fake_prob * 0.45 +
            gan_freq_score * 0.25 +
            checkerboard_score * 0.15 +
            texture_uniformity * 0.15
        )
        combined_score = min(max(combined_score, 0.0), 1.0)

        liveness_score = round(1.0 - combined_score, 4)

        if combined_score > 0.5:
            result = "DEEPFAKE"
            alert_level = "CRITICAL" if combined_score > 0.75 else "HIGH RISK"
        elif combined_score > 0.28:
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
            "texture_score": round(texture_uniformity, 4),
            "frequency_score": round(gan_freq_score, 4)
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