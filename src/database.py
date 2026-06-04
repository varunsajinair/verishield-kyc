import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT', 5432)
    dbname = os.getenv('DB_NAME', 'postgres')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD')
    
    print(f"🔌 Connecting to DB: {host}:{port}/{dbname} as {user}")
    
    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        sslmode='require'
    )

def log_verification(data: dict):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO kyc_verifications (
                verification_id, document_result, document_confidence,
                face_result, face_confidence, match_result, match_score,
                overall_result, overall_risk_score, alert_level, processing_time_ms
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get('verification_id', 'UNKNOWN'),
            data.get('document_result', 'N/A'),
            float(data.get('document_confidence', 0.0)),
            data.get('face_result', 'UNKNOWN'),
            float(data.get('face_confidence', 0.0)),
            data.get('match_result', 'UNKNOWN'),
            float(data.get('match_score', 0.0)),
            data.get('overall_result', 'UNKNOWN'),
            float(data.get('overall_risk_score', 0.0)),
            data.get('alert_level', 'UNKNOWN'),
            float(data.get('processing_time_ms', 0.0))
        ))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ DB: Logged verification {data.get('verification_id')}")
    except Exception as e:
        print(f"❌ DB ERROR: {e}")
        print(f"❌ DB_HOST: {os.getenv('DB_HOST')}")
        print(f"❌ DB_USER: {os.getenv('DB_USER')}")
        print(f"❌ DB_NAME: {os.getenv('DB_NAME')}")

def load_all_verifications():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM kyc_verifications
            ORDER BY timestamp DESC
        """)
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()
        return rows, cols
    except Exception as e:
        print(f"❌ DB ERROR: {e}")
        return [], []

def load_recent_verifications(limit=50):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM kyc_verifications
            ORDER BY timestamp DESC
            LIMIT %s
        """, (limit,))
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()
        return rows, cols
    except Exception as e:
        print(f"❌ DB ERROR: {e}")
        return [], []