from PIL import Image, ImageChops, ImageEnhance, ImageFilter
import numpy as np
import cv2
import io

def error_level_analysis_sensitive(image: Image.Image) -> float:
    """
    Highly sensitive ELA — detects even small Paint edits.
    Paint editing creates distinct compression artifacts.
    """
    scores = []
    
    for quality in [75, 85, 95]:
        # Save at specific quality
        buffer = io.BytesIO()
        image.convert('RGB').save(buffer, format='JPEG', quality=quality)
        buffer.seek(0)
        compressed = Image.open(buffer).copy()
        buffer.close()

        # Calculate pixel-level difference
        original = np.array(image.convert('RGB')).astype(np.float32)
        comp = np.array(compressed.convert('RGB')).astype(np.float32)
        
        diff = np.abs(original - comp)
        
        # Amplify and analyze
        diff_amplified = np.clip(diff * 15, 0, 255)
        
        h, w = diff_amplified.shape[:2]
        block_size = h // 8
        
        block_means = []
        for i in range(8):
            for j in range(8):
                block = diff_amplified[
                    i*block_size:(i+1)*block_size,
                    j*block_size:(j+1)*block_size
                ]
                if block.size > 0:
                    block_means.append(np.mean(block))
        
        if block_means:
            # High variance = some blocks have much higher ELA = tampered
            variance = np.std(block_means) / (np.mean(block_means) + 1e-6)
            max_mean = max(block_means)
            avg_mean = np.mean(block_means)
            
            # Ratio of highest block to average
            suspicion = (max_mean / (avg_mean + 1e-6)) - 1
            ela_score = min(suspicion / 3.0, 1.0)
            scores.append(ela_score)
    
    return float(np.mean(scores)) if scores else 0.0

def detect_paint_artifacts(image: Image.Image) -> float:
    """
    Specifically detect Paint.exe editing artifacts.
    Paint uses specific color quantization and anti-aliasing.
    """
    img_array = np.array(image.convert('RGB'))
    
    # Paint text/drawings have very sharp edges (0 anti-aliasing)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Detect unnaturally sharp edges (Paint artifacts)
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient = np.sqrt(sobelx**2 + sobely**2)
    
    # Paint creates pixel-perfect edges — look for very high gradient pixels
    very_sharp = np.sum(gradient > 200) / gradient.size
    
    # Check for solid color regions (Paint fill tool)
    # Convert to HSV and look for unnaturally uniform regions
    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
    saturation = hsv[:,:,1]
    
    h, w = saturation.shape
    block_size = h // 6
    uniform_blocks = 0
    total_blocks = 0
    
    for i in range(6):
        for j in range(6):
            block = saturation[
                i*block_size:(i+1)*block_size,
                j*block_size:(j+1)*block_size
            ]
            if block.size > 0:
                total_blocks += 1
                # Very uniform saturation = solid color fill (Paint artifact)
                if np.std(block) < 5 and np.mean(block) > 50:
                    uniform_blocks += 1
    
    uniform_ratio = uniform_blocks / (total_blocks + 1e-6)
    paint_score = min(very_sharp * 10 + uniform_ratio * 0.5, 1.0)
    
    return float(paint_score)

def detect_double_compression(image: Image.Image) -> float:
    """
    Detect double JPEG compression — happens when you 
    edit and re-save a JPEG in Paint.
    """
    try:
        img_array = np.array(image.convert('L')).astype(np.float32)
        
        # DCT analysis — double compression leaves specific artifacts
        h, w = img_array.shape
        block_size = 8
        dct_variances = []
        
        for i in range(0, h-block_size, block_size):
            for j in range(0, w-block_size, block_size):
                block = img_array[i:i+block_size, j:j+block_size]
                dct_block = cv2.dct(block)
                # High frequency DCT coefficients
                high_freq = dct_block[4:, 4:]
                dct_variances.append(np.var(high_freq))
        
        if not dct_variances:
            return 0.0
        
        # Double compression creates periodic patterns in DCT variances
        dct_array = np.array(dct_variances)
        periodicity = np.std(dct_array) / (np.mean(dct_array) + 1e-6)
        
        return float(min(periodicity / 5.0, 1.0))
    except:
        return 0.0

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
        image_resized = image.resize((512, 512))

        # Run all checks
        ela_score = error_level_analysis_sensitive(image_resized)
        paint_score = detect_paint_artifacts(image_resized)
        dct_score = detect_double_compression(image_resized)
        has_face, face_count = check_face_presence(img_resized)
        quality_score = check_image_quality(img_resized)
        text_density = check_text_density(img_resized)
        resolution_score = check_resolution(image)
        ratio_score = check_aspect_ratio(image)
        metadata = check_metadata(image)

        risk_score = 0.0
        findings = []

        # FORGERY CHECKS — primary signals
        forgery_score = (
            ela_score * 0.45 +
            paint_score * 0.30 +
            dct_score * 0.25
        )

        if forgery_score > 0.5:
            findings.append(f"🚨 ELA: Significant compression inconsistency detected ({ela_score:.0%})")
            findings.append(f"🚨 Paint artifacts detected in edited regions ({paint_score:.0%})")
            risk_score += 0.6
        elif forgery_score > 0.25:
            findings.append(f"⚠️ ELA: Minor compression inconsistency ({ela_score:.0%})")
            risk_score += 0.3
        else:
            findings.append(f"✅ No editing artifacts detected")

        # Metadata check
        if metadata.get('is_edited'):
            findings.append("🚨 Editing software detected in metadata!")
            risk_score += 0.40
        elif metadata.get('is_camera'):
            findings.append("✅ Camera metadata present")
        else:
            findings.append("⚠️ No camera metadata")
            risk_score += 0.10

        # Document validation checks
        if has_face:
            findings.append(f"✅ Face photo detected ({face_count} face(s))")
        else:
            findings.append("⚠️ No face detected")
            risk_score += 0.15

        if text_density > 0.05:
            findings.append(f"✅ Text regions detected")
        else:
            findings.append("⚠️ Insufficient text")
            risk_score += 0.15

        if quality_score > 0.3:
            findings.append(f"✅ Image quality acceptable")
        else:
            findings.append("⚠️ Low quality")
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
            "ela_score": round(ela_score, 4),
            "paint_score": round(paint_score, 4),
            "dct_score": round(dct_score, 4),
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