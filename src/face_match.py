from PIL import Image
import numpy as np
import cv2

def extract_face(img_array: np.ndarray) -> np.ndarray:
    """Extract and crop face region from image"""
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
    
    if len(faces) > 0:
        # Get largest face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        # Add padding
        pad = int(0.2 * min(w, h))
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(img_array.shape[1], x + w + pad)
        y2 = min(img_array.shape[0], y + h + pad)
        return img_array[y1:y2, x1:x2]
    return img_array

def compute_face_histogram(face_array: np.ndarray) -> np.ndarray:
    """Compute color histogram of face region"""
    face_resized = cv2.resize(face_array, (64, 64))
    hist_features = []
    
    for channel in range(3):
        hist = cv2.calcHist(
            [face_resized], [channel], None, [64], [0, 256]
        )
        cv2.normalize(hist, hist)
        hist_features.extend(hist.flatten())
    
    return np.array(hist_features)

def compute_lbp_features(face_array: np.ndarray) -> np.ndarray:
    """Local Binary Pattern features for face comparison"""
    gray = cv2.cvtColor(face_array, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, (64, 64))
    
    # Simple LBP implementation
    lbp = np.zeros_like(gray)
    for i in range(1, gray.shape[0]-1):
        for j in range(1, gray.shape[1]-1):
            center = gray[i, j]
            binary = 0
            neighbors = [
                gray[i-1, j-1], gray[i-1, j], gray[i-1, j+1],
                gray[i, j+1], gray[i+1, j+1], gray[i+1, j],
                gray[i+1, j-1], gray[i, j-1]
            ]
            for k, neighbor in enumerate(neighbors):
                if neighbor >= center:
                    binary += (1 << k)
            lbp[i, j] = binary
    
    hist = cv2.calcHist([lbp], [0], None, [256], [0, 256])
    cv2.normalize(hist, hist)
    return hist.flatten()

def match_faces(doc_image: Image.Image, selfie_image: Image.Image) -> dict:
    """
    Compare face on ID document vs selfie using multiple methods.
    Uses face detection + LBP texture features + color histogram.
    """
    try:
        doc_array = np.array(doc_image.resize((300, 300)))
        selfie_array = np.array(selfie_image.resize((300, 300)))

        # Extract face regions
        doc_face = extract_face(doc_array)
        selfie_face = extract_face(selfie_array)

        # Method 1: Color histogram similarity on face region
        doc_hist = compute_face_histogram(doc_face)
        selfie_hist = compute_face_histogram(selfie_face)
        hist_similarity = float(np.dot(doc_hist, selfie_hist) / 
                               (np.linalg.norm(doc_hist) * np.linalg.norm(selfie_hist) + 1e-6))

        # Method 2: LBP texture features
        doc_lbp = compute_lbp_features(doc_face)
        selfie_lbp = compute_lbp_features(selfie_face)
        lbp_similarity = float(cv2.compareHist(
            doc_lbp.astype(np.float32).reshape(-1, 1),
            selfie_lbp.astype(np.float32).reshape(-1, 1),
            cv2.HISTCMP_CORREL
        ))
        lbp_similarity = max(0.0, lbp_similarity)

        # Method 3: Structural similarity on grayscale face
        doc_gray = cv2.cvtColor(cv2.resize(doc_face, (64, 64)), cv2.COLOR_RGB2GRAY)
        selfie_gray = cv2.cvtColor(cv2.resize(selfie_face, (64, 64)), cv2.COLOR_RGB2GRAY)
        
        diff = np.abs(doc_gray.astype(float) - selfie_gray.astype(float))
        structural_sim = 1.0 - (np.mean(diff) / 255.0)

        # Weighted combination
        combined_similarity = (
            hist_similarity * 0.4 +
            lbp_similarity * 0.4 +
            structural_sim * 0.2
        )
        combined_similarity = round(min(max(combined_similarity, 0.0), 1.0), 4)

        # Stricter thresholds for face matching
        if combined_similarity > 0.75:
            result = "MATCH"
            alert_level = "LOW RISK"
        elif combined_similarity > 0.55:
            result = "POSSIBLE MATCH"
            alert_level = "MEDIUM RISK"
        else:
            result = "NO MATCH"
            alert_level = "HIGH RISK"

        return {
            "result": result,
            "similarity_score": combined_similarity,
            "histogram_similarity": round(hist_similarity, 4),
            "lbp_similarity": round(lbp_similarity, 4),
            "structural_similarity": round(structural_sim, 4),
            "alert_level": alert_level
        }

    except Exception as e:
        print(f"Face match error: {e}")
        return {
            "result": "ERROR",
            "similarity_score": 0.0,
            "histogram_similarity": 0.0,
            "lbp_similarity": 0.0,
            "structural_similarity": 0.0,
            "alert_level": "UNKNOWN"
        }