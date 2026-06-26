import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from src.database import get_connection
from src.views.v3_control.v3_4_spc_excel import format_tolerance
from src.utils import calculate_spc_stats
from src.pdf_generator import generate_remision_pdf

def show_remision():
    st.title("3.3. Consolidación de Remisión Diaria")
    st.subheader("Liberación de Embarques, Consolidado e Indicadores SPC del Día")

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Select Date
    st.markdown("#### 📅 Selección de Periodo y SKU")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        selected_date = st.date_input("Fecha a Consolidar", value=datetime.today().date(), key="remision_date")
    
    # Load SKUs with inspections on that date
    cursor.execute(
        """
        SELECT DISTINCT p.id, p.nombre_sku 
        FROM inspecciones i
        JOIN piezas p ON i.pieza_id = p.id
        WHERE DATE(i.fecha_hora) = DATE(?)
        """, (str(selected_date),)
    )
    skus_on_date = cursor.fetchall()

    if not skus_on_date:
        st.info(f"💡 No hay registros de inspecciones de calidad cargadas para la fecha seleccionada ({selected_date.strftime('%d/%m/%Y')}).")
        st.info("Sugerencia: Cambia la fecha de consolidación o ve a '3.2. Carga de Inspección' para registrar nuevas piezas.")
        conn.close()
        return

    sku_options = {r["nombre_sku"]: r["id"] for r in skus_on_date}
    with col_d2:
        selected_sku = st.selectbox("Seleccione el SKU a Consolidar para Embarque:", list(sku_options.keys()))

    piece_id = sku_options[selected_sku]

    # 2. Fetch all inspections for this SKU on this date
    cursor.execute(
        """
        SELECT id, codigo_inspeccion, fecha_hora, operador, turno, estatus_general, excel_nombre
        FROM inspecciones
        WHERE pieza_id = ? AND DATE(fecha_hora) = DATE(?)
        """, (piece_id, str(selected_date))
    )
    inspections = cursor.fetchall()
    
    num_inspecciones = len(inspections)
    
    st.markdown("---")
    st.markdown(f"#### 📦 Inspecciones del Día para: **{selected_sku}**")
    
    # Display inspections table
    insp_list = []
    insp_ids = []
    all_approved = True
    
    for r in inspections:
        insp_ids.append(r["id"])
        if r["estatus_general"] != "Aprobado":
            all_approved = False
        insp_list.append({
            "Código": r["codigo_inspeccion"],
            "Fecha/Hora": pd.to_datetime(r["fecha_hora"]).strftime("%H:%M"),
            "Inspector": r["operador"],
            "Turno": r["turno"],
            "Estatus": "🟢 Aprobado" if r["estatus_general"] == "Aprobado" else "🔴 Fuera de Tol.",
            "Archivo Excel": r["excel_nombre"]
        })
        
    df_insp = pd.DataFrame(insp_list)
    st.dataframe(df_insp, use_container_width=True, hide_index=True)

    # 3. Consolidation SPC Analysis
    st.markdown("---")
    st.markdown("#### 📊 Análisis SPC Consolidado de la Remisión")
    
    # Load all measurements for the inspections of this day
    # We group by dimension
    cursor.execute(
        """
        SELECT DISTINCT dimension_nombre, estacion 
        FROM mediciones_excel 
        WHERE pieza_id = ? AND inspeccion_id IN ({})
        ORDER BY estacion, dimension_nombre
        """.format(",".join(["?"] * num_inspecciones)),
        [piece_id] + insp_ids
    )
    dimensions = cursor.fetchall()

    consolidated_stats = []
    
    if not dimensions:
        st.warning("No hay mediciones registradas para las inspecciones seleccionadas.")
    else:
        for dim in dimensions:
            d_name = dim["dimension_nombre"]
            d_est = dim["estacion"]
            
            # Fetch all valor_cal values for this dimension across the inspections of the day
            cursor.execute(
                """
                SELECT valor_cal, nominal, limite_inferior, limite_superior 
                FROM mediciones_excel 
                WHERE pieza_id = ? AND estacion = ? AND dimension_nombre = ? AND inspeccion_id IN ({})
                """.format(",".join(["?"] * num_inspecciones)),
                [piece_id, d_est, d_name] + insp_ids
            )
            rows_meas = cursor.fetchall()
            
            if rows_meas:
                nominal = float(rows_meas[0]["nominal"])
                li = float(rows_meas[0]["limite_inferior"])
                ls = float(rows_meas[0]["limite_superior"])
                
                vals = [r["valor_cal"] for r in rows_meas if r["valor_cal"] is not None]
                
                if len(vals) >= 2:
                    stats = calculate_spc_stats(vals, nominal, li, ls)
                    
                    consolidated_stats.append({
                        "Estación": d_est,
                        "Cota": d_name.replace("Corte - ", "").replace("Doblez - ", ""),
                        "Muestras": len(vals),
                        "Nominal": f"{nominal:.4f}",
                        "Media": f"{stats['mean']:.4f}",
                        "Desv. Est. (σ)": f"{stats['std']:.4f}",
                        "Cp": f"{stats['cp']:.2f}" if stats['cp'] is not None else "N/A",
                        "Cpk": f"{stats['cpk']:.2f}" if stats['cpk'] is not None else "N/A",
                        "Habilidad": stats["status_desc"]
                    })
                else:
                    # Not enough samples for Cp/Cpk
                    mean_val = np.mean(vals) if vals else 0.0
                    consolidated_stats.append({
                        "Estación": d_est,
                        "Cota": d_name.replace("Corte - ", "").replace("Doblez - ", ""),
                        "Muestras": len(vals),
                        "Nominal": f"{nominal:.4f}",
                        "Media": f"{mean_val:.4f}",
                        "Desv. Est. (σ)": "N/D",
                        "Cp": "N/D",
                        "Cpk": "N/D",
                        "Habilidad": "Muestras Insuficientes (<2)"
                    })

        df_spc = pd.DataFrame(consolidated_stats)
        st.dataframe(df_spc, use_container_width=True, hide_index=True)

    # 4. Generate Remisión PDF
    st.markdown("---")
    st.markdown("#### 🚚 Liberación de Embarque y Remisión")
    
    # Remisión Code Generator
    date_code = selected_date.strftime("%Y%m%d")
    remision_code = f"REM-{date_code}-{piece_id:03d}"
    
    status_text = "🟢 EMBARQUE APROBADO" if all_approved else "🔴 EMBARQUE EN REVISIÓN (CONTENCIÓN)"
    st.markdown(f"**Código de Remisión:** `{remision_code}`")
    st.markdown(f"**Estatus de Embarque:** **{status_text}**")
    
    st.markdown("Presione el botón inferior para consolidar las inspecciones y generar el reporte en PDF oficial para el embarque:")
    
    # PDF generation details
    if consolidated_stats:
        # Prepare list for PDF
        pdf_inspections = []
        for r in inspections:
            pdf_inspections.append({
                "code": r["codigo_inspeccion"],
                "time": pd.to_datetime(r["fecha_hora"]).strftime("%H:%M"),
                "operator": r["operador"],
                "shift": r["turno"],
                "status": r["estatus_general"]
            })
            
        pdf_stats = []
        for s in consolidated_stats:
            pdf_stats.append({
                "name": f"{s['Estación']} - {s['Cota']}",
                "samples": s["Muestras"],
                "mean": float(s["Media"]),
                "std": float(s["Desv. Est. (σ)"]) if s["Desv. Est. (σ)"] != "N/D" else 0.0,
                "cp": float(s["Cp"]) if s["Cp"] != "N/D" and s["Cp"] != "N/A" else None,
                "cpk": float(s["Cpk"]) if s["Cpk"] != "N/D" and s["Cpk"] != "N/A" else None,
                "status_desc": s["Habilidad"]
            })
            
        pdf_bytes = generate_remision_pdf(
            remision_code=remision_code,
            date_str=selected_date.strftime("%d/%m/%Y"),
            piece_sku=selected_sku,
            inspections_list=pdf_inspections,
            consolidated_stats=pdf_stats
        )
        
        st.download_button(
            label="📥 Descargar Reporte de Remisión y SPC Consolidado (PDF)",
            data=pdf_bytes,
            file_name=f"Reporte_Remision_{remision_code}.pdf",
            mime="application/pdf",
            key="btn_download_remision_pdf_red"
        )

    conn.close()
