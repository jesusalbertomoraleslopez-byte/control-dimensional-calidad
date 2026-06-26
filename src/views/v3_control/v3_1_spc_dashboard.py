import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from src.database import get_connection
from src.views.v3_control.v3_4_spc_excel import format_tolerance
from src.pdf_generator import generate_excel_spc_report_pdf

def show_spc_dashboard():
    st.title("3.1. Dashboard de Inspecciones de Calidad")
    st.subheader("Indicadores, Métricas de Aprobación e Historial de Revisiones")

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Filters Section
    st.markdown("#### 🔍 Filtros de Búsqueda")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        # Date Range Filter
        today = datetime.today().date()
        start_default = today - timedelta(days=30)
        date_range = st.date_input(
            "Rango de Fechas",
            value=(start_default, today),
            max_value=today,
            key="dashboard_date_range"
        )
        
    with col_f2:
        # SKU Filter
        cursor.execute("SELECT DISTINCT nombre_sku FROM piezas ORDER BY nombre_sku")
        sku_list = ["Todos"] + [r[0] for r in cursor.fetchall()]
        selected_sku = st.selectbox("Número de Parte / SKU", sku_list, key="dashboard_sku")
        
    with col_f3:
        # Caliber Filter
        cursor.execute("SELECT DISTINCT material FROM piezas ORDER BY material")
        caliber_list = ["Todos"] + [r[0] for r in cursor.fetchall()]
        selected_caliber = st.selectbox("Calibre / Material", caliber_list, key="dashboard_caliber")

    # Build SQL Query based on filters
    query = """
        SELECT i.id, i.codigo_inspeccion, i.fecha_hora, p.nombre_sku, i.calibre, i.operador, i.turno, i.estatus_general, i.excel_nombre
        FROM inspecciones i
        JOIN piezas p ON i.pieza_id = p.id
        WHERE 1=1
    """
    params = []

    # Apply date filters
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        query += " AND DATE(i.fecha_hora) >= DATE(?) AND DATE(i.fecha_hora) <= DATE(?)"
        params.extend([str(start_date), str(end_date)])
    elif isinstance(date_range, datetime) or isinstance(date_range, datetime.date):
        query += " AND DATE(i.fecha_hora) = DATE(?)"
        params.append(str(date_range))

    # Apply SKU filter
    if selected_sku != "Todos":
        query += " AND p.nombre_sku = ?"
        params.append(selected_sku)

    # Apply caliber filter
    if selected_caliber != "Todos":
        query += " AND i.calibre = ?"
        params.append(selected_caliber)

    query += " ORDER BY i.fecha_hora DESC"

    # Fetch data
    df_insp = pd.read_sql_query(query, conn, params=params)

    if df_insp.empty:
        st.info("💡 No se encontraron registros de inspección en el periodo seleccionado con los filtros especificados.")
        
        # Display simulated data banner if database is completely empty
        cursor.execute("SELECT COUNT(*) FROM inspecciones")
        if cursor.fetchone()[0] == 0:
            st.warning("⚠️ La base de datos de inspecciones de calidad está vacía. Ve a la pestaña '3.2. Carga de Inspección' para registrar una nueva.")
        conn.close()
        return

    # 2. Metrics Block
    total_insp = len(df_insp)
    approved_insp = len(df_insp[df_insp["estatus_general"] == "Aprobado"])
    rejected_insp = len(df_insp[df_insp["estatus_general"] != "Aprobado"])
    approval_rate = (approved_insp / total_insp) * 100 if total_insp > 0 else 0

    st.markdown("---")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric("Total Inspecciones", f"{total_insp} pz")
    with m_col2:
        st.metric("Lotes Aprobados", f"🟢 {approved_insp} pz")
    with m_col3:
        st.metric("Lotes Rechazados", f"🔴 {rejected_insp} pz")
    with m_col4:
        st.metric("Tasa de Aprobación", f"{approval_rate:.1f}%")

    # 3. Charts Block
    st.markdown("---")
    c_col1, c_col2 = st.columns([1, 1.5])
    
    with c_col1:
        # Donut Chart for Status
        status_counts = df_insp["estatus_general"].value_counts().reset_index()
        status_counts.columns = ["Estatus", "Total"]
        fig_donut = px.pie(
            status_counts, 
            values="Total", 
            names="Estatus", 
            hole=0.4,
            color="Estatus",
            color_discrete_map={"Aprobado": "#16a34a", "Fuera de Tolerancia": "#dc2626", "Rechazado": "#dc2626"},
            title="Estatus de Aprobación General"
        )
        fig_donut.update_layout(margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_donut, use_container_width=True)
        
    with c_col2:
        # Bar Chart of Inspections by SKU
        sku_counts = df_insp["nombre_sku"].value_counts().reset_index()
        sku_counts.columns = ["SKU", "Total"]
        # Limit SKU length for display
        sku_counts["SKU_Short"] = sku_counts["SKU"].apply(lambda x: x[:30] + "..." if len(x) > 30 else x)
        fig_bar = px.bar(
            sku_counts.head(10), 
            x="Total", 
            y="SKU_Short", 
            orientation="h",
            labels={"SKU_Short": "SKU de Pieza", "Total": "Cantidad de Inspecciones"},
            title="Top 10 Piezas Inspeccionadas",
            color_discrete_sequence=["#B30000"]
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)

    # 4. History Table
    st.markdown("---")
    st.markdown("#### 📋 Historial de Inspecciones")
    
    # Styled dataframe
    df_display = df_insp.copy()
    df_display["fecha_hora"] = pd.to_datetime(df_display["fecha_hora"]).dt.strftime("%d/%m/%Y %H:%M")
    df_display.rename(columns={
        "codigo_inspeccion": "Código",
        "fecha_hora": "Fecha/Hora",
        "nombre_sku": "SKU del Componente",
        "calibre": "Calibre",
        "operador": "Inspector",
        "turno": "Turno",
        "estatus_general": "Estatus"
    }, inplace=True)
    
    st.dataframe(
        df_display[["Código", "Fecha/Hora", "SKU del Componente", "Calibre", "Inspector", "Turno", "Estatus"]],
        use_container_width=True,
        hide_index=True
    )

    # 5. Detail Viewer (Per-piece report print/download)
    st.markdown("---")
    st.markdown("#### 🔍 Detalle Individual de Inspección")
    selected_code = st.selectbox(
        "Seleccione el Código de Inspección para ver detalles y descargar reporte:",
        df_insp["codigo_inspeccion"].tolist()
    )

    if selected_code:
        # Load details of the selected inspection
        insp_row = df_insp[df_insp["codigo_inspeccion"] == selected_code].iloc[0]
        insp_id = int(insp_row["id"])
        piece_sku = str(insp_row["nombre_sku"])
        excel_name = str(insp_row["excel_nombre"])
        
        # Display Inspection Details Card
        st.markdown(f"""
        <div style="background-color: #F8F9FA; border-left: 5px solid #B30000; border-radius: 4px; padding: 1rem; margin-bottom: 1.5rem;">
            <h5 style="margin-top: 0; color: #111111;">FICHA TÉCNICA - {selected_code}</h5>
            <div style="display: flex; flex-wrap: wrap; gap: 2rem; font-size: 0.9rem; font-family: 'Questrial', sans-serif;">
                <span>📅 <b>Fecha:</b> {pd.to_datetime(insp_row['fecha_hora']).strftime('%d/%m/%Y %H:%M')}</span>
                <span>👤 <b>Inspector:</b> {insp_row['operador']}</span>
                <span>⏰ <b>Turno:</b> {insp_row['turno']}</span>
                <span>🧱 <b>Material:</b> {insp_row['calibre']}</span>
                <span>🟢 <b>Estatus:</b> {insp_row['estatus_general']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Load measurements for this inspection
        df_c = pd.read_sql_query(
            "SELECT * FROM mediciones_excel WHERE inspeccion_id = ? AND estacion = 'Corte Láser'",
            conn, params=(insp_id,)
        )
        df_d = pd.read_sql_query(
            "SELECT * FROM mediciones_excel WHERE inspeccion_id = ? AND estacion = 'Doblez'",
            conn, params=(insp_id,)
        )
        
        # Show tables
        tab_c, tab_d = st.tabs(["⚡ Corte Láser", "📐 Doblez"])
        
        active_corte = []
        active_doblez = []
        
        with tab_c:
            if df_c.empty:
                st.info("No hay registros de Corte Láser para esta inspección.")
            else:
                for idx, row in df_c.iterrows():
                    tol_f = format_tolerance(row["nominal"], row["limite_inferior"], row["limite_superior"])
                    est_m = "🟢 PASA" if row["valor_mfg"] is not None and row["limite_inferior"] <= row["valor_mfg"] <= row["limite_superior"] else "🔴 FUERA" if row["valor_mfg"] is not None else "N/D"
                    est_c = "🟢 PASA" if row["valor_cal"] is not None and row["limite_inferior"] <= row["valor_cal"] <= row["limite_superior"] else "🔴 FUERA" if row["valor_cal"] is not None else "N/D"
                    
                    active_corte.append({
                        "No.": idx + 1, "RESP": "LASER", "DIM": row["nominal"], "TOLERANCIA": tol_f,
                        "VALOR MFG": row["valor_mfg"], "ESTATUS_MFG": est_m, "VALOR CAL": row["valor_cal"], "ESTATUS_CAL": est_c
                    })
                df_c_show = pd.DataFrame(active_corte)
                st.table(df_c_show[["No.", "RESP", "DIM", "TOLERANCIA", "VALOR MFG", "ESTATUS_MFG", "VALOR CAL", "ESTATUS_CAL"]])
                
        with tab_d:
            if df_d.empty:
                st.info("No hay registros de Doblez para esta inspección.")
            else:
                for idx, row in df_d.iterrows():
                    tol_f = format_tolerance(row["nominal"], row["limite_inferior"], row["limite_superior"])
                    est_m = "🟢 PASA" if row["valor_mfg"] is not None and row["limite_inferior"] <= row["valor_mfg"] <= row["limite_superior"] else "🔴 FUERA" if row["valor_mfg"] is not None else "N/D"
                    est_c = "🟢 PASA" if row["valor_cal"] is not None and row["limite_inferior"] <= row["valor_cal"] <= row["limite_superior"] else "🔴 FUERA" if row["valor_cal"] is not None else "N/D"
                    
                    active_doblez.append({
                        "MEDIDA": row["dimension_nombre"].replace("Doblez - ", ""),
                        "DIMENSION": row["nominal"],
                        "TOLERANCIA": tol_f,
                        "VALOR MFG": row["valor_mfg"],
                        "ESTATUS_MFG": est_m,
                        "VALOR CAL": row["valor_cal"],
                        "ESTATUS_CAL": est_c
                    })
                df_d_show = pd.DataFrame(active_doblez)
                st.table(df_d_show[["MEDIDA", "DIMENSION", "TOLERANCIA", "VALOR MFG", "ESTATUS_MFG", "VALOR CAL", "ESTATUS_CAL"]])

        # Retrieve SPC Stats for PDF report
        # We need historical stats to include Cp/Cpk in the individual PDF report too
        hist_stats = []
        cursor.execute(
            "SELECT DISTINCT dimension_nombre, estacion FROM mediciones_excel WHERE pieza_id = (SELECT id FROM piezas WHERE nombre_sku = ?) ORDER BY estacion, dimension_nombre",
            (piece_sku,)
        )
        dimensions_available = cursor.fetchall()
        
        from src.utils import calculate_spc_stats
        for dim_row in dimensions_available:
            d_name = dim_row["dimension_nombre"]
            d_est = dim_row["estacion"]
            
            df_dim = pd.read_sql_query(
                "SELECT valor_cal, nominal, limite_inferior, limite_superior FROM mediciones_excel WHERE pieza_id = (SELECT id FROM piezas WHERE nombre_sku = ?) AND estacion = ? AND dimension_nombre = ?",
                conn, params=(piece_sku, d_est, d_name)
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

        # Download Report PDF
        if active_corte or active_doblez:
            # Custom styled download button
            from src.pdf_generator import generate_excel_spc_report_pdf
            
            # Add inspection header details to PDF
            rep_pdf_bytes = generate_excel_spc_report_pdf(
                piece_sku, excel_name, active_corte, active_doblez, hist_stats,
                insp_code=selected_code,
                insp_date=pd.to_datetime(insp_row['fecha_hora']).strftime('%d/%m/%Y %H:%M'),
                operator=str(insp_row['operador']),
                shift=str(insp_row['turno'])
            )
            
            st.download_button(
                label=f"📥 Imprimir Reporte de Inspección {selected_code} (PDF)",
                data=rep_pdf_bytes,
                file_name=f"Reporte_{selected_code}_{piece_sku.replace(' ', '_')}.pdf",
                mime="application/pdf",
                key=f"btn_dl_insp_pdf_{selected_code}"
            )

    conn.close()
