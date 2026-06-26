import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_connection, initialize_database
from src.utils import calculate_spc_stats
from src.pdf_generator import generate_excel_spc_report_pdf

def test_flow():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    print("=== INICIANDO PRUEBA DE CONTROL ESTADÍSTICO DESDE EXCEL ===")
    
    # 1. Initialize database
    print("\n1. Inicializando base de datos...")
    initialize_database()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 2. Check if test piece exists, create if not
    sku = "12-A-6004-01-(16ga ANSI-61) - K48 - V3-R0"
    cursor.execute("SELECT id FROM piezas WHERE nombre_sku = ?", (sku,))
    piece_row = cursor.fetchone()
    
    design_excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_design.xlsx")
    
    # Create mock design Excel
    import pandas as pd
    corte_design = {
        "No.": [1, 2],
        "RESP": ["LASER", "LASER"],
        "DIM": [19.000, 3.527],
        "LIM.I": [18.985, 3.512],
        "LIM.S": [19.015, 3.542]
    }
    doblez_design = {
        "MEDIDA": ["A", "B"],
        "DIMENSION": [0.630, 1.250],
        "LIM.I": [0.615, 1.235],
        "LIM.S": [0.645, 1.265]
    }
    with pd.ExcelWriter(design_excel_path, engine="openpyxl") as writer:
        pd.DataFrame(corte_design).to_excel(writer, sheet_name="CORTE", index=False)
        pd.DataFrame(doblez_design).to_excel(writer, sheet_name="DOBLEZ", index=False)
        
    if not piece_row:
        print(f"   Creando pieza de prueba: {sku}")
        cursor.execute(
            """
            INSERT INTO piezas (
                numero_pieza, material, acabado_estandar, factor_k, version, revision, nombre_sku,
                espesor_materia_prima, ancho_materia_prima, largo_materia_prima, ruta_almacenamiento,
                archivo_excel_resumen, usuario_registro
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "12-A-6004-01", "16ga", "ANSI-61", 48, "V3", "R0", sku,
                0.060, 3.527, 19.000, "Proyectos/END_FILLER", design_excel_path, "Test_SPC"
            )
        )
        conn.commit()
        cursor.execute("SELECT id FROM piezas WHERE nombre_sku = ?", (sku,))
        piece_id = cursor.fetchone()[0]
    else:
        piece_id = piece_row["id"]
        cursor.execute("UPDATE piezas SET archivo_excel_resumen = ? WHERE id = ?", (design_excel_path, piece_id))
        conn.commit()
        
    print(f"   ID de la pieza asociada: {piece_id}")
    
    # Verify custom template generator
    from src.views.v3_control.v3_4_spc_excel import generate_custom_excel_template
    template_bytes = generate_custom_excel_template(design_excel_path)
    import io
    df_c_tpl = pd.read_excel(io.BytesIO(template_bytes), sheet_name="CORTE")
    assert "VALOR MFG" in df_c_tpl.columns
    assert pd.isna(df_c_tpl["VALOR MFG"].iloc[0])
    print("   Custom template generated and verified successfully.")
    
    # 3. Clean previous test measurements
    cursor.execute("DELETE FROM mediciones_excel WHERE pieza_id = ? AND excel_nombre LIKE 'Test_%'", (piece_id,))
    conn.commit()
    
    # 4. Insert mock Excel data
    print("\n2. Insertando mediciones simuladas de Excel...")
    corte_meds = [
        {"name": "Corte - No. 1", "nominal": 19.000, "li": 18.985, "ls": 19.015, "val_mfg": 19.002, "val_cal": 18.999},
        {"name": "Corte - No. 1", "nominal": 19.000, "li": 18.985, "ls": 19.015, "val_mfg": 19.004, "val_cal": 19.001},
        {"name": "Corte - No. 1", "nominal": 19.000, "li": 18.985, "ls": 19.015, "val_mfg": 18.998, "val_cal": 18.997},
    ]
    
    for idx, m in enumerate(corte_meds):
        filename = f"Test_Excel_Carga_{idx+1}.xlsx"
        cursor.execute(
            """
            INSERT INTO mediciones_excel (
                pieza_id, excel_nombre, estacion, dimension_nombre, nominal,
                limite_inferior, limite_superior, valor_mfg, vobo_mfg, valor_cal, vobo_cal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                piece_id, filename, "Corte Láser", m["name"], m["nominal"],
                m["li"], m["ls"], m["val_mfg"], "Aprobado", m["val_cal"], "Aprobado"
            )
        )
    conn.commit()
    print(f"   Insertadas {len(corte_meds)} mediciones de prueba.")
    
    # 5. Retrieve and compute stats
    print("\n3. Calculando estadísticas de capacidad SPC...")
    cursor.execute(
        """
        SELECT valor_cal, nominal, limite_inferior, limite_superior 
        FROM mediciones_excel 
        WHERE pieza_id = ? AND estacion = 'Corte Láser' AND dimension_nombre = 'Corte - No. 1'
        """, (piece_id,)
    )
    rows = cursor.fetchall()
    cal_vals = [r["valor_cal"] for r in rows]
    nominal = rows[0]["nominal"]
    li = rows[0]["limite_inferior"]
    ls = rows[0]["limite_superior"]
    
    stats = calculate_spc_stats(cal_vals, nominal, li, ls)
    print(f"   [Corte - No. 1] Muestras: {len(cal_vals)}")
    print(f"   [Corte - No. 1] Media: {stats['mean']:.4f}, StdDev: {stats['std']:.4f}")
    print(f"   [Corte - No. 1] Cp: {stats['cp']:.2f}, Cpk: {stats['cpk']:.2f} ({stats['status_desc']})")
    
    # 6. Verify PDF Report Generation
    print("\n4. Verificando generación del Reporte PDF...")
    corte_data = [
        {"No.": 1, "RESP": "LASER", "DIM": 19.000, "TOLERANCIA": "±0.0150", "VALOR MFG": 19.002, "ESTATUS_MFG": "🟢 PASA", "VALOR CAL": 18.999, "ESTATUS_CAL": "🟢 PASA"}
    ]
    doblez_data = [
        {"MEDIDA": "A", "DIMENSION": 0.630, "TOLERANCIA": "±0.0150", "VALOR MFG": 0.628, "ESTATUS_MFG": "🟢 PASA", "VALOR CAL": 0.631, "ESTATUS_CAL": "🟢 PASA"}
    ]
    hist_stats = [
        {"name": "Corte Láser - Corte - No. 1", "samples": len(cal_vals), "mean": stats["mean"], "std": stats["std"], "cp": stats["cp"], "cpk": stats["cpk"], "status_desc": stats["status_desc"]}
    ]
    
    pdf_bytes = generate_excel_spc_report_pdf(sku, "Test_Report.xlsx", corte_data, doblez_data, hist_stats)
    print(f"   PDF de reporte SPC generado con éxito ({len(pdf_bytes)} bytes).")
    
    conn.close()
    print("\n=== PRUEBA COMPLETADA CON ÉXITO ===")

if __name__ == "__main__":
    test_flow()
