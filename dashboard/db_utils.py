import psycopg2
import pandas as pd
import streamlit as st
import os

def get_connection():
    return psycopg2.connect(
        host=st.secrets.get("DB_HOST") or os.getenv('DB_HOST'),
        port=st.secrets.get("DB_PORT") or os.getenv('DB_PORT', 5432),
        dbname=st.secrets.get("DB_NAME") or os.getenv('DB_NAME', 'postgres'),
        user=st.secrets.get("DB_USER") or os.getenv('DB_USER', 'postgres'),
        password=st.secrets.get("DB_PASSWORD") or os.getenv('DB_PASSWORD'),
        sslmode='require'
    )

def load_recent(limit=20):
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
        if rows:
            return pd.DataFrame(rows, columns=cols)
        return pd.DataFrame()
    except Exception as e:
        print(f"DB error: {e}")
        return pd.DataFrame()

def load_all():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM kyc_verifications ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()
        if rows:
            return pd.DataFrame(rows, columns=cols)
        return pd.DataFrame()
    except Exception as e:
        print(f"DB error: {e}")
        return pd.DataFrame()

def load_stats():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN overall_result = 'APPROVED' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN overall_result = 'REJECTED' THEN 1 ELSE 0 END) as rejected,
                SUM(CASE WHEN overall_result = 'REVIEW' THEN 1 ELSE 0 END) as review
            FROM kyc_verifications
        """)
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return {
                "total": int(row[0] or 0),
                "approved": int(row[1] or 0),
                "rejected": int(row[2] or 0),
                "review": int(row[3] or 0)
            }
        return {"total": 0, "approved": 0, "rejected": 0, "review": 0}
    except Exception as e:
        print(f"DB error: {e}")
        return {"total": 0, "approved": 0, "rejected": 0, "review": 0}