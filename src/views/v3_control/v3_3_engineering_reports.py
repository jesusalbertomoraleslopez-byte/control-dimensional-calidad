import streamlit as st
import os
import pandas as pd
from src.database import get_connection
from src.pdf_generator import generate_first_piece_pdf

def show_engineering_reports():
    st.title("3.3. Impresión de Reportes de Ingeniería")
    st.subheader("Centro de Consulta de Planos y Descarga de Archivos Nativos")
    
    st.markdown("""
    Consulte y descargue los archivos originales de diseño, dibujos en formato PDF,
    desplegados en DXF, y el **Reporte de Liberación de Primera Pieza** para cada SKU registrado.
    """)
    
    conn = get_connection()
    df_pieces = pd.read_sql_query("SELECT * FROM piezas ORDER BY nombre_sku ASC", conn)
    
    if len(df_pieces) == 0:
        st.info("💡 No hay piezas registradas en el catálogo de ingeniería. Registre un nuevo componente en **Carga de Registros de Diseño** para habilitar esta pantalla.")
        conn.close()
        return
        
    # Selection of Piece
    sku_list = df_pieces["nombre_sku"].tolist()
    selected_sku = st.selectbox("Seleccione el SKU del Componente:", sku_list)
    
    if selected_sku:
        # Get piece data
        piece_row = df_pieces[df_pieces["nombre_sku"] == selected_sku].iloc[0]
        piece_id = int(piece_row["id"])
        
        # Display metadata card
        st.markdown("---")
        st.markdown(f"### 📋 Ficha Técnica y Archivos: `{selected_sku}`")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Número de Pieza:** {piece_row['numero_pieza']}")
            st.markdown(f"**Material Estándar:** {piece_row['material']}")
            st.markdown(f"**Acabado Requerido:** {piece_row['acabado_estandar']}")
        with col2:
            st.markdown(f"**Factor K Doblez:** {piece_row['factor_k'] / 100:.2f} ({piece_row['factor_k']}%)")
            st.markdown(f"**Espesor Nominal:** {piece_row['espesor_materia_prima']:.4f} in")
            st.markdown(f"**Dimensión Corte:** {piece_row['ancho_materia_prima']:.3f} x {piece_row['largo_materia_prima']:.3f} in")
        with col3:
            st.markdown(f"**Versión / Revisión:** {piece_row['version']} - R{piece_row['revision']}")
            st.markdown(f"**Usuario Registro:** {piece_row['usuario_registro']}")
            st.markdown(f"**Fecha Registro:** {str(piece_row['fecha_registro']).split(' ')[0]}")
            
        st.markdown("---")
        
        # Split into tabs for clean organization
        tab_drawings, tab_vobo = st.tabs(["📐 Planos y Archivos de Diseño", "✅ Liberación de Primera Pieza (VoBo)"])
        
        with tab_drawings:
            st.markdown("#### Descarga de Planos y Archivos Nativos 3D/2D")
            st.markdown("A continuación se enlistan los archivos de diseño asociados a esta pieza. Los botones se habilitarán automáticamente si el archivo físico está presente en el servidor.")
            
            # Helper to check file and render download button
            def render_download_btn(label, file_path, file_name, mime_type, key):
                if file_path and os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        file_bytes = f.read()
                    st.download_button(
                        label=label,
                        data=file_bytes,
                        file_name=file_name,
                        mime=mime_type,
                        key=key,
                        use_container_width=True
                    )
                else:
                    st.button(f"🚫 {label.replace('📥 ', '')} (No Cargado)", disabled=True, use_container_width=True, key=f"disabled_{key}")
            
            c1, c2 = st.columns(2)
            with c1:
                render_download_btn(
                    "📥 Descargar Dibujo Original Cliente (PDF)",
                    piece_row["archivo_dibujo_original"],
                    f"{piece_row['numero_pieza']}_Original.pdf",
                    "application/pdf",
                    f"dl_orig_{piece_id}"
                )
                
                render_download_btn(
                    "📥 Descargar Plano de Control PDF",
                    piece_row["archivo_plano_control"],
                    f"{selected_sku}.pdf",
                    "application/pdf",
                    f"dl_ctrl_{piece_id}"
                )
                
                render_download_btn(
                    "📥 Descargar Archivo Unfolded DXF",
                    piece_row["archivo_dxf"],
                    f"{selected_sku}.dxf",
                    "application/dxf",
                    f"dl_dxf_{piece_id}"
                )
                
                render_download_btn(
                    "📥 Descargar Tabla Dimensiones Excel (.xlsx)",
                    piece_row["archivo_excel_resumen"],
                    f"{selected_sku}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    f"dl_xlsx_{piece_id}"
                )
                
            with c2:
                render_download_btn(
                    "📥 Descargar Modelo 3D STEP (.step)",
                    piece_row["archivo_step"],
                    f"{selected_sku}.step",
                    "application/step",
                    f"dl_step_{piece_id}"
                )
                
                render_download_btn(
                    "📥 Descargar SolidWorks Part (.SLDPRT)",
                    piece_row["archivo_plano_nativo_3d"],
                    f"{selected_sku}.sldprt",
                    "application/octet-stream",
                    f"dl_sldprt_{piece_id}"
                )
                
                render_download_btn(
                    "📥 Descargar SolidWorks Drawing (.SLDDRW)",
                    piece_row["archivo_dibujo_nativo_2d"] if "archivo_dibujo_nativo_2d" in piece_row.keys() else (piece_row["archivo_dibujo_native_2d"] if "archivo_dibujo_native_2d" in piece_row.keys() else None),
                    f"{selected_sku}.slddrw",
                    "application/octet-stream",
                    f"dl_slddrw_{piece_id}"
                )
                
        with tab_vobo:
            st.markdown("#### Reportes de Validación y Visto Bueno (VoBo)")
            st.markdown("La liberación de primera pieza es un requisito obligatorio antes de iniciar la producción en serie.")
            
            vobo_col1, vobo_col2 = st.columns(2)
            
            with vobo_col1:
                st.markdown("##### 📄 Reporte Oficial de Liberación (VoBo)")
                st.markdown("Este reporte se genera en tiempo real consolidando los parámetros del diseño y las firmas de aprobación.")
                
                try:
                    # Generate report bytes
                    piece_dict = dict(piece_row)
                    report_bytes = generate_first_piece_pdf(piece_dict)
                    
                    st.download_button(
                        label="📥 Descargar Reporte de Liberación de Primera Pieza (PDF)",
                        data=report_bytes,
                        file_name=f"Reporte_Liberacion_{selected_sku}.pdf",
                        mime="application/pdf",
                        key=f"dl_vobo_report_{piece_id}",
                        use_container_width=True
                    )
                except Exception as ex:
                    st.error(f"Error al generar el reporte PDF: {str(ex)}")
            
            with vobo_col2:
                st.markdown("##### 📂 Evidencia de Validación en Planta")
                st.markdown("Descargue el plano firmado físicamente o las plantillas escaneadas de visto bueno subidas durante el registro.")
                
                # Check for physical signed sheets
                render_download_btn(
                    "📥 Descargar Plano Escaneado Firmado",
                    piece_row["plano_validado_impreso"],
                    f"Plano_Validado_{selected_sku}.pdf",
                    "application/pdf",
                    f"dl_signed_{piece_id}"
                )
                
                render_download_btn(
                    "📥 Descargar Documento de Primera Pieza VoBo",
                    piece_row["documento_primera_pieza"],
                    f"VoBo_Primera_Pieza_{selected_sku}.pdf",
                    "application/pdf",
                    f"dl_vobo_doc_{piece_id}"
                )
                
    conn.close()
