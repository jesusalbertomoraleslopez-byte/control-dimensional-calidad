"""
Script para subir la base de datos local al bucket de GCS
como punto de arranque persistente para Streamlit Cloud.
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DB_PATH = os.path.join(PROJECT_ROOT, "data", "sigrama_calidad.db")
GCS_DB_BLOB = "system/sigrama_calidad.db"

from src.services.gcs_storage import get_bucket, DEFAULT_BUCKET_NAME

print(f"Subiendo {DB_PATH} -> gs://{DEFAULT_BUCKET_NAME}/{GCS_DB_BLOB}")
bucket = get_bucket()
if bucket is None:
    print("ERROR: No se pudo conectar a GCS.")
    sys.exit(1)

blob = bucket.blob(GCS_DB_BLOB)
blob.upload_from_filename(DB_PATH, content_type="application/octet-stream")
print(f"OK! Base de datos persistida en gs://{DEFAULT_BUCKET_NAME}/{GCS_DB_BLOB}")

import sqlite3
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("SELECT COUNT(*), estatus_auditoria FROM piezas GROUP BY estatus_auditoria")
for row in c.fetchall():
    print(f"  {row[1]}: {row[0]} piezas")
conn.close()
