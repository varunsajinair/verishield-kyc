import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image, ImageChops, ImageEnhance
import numpy as np
import cv2
import io
import os

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def load_model():
    model = models.efficientnet_b0(weights='DEFAULT')
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, 2)
    model.eval()
    return model

_model = None

def get_model():
    global _model
    if _model is None:
        _model = load_model()
    return _model

def error_level_analysis(image: Image.Image) -> float:
    """
    Error Level Analysis (ELA) — industry standard forensic technique.
    Detects regions with different compression history = tampered areas.
    Used by forensic experts and commercial KYC systems worldwide.
    """
    # Save at specific quality
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=90)
    buffer.seek(0)
    compressed = Image.open(buffer).copy()
    buffer.close()

    # Calculate difference
    ela_image = ImageChops.difference(image.convert('RGB'), compressed.convert('RGB'))
    ela_array = np.array(ela_image).astype(np.float32)

    # Amplify differences
    ela_array = ela_array * 10
    ela_array = np.clip(ela_array, 0, 255)

    # Split image into regions and check consistency
    h, w = ela_array.shape[:2]
    region_size = h // 4

    region_stds = []
    for i in range(4):
        for j in range(4):
            region = ela_array[
                i*region_size:(i+1)*region_size,
                j*region_size:(j+1)*region_size
            ]
            region_stds.append(np.std(region))

    # High variance between regions = inconsistent compression = tampering
    overall_std = np.std(region_stds)
    max_std = max(region_stds)
    mean_std = np.mean(region_stds)

    # Normalize ELA score
    # Authentic documents have consistent ELA levels
    # Tampered documents have regions with much higher ELA
    if mean_std > 0:
        inconsistency = overall_std / mean_std
    else:
        inconsistency = 0

    ela_score = min(inconsistency / 3.0, 1.0)
    return float(ela_score)

def detect_copy_move(img_array: np.ndarray) -> float:
    """
    Copy-move forgery detection using SIFT feature matching.
    Detects if parts of the document were copied and pasted.
    """
    try:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # Use ORB (faster than SIFT, no patent issues)
        orb = cv2.ORB_create(nfeatures=500)
        keypoints, descriptors = orb.detectAndCompute(gray, None)

        if descriptors is None or len(keypoints) < 10:
            return 0.0

        # Match features within same image
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        matches = bf.knnMatch(descriptors, descriptors, k=3)

        # Find suspicious matches (same region matched to different region)
        suspicious = 0
        total = 0
        for match_group in matches:
            if len(match_group) >= 2:
                m, n = match_group[0], match_group[1]
                if m.trainIdx != m.queryIdx:  # Not self-match
                    pt1 = keypoints[m.queryIdx].pt
                    pt2 = keypoints[m.trainIdx].pt
                    dist = np.sqrt((pt1[0]-pt2[0])**2 + (pt1[1]-pt2[1])**2)
                    if dist > 20:  # Points far apart but similar
                        if m.distance < 0.8 * n.distance:
                            suspicious += 1
                total += 1

        if total > 0:
            copy_move_score = min(suspicious / (total * 0.1), 1.0)
        else:
            copy_move_score = 0.0

        return float(copy_move_score)

    except Exception:
        return 0.0

def detect_noise_inconsistency(img_array: np.ndarray) -> float:
    """
    Detect noise inconsistency between regions.
    Authentic documents have uniform noise from single scan/photo.
    Tampered documents have regions with different noise patterns.
    """
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY).astype(np.float32)

    # Extract noise map
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    noise = gray - blur

    # Divide into blocks and measure noise statistics
    h, w = noise.shape
    block_size = h // 6
    block_stds = []

    for i in range(6):
        for j in range(6):
            block = noise[
                i*block_size:(i+1)*block_size,
                j*block_size:(j+1)*block_size
            ]
            if block.size > 0:
                block_stds.append(np.std(block))

    if len(block_stds) == 0:
        return 0.0

    # High variance in noise levels = tampering
    noise_variance = np.std(block_stds) / (np.mean(block_stds) + 1e-6)
    noise_score = min(noise_variance / 2.0, 1.0)

    return float(noise_score)

def detect_jpeg_ghost(image: Image.Image) -> float:
    """
    JPEG Ghost detection — finds regions saved at different quality levels.
    Pasted content has different JPEG compression artifacts.
    """
    try:
        original = np.array(image.convert('L')).astype(np.float32)
        ghost_scores = []

        for quality in [50, 70, 85]:
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=quality)
            buffer.seek(0)
            compressed = np.array(Image.open(buffer).convert('L')).astype(np.float32)
            buffer.close()

            diff = np.abs(original - compressed)

            # Check regional consistency
            h, w = diff.shape
            region_means = []
            rs = h // 4
            for i in range(4):
                for j in range(4):
                    region = diff[i*rs:(i+1)*rs, j*rs:(j+1)*rs]
                    if region.size > 0:
                        region_means.append(np.mean(region))

            if region_means:
                ghost_score = np.std(region_means) / (np.mean(region_means) + 1e-6)
                ghost_scores.append(min(ghost_score / 2.0, 1.0))

        return float(np.mean(ghost_scores)) if ghost_scores else 0.0

    except Exception:
        return 0.0

def check_image_quality(image: Image.Image) -> float:
    """
    Check image quality consistency.
    Forged documents often have blur/sharpness inconsistencies.
    """
    img_array = np.array(image.convert('L'))

    # Laplacian variance = sharpness measure
    laplacian = cv2.Laplacian(img_array, cv2.CV_64F)

    # Check sharpness in different regions
    h, w = laplacian.shape
    rs = h // 4
    region_vars = []

    for i in range(4):
        for j in range(4):
            region = laplacian[i*rs:(i+1)*rs, j*rs:(j+1)*rs]
            if region.size > 0:
                region_vars.append(np.var(region))

    if not region_vars:
        return 0.0

    # High variance between region sharpness = inconsistency = forgery
    sharpness_inconsistency = np.std(region_vars) / (np.mean(region_vars) + 1e-6)
    quality_score = min(sharpness_inconsistency / 5.0, 1.0)

    return float(quality_score)

def predict_document(image: Image.Image) -> dict:
    try:
        # Resize for processing
        image_resized = image.resize((512, 512))
        img_array = np.array(image_resized.convert('RGB'))

        # Run all forensic checks
        ela_score = error_level_analysis(image_resized)
        copy_move_score = detect_copy_move(img_array)
        noise_score = detect_noise_inconsistency(img_array)
        jpeg_ghost_score = detect_jpeg_ghost(image_resized)
        quality_score = check_image_quality(image_resized)

        # Weighted ensemble — ELA is most reliable
        combined_score = (
            ela_score * 0.35 +
            noise_score * 0.25 +
            jpeg_ghost_score * 0.20 +
            copy_move_score * 0.10 +
            quality_score * 0.10
        )
        combined_score = min(max(combined_score, 0.0), 1.0)

        # Determine result
        if combined_score > 0.55:
            result = "FORGED"
            alert_level = "CRITICAL" if combined_score > 0.75 else "HIGH RISK"
        elif combined_score > 0.30:
            result = "SUSPICIOUS"
            alert_level = "MEDIUM RISK"
        else:
            result = "AUTHENTIC"
            alert_level = "LOW RISK"

        # Build findings
        tampered_regions = []
        if ela_score > 0.4:
            tampered_regions.append(f"ELA: Compression inconsistency detected ({ela_score:.0%})")
        if noise_score > 0.4:
            tampered_regions.append(f"Noise: Regional noise inconsistency ({noise_score:.0%})")
        if jpeg_ghost_score > 0.4:
            tampered_regions.append(f"JPEG Ghost: Multi-quality artifacts detected ({jpeg_ghost_score:.0%})")
        if copy_move_score > 0.3:
            tampered_regions.append(f"Copy-Move: Duplicated regions detected ({copy_move_score:.0%})")
        if quality_score > 0.4:
            tampered_regions.append(f"Quality: Sharpness inconsistency detected ({quality_score:.0%})")
        if not tampered_regions:
            tampered_regions.append("No tampering detected — document appears authentic")

        return {
            "result": result,
            "confidence": round(combined_score, 4),
            "forgery_probability": round(combined_score, 4),
            "real_probability": round(1 - combined_score, 4),
            "risk_score": round(combined_score, 4),
            "alert_level": alert_level,
            "tampered_regions": tampered_regions,
            "ela_score": round(ela_score, 4),
            "noise_score": round(noise_score, 4),
            "jpeg_ghost_score": round(jpeg_ghost_score, 4),
            "copy_move_score": round(copy_move_score, 4),
            "quality_score": round(quality_score, 4)
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
            "ela_score": 0.0,
            "noise_score": 0.0,
            "jpeg_ghost_score": 0.0,
            "copy_move_score": 0.0,
            "quality_score": 0.0
        }