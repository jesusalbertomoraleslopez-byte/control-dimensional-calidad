import os
import sys
import shutil
from src.database import initialize_database, get_connection
from src.pdf_generator import generate_first_piece_pdf, generate_spc_lote_pdf
from src.utils import calculate_spc_stats

def run_integration_test():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    print("=== INICIANDO PRUEBA DE INTEGRACIÓN Y VERIFICACIÓN ===")
    
    # 1. Initialize DB
    print("\n1. Inicializando Base de Datos...")
    initialize_database()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 2. Check Seed Data
    cursor.execute("SELECT count(*) FROM usuarios")
    users_count = cursor.fetchone()[0]
    print(f"   Usuarios en BD: {users_count}")
    
    cursor.execute("SELECT count(*) FROM materias_primas")
    mats_count = cursor.fetchone()[0]
    print(f"   Materias primas registradas: {mats_count}")
    
    cursor.execute("SELECT count(*) FROM glosario_documentos")
    glossary_count = cursor.fetchone()[0]
    print(f"   Documentos en Glosario: {glossary_count}")
    
    # 3. Register a component
    print("\n2. Registrando Pieza de Prueba...")
    sku = "12-A-6004-01-(16ga ANSI-61) - K48 - V3-R0"
    dest_dir = os.path.join(os.path.dirname(__file__), "src", "Proyectos", "END_FILLER", "Rev_R0", "FactorK_48", "Espesor_0.060")
    os.makedirs(dest_dir, exist_ok=True)
    
    # Clean previous record if exists
    cursor.execute("DELETE FROM piezas WHERE nombre_sku = ?", (sku,))
    conn.commit()
    
    cursor.execute(
        """
        INSERT INTO piezas (
            numero_pieza, material, acabado_estandar, factor_k, version, revision, nombre_sku,
            espesor_materia_prima, ancho_materia_prima, largo_materia_prima, ruta_almacenamiento,
            archivo_dibujo_original, archivo_dxf, archivo_plano_control, archivo_plano_nativo_3d,
            archivo_dibujo_nativo_2d, archivo_excel_resumen, archivo_step, usuario_registro
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "12-A-6004-01", "16ga", "ANSI-61", 48, "V3", "R0", sku,
            0.060, 3.527, 19.000, dest_dir,
            os.path.join(dest_dir, "Original.pdf"), os.path.join(dest_dir, f"{sku}.dxf"), 
            os.path.join(dest_dir, f"{sku}.pdf"), os.path.join(dest_dir, f"{sku}.slddrw"), 
            os.path.join(dest_dir, f"{sku}.sldprt"), os.path.join(dest_dir, f"{sku}.xlsx"),
            os.path.join(dest_dir, f"{sku}.step"), "Prueba_Automatizada"
        )
    )
    conn.commit()
    cursor.execute("SELECT id FROM piezas WHERE nombre_sku = ?", (sku,))
    piece_id = cursor.fetchone()[0]
    print(f"   Pieza '{sku}' registrada con ID: {piece_id}")
    
    # 4. Generate first piece validation backup
    print("\n3. Generando Reporte de Liberación de Primera Pieza...")
    cursor.execute("SELECT * FROM piezas WHERE id = ?", (piece_id,))
    piece_data = dict(cursor.fetchone())
    
    # Simulate uploads for validation
    val_pdf = os.path.join(dest_dir, f"Plano_Validado_{sku}.pdf")
    doc_primera = os.path.join(dest_dir, f"Reporte_Primera_Pieza_{sku}.pdf")
    
    piece_data["plano_validado_impreso"] = val_pdf
    piece_data["documento_primera_pieza"] = doc_primera
    
    pdf_bytes = generate_first_piece_pdf(piece_data)
    with open(doc_primera, "wb") as f:
        f.write(pdf_bytes)
        
    cursor.execute(
        "UPDATE piezas SET plano_validado_impreso = ?, documento_primera_pieza = ? WHERE id = ?",
        (val_pdf, doc_primera, piece_id)
    )
    conn.commit()
    print(f"   PDF Generado con éxito ({len(pdf_bytes)} bytes) en: {doc_primera}")
    
    # 5. Simulate floor capture (Láser)
    print("\n4. Simulando Captura en Piso (Estación Corte Láser, n=3)...")
    # Insert lote
    cursor.execute(
        """
        INSERT INTO lotes_control (pieza_id, operador, turno, estacion, estatus, v_dobladura, gauge_perfil)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (piece_id, "Operador Test", "Turno 1", "Corte Láser", "Aprobado", 10.0, "N/A")
    )
    lote_id = cursor.lastrowid
    print(f"   Lote Láser Creado con ID: {lote_id}")
    
    # Insert measurements
    laser_largo = [19.002, 18.998, 19.000]
    laser_ancho = [3.528, 3.526, 3.527]
    laser_diam = [0.312, 0.311, 0.312]
    
    for i in range(3):
        cursor.execute(
            """
            INSERT INTO mediciones (lote_id, muestra_numero, laser_largo, laser_ancho, laser_diametro)
            VALUES (?, ?, ?, ?, ?)
            """,
            (lote_id, i+1, laser_largo[i], laser_ancho[i], laser_diam[i])
        )
    conn.commit()
    print("   Mediciones registradas en BD.")
    
    # 6. Verify SPC calculations
    print("\n5. Validando Cálculos de Capacidad SPC (Cp/Cpk)...")
    largo_stats = calculate_spc_stats(laser_largo, 19.000, 18.985, 19.015)
    print(f"   [Largo] Media: {largo_stats['mean']:.4f}, StdDev: {largo_stats['std']:.4f}")
    print(f"   [Largo] Cp: {largo_stats['cp']:.2f}, Cpk: {largo_stats['cpk']:.2f} ({largo_stats['status_desc']})")
    
    # 7. Generate SPC batch report
    print("\n6. Generando Reporte de Respaldo SPC en PDF...")
    cursor.execute("SELECT * FROM lotes_control WHERE id = ?", (lote_id,))
    lote_data = dict(cursor.fetchone())
    lote_data["nombre_sku"] = sku
    
    cursor.execute("SELECT * FROM mediciones WHERE lote_id = ?", (lote_id,))
    meas_data = [dict(r) for r in cursor.fetchall()]
    
    pdf_stats = [
        {
            "name": "Dim 1 (Largo)", "mean": largo_stats["mean"], "std": largo_stats["std"], 
            "cp": largo_stats["cp"], "cpk": largo_stats["cpk"], "status_desc": largo_stats["status_desc"]
        }
    ]
    
    spc_pdf_bytes = generate_spc_lote_pdf(lote_data, meas_data, pdf_stats)
    spc_report_path = os.path.join(dest_dir, f"Reporte_SPC_Laser_Lote_{lote_id}.pdf")
    with open(spc_report_path, "wb") as f:
        f.write(spc_pdf_bytes)
    print(f"   PDF SPC Generado con éxito ({len(spc_pdf_bytes)} bytes) en: {spc_report_path}")
    
    # 7. Clean up test data from DB and disk
    print("\n7. Limpiando datos de prueba del sistema...")
    try:
        # Delete measurements
        cursor.execute("DELETE FROM mediciones WHERE lote_id = ?", (lote_id,))
        # Delete lote
        cursor.execute("DELETE FROM lotes_control WHERE id = ?", (lote_id,))
        # Delete piece
        cursor.execute("DELETE FROM piezas WHERE id = ?", (piece_id,))
        conn.commit()
        print("   Datos eliminados de la Base de Datos con éxito.")
    except Exception as e:
        print(f"   Error al limpiar Base de Datos: {e}")
        
    # Delete files
    for path in [doc_primera, spc_report_path, val_pdf]:
        if path and os.path.exists(path):
            try:
                os.remove(path)
                print(f"   Archivo de prueba eliminado: {os.path.basename(path)}")
            except Exception as e:
                print(f"   Error al eliminar archivo {os.path.basename(path)}: {e}")
                
    # Clean up dest_dir if empty
    if dest_dir and os.path.exists(dest_dir) and not os.listdir(dest_dir):
        try:
            os.rmdir(dest_dir)
            # Try cleaning parent directories if they are empty
            parent = os.path.dirname(dest_dir)
            for _ in range(4): # clean up empty folders up to Proyectos
                if os.path.exists(parent) and not os.listdir(parent) and os.path.basename(parent) != "Proyectos":
                    os.rmdir(parent)
                    parent = os.path.dirname(parent)
            print("   Directorios de prueba vacíos eliminados.")
        except Exception as e:
            print(f"   Error al limpiar directorios: {e}")
            
    conn.close()
    print("\n=== PRUEBA DE INTEGRACIÓN COMPLETADA CON ÉXITO ===")

if __name__ == "__main__":
    run_integration_test()
