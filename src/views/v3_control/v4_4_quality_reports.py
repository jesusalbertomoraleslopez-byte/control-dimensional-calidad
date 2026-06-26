import streamlit as st
import os
import pandas as pd
from datetime import datetime
from src.database import get_connection
from src.pdf_generator import generate_excel_spc_report_pdf, generate_spc_lote_pdf, generate_remision_pdf
from src.utils import calculate_spc_stats

def show_quality_reports():
    st.title("4.4. Impresión de Reportes de Calidad")
    st.subheader("Consola Central de Reportes SPC y Liberaciones de Calidad")
    
    st.markdown("""
    Consulte y descargue en formato PDF los reportes individuales de inspección por Excel,
    los reportes de control estadístico (SPC) manuales por lote de planta,
    y consolide la remisión diaria de embarque.
    """)
    
    tab_excel, tab_lotes, tab_remisiones = st.tabs([
        "📊 Reportes de Inspección (Excel)",
        "🏭 Reportes de Lote (SPC Planta)",
        "🚚 Remisiones y Embarques Consolidados"
    ])
    
    conn = get_connection()
    cursor = conn.cursor()
    
    with tab_excel:
        st.markdown("#### Histórico de Reportes de Inspección Individuales")
        st.markdown("Consulte el histórico de inspecciones y descargue el reporte individual PDF asociado.")
        
        # Load all inspections
        df_inspecciones = pd.read_sql_query("""
            SELECT i.id, i.codigo_inspeccion, i.fecha_hora, p.nombre_sku, i.operador, i.turno, i.estatus_general, i.excel_nombre, i.pieza_id
            FROM inspecciones i
            JOIN piezas p ON i.pieza_id = p.id
            ORDER BY i.id DESC
        """, conn)
        
        if len(df_inspecciones) == 0:
            st.info("💡 No hay inspecciones de Excel registradas en el histórico.")
        else:
            st.dataframe(
                df_inspecciones[["codigo_inspeccion", "fecha_hora", "nombre_sku", "operador", "turno", "estatus_general", "excel_nombre"]].rename(columns={
                    "codigo_inspeccion": "Código",
                    "fecha_hora": "Fecha/Hora",
                    "nombre_sku": "SKU",
                    "operador": "Operador",
                    "turno": "Turno",
                    "estatus_general": "Estatus",
                    "excel_nombre": "Archivo Origen"
                }),
                use_container_width=True
            )
            
            selected_insp_code = st.selectbox(
                "Seleccione Inspección para descargar Reporte:", 
                df_inspecciones["codigo_inspeccion"].tolist(),
                key="sb_quality_inspections"
            )
            
            if selected_insp_code:
                insp_row = df_inspecciones[df_inspecciones["codigo_inspeccion"] == selected_insp_code].iloc[0]
                insp_id = int(insp_row["id"])
                piece_id = int(insp_row["pieza_id"])
                sku_selected = insp_row["nombre_sku"]
                excel_name = insp_row["excel_nombre"]
                
                # Fetch measurements for this inspection
                cursor.execute("SELECT * FROM mediciones_excel WHERE inspeccion_id = ?", (insp_id,))
                meas_rows = [dict(r) for r in cursor.fetchall()]
                
                corte_list = []
                doblez_list = []
                for m in meas_rows:
                    if m["estacion"] == "Corte Láser":
                        corte_list.append({
                            "DIM_NAME": m["dimension_nombre"],
                            "DIM": m["nominal"],
                            "LIM.I": m["limite_inferior"],
                            "LIM.S": m["limite_superior"],
                            "VALOR MFG": m["valor_mfg"],
                            "VOBO MFG": m["vobo_mfg"],
                            "VALOR CAL": m["valor_cal"],
                            "VOBO CAL": m["vobo_cal"]
                        })
                    else:
                        corte_list.append({
                            "DIM_NAME": m["dimension_nombre"],
                            "DIMENSION": m["nominal"],
                            "LIM.I": m["limite_inferior"],
                            "LIM.S": m["limite_superior"],
                            "VALOR MFG": m["valor_mfg"],
                            "VOBO MFG": m["vobo_mfg"],
                            "VALOR CAL": m["valor_cal"],
                            "VOBO CAL": m["vobo_cal"]
                        }) if False else doblez_list.append({
                            "DIM_NAME": m["dimension_nombre"],
                            "DIMENSION": m["nominal"],
                            "LIM.I": m["limite_inferior"],
                            "LIM.S": m["limite_superior"],
                            "VALOR MFG": m["valor_mfg"],
                            "VOBO MFG": m["vobo_mfg"],
                            "VALOR CAL": m["valor_cal"],
                            "VOBO CAL": m["vobo_cal"]
                        })
                
                # Calculate stats
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
                            "name": f"{d_est} - {d_name}", 
                            "samples": len(d_vals), 
                            "mean": d_stats["mean"], 
                            "std": d_stats["std"],
                            "cp": d_stats["cp"], 
                            "cpk": d_stats["cpk"], 
                            "status_desc": d_stats["status_desc"]
                        })
                
                # Generate PDF bytes
                try:
                    rep_pdf_bytes = generate_excel_spc_report_pdf(
                        sku_selected=sku_selected,
                        excel_name=excel_name,
                        corte_data=corte_list,
                        doblez_data=doblez_list,
                        stats_list=hist_stats,
                        insp_code=selected_insp_code,
                        insp_date=pd.to_datetime(insp_row["fecha_hora"]).strftime('%d/%m/%Y %H:%M'),
                        operator=insp_row["operador"],
                        shift=insp_row["turno"]
                    )
                    
                    st.download_button(
                        label=f"📥 Descargar PDF Reporte {selected_insp_code}",
                        data=rep_pdf_bytes,
                        file_name=f"Reporte_{selected_insp_code}_{sku_selected.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        key=f"dl_insp_pdf_{insp_id}",
                        use_container_width=True
                    )
                except Exception as ex:
                    st.error(f"Error al generar reporte PDF para {selected_insp_code}: {str(ex)}")

    with tab_lotes:
        st.markdown("#### Reportes de Lotes de Producción (Captura Manual)")
        st.markdown("Descargue los reportes de control estadístico (SPC) generados a partir de las capturas de inspección en piso.")
        
        # Load all lotes
        df_lotes = pd.read_sql_query("""
            SELECT l.id, l.fecha_captura, p.nombre_sku, l.estacion, l.operador, l.turno, l.estatus
            FROM lotes_control l
            JOIN piezas p ON l.pieza_id = p.id
            ORDER BY l.id DESC
        """, conn)
        
        if len(df_lotes) == 0:
            st.info("💡 No hay lotes de producción registrados.")
        else:
            st.dataframe(
                df_lotes.rename(columns={
                    "id": "ID Lote",
                    "fecha_captura": "Fecha Captura",
                    "nombre_sku": "SKU Componente",
                    "estacion": "Estación",
                    "operador": "Operador",
                    "turno": "Turno",
                    "estatus": "Estatus"
                }),
                use_container_width=True,
                hide_index=True
            )
            
            selected_lote_id = st.selectbox(
                "Seleccione ID de Lote para Reporte:", 
                df_lotes["id"].tolist(),
                key="sb_quality_lotes"
            )
            
            if selected_lote_id:
                # Fetch details
                cursor.execute("""
                    SELECT l.*, p.nombre_sku 
                    FROM lotes_control l
                    JOIN piezas p ON l.pieza_id = p.id
                    WHERE l.id = ?
                """, (selected_lote_id,))
                lote_row = cursor.fetchone()
                lote_data = dict(lote_row)
                
                cursor.execute("SELECT * FROM mediciones WHERE lote_id = ?", (selected_lote_id,))
                measurements = [dict(r) for r in cursor.fetchall()]
                
                try:
                    pdf_lote_bytes = generate_spc_lote_pdf(lote_data, measurements)
                    st.download_button(
                        label=f"📥 Descargar PDF Reporte Lote #{selected_lote_id}",
                        data=pdf_lote_bytes,
                        file_name=f"Reporte_Lote_{selected_lote_id}_{lote_data['estacion'].replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        key=f"dl_lote_pdf_{selected_lote_id}",
                        use_container_width=True
                    )
                except Exception as ex:
                    st.error(f"Error al generar reporte PDF para Lote #{selected_lote_id}: {str(ex)}")

    with tab_remisiones:
        st.markdown("#### Consolidación y Remisiones Diarias")
        st.markdown("Seleccione una fecha y un SKU para consolidar todas las mediciones de inspección del día y generar el reporte consolidado de embarque.")
        
        # Load unique pieces
        df_pieces = pd.read_sql_query("SELECT id, nombre_sku FROM piezas ORDER BY nombre_sku ASC", conn)
        
        if len(df_pieces) == 0:
            st.info("💡 No hay piezas en el catálogo de ingeniería.")
        else:
            sku_options = df_pieces["nombre_sku"].tolist()
            sel_sku = st.selectbox("Seleccione SKU para la Remisión:", sku_options, key="rem_rep_sku")
            sel_date = st.date_input("Seleccione Fecha de Embarque:", datetime.now().date(), key="rem_rep_date")
            
            piece_row = df_pieces[df_pieces["nombre_sku"] == sel_sku].iloc[0]
            piece_id = int(piece_row["id"])
            
            # Fetch inspections for this day and piece
            date_str = sel_date.strftime("%Y-%m-%d")
            cursor.execute(
                """
                SELECT * FROM inspecciones 
                WHERE pieza_id = ? AND date(fecha_hora) = ?
                ORDER BY fecha_hora ASC
                """,
                (piece_id, date_str)
            )
            inspections = [dict(r) for r in cursor.fetchall()]
            
            if not inspections:
                st.warning(f"No hay inspecciones registradas el {sel_date.strftime('%d/%m/%Y')} para el SKU '{sel_sku}'.")
            else:
                st.success(f"Se encontraron {len(inspections)} inspecciones para consolidar el embarque.")
                
                # Show list of inspections to consolidate
                df_insp_day = pd.DataFrame(inspections)
                st.dataframe(
                    df_insp_day[["codigo_inspeccion", "fecha_hora", "operador", "turno", "excel_nombre", "estatus_general"]].rename(columns={
                        "codigo_inspeccion": "Código",
                        "fecha_hora": "Fecha/Hora",
                        "operador": "Operador",
                        "turno": "Turno",
                        "excel_nombre": "Archivo de Carga",
                        "estatus_general": "Estatus"
                    }),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Calculate consolidated stats
                insp_ids = [r["id"] for r in inspections]
                num_inspecciones = len(insp_ids)
                
                # Get unique dimensions for this piece
                cursor.execute(
                    "SELECT DISTINCT dimension_nombre, estacion FROM mediciones_excel WHERE pieza_id = ? ORDER BY estacion, dimension_nombre",
                    (piece_id,)
                )
                dimensions = cursor.fetchall()
                
                consolidated_stats = []
                all_approved = True
                for insp in inspections:
                    if insp["estatus_general"] != "Aprobado":
                        all_approved = False
                
                if dimensions:
                    for dim in dimensions:
                        d_name = dim["dimension_nombre"]
                        d_est = dim["estacion"]
                        
                        # Fetch all values
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
                                mean_val = sum(vals)/len(vals) if vals else 0.0
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
                
                # Show consolidated stats table
                st.markdown("##### 📊 Capacidad de Proceso Consolidada (SPC)")
                st.dataframe(pd.DataFrame(consolidated_stats), use_container_width=True, hide_index=True)
                
                # Remisión Code
                remision_code = f"REM-{sel_date.strftime('%Y%m%d')}-{piece_id:03d}"
                status_text = "🟢 EMBARQUE APROBADO" if all_approved else "🔴 EMBARQUE EN REVISIÓN (CONTENCIÓN)"
                
                st.markdown("##### 🚚 Generar Código de Remisión")
                st.markdown(f"**Código de Remisión:** `{remision_code}`")
                st.markdown(f"**Estatus de Embarque:** **{status_text}**")
                
                # Generate Remisión PDF
                if consolidated_stats:
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
                        
                    try:
                        rem_pdf_bytes = generate_remision_pdf(
                            remision_code=remision_code,
                            date_str=sel_date.strftime("%d/%m/%Y"),
                            piece_sku=sel_sku,
                            inspections_list=pdf_inspections,
                            consolidated_stats=pdf_stats
                        )
                        
                        st.download_button(
                            label="📥 Descargar Reporte de Remisión y SPC Consolidado (PDF)",
                            data=rem_pdf_bytes,
                            file_name=f"Reporte_Remision_{remision_code}.pdf",
                            mime="application/pdf",
                            key=f"dl_rem_pdf_{remision_code}",
                            use_container_width=True
                        )
                    except Exception as ex:
                        st.error(f"Error al generar reporte de remisión PDF: {str(ex)}")
                        
    conn.close()
