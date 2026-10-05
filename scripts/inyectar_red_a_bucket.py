# -*- coding: utf-8 -*-
"""
Script Oficial de Sincronización Incremental Inteligente de Ingeniería a Google Cloud Storage
SIGRAMA - Control Dimensional y Calidad Industrial 4.0

Garantiza la sincronización incremental estricta (Smart Incremental Sync):
1. Consulta el inventario completo existente en Google Cloud Storage (Sin_Auditar/ y Auditadas/).
2. Compara cada archivo local contra la nube por nombre y tamaño exacto en bytes.
3. OMITE automáticamente cualquier archivo que ya exista en la nube con tamaño idéntico.
4. Sube ÚNICAMENTE los archivos faltantes o que hayan sido modificados por el equipo de diseño.
5. Evita cargos innecesarios de red y de operaciones de escritura en Google Cloud Platform.
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

def inyectar_carpetas_red(logger=print, progress_cb=None):
    """
    Sincronización incremental estricta:
    Solo sube archivos nuevos o modificados.
    """
    logger("=" * 75)
    logger("🚀 INICIANDO SINCRONIZACIÓN INCREMENTAL INTELIGENTE (SIGRAMA 4.0)")
    logger(f"Ruta Origen (LAN): {NETWORK_PATH}")
    logger(f"Bucket Destino: gs://{DEFAULT_BUCKET_NAME}/")
    logger("=" * 75)

    if not os.path.exists(NETWORK_PATH):
        err_msg = f"❌ ERROR: La ruta de red '{NETWORK_PATH}' no está accesible en este equipo."
        logger(err_msg)
        return {"error": err_msg}

    if not is_gcs_available():
        err_msg = "❌ ERROR: Google Cloud Storage no está autenticado. Verifique credentials/."
        logger(err_msg)
        return {"error": err_msg}

    initialize_database()
    bucket = get_bucket()

    # ── PASO 1: OBTENER INVENTARIO GLOBAL DE GOOGLE CLOUD EN UNA SOLA CONSULTA ──
    logger("☁️ [1/4] Consultando inventario actual en Google Cloud Storage...")
    existing_blobs = {}
    try:
        for b in bucket.list_blobs(prefix="Sin_Auditar/"):
            existing_blobs[b.name] = b.size
        for b in bucket.list_blobs(prefix="Auditadas/"):
            existing_blobs[b.name] = b.size
        logger(f"   Inventario remoto: {len(existing_blobs)} archivos ya presentes en la nube.")
    except Exception as e:
        logger(f"   ⚠️ Advertencia al consultar inventario remoto: {e}")

    # ── PASO 2: ESCANEAR Y CLASIFICAR CARPETAS LOCALES ──
    all_dirs = sorted([d for d in os.listdir(NETWORK_PATH) if os.path.isdir(os.path.join(NETWORK_PATH, d))])
    logger(f"📁 [2/4] Analizando {len(all_dirs)} carpetas en la unidad de ingeniería Z:\\...")

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

    logger(f"   Carpetas válidas identificadas con consecutivo ING: {len(parsed_pieces)}")

    # Obtener espesores conocidos
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT material, espesor_nominal FROM materias_primas")
    mat_thickness = {r["material"]: r["espesor_nominal"] for r in c.fetchall()}

    # ── PASO 3: COMPARAR ARCHIVO POR ARCHIVO CONTRA LA NUBE (FILTRADO ESTRICTO) ──
    logger("🔍 [3/4] Comparando archivos locales vs nube (Detección de faltantes)...")
    upload_tasks = []
    skipped_count = 0
    already_synced_bytes = 0
    missing_bytes = 0
    total_local_files = 0

    for item in parsed_pieces:
        classified = classify_files_in_folder(item["dir_path"], item["part_no"], item["sku"])
        item["files"] = classified
        
        # Dimensiones desde Excel
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

        # Evaluar completitud
        has_ctrl = classified["control_pdf"] is not None
        has_orig = classified["pdf_orig"] is not None
        has_dxf = classified["dxf"] is not None
        has_xlsx = classified["xlsx"] is not None
        item["docs_completos"] = 1 if (has_ctrl and has_dxf and has_xlsx) else 0

        # Determinar si la carpeta ya está en Auditadas/ o Sin_Auditar/
        blob_folder_sin = f"Sin_Auditar/{item['ing']} - {item['sku']}"
        blob_folder_aud = f"Auditadas/{item['ing']} - {item['sku']}"
        
        is_already_audited = any(k.startswith(blob_folder_aud) for k in existing_blobs)
        active_folder = blob_folder_aud if is_already_audited else blob_folder_sin
        item["gcs_folder"] = f"gs://{DEFAULT_BUCKET_NAME}/{active_folder}"
        item["gcs_paths"] = {}

        for k, src_f in classified.items():
            if src_f and os.path.exists(src_f):
                total_local_files += 1
                f_name = os.path.basename(src_f)
                dest_blob_sin = f"{blob_folder_sin}/{f_name}"
                dest_blob_aud = f"{blob_folder_aud}/{f_name}"
                f_size = os.path.getsize(src_f)

                # Comprobación de existencia idéntica
                if dest_blob_aud in existing_blobs and existing_blobs[dest_blob_aud] == f_size:
                    skipped_count += 1
                    already_synced_bytes += f_size
                    item["gcs_paths"][k] = f"gs://{DEFAULT_BUCKET_NAME}/{dest_blob_aud}"
                elif dest_blob_sin in existing_blobs and existing_blobs[dest_blob_sin] == f_size:
                    skipped_count += 1
                    already_synced_bytes += f_size
                    item["gcs_paths"][k] = f"gs://{DEFAULT_BUCKET_NAME}/{dest_blob_sin}"
                else:
                    # Falta en la nube o cambió de tamaño -> SUBIR ÚNICAMENTE ESTE
                    upload_tasks.append((src_f, dest_blob_sin, f_size, item, k))
                    missing_bytes += f_size
                    item["gcs_paths"][k] = f"gs://{DEFAULT_BUCKET_NAME}/{dest_blob_sin}"
            else:
                item["gcs_paths"][k] = None

    logger(f"📊 RESUMEN DEL ANÁLISIS DE SINCRONIZACIÓN:")
    logger(f"   • Total de archivos en red local: {total_local_files}")
    logger(f"   • Archivos ya presentes e idénticos en GCP (OMITIDOS - $0.00 costo): {skipped_count} ({already_synced_bytes / (1024*1024):.2f} MB)")
    logger(f"   • Archivos FALTANTES o MODIFICADOS a subir: {len(upload_tasks)} ({missing_bytes / (1024*1024):.2f} MB)")

    # ── PASO 4: TRANSFERENCIA EXCLUSIVA DE ARCHIVOS FALTANTES ──
    uploaded_count = 0
    if len(upload_tasks) == 0:
        logger("🎉 ¡Tu repositorio en Google Cloud está 100% AL DÍA!")
        logger("   No hay archivos faltantes ni modificados. Cero peticiones de subida a GCP.")
        if progress_cb:
            progress_cb(100)
    else:
        logger(f"🚀 [4/4] Transfiriendo ÚNICAMENTE los {len(upload_tasks)} archivos faltantes...")
        lock = threading.Lock()
        bytes_done = 0
        total_tasks = len(upload_tasks)
        start_time = time.time()

        def do_upload(task):
            nonlocal uploaded_count, bytes_done
            src_path, dest_blob, size, _, _ = task
            ok, _ = upload_file_to_gcs(src_path, dest_blob)
            with lock:
                if ok:
                    uploaded_count += 1
                    bytes_done += size
                    logger(f"   [SUBIDO] {os.path.basename(src_path)} ({size / 1024:.1f} KB)")
            return ok

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(do_upload, t): t for t in upload_tasks}
            completed = 0
            for f in as_completed(futures):
                completed += 1
                if progress_cb:
                    pct = int((completed / total_tasks) * 100)
                    progress_cb(pct)

        logger(f"✅ Subida de faltantes finalizada en {time.time() - start_time:.1f} segundos.")
        logger(f"   Archivos subidos exitosamente: {uploaded_count}/{total_tasks}")

    # ── PASO 5: ACTUALIZAR BASE DE DATOS SIN DEGRADAR AUDITORÍAS PREVIAS ──
    logger("🔄 Actualizando catálogo en la base de datos...")
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
                ruta_almacenamiento = CASE WHEN piezas.estatus_auditoria = 'Auditada' THEN piezas.ruta_almacenamiento ELSE excluded.ruta_almacenamiento END,
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

    logger(f"💾 Catálogo de base de datos sincronizado ({saved_db} piezas).")
    logger("=" * 75)

    return {
        "total_scanned": total_local_files,
        "skipped": skipped_count,
        "uploaded": uploaded_count,
        "missing_bytes": missing_bytes,
        "already_bytes": already_synced_bytes
    }

if __name__ == "__main__":
    inyectar_carpetas_red()
