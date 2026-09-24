"""
Diagnóstico: verifica cuánto pesan los archivos STEP del bucket
y si el base64 embedded podría ser demasiado grande para el iframe.
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3, base64

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'sigrama_calidad.db')
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("SELECT consecutivo_ing, nombre_sku, archivo_step, archivo_plano_control FROM piezas LIMIT 5")
rows = c.fetchall()

from google.cloud import storage
cred_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'credentials', 'sigrama-cloud-calidad-d8baef08fd5b.json')
gcs_client = storage.Client.from_service_account_json(cred_path)
bucket = gcs_client.bucket('sigrama-planos-calidad-2026')

print(f"{'ING':8} {'Step file size (KB)':25} {'Base64 size (KB)':18} {'PDF file size (KB)':20}")
print("-" * 80)

for row in rows:
    ing = row['consecutivo_ing'] or 'N/A'
    step_path = row['archivo_step']
    pdf_path = row['archivo_plano_control']
    
    step_size = 0
    pdf_size = 0
    
    if step_path and step_path.startswith('gs://'):
        blob_name = step_path[len('gs://sigrama-planos-calidad-2026/'):]
        try:
            blob = bucket.blob(blob_name)
            blob.reload()
            step_size = blob.size or 0
        except Exception as e:
            step_size = -1
    
    if pdf_path and pdf_path.startswith('gs://'):
        blob_name = pdf_path[len('gs://sigrama-planos-calidad-2026/'):]
        try:
            blob = bucket.blob(blob_name)
            blob.reload()
            pdf_size = blob.size or 0
        except Exception as e:
            pdf_size = -1
    
    b64_size = int(step_size * 4 / 3) if step_size > 0 else 0
    # Streamlit components.html has a size limit
    # Streamlit iframe HTML has practical limits around 50-100MB
    warning = " ⚠️ DEMASIADO GRANDE" if b64_size > 50_000_000 else ""
    print(f"{ing:8} {step_size/1024:20.1f} KB   {b64_size/1024:15.1f} KB   {pdf_size/1024:15.1f} KB{warning}")

print()
print("NOTA: Streamlit components.html tiene limite practico de ~50MB en el HTML embebido")
print("Si el base64 del STEP es muy grande, el iframe falla silenciosamente")
