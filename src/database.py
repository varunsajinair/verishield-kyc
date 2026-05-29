import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT', 5432),
        dbname=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD'),
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
            data['verification_id'],
            data['document_result'],
            data['document_confidence'],
            data['face_result'],
            data['face_confidence'],
            data['match_result'],
            data['match_score'],
            data['overall_result'],
            data['overall_risk_score'],
            data['alert_level'],
            data['processing_time_ms']
        ))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB error: {e}")

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
        print(f"DB error: {e}")
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
        print(f"DB error: {e}")
        return [], []