"""
Script de Migración e Inyección Masiva de Planos a Google Cloud Storage
SIGRAMA - Control Dimensional y Calidad Industria 4.0

Escanea todas las carpetas físicas de piezas en 'src/Proyectos' y las sube
al bucket privado 'sigrama-planos-calidad-2026', actualizando los registros
en la base de datos SQLite para apuntar a sus URIs seguras en la nube.
"""

import os
import sys
import time
import sqlite3

# Asegurar importación de módulos del proyecto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.services.gcs_storage import (
    is_gcs_available,
    get_bucket,
    upload_file_to_gcs,
    normalize_blob_name,
    DEFAULT_BUCKET_NAME
)
from src.database import get_connection

def migrar_planos_a_gcs():
    print("=" * 75)
    print("🚀 INICIANDO MIGRACIÓN E INYECCIÓN DE PLANOS A GOOGLE CLOUD STORAGE")
    print(f"Bucket Destino: gs://{DEFAULT_BUCKET_NAME}")
    print("=" * 75)

    if not is_gcs_available():
        print("❌ ERROR: No se pudo conectar a Google Cloud Storage.")
        print("Verifique que la llave JSON exista en 'credentials/' y tenga permisos.")
        return

    bucket = get_bucket()
    proyectos_dir = os.path.join(PROJECT_ROOT, "src", "Proyectos")
    if not os.path.exists(proyectos_dir):
        print(f"❌ ERROR: La carpeta local '{proyectos_dir}' no existe.")
        return

    # 1. Recolectar todos los archivos físicos a migrar
    files_to_upload = []
    total_bytes = 0
    for root, _, files in os.walk(proyectos_dir):
        for f in files:
            full_path = os.path.join(root, f)
            rel_blob = normalize_blob_name(full_path)
            f_size = os.path.getsize(full_path)
            files_to_upload.append((full_path, rel_blob, f_size))
            total_bytes += f_size

    total_files = len(files_to_upload)
    total_mb = total_bytes / (1024 * 1024)
    print(f"📦 Total de archivos a migrar: {total_files}")
    print(f"💾 Tamaño total a transferir: {total_mb:.2f} MB\n")

    # 2. Inyección y carga al Bucket con hilos paralelos
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading

    uploaded_count = 0
    skipped_count = 0
    bytes_transferred = 0
    lock = threading.Lock()
    start_time = time.time()

    def process_file(item):
        nonlocal uploaded_count, skipped_count, bytes_transferred
        local_path, blob_name, file_size = item
        blob = bucket.blob(blob_name)
        try:
            if blob.exists():
                blob.reload()
                if blob.size == file_size:
                    with lock:
                        skipped_count += 1
                    return True, blob_name, True
        except Exception:
            pass

        success, res = upload_file_to_gcs(local_path, blob_name)
        with lock:
            if success:
                uploaded_count += 1
                bytes_transferred += file_size
            else:
                print(f"[ERROR] Subiendo {blob_name}: {res}")
        return success, blob_name, False

    print("Transfiriendo archivos con 12 hilos concurrentes...")
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(process_file, item): item for item in files_to_upload}
        completed = 0
        for future in as_completed(futures):
            completed += 1
            if completed % 50 == 0 or completed == total_files:
                pct = (completed / total_files) * 100
                elapsed = time.time() - start_time
                mb_done = bytes_transferred / (1024 * 1024)
                rate = mb_done / elapsed if elapsed > 0 else 0
                print(f"[{completed}/{total_files} - {pct:.1f}%] {mb_done:.1f} MB procesados ({rate:.2f} MB/s)")

    elapsed_total = time.time() - start_time
    print("\n" + "-" * 75)
    print(f"CARGA AL BUCKET COMPLETADA en {elapsed_total:.1f} segundos.")
    print(f"   Archivos subidos nuevos: {uploaded_count}")
    print(f"   Archivos ya existentes: {skipped_count}")
    print("-" * 75 + "\n")

    # 3. Actualizar rutas en la base de datos SQLite
    print("🔄 ACTUALIZANDO RUTAS EN LA BASE DE DATOS LOCAL Y EN LA NUBE...")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre_sku, ruta_almacenamiento, archivo_dibujo_original, archivo_dxf, archivo_plano_control, archivo_plano_nativo_3d, archivo_dibujo_nativo_2d, archivo_excel_resumen, archivo_step, plano_validado_impreso, documento_primera_pieza FROM piezas")
    rows = cursor.fetchall()

    def to_gs_uri(p):
        if not p:
            return None
        norm = normalize_blob_name(p)
        return f"gs://{DEFAULT_BUCKET_NAME}/{norm}" if norm else None

    updated_db = 0
    for r in rows:
        p_id = r["id"]
        new_ruta = to_gs_uri(r["ruta_almacenamiento"])
        new_orig = to_gs_uri(r["archivo_dibujo_original"])
        new_dxf = to_gs_uri(r["archivo_dxf"])
        new_ctrl = to_gs_uri(r["archivo_plano_control"])
        new_3d = to_gs_uri(r["archivo_plano_nativo_3d"])
        new_2d = to_gs_uri(r["archivo_dibujo_nativo_2d"])
        new_xlsx = to_gs_uri(r["archivo_excel_resumen"])
        new_step = to_gs_uri(r["archivo_step"])
        new_val = to_gs_uri(r["plano_validado_impreso"])
        new_vobo = to_gs_uri(r["documento_primera_pieza"])

        cursor.execute("""
            UPDATE piezas SET
                ruta_almacenamiento = COALESCE(?, ruta_almacenamiento),
                archivo_dibujo_original = COALESCE(?, archivo_dibujo_original),
                archivo_dxf = COALESCE(?, archivo_dxf),
                archivo_plano_control = COALESCE(?, archivo_plano_control),
                archivo_plano_nativo_3d = COALESCE(?, archivo_plano_nativo_3d),
                archivo_dibujo_nativo_2d = COALESCE(?, archivo_dibujo_nativo_2d),
                archivo_excel_resumen = COALESCE(?, archivo_excel_resumen),
                archivo_step = COALESCE(?, archivo_step),
                plano_validado_impreso = COALESCE(?, plano_validado_impreso),
                documento_primera_pieza = COALESCE(?, documento_primera_pieza)
            WHERE id = ?
        """, (new_ruta, new_orig, new_dxf, new_ctrl, new_3d, new_2d, new_xlsx, new_step, new_val, new_vobo, p_id))
        updated_db += 1

    conn.commit()
    conn.close()
    print(f"✅ Base de datos actualizada: {updated_db} registros de piezas ahora apuntan a Cloud Storage.\n")
    print("=" * 75)
    print("🎉 MIGRACIÓN FINALIZADA CON ÉXITO")
    print("=" * 75)

if __name__ == "__main__":
    migrar_planos_a_gcs()
