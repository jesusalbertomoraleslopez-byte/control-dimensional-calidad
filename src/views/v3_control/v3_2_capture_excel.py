import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import io
import os
from datetime import datetime
from src.database import get_connection
from src.utils import calculate_spc_stats, generate_gauss_chart
from src.pdf_generator import generate_excel_spc_report_pdf
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side, Protection
from openpyxl.formatting.rule import CellIsRule
from openpyxl.utils import get_column_letter

# Re-use tolerance formatting function
from src.views.v3_control.v3_4_spc_excel import format_tolerance, apply_excel_template_styling, generate_excel_template_empty, generate_custom_excel_template

def show_spc_excel():
    st.title("3.2. Carga e Importación de Inspección (Excel)")
    st.subheader("Carga Dinámica de Mediciones de Corte Láser y Doblez")

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Select registered piece SKU
    cursor.execute("SELECT id, nombre_sku, material, ruta_almacenamiento, archivo_excel_resumen FROM piezas")
    pieces = cursor.fetchall()

    fallback_sku = "12-A-6004-01-(16ga ANSI-61) - K48 - V3-R0"
    
    if not pieces:
        st.warning("⚠️ No hay piezas registradas en el sistema. Trabajando en Modo Demostración.")
        sku_selected = fallback_sku
        piece_id = 1
        dest_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Proyectos", "END_FILLER", "Rev_R0", "FactorK_48", "Espesor_0.060")
        archivo_excel_resumen = None
        piece_material = "16ga"
    else:
        piece_options = [r["nombre_sku"] for r in pieces]
        sku_selected = st.selectbox("Seleccione el SKU asociado:", piece_options)
        piece_row = [r for r in pieces if r["nombre_sku"] == sku_selected][0]
        piece_id = piece_row["id"]
        dest_dir = piece_row["ruta_almacenamiento"]
        archivo_excel_resumen = piece_row["archivo_excel_resumen"]
        piece_material = piece_row["material"]

    # Display copiable SKU button
    sku = sku_selected
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: space-between; 
                    background-color: #F8F9FA; border: 1px solid #D2D3D5; border-radius: 6px; 
                    padding: 0.5rem 1rem; margin-bottom: 0.8rem; font-family: 'Questrial', sans-serif;">
            <span style="font-family: 'Montserrat', sans-serif; font-weight: bold; font-size: 1.1rem; color: #111111;">
                {sku}
            </span>
            <button onclick="navigator.clipboard.writeText('{sku}').then(() => {{
                const btn = document.getElementById('copy-btn-spc');
                btn.innerHTML = '✅ Copiado!';
                btn.style.backgroundColor = '#16a34a';
                setTimeout(() => {{
                    btn.innerHTML = '📋 Copiar SKU';
                    btn.style.backgroundColor = '#EC2024';
                }}, 2000);
            }})" id="copy-btn-spc" style="
                background-color: #EC2024;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
                font-weight: bold;
                font-family: 'Questrial', sans-serif;
                cursor: pointer;
                transition: all 0.2s ease;
            " onmouseover="this.style.backgroundColor='#111111'" onmouseout="if(this.innerHTML!=='✅ Copiado!') this.style.backgroundColor='#EC2024'">
                📋 Copiar SKU
            </button>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Operator and metadata setup
    st.markdown("#### 👤 Datos de Control")
    col_meta1, col_meta2 = st.columns(2)
    with col_meta1:
        operator_name = st.text_input("Operador/Inspector de Calidad", value=st.session_state.get("nombre_completo", "Inspector Calidad"))
    with col_meta2:
        shift_name = st.selectbox("Turno", ["Turno 1", "Turno 2", "Turno 3"])

    st.markdown("---")

    # Template download action
    st.markdown("##### 📥 Descarga de Plantilla de Inspección para Capturas")
    st.markdown("Descargue la plantilla de Excel oficial con bloqueo de especificaciones de ingeniería:")

    has_design_excel = False
    if archivo_excel_resumen and os.path.exists(archivo_excel_resumen):
        has_design_excel = True

    if has_design_excel:
        st.success(f"✅ Formato de medición personalizado disponible para esta pieza.")
        excel_tpl_bytes = generate_custom_excel_template(archivo_excel_resumen)
    else:
        st.warning("⚠️ Esta pieza no cuenta con un Excel de especificaciones de diseño. Cargando plantilla genérica de demostración.")
        excel_tpl_bytes = generate_excel_template_empty()

    template_filename = f"Plantilla_Medicion_SPC_{sku_selected}.xlsx"
    st.download_button(
        label=f"📥 Descargar Formato de Medición para {sku_selected}",
        data=excel_tpl_bytes,
        file_name=template_filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="btn_download_spc_template_red"
    )

    st.markdown("---")

    # 2. Excel File Upload
    st.markdown("##### 📁 Cargar Mediciones Dimensionales de Excel")
    uploaded_file = st.file_uploader("Cargar Archivo Excel de SPC (.XLSX)", type=["xlsx"])

    corte_rows_data = []
    doblez_rows_data = []
    file_processed = False
    excel_name = ""

    if uploaded_file:
        excel_name = uploaded_file.name
        try:
            # Read sheets
            xls = pd.ExcelFile(uploaded_file)
            sheets = xls.sheet_names

            if "CORTE" not in sheets or "DOBLEZ" not in sheets:
                st.error("❌ El archivo Excel debe contener obligatoriamente las hojas de trabajo con nombres exactos: 'CORTE' y 'DOBLEZ'.")
            else:
                df_corte_raw = pd.read_excel(uploaded_file, sheet_name="CORTE")
                df_doblez_raw = pd.read_excel(uploaded_file, sheet_name="DOBLEZ")

                # Check columns case insensitively & trim spaces
                df_corte_raw.columns = [c.strip().upper() for c in df_corte_raw.columns]
                df_doblez_raw.columns = [c.strip().upper() for c in df_doblez_raw.columns]

                corte_required = ["NO.", "RESP", "DIM", "LIM.I", "LIM.S"]
                doblez_required = ["MEDIDA", "DIMENSION", "LIM.I", "LIM.S"]

                missing_corte = [col for col in corte_required if col not in df_corte_raw.columns]
                missing_doblez = [col for col in doblez_required if col not in df_doblez_raw.columns]

                if missing_corte:
                    st.error(f"❌ La hoja 'CORTE' no contiene todas las columnas requeridas: {missing_corte}")
                elif missing_doblez:
                    st.error(f"❌ La hoja 'DOBLEZ' no contiene todas las columnas requeridas: {missing_doblez}")
                else:
                    file_processed = True

                    # Process Corte
                    st.markdown("### ⚡ Resumen de Dimensiones - Corte Láser")
                    corte_list = []
                    for idx, row in df_corte_raw.iterrows():
                        dim_name = f"Corte - No. {int(row['NO.'])}"
                        nominal = float(row["DIM"])
                        li = float(row["LIM.I"])
                        ls = float(row["LIM.S"])

                        val_mfg = float(row["VALOR MFG"]) if "VALOR MFG" in row and not pd.isna(row["VALOR MFG"]) else None
                        val_cal = float(row["VALOR CAL"]) if "VALOR CAL" in row and not pd.isna(row["VALOR CAL"]) else None

                        vobo_mfg = str(row["VOBO MFG"]) if "VOBO MFG" in row and not pd.isna(row["VOBO MFG"]) else "N/A"
                        vobo_cal = str(row["VOBO CAL"]) if "VOBO CAL" in row and not pd.isna(row["VOBO CAL"]) else "N/A"

                        tol_formatted = format_tolerance(nominal, li, ls)
                        
                        dev_mfg = val_mfg - nominal if val_mfg is not None else None
                        dev_cal = val_cal - nominal if val_cal is not None else None

                        est_mfg = "🟢 PASA" if val_mfg is not None and li <= val_mfg <= ls else "🔴 FUERA" if val_mfg is not None else "N/D"
                        est_cal = "🟢 PASA" if val_cal is not None and li <= val_cal <= ls else "🔴 FUERA" if val_cal is not None else "N/D"

                        corte_list.append({
                            "No.": int(row["NO."]),
                            "RESP": str(row["RESP"]),
                            "DIM": nominal,
                            "LIM.I": li,
                            "LIM.S": ls,
                            "TOLERANCIA": tol_formatted,
                            "VALOR MFG": val_mfg,
                            "DEV. MFG": f"{dev_mfg:+.4f}" if dev_mfg is not None else "N/A",
                            "ESTATUS_MFG": est_mfg,
                            "VALOR CAL": val_cal,
                            "DEV. CAL": f"{dev_cal:+.4f}" if dev_cal is not None else "N/A",
                            "ESTATUS_CAL": est_cal,
                            "VOBO MFG": vobo_mfg,
                            "VOBO CAL": vobo_cal,
                            "DIM_NAME": dim_name
                        })

                    corte_rows_data = corte_list
                    df_corte_show = pd.DataFrame(corte_list)
                    st.table(df_corte_show[["No.", "RESP", "DIM", "TOLERANCIA", "VALOR MFG", "DEV. MFG", "ESTATUS_MFG", "VALOR CAL", "DEV. CAL", "ESTATUS_CAL"]])

                    # Process Doblez
                    st.markdown("### 📐 Resumen de Dimensiones - Doblez")
                    doblez_list = []
                    for idx, row in df_doblez_raw.iterrows():
                        dim_name = f"Doblez - {str(row['MEDIDA'])}"
                        nominal = float(row["DIMENSION"])
                        li = float(row["LIM.I"])
                        ls = float(row["LIM.S"])

                        val_mfg = float(row["VALOR MFG"]) if "VALOR MFG" in row and not pd.isna(row["VALOR MFG"]) else None
                        val_cal = float(row["VALOR CAL"]) if "VALOR CAL" in row and not pd.isna(row["VALOR CAL"]) else None

                        vobo_mfg = str(row["VOBO MFG"]) if "VOBO MFG" in row and not pd.isna(row["VOBO MFG"]) else "N/A"
                        vobo_cal = str(row["VOBO CAL"]) if "VOBO CAL" in row and not pd.isna(row["VOBO CAL"]) else "N/A"

                        tol_formatted = format_tolerance(nominal, li, ls)

                        dev_mfg = val_mfg - nominal if val_mfg is not None else None
                        dev_cal = val_cal - nominal if val_cal is not None else None

                        est_mfg = "🟢 PASA" if val_mfg is not None and li <= val_mfg <= ls else "🔴 FUERA" if val_mfg is not None else "N/D"
                        est_cal = "🟢 PASA" if val_cal is not None and li <= val_cal <= ls else "🔴 FUERA" if val_cal is not None else "N/D"

                        doblez_list.append({
                            "MEDIDA": str(row["MEDIDA"]),
                            "DIMENSION": nominal,
                            "LIM.I": li,
                            "LIM.S": ls,
                            "TOLERANCIA": tol_formatted,
                            "VALOR MFG": val_mfg,
                            "DEV. MFG": f"{dev_mfg:+.4f}" if dev_mfg is not None else "N/A",
                            "ESTATUS_MFG": est_mfg,
                            "VALOR CAL": val_cal,
                            "DEV. CAL": f"{dev_cal:+.4f}" if dev_cal is not None else "N/A",
                            "ESTATUS_CAL": est_cal,
                            "VOBO MFG": vobo_mfg,
                            "VOBO CAL": vobo_cal,
                            "DIM_NAME": dim_name
                        })

                    doblez_rows_data = doblez_list
                    df_doblez_show = pd.DataFrame(doblez_list)
                    st.table(df_doblez_show[["MEDIDA", "DIMENSION", "TOLERANCIA", "VALOR MFG", "DEV. MFG", "ESTATUS_MFG", "VALOR CAL", "DEV. CAL", "ESTATUS_CAL"]])

                    # 3. Save to DB Button
                    st.markdown("##### 💾 Registrar Inspección")
                    if st.button("💾 Guardar Inspección en Base de Datos", key="btn_save_excel_spc_blue"):
                        try:
                            # 1. Determine general status
                            all_ok = True
                            for r in corte_list:
                                if r["ESTATUS_MFG"] == "🔴 FUERA" or r["ESTATUS_CAL"] == "🔴 FUERA":
                                    all_ok = False
                            for r in doblez_list:
                                if r["ESTATUS_MFG"] == "🔴 FUERA" or r["ESTATUS_CAL"] == "🔴 FUERA":
                                    all_ok = False
                            
                            status_general = "Aprobado" if all_ok else "Fuera de Tolerancia"

                            # 2. Get next inspection ID and code
                            cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM inspecciones")
                            next_id = int(cursor.fetchone()[0])
                            insp_code = f"INSP-{next_id:05d}"

                            # 3. Insert into Inspecciones
                            cursor.execute(
                                """
                                INSERT INTO inspecciones (codigo_inspeccion, pieza_id, fecha_hora, operador, turno, excel_nombre, estatus_general, calibre)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (insp_code, piece_id, datetime.now(), operator_name, shift_name, excel_name, status_general, piece_material)
                            )
                            inspeccion_db_id = cursor.lastrowid

                            # 4. Insert Corte Laser measurements
                            for r in corte_list:
                                cursor.execute(
                                    """
                                    INSERT INTO mediciones_excel (
                                        pieza_id, excel_nombre, estacion, dimension_nombre, nominal,
                                        limite_inferior, limite_superior, valor_mfg, vobo_mfg, valor_cal, vobo_cal, inspeccion_id
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (
                                        piece_id, excel_name, "Corte Láser", r["DIM_NAME"], r["DIM"],
                                        r["LIM.I"], r["LIM.S"], r["VALOR MFG"], r["VOBO MFG"], r["VALOR CAL"], r["VOBO CAL"], inspeccion_db_id
                                    )
                                )
                            # 5. Insert Doblez measurements
                            for r in doblez_list:
                                cursor.execute(
                                    """
                                    INSERT INTO mediciones_excel (
                                        pieza_id, excel_nombre, estacion, dimension_nombre, nominal,
                                        limite_inferior, limite_superior, valor_mfg, vobo_mfg, valor_cal, vobo_cal, inspeccion_id
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (
                                        piece_id, excel_name, "Doblez", r["DIM_NAME"], r["DIMENSION"],
                                        r["LIM.I"], r["LIM.S"], r["VALOR MFG"], r["VOBO MFG"], r["VALOR CAL"], r["VOBO CAL"], inspeccion_db_id
                                    )
                                )
                            conn.commit()
                            st.success(f"✅ ¡Inspección {insp_code} registrada exitosamente para el archivo '{excel_name}' en la Base de Datos!")
                            
                            # Habilitar descarga inmediata del PDF generado
                            st.markdown("##### 📄 Descargar Reporte de esta Inspección")
                            
                            # Retrieve stats for PDF report
                            hist_stats = []
                            cursor.execute(
                                "SELECT DISTINCT dimension_nombre, estacion FROM mediciones_excel WHERE pieza_id = ? ORDER BY estacion, dimension_nombre",
                                (piece_id,)
                            )
                            dimensions_available = cursor.fetchall()
                            for dim_row in dimensions_available:
                                d_name = dim_row["dimension_nombre"]
                                d_est = dim_row["estacion"]
                                df_dim = pd.read_sql_query(
                                    "SELECT valor_cal, nominal, limite_inferior, limite_superior FROM mediciones_excel WHERE pieza_id = ? AND estacion = ? AND dimension_nombre = ?",
                                    conn, params=(piece_id, d_est, d_name)
                                )
                                if len(df_dim) >= 2:
                                    d_nominal = float(df_dim["nominal"].iloc[0])
                                    d_li = float(df_dim["limite_inferior"].iloc[0])
                                    d_ls = float(df_dim["limite_superior"].iloc[0])
                                    d_vals = df_dim["valor_cal"].dropna().tolist()
                                    d_stats = calculate_spc_stats(d_vals, d_nominal, d_li, d_ls)
                                    hist_stats.append({
                                        "name": f"{d_est} - {d_name}", "samples": len(d_vals), "mean": d_stats["mean"], "std": d_stats["std"],
                                        "cp": d_stats["cp"], "cpk": d_stats["cpk"], "status_desc": d_stats["status_desc"]
                                    })
                            
                            rep_pdf_bytes = generate_excel_spc_report_pdf(
                                sku_selected, excel_name, corte_list, doblez_list, hist_stats,
                                insp_code=insp_code,
                                insp_date=datetime.now().strftime('%d/%m/%Y %H:%M'),
                                operator=operator_name,
                                shift=shift_name
                            )
                            
                            st.download_button(
                                label=f"📥 Descargar Reporte de Inspección {insp_code} (PDF)",
                                data=rep_pdf_bytes,
                                file_name=f"Reporte_{insp_code}_{sku_selected.replace(' ', '_')}.pdf",
                                mime="application/pdf",
                                key="btn_download_new_insp_pdf"
                            )

                        except Exception as ex:
                            st.error(f"Error al guardar datos de inspección: {str(ex)}")

        except Exception as e:
            st.error(f"Error al procesar el archivo Excel: {str(e)}")

    st.markdown("---")

    # 4. Simulation Tool for Demo/Testing
    st.markdown("##### 🧪 Generar Lotes Simulados de Calidad (Para Análisis SPC)")
    st.markdown("""
        Los cálculos de capacidad de proceso ($C_p$/$C_{pk}$) e histogramas requieren muestras de múltiples piezas cargadas históricamente.
        Presione el botón de abajo para simular e insertar **25 reportes de control dimensional** con variación aleatoria real.
        Esto generará automáticamente 25 registros en el histórico de inspecciones (`INSP-XXXXX`).
    """)
    if st.button("🧪 Generar e Insertar 25 Lotes de Prueba en BD", key="btn_generate_sim_spc_blue"):
        try:
            sim_corte_spec = [
                {"name": "Corte - No. 1", "nominal": 19.000, "li": 18.985, "ls": 19.015, "std": 0.0035},
                {"name": "Corte - No. 2", "nominal": 3.527, "li": 3.512, "ls": 3.542, "std": 0.0040},
                {"name": "Corte - No. 3", "nominal": 0.312, "li": 0.297, "ls": 0.327, "std": 0.0030}
            ]
            sim_doblez_spec = [
                {"name": "Doblez - A", "nominal": 0.630, "li": 0.615, "ls": 0.645, "std": 0.0045},
                {"name": "Doblez - B", "nominal": 1.250, "li": 1.235, "ls": 1.265, "std": 0.0050},
                {"name": "Doblez - C", "nominal": 1.880, "li": 1.865, "ls": 1.895, "std": 0.0045},
                {"name": "Doblez - D", "nominal": 0.380, "li": 0.365, "ls": 0.395, "std": 0.0055},
                {"name": "Doblez - E", "nominal": 18.630, "li": 18.615, "ls": 18.645, "std": 0.0060}
            ]
            
            # Generate 25 records
            for run_idx in range(1, 26):
                # 1. Get next inspection ID
                cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM inspecciones")
                next_id = int(cursor.fetchone()[0])
                sim_code = f"INSP-{next_id:05d}"
                sim_filename = f"Reporte_Piso_Simulado_Pieza_{run_idx}.xlsx"
                
                # Alternate operators & shifts
                sim_operator = "Inspector Automático" if run_idx % 2 == 0 else "Auditor Calidad"
                sim_shift = f"Turno {(run_idx % 3) + 1}"
                
                # Check status
                all_sim_ok = True
                
                # 2. Insert into Inspecciones
                cursor.execute(
                    """
                    INSERT INTO inspecciones (codigo_inspeccion, pieza_id, fecha_hora, operador, turno, excel_nombre, estatus_general, calibre)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (sim_code, piece_id, datetime.now(), sim_operator, sim_shift, sim_filename, "Aprobado", piece_material)
                )
                sim_db_id = cursor.lastrowid
                
                # Corte Laser
                for c_spec in sim_corte_spec:
                    mfg_val = float(np.random.normal(c_spec["nominal"] + 0.001, c_spec["std"]))
                    cal_val = float(np.random.normal(c_spec["nominal"] - 0.0005, c_spec["std"] * 0.9))
                    
                    if not (c_spec["li"] <= cal_val <= c_spec["ls"]):
                        all_sim_ok = False
                        
                    cursor.execute(
                        """
                        INSERT INTO mediciones_excel (
                            pieza_id, excel_nombre, estacion, dimension_nombre, nominal,
                            limite_inferior, limite_superior, valor_mfg, vobo_mfg, valor_cal, vobo_cal, inspeccion_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            piece_id, sim_filename, "Corte Láser", c_spec["name"], c_spec["nominal"],
                            c_spec["li"], c_spec["ls"], mfg_val, "Aprobado", cal_val, "Aprobado", sim_db_id
                        )
                    )
                    
                # Doblez
                for d_spec in sim_doblez_spec:
                    mfg_val = float(np.random.normal(d_spec["nominal"] + 0.0015, d_spec["std"]))
                    cal_val = float(np.random.normal(d_spec["nominal"] - 0.0002, d_spec["std"] * 0.85))
                    
                    if not (d_spec["li"] <= cal_val <= d_spec["ls"]):
                        all_sim_ok = False
                        
                    cursor.execute(
                        """
                        INSERT INTO mediciones_excel (
                            pieza_id, excel_nombre, estacion, dimension_nombre, nominal,
                            limite_inferior, limite_superior, valor_mfg, vobo_mfg, valor_cal, vobo_cal, inspeccion_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            piece_id, sim_filename, "Doblez", d_spec["name"], d_spec["nominal"],
                            d_spec["li"], d_spec["ls"], mfg_val, "Aprobado", cal_val, "Aprobado", sim_db_id
                        )
                    )
                
                # Update status of simulation
                if not all_sim_ok:
                    cursor.execute(
                        "UPDATE inspecciones SET estatus_general = 'Fuera de Tolerancia' WHERE id = ?",
                        (sim_db_id,)
                    )
            
            conn.commit()
            st.success("✅ ¡25 lotes simulados insertados con éxito en la base de datos y vinculados a códigos históricos `INSP-XXXXX`!")
            
        except Exception as e_sim:
            st.error(f"Error al generar lotes simulados: {str(e_sim)}")

    conn.close()
