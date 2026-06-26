import streamlit as st
import pandas as pd
from src.database import get_connection
from src.pdf_generator import generate_first_piece_pdf

def show_glossary():
    st.title("5. Glosario de Documentación de Calidad")
    st.subheader("Tabla Maestra de Control Documental y Plantillas Muestra")
    
    st.markdown("""
        Esta tabla contiene todos los tipos de documentos e informes que interactúan con la aplicación web.
        Puede descargar formatos de muestra y plantillas para cada código documental.
    """)
    
    conn = get_connection()
    df_glossary = pd.read_sql_query("SELECT * FROM glosario_documentos", conn)
    conn.close()
    
    # Custom CSS table formatting
    st.markdown("#### 📋 Matriz de Control Documental")
    
    # We display the clean dataframe
    st.dataframe(
        df_glossary[["codigo_documento", "nombre_oficial", "asociado_a"]].rename(columns={
            "codigo_documento": "Código del Documento",
            "nombre_oficial": "Descripción / Nombre Oficial",
            "asociado_a": "Asociado a / Referenciado en"
        }),
        use_container_width=True
    )
    
    st.markdown("---")
    st.markdown("#### 📥 Centro de Descargas de Muestra")
    
    # Grid of download buttons based on the glossary items
    cols = st.columns(3)
    
    for i, idx_row in enumerate(df_glossary.iterrows()):
        idx, row = idx_row
        col = cols[i % 3]
        
        with col:
            st.markdown(f"**{row['codigo_documento']}**")
            st.markdown(f"<span style='font-size: 11px; color: #64748b;'>{row['nombre_oficial']}</span>", unsafe_allow_html=True)
            
            # Choose correct file type to simulate download
            file_code = row['codigo_documento']
            file_name_download = f"{file_code}_Muestra.pdf"
            mime_type = "application/pdf"
            
            # Mock content - We will generate a generic PDF for download samples
            from src.pdf_generator import generate_first_piece_pdf
            dummy_piece = {
                "numero_pieza": "SIG-SAMPLE-01",
                "nombre_sku": f"Muestra Documento {file_code} - SIGRAMA",
                "material": "16ga",
                "espesor_materia_prima": 0.060,
                "acabado_estandar": "ANSI-61",
                "factor_k": 48,
                "version": "V0",
                "revision": "R0",
                "ancho_materia_prima": 3.527,
                "largo_materia_prima": 19.000,
                "ruta_almacenamiento": "/Proyectos/MUESTRAS/",
                "usuario_registro": "Sistema de Gestión",
                "archivo_step": None
            }
            
            # Adjust downloaded filename extension based on document type
            if "DXF" in file_code:
                # Mock DXF content as flat text
                file_data = b"0\nSECTION\n2\nHEADER\n0\nENDSEC\n0\nEOF"
                file_name_download = f"{file_code}_Plantilla.dxf"
                mime_type = "application/dxf"
            elif "XLS" in file_code:
                # Mock XLSX
                import io
                excel_df = pd.DataFrame([{"ITEM": 1, "SKU": "12-A-6004-01-(16ga ANSI-61) - K48 - V3-R0", "CANTIDAD": 25}])
                excel_buf = io.BytesIO()
                excel_df.to_excel(excel_buf, index=False)
                file_data = excel_buf.getvalue()
                file_name_download = f"{file_code}_Plantilla.xlsx"
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:
                # Generate sample PDF
                file_data = generate_first_piece_pdf(dummy_piece)
                
            st.download_button(
                label=f"📥 Descargar {row['codigo_documento']}",
                data=file_data,
                file_name=file_name_download,
                mime=mime_type,
                key=f"btn_dl_glossary_{file_code}"
            )
            st.markdown("<br/>", unsafe_allow_html=True)
