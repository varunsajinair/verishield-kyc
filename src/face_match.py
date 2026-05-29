from PIL import Image
import numpy as np
import cv2

def match_faces(doc_image: Image.Image, selfie_image: Image.Image) -> dict:
    """
    Compare face on ID document vs selfie using histogram similarity
    In production this would use a dedicated face recognition model
    """
    try:
        # Convert to numpy arrays
        doc_array = np.array(doc_image.resize((224, 224)))
        selfie_array = np.array(selfie_image.resize((224, 224)))

        # Convert to grayscale for comparison
        doc_gray = cv2.cvtColor(doc_array, cv2.COLOR_RGB2GRAY)
        selfie_gray = cv2.cvtColor(selfie_array, cv2.COLOR_RGB2GRAY)

        # Histogram comparison
        doc_hist = cv2.calcHist([doc_gray], [0], None, [256], [0, 256])
        selfie_hist = cv2.calcHist([selfie_gray], [0], None, [256], [0, 256])

        cv2.normalize(doc_hist, doc_hist)
        cv2.normalize(selfie_hist, selfie_hist)

        # Correlation similarity
        similarity = cv2.compareHist(doc_hist, selfie_hist, cv2.HISTCMP_CORREL)
        similarity = max(0.0, float(similarity))

        # Structural similarity
        doc_resized = cv2.resize(doc_array, (64, 64))
        selfie_resized = cv2.resize(selfie_array, (64, 64))

        diff = np.abs(doc_resized.astype(float) - selfie_resized.astype(float))
        structural_sim = 1.0 - (np.mean(diff) / 255.0)

        # Combined score
        combined_similarity = (similarity * 0.6 + structural_sim * 0.4)
        combined_similarity = round(min(max(combined_similarity, 0.0), 1.0), 4)

        if combined_similarity > 0.6:
            result = "MATCH"
            alert_level = "LOW RISK"
        elif combined_similarity > 0.35:
            result = "POSSIBLE MATCH"
            alert_level = "MEDIUM RISK"
        else:
            result = "NO MATCH"
            alert_level = "HIGH RISK"

        return {
            "result": result,
            "similarity_score": combined_similarity,
            "histogram_similarity": round(similarity, 4),
            "structural_similarity": round(structural_sim, 4),
            "alert_level": alert_level
        }

    except Exception as e:
        print(f"Face match error: {e}")
        return {
            "result": "ERROR",
            "similarity_score": 0.0,
            "histogram_similarity": 0.0,
            "structural_similarity": 0.0,
            "alert_level": "UNKNOWN"
        }