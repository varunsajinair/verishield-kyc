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
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=90)
    buffer.seek(0)
    compressed = Image.open(buffer).copy()
    buffer.close()

    ela_image = ImageChops.difference(image.convert('RGB'), compressed.convert('RGB'))
    ela_array = np.array(ela_image).astype(np.float32)
    ela_array = ela_array * 10
    ela_array = np.clip(ela_array, 0, 255)

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

    overall_std = np.std(region_stds)
    mean_std = np.mean(region_stds)

    if mean_std > 0:
        inconsistency = overall_std / mean_std
    else:
        inconsistency = 0

    ela_score = min(inconsistency / 3.0, 1.0)
    return float(ela_score)

def detect_copy_move(img_array: np.ndarray) -> float:
    try:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        orb = cv2.ORB_create(nfeatures=500)
        keypoints, descriptors = orb.detectAndCompute(gray, None)

        if descriptors is None or len(keypoints) < 10:
            return 0.0

        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        matches = bf.knnMatch(descriptors, descriptors, k=3)

        suspicious = 0
        total = 0
        for match_group in matches:
            if len(match_group) >= 2:
                m, n = match_group[0], match_group[1]
                if m.trainIdx != m.queryIdx:
                    pt1 = keypoints[m.queryIdx].pt
                    pt2 = keypoints[m.trainIdx].pt
                    dist = np.sqrt((pt1[0]-pt2[0])**2 + (pt1[1]-pt2[1])**2)
                    if dist > 20:
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
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY).astype(np.float32)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    noise = gray - blur

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

    noise_variance = np.std(block_stds) / (np.mean(block_stds) + 1e-6)
    noise_score = min(noise_variance / 2.0, 1.0)
    return float(noise_score)

def detect_jpeg_ghost(image: Image.Image) -> float:
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
    img_array = np.array(image.convert('L'))
    laplacian = cv2.Laplacian(img_array, cv2.CV_64F)

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

    sharpness_inconsistency = np.std(region_vars) / (np.mean(region_vars) + 1e-6)
    quality_score = min(sharpness_inconsistency / 5.0, 1.0)
    return float(quality_score)

def check_metadata_tampering(image: Image.Image) -> float:
    """Check EXIF metadata for editing software signatures"""
    try:
        exif_data = image._getexif()
        if exif_data is None:
            # No EXIF = likely edited/screenshot = suspicious
            return 0.4

        # Check for editing software in EXIF
        software_tag = 305
        if software_tag in exif_data:
            software = str(exif_data[software_tag]).lower()
            suspicious_software = ['photoshop', 'gimp', 'paint', 'pixlr',
                                  'canva', 'snapseed', 'lightroom', 'affinity']
            if any(s in software for s in suspicious_software):
                return 0.8
        return 0.1
    except:
        return 0.3

def detect_color_inconsistency(img_array: np.ndarray) -> float:
    """
    Detect color space inconsistencies.
    Pasted regions often have different color statistics.
    """
    try:
        # Split into RGB channels
        r, g, b = img_array[:,:,0], img_array[:,:,1], img_array[:,:,2]

        h, w = r.shape
        block_size = h // 4
        block_ratios = []

        for i in range(4):
            for j in range(4):
                br = r[i*block_size:(i+1)*block_size, j*block_size:(j+1)*block_size]
                bg = g[i*block_size:(i+1)*block_size, j*block_size:(j+1)*block_size]
                bb = b[i*block_size:(i+1)*block_size, j*block_size:(j+1)*block_size]

                if br.size > 0 and np.mean(bg) > 0:
                    rg_ratio = np.mean(br) / (np.mean(bg) + 1e-6)
                    block_ratios.append(rg_ratio)

        if len(block_ratios) < 2:
            return 0.0

        color_inconsistency = np.std(block_ratios) / (np.mean(block_ratios) + 1e-6)
        color_score = min(color_inconsistency / 0.5, 1.0)
        return float(color_score)

    except Exception:
        return 0.0

def predict_document(image: Image.Image) -> dict:
    try:
        image_resized = image.resize((512, 512))
        img_array = np.array(image_resized.convert('RGB'))

        # Run all 6 forensic checks
        ela_score = error_level_analysis(image_resized)
        copy_move_score = detect_copy_move(img_array)
        noise_score = detect_noise_inconsistency(img_array)
        jpeg_ghost_score = detect_jpeg_ghost(image_resized)
        quality_score = check_image_quality(image_resized)
        metadata_score = check_metadata_tampering(image)
        color_score = detect_color_inconsistency(img_array)

        # Weighted ensemble
        combined_score = (
            ela_score * 0.25 +
            noise_score * 0.20 +
            jpeg_ghost_score * 0.15 +
            metadata_score * 0.15 +
            color_score * 0.10 +
            copy_move_score * 0.10 +
            quality_score * 0.05
        )
        combined_score = min(max(combined_score, 0.0), 1.0)

        if combined_score > 0.55:
            result = "FORGED"
            alert_level = "CRITICAL" if combined_score > 0.75 else "HIGH RISK"
        elif combined_score > 0.30:
            result = "SUSPICIOUS"
            alert_level = "MEDIUM RISK"
        else:
            result = "AUTHENTIC"
            alert_level = "LOW RISK"

        tampered_regions = []
        if ela_score > 0.4:
            tampered_regions.append(f"ELA: Compression inconsistency ({ela_score:.0%})")
        if noise_score > 0.4:
            tampered_regions.append(f"Noise: Regional inconsistency ({noise_score:.0%})")
        if jpeg_ghost_score > 0.4:
            tampered_regions.append(f"JPEG Ghost: Multi-quality artifacts ({jpeg_ghost_score:.0%})")
        if metadata_score > 0.5:
            tampered_regions.append(f"Metadata: Editing software detected ({metadata_score:.0%})")
        if color_score > 0.4:
            tampered_regions.append(f"Color: Inconsistency detected ({color_score:.0%})")
        if copy_move_score > 0.3:
            tampered_regions.append(f"Copy-Move: Duplicated regions ({copy_move_score:.0%})")
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
            "quality_score": round(quality_score, 4),
            "metadata_score": round(metadata_score, 4),
            "color_score": round(color_score, 4)
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
            "quality_score": 0.0,
            "metadata_score": 0.0,
            "color_score": 0.0
        }