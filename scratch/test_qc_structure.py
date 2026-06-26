import os
import sys
from datetime import datetime
from src.database import initialize_database, get_connection
from src.pdf_generator import generate_excel_spc_report_pdf, generate_remision_pdf

def test_qc_flow():
    print("=== INICIANDO VALIDACIÓN DEL FLUJO DE CALIDAD Y REMISIÓN ===")
    
    # 1. Initialize database
    print("\n1. Inicializando Base de Datos...")
    initialize_database()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 2. Check or create a test piece SKU
    sku = "12-A-6004-01-(16ga ANSI-61) - K48 - V3-R0"
    cursor.execute("SELECT id FROM piezas WHERE nombre_sku = ?", (sku,))
    piece_row = cursor.fetchone()
    if not piece_row:
        print("   Registrando pieza de prueba...")
        dest_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "Proyectos", "END_FILLER", "Rev_R0", "FactorK_48", "Espesor_0.060")
        os.makedirs(dest_dir, exist_ok=True)
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
                "Original.pdf", "Original.dxf", "Original.pdf", "Original.slddrw", "Original.sldprt", "Original.xlsx", "Original.step", "TestRunner"
            )
        )
        conn.commit()
        cursor.execute("SELECT id FROM piezas WHERE nombre_sku = ?", (sku,))
        piece_id = cursor.fetchone()[0]
    else:
        piece_id = piece_row[0]
        
    print(f"   ID de la Pieza a usar: {piece_id}")
    
    # 3. Simulate getting next inspection code
    cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM inspecciones")
    next_id = int(cursor.fetchone()[0])
    insp_code = f"INSP-{next_id:05d}"
    print(f"\n2. Siguiente Código Correlativo Calculado: {insp_code}")
    
    # 4. Insert an inspection
    print("   Insertando registro de inspección en BD...")
    excel_name = "Inspeccion_Prueba_Calidad.xlsx"
    operator = "Validador Automático"
    shift = "Turno 2"
    
    cursor.execute(
        """
        INSERT INTO inspecciones (codigo_inspeccion, pieza_id, fecha_hora, operador, turno, excel_nombre, estatus_general, calibre)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (insp_code, piece_id, datetime.now(), operator, shift, excel_name, "Aprobado", "16ga")
    )
    insp_db_id = cursor.lastrowid
    conn.commit()
    print(f"   Inspección registrada con ID de fila: {insp_db_id}")
    
    # 5. Insert mediciones_excel associated with that inspection
    print("\n3. Registrando mediciones individuales en mediciones_excel...")
    cursor.execute(
        """
        INSERT INTO mediciones_excel (
            pieza_id, excel_nombre, estacion, dimension_nombre, nominal,
            limite_inferior, limite_superior, valor_mfg, vobo_mfg, valor_cal, vobo_cal, inspeccion_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (piece_id, excel_name, "Corte Láser", "Corte - No. 1", 19.000, 18.985, 19.015, 19.002, "Aprobado", 19.001, "Aprobado", insp_db_id)
    )
    
    cursor.execute(
        """
        INSERT INTO mediciones_excel (
            pieza_id, excel_nombre, estacion, dimension_nombre, nominal,
            limite_inferior, limite_superior, valor_mfg, vobo_mfg, valor_cal, vobo_cal, inspeccion_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (piece_id, excel_name, "Doblez", "Doblez - A", 0.630, 0.615, 0.645, 0.628, "Aprobado", 0.629, "Aprobado", insp_db_id)
    )
    conn.commit()
    print("   Mediciones registradas exitosamente.")
    
    # 6. Verify foreign key links
    cursor.execute("SELECT count(*) FROM mediciones_excel WHERE inspeccion_id = ?", (insp_db_id,))
    count_meds = cursor.fetchone()[0]
    print(f"   Verificando enlace: se encontraron {count_meds} mediciones vinculadas a la inspección ID {insp_db_id}.")
    assert count_meds == 2, "Error: Las mediciones no se vincularon correctamente."
    
    # 7. Test PDF individual report generation
    print("\n4. Probando Generación del PDF de Inspección Individual...")
    # Prepare dummy data
    corte_list = [{"No.": "No. 1", "RESP": "MFG/CAL", "DIM": 19.000, "TOLERANCIA": "±0.015", "VALOR MFG": 19.002, "ESTATUS_MFG": "Aprobado", "VALOR CAL": 19.001, "ESTATUS_CAL": "Aprobado"}]
    doblez_list = [{"MEDIDA": "A", "DIMENSION": 0.630, "TOLERANCIA": "±0.015", "VALOR MFG": 0.628, "ESTATUS_MFG": "Aprobado", "VALOR CAL": 0.629, "ESTATUS_CAL": "Aprobado"}]
    stats_list = [{"name": "Corte - No. 1", "samples": 1, "mean": 19.001, "std": 0.0, "cp": 1.0, "cpk": 1.0, "status_desc": "Proceso Estable"}]
    
    pdf_bytes = generate_excel_spc_report_pdf(
        sku_selected=sku,
        excel_name=excel_name,
        corte_data=corte_list,
        doblez_data=doblez_list,
        stats_list=stats_list,
        insp_code=insp_code,
        insp_date=datetime.now().strftime('%d/%m/%Y %H:%M'),
        operator=operator,
        shift=shift
    )
    print(f"   Individual PDF generado con éxito ({len(pdf_bytes)} bytes)")
    assert len(pdf_bytes) > 0, "Error: El PDF de reporte individual está vacío."
    
    # 8. Test PDF consolidated remisión report generation
    print("\n5. Probando Generación del PDF de Remisión Consolidada...")
    inspections_list = [{
        "code": insp_code,
        "time": datetime.now().strftime("%H:%M"),
        "operator": operator,
        "shift": shift,
        "status": "Aprobado"
    }]
    consolidated_stats = [{
        "name": "Corte Láser - Corte - No. 1",
        "samples": 1,
        "mean": 19.001,
        "std": 0.0,
        "cp": 1.5,
        "cpk": 1.5,
        "status_desc": "Proceso Capaz"
    }]
    
    rem_code = f"REM-20260624-{piece_id:03d}"
    remision_pdf_bytes = generate_remision_pdf(
        remision_code=rem_code,
        date_str="24/06/2026",
        piece_sku=sku,
        inspections_list=inspections_list,
        consolidated_stats=consolidated_stats
    )
    print(f"   Consolidated PDF generado con éxito ({len(remision_pdf_bytes)} bytes)")
    assert len(remision_pdf_bytes) > 0, "Error: El PDF de remisión está vacío."
    
    # Cleanup DB test insertion
    print("\n6. Limpiando datos de prueba...")
    cursor.execute("DELETE FROM mediciones_excel WHERE inspeccion_id = ?", (insp_db_id,))
    cursor.execute("DELETE FROM inspecciones WHERE id = ?", (insp_db_id,))
    conn.commit()
    conn.close()
    
    print("\n=== PRUEBA DE FLUJO DE CALIDAD COMPLETADA CON ÉXITO ===")

if __name__ == "__main__":
    test_qc_flow()
