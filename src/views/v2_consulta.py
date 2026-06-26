import streamlit as st
import pandas as pd
from src.database import get_connection
from src.pdf_generator import generate_spc_lote_pdf

def show_consulta():
    st.title("2. Área de Consulta - Historial de Control Dimensional")
    st.subheader("Auditoría Rápida y Filtros Dinámicos de Producción")
    
    conn = get_connection()
    
    # Load all pieces, lotes and operators for filter lists
    df_lotes = pd.read_sql_query("""
        SELECT l.*, p.nombre_sku, p.numero_pieza 
        FROM lotes_control l
        JOIN piezas p ON l.pieza_id = p.id
        ORDER BY l.fecha_captura DESC
    """, conn)
    
    # Get lists for filter dropdowns
    part_number_list = ["Todos"] + list(df_lotes["numero_pieza"].unique()) if len(df_lotes) > 0 else ["Todos", "12-A-6004-01"]
    operators_list = ["Todos"] + list(df_lotes["operador"].unique()) if len(df_lotes) > 0 else ["Todos", "Operador de Planta", "Administrador de Calidad"]
    sku_list = ["Todos"] + list(df_lotes["nombre_sku"].unique()) if len(df_lotes) > 0 else ["Todos", "12-A-6004-01-(16ga ANSI-61) - K48 - V3-R0"]
    turns_list = ["Todos", "Turno 1", "Turno 2", "Turno 3"]
    status_list = ["Todos", "Aprobado", "Rechazado", "Pendiente"]
    
    # Sidebar or top container for filters
    st.markdown("#### 🔍 Filtros de Búsqueda")
    
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)
    
    with col1:
        selected_part_no = st.selectbox("Número de Pieza", part_number_list)
    with col2:
        selected_sku = st.selectbox("Número de Parte / SKU", sku_list)
    with col3:
        selected_operator = st.selectbox("Operador", operators_list)
    with col4:
        selected_turn = st.selectbox("Turno", turns_list)
    with col5:
        selected_status = st.selectbox("Estatus del Lote", status_list)
    with col6:
        # Date filter range
        date_range = st.date_input("Rango de Fechas", [])
        
    st.markdown("---")
    
    # If no data exists in DB, show a clean message
    if len(df_lotes) == 0:
        st.info("💡 No se encontraron registros de producción en la base de datos. Realice capturas en piso (3.3 / 3.4) para poblar el historial.")
    else:
        # Apply filters to df_lotes
        filtered_df = df_lotes.copy()
        
        if selected_part_no != "Todos":
            filtered_df = filtered_df[filtered_df["numero_pieza"] == selected_part_no]
        if selected_sku != "Todos":
            filtered_df = filtered_df[filtered_df["nombre_sku"] == selected_sku]
        if selected_operator != "Todos":
            filtered_df = filtered_df[filtered_df["operador"] == selected_operator]
        if selected_turn != "Todos":
            filtered_df = filtered_df[filtered_df["turno"] == selected_turn]
        if selected_status != "Todos":
            filtered_df = filtered_df[filtered_df["estatus"] == selected_status]
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df["fecha_dt"] = pd.to_datetime(filtered_df["fecha_captura"]).dt.date
            filtered_df = filtered_df[(filtered_df["fecha_dt"] >= start_date) & (filtered_df["fecha_dt"] <= end_date)]
            filtered_df.drop(columns=["fecha_dt"], inplace=True)
            
        if len(filtered_df) == 0:
            st.warning("No se encontraron registros que coincidan con los filtros seleccionados.")
        else:
            # Display Table
            st.dataframe(filtered_df[["id", "fecha_captura", "nombre_sku", "estacion", "operador", "turno", "estatus", "v_dobladura", "gauge_perfil"]], use_container_width=True)
            
            # Select individual lote to view details & download PDF
            st.markdown("#### 📂 Consultar Detalle de Lote Específico")
            lote_options = [f"Lote #{r['id']} - {r['nombre_sku']} ({r['estacion']})" for idx, r in filtered_df.iterrows()]
            selected_lote_option = st.selectbox("Seleccione el Lote:", lote_options)
            
            if selected_lote_option:
                selected_lote_id = int(selected_lote_option.split(" - ")[0].replace("Lote #", ""))
                
                # Fetch details
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM lotes_control WHERE id = ?", (selected_lote_id,))
                lote_row = cursor.fetchone()
                
                cursor.execute("""
                    SELECT l.*, p.nombre_sku 
                    FROM lotes_control l
                    JOIN piezas p ON l.pieza_id = p.id
                    WHERE l.id = ?
                """, (selected_lote_id,))
                lote_data = dict(cursor.fetchone())
                
                cursor.execute("SELECT * FROM mediciones WHERE lote_id = ?", (selected_lote_id,))
                measurements = [dict(r) for r in cursor.fetchall()]
                
                st.markdown(f"**Detalles del Lote #{selected_lote_id}:**")
                
                # Visualización Premium en lugar de JSON (Evita visual de código)
                det_col1, det_col2, det_col3, det_col4 = st.columns(4)
                with det_col1:
                    st.metric("Estatus del Lote", lote_data["estatus"])
                    st.metric("Estación", lote_data["estacion"])
                with det_col2:
                    st.metric("Operador", lote_data["operador"])
                    st.metric("Turno", lote_data["turno"])
                with det_col3:
                    st.metric("V de Doblado", f"{lote_data['v_dobladura']} mm")
                    st.metric("Fecha de Registro", lote_data["fecha_captura"].split(" ")[0])
                with det_col4:
                    st.metric("Gauge de Perfil", lote_data["gauge_perfil"])
                
                st.markdown("---")
                
                st.markdown("**Mediciones Capturadas (n=3):**")
                st.dataframe(pd.DataFrame(measurements), use_container_width=True)
                
                # Generate PDF
                pdf_bytes = generate_spc_lote_pdf(lote_data, measurements)
                st.download_button(
                    label=f"📥 Descargar PDF Reporte Lote #{selected_lote_id}",
                    data=pdf_bytes,
                    file_name=f"Reporte_Lote_{selected_lote_id}_{lote_data['estacion'].replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    key=f"download_lote_{selected_lote_id}_pdf"
                )
                
    conn.close()
