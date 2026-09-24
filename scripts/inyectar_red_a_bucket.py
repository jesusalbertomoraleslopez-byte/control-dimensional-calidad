"""
Script Oficial de Inyección Masiva de Ingeniería a Google Cloud Storage
SIGRAMA - Control Dimensional y Calidad Industrial 4.0

Inyecta las carpetas oficiales desde la ruta de red:
'Z:\\02 - INGENIERIA\\BASE DE DATOS PRODUCTOS'
hacia el Bucket 'sigrama-planos-calidad-2026' bajo la estructura 'Sin_Auditar/',
clasificando cada documento y registrando el consecutivo ING (ej. ING0001 a ING0267)
con estatus 'Sin Auditar' para el Proceso de Validación del Administrador.
"""

import os
import re
import sys
import time
import sqlite3
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

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
    DEFAULT_BUCKET_NAME
)
from src.database import get_connection, initialize_database

NETWORK_PATH = r"Z:\02 - INGENIERIA\BASE DE DATOS PRODUCTOS"

FOLDER_PATTERN = r"^(?P<ing>ING\d+)\s*-\s*(?P<part_no>.+?)-\((?P<material>[a-zA-Z0-9]+)[\s\-]+(?P<finish>.+?)\)\s*-\s*K(?P<k_factor>[0-9\.]*)\s*-\s*(?P<version>V\d+)-(?P<revision>R\d+)"

def classify_files_in_folder(folder_path, part_no, sku):
    """Clasifica los archivos de una subcarpeta de ingeniería"""
    try:
        all_files = os.listdir(folder_path)
    except Exception:
        return {}

    classified = {
        "pdf_orig": None,
        "control_pdf": None,
        "dxf": None,
        "slddrw": None,
        "sldprt": None,
        "step": None,
        "xlsx": None,
        "plano_validado": None,
        "vobo_pdf": None
    }
    
    pdf_candidates = []
    
    for f in all_files:
        f_lower = f.lower()
        if f_lower in ["thumbs.db", "desktop.ini"] or f.startswith("~$") or f_lower.endswith(".rar") or f_lower.endswith(".zip"):
            continue
        full_p = os.path.join(folder_path, f)
        if not os.path.isfile(full_p):
            continue

        if f_lower.endswith(".dxf"):
            classified["dxf"] = full_p
        elif f_lower.endswith(".slddrw"):
            classified["slddrw"] = full_p
        elif f_lower.endswith(".sldprt"):
            classified["sldprt"] = full_p
        elif f_lower.endswith(".step") or f_lower.endswith(".stp"):
            classified["step"] = full_p
        elif f_lower.endswith(".xlsx") or f_lower.endswith(".xls"):
            classified["xlsx"] = full_p
        elif f_lower.endswith(".pdf"):
            if "validado" in f_lower:
                classified["plano_validado"] = full_p
            elif "vobo" in f_lower or "primera" in f_lower:
                classified["vobo_pdf"] = full_p
            else:
                pdf_candidates.append(full_p)

    # Identificar Plano de Control vs Plano Original del Cliente
    if len(pdf_candidates) == 1:
        # Si solo hay uno, verificar si tiene el nombre del SKU o el número de pieza
        p_name = os.path.basename(pdf_candidates[0]).lower()
        if "rev" in p_name or "k" in p_name:
            classified["control_pdf"] = pdf_candidates[0]
        else:
            classified["pdf_orig"] = pdf_candidates[0]
            classified["control_pdf"] = pdf_candidates[0]
    elif len(pdf_candidates) >= 2:
        for p in pdf_candidates:
            p_name = os.path.basename(p).lower()
            if any(k in p_name for k in ["original", "orig", "cliente", "dibujo"]) or ("rev." in p_name and not "- k" in p_name):
                classified["pdf_orig"] = p
            elif any(k in p_name for k in ["control", "plano"]) or ("- k" in p_name) or ("v0" in p_name or "v1" in p_name or "v2" in p_name):
                classified["control_pdf"] = p
                
        # Si aún no se asignaron
        if not classified["pdf_orig"] and not classified["control_pdf"]:
            pdf_candidates.sort(key=len)
            classified["pdf_orig"] = pdf_candidates[0]
            classified["control_pdf"] = pdf_candidates[1]
        elif classified["control_pdf"] and not classified["pdf_orig"]:
            rem = [p for p in pdf_candidates if p != classified["control_pdf"]]
            if rem: classified["pdf_orig"] = rem[0]
        elif classified["pdf_orig"] and not classified["control_pdf"]:
            rem = [p for p in pdf_candidates if p != classified["pdf_orig"]]
            if rem: classified["control_pdf"] = rem[0]

    return classified

def inyectar_carpetas_red():
    print("=" * 80)
    print("🚀 INICIANDO INYECCIÓN DESDE RED Z:\\ A GOOGLE CLOUD STORAGE")
    print(f"Ruta Origen: {NETWORK_PATH}")
    print(f"Bucket Destino: gs://{DEFAULT_BUCKET_NAME}/Sin_Auditar/")
    print("=" * 80)

    if not os.path.exists(NETWORK_PATH):
        print(f"❌ ERROR: La ruta de red '{NETWORK_PATH}' no está accesible en este equipo.")
        return

    if not is_gcs_available():
        print("❌ ERROR: Google Cloud Storage no está autenticado. Verifique credentials/.")
        return

    initialize_database()
    bucket = get_bucket()

    all_dirs = sorted([d for d in os.listdir(NETWORK_PATH) if os.path.isdir(os.path.join(NETWORK_PATH, d))])
    print(f"📂 Total de carpetas encontradas en red: {len(all_dirs)}\n")

    parsed_pieces = []
    for d in all_dirs:
        clean_name = re.sub(r'[^\x00-\x7F]+', '', d.strip())
        m = re.match(FOLDER_PATTERN, clean_name, re.IGNORECASE)
        if not m:
            continue
        gd = m.groupdict()
        ing_code = gd["ing"].upper()
        part_no = gd["part_no"].strip()
        mat = gd["material"].strip()
        finish = gd["finish"].strip()
        k_val = int(float(gd["k_factor"])) if gd["k_factor"] and gd["k_factor"].replace(".", "").isdigit() else 48
        ver = gd["version"].upper()
        rev = gd["revision"].upper()
        sku = f"{part_no}-({mat} {finish}) - K{k_val} - {ver}-{rev}"
        full_dir = os.path.join(NETWORK_PATH, d)

        parsed_pieces.append({
            "ing": ing_code,
            "part_no": part_no,
            "material": mat,
            "finish": finish,
            "factor_k": k_val,
            "version": ver,
            "revision": rev,
            "sku": sku,
            "dir_path": full_dir,
            "folder_name": d
        })

    print(f"✅ Carpetas procesables con formato ING: {len(parsed_pieces)}")

    # Obtener espesores conocidos
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT material, espesor_nominal FROM materias_primas")
    mat_thickness = {r["material"]: r["espesor_nominal"] for r in c.fetchall()}

    # 1. Preparar lista de archivos a subir
    upload_tasks = []
    total_bytes = 0

    print("🔍 Analizando y clasificando archivos por carpeta...")
    for item in parsed_pieces:
        classified = classify_files_in_folder(item["dir_path"], item["part_no"], item["sku"])
        item["files"] = classified
        
        # Calcular dimensiones desde Excel si existe
        largo = 10.0
        ancho = 5.0
        if classified["xlsx"] and os.path.exists(classified["xlsx"]):
            try:
                df_c = pd.read_excel(classified["xlsx"], sheet_name="CORTE")
                df_c.columns = [str(x).strip().upper() for x in df_c.columns]
                if "DIM" in df_c.columns and len(df_c) >= 2:
                    largo = float(df_c["DIM"].iloc[0])
                    ancho = float(df_c["DIM"].iloc[1])
            except Exception:
                pass
        item["largo"] = largo
        item["ancho"] = ancho
        item["espesor"] = mat_thickness.get(item["material"], 0.060)

        # Evaluar completitud de documentos requeridos
        has_ctrl = classified["control_pdf"] is not None
        has_orig = classified["pdf_orig"] is not None
        has_dxf = classified["dxf"] is not None
        has_3d = (classified["step"] is not None) or (classified["sldprt"] is not None)
        has_xlsx = classified["xlsx"] is not None
        item["docs_completos"] = 1 if (has_ctrl and has_dxf and has_xlsx) else 0

        # Crear tareas de subida al Bucket
        blob_folder = f"Sin_Auditar/{item['ing']} - {item['sku']}"
        item["gcs_folder"] = f"gs://{DEFAULT_BUCKET_NAME}/{blob_folder}"
        item["gcs_paths"] = {}

        for k, src_f in classified.items():
            if src_f and os.path.exists(src_f):
                f_name = os.path.basename(src_f)
                dest_blob = f"{blob_folder}/{f_name}"
                f_size = os.path.getsize(src_f)
                upload_tasks.append((src_f, dest_blob, f_size, item, k))
                total_bytes += f_size
                item["gcs_paths"][k] = f"gs://{DEFAULT_BUCKET_NAME}/{dest_blob}"
            else:
                item["gcs_paths"][k] = None

    print(f"📦 Total de archivos a transferir a GCS: {len(upload_tasks)}")
    print(f"💾 Tamaño total a transferir: {total_bytes / (1024 * 1024):.2f} MB\n")

    # 2. Transferencia a Google Cloud Storage
    uploaded_count = 0
    skipped_count = 0
    bytes_done = 0
    lock = threading.Lock()
    start_time = time.time()
    total_tasks = len(upload_tasks)

    def do_upload(task):
        nonlocal uploaded_count, skipped_count, bytes_done
        src_path, dest_blob, size, _, _ = task
        blob = bucket.blob(dest_blob)
        try:
            if blob.exists():
                blob.reload()
                if blob.size == size:
                    with lock:
                        skipped_count += 1
                        bytes_done += size
                    return True
        except Exception:
            pass

        ok, _ = upload_file_to_gcs(src_path, dest_blob)
        with lock:
            if ok:
                uploaded_count += 1
                bytes_done += size
        return ok

    print("Transfiriendo archivos hacia Google Cloud Storage con 12 hilos concurrentes...")
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(do_upload, t): t for t in upload_tasks}
        completed = 0
        for f in as_completed(futures):
            completed += 1
            if completed % 50 == 0 or completed == total_tasks:
                pct = (completed / total_tasks) * 100
                elapsed = time.time() - start_time
                mb = bytes_done / (1024 * 1024)
                rate = mb / elapsed if elapsed > 0 else 0
                print(f"[{completed}/{total_tasks} - {pct:.1f}%] {mb:.1f} MB procesados ({rate:.2f} MB/s)")

    print(f"\n✅ Transferencia finalizada en {time.time() - start_time:.1f} segundos.")
    print(f"   Archivos nuevos subidos: {uploaded_count}")
    print(f"   Archivos existentes verificados: {skipped_count}\n")

    # 3. Registrar / Actualizar piezas en la base de datos
    print("🔄 Guardando las 206 piezas en la base de datos como 'Sin Auditar'...")
    cursor = conn.cursor()
    saved_db = 0

    for item in parsed_pieces:
        gp = item["gcs_paths"]
        cursor.execute(
            """
            INSERT INTO piezas (
                consecutivo_ing, numero_pieza, material, acabado_estandar, factor_k, version, revision, nombre_sku,
                espesor_materia_prima, ancho_materia_prima, largo_materia_prima, ruta_almacenamiento,
                archivo_dibujo_original, archivo_dxf, archivo_plano_control, archivo_plano_nativo_3d,
                archivo_dibujo_nativo_2d, archivo_excel_resumen, archivo_step,
                plano_validado_impreso, documento_primera_pieza,
                estatus_auditoria, documentos_completos, usuario_registro
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Sin Auditar', ?, 'Ingesta Red Z:\\')
            ON CONFLICT(nombre_sku) DO UPDATE SET
                consecutivo_ing = excluded.consecutivo_ing,
                ruta_almacenamiento = excluded.ruta_almacenamiento,
                archivo_dibujo_original = COALESCE(excluded.archivo_dibujo_original, piezas.archivo_dibujo_original),
                archivo_dxf = COALESCE(excluded.archivo_dxf, piezas.archivo_dxf),
                archivo_plano_control = COALESCE(excluded.archivo_plano_control, piezas.archivo_plano_control),
                archivo_plano_nativo_3d = COALESCE(excluded.archivo_plano_nativo_3d, piezas.archivo_plano_nativo_3d),
                archivo_dibujo_nativo_2d = COALESCE(excluded.archivo_dibujo_nativo_2d, piezas.archivo_dibujo_nativo_2d),
                archivo_excel_resumen = COALESCE(excluded.archivo_excel_resumen, piezas.archivo_excel_resumen),
                archivo_step = COALESCE(excluded.archivo_step, piezas.archivo_step),
                documentos_completos = excluded.documentos_completos
            """,
            (
                item["ing"], item["part_no"], item["material"], item["finish"], item["factor_k"], item["version"], item["revision"], item["sku"],
                item["espesor"], item["ancho"], item["largo"], item["gcs_folder"],
                gp.get("pdf_orig"), gp.get("dxf"), gp.get("control_pdf"), gp.get("slddrw"),
                gp.get("sldprt"), gp.get("xlsx"), gp.get("step"),
                gp.get("plano_validado"), gp.get("vobo_pdf"),
                item["docs_completos"]
            )
        )
        saved_db += 1

    conn.commit()
    conn.close()

    print(f"✅ ¡{saved_db} piezas registradas con éxito con estatus 'Sin Auditar'!")
    print("=" * 80)
    print("🎉 INYECCIÓN COMPLETADA. Listas para auditoría por el Administrador en la App.")
    print("=" * 80)

if __name__ == "__main__":
    inyectar_carpetas_red()
