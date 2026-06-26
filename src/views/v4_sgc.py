import streamlit as st
import pandas as pd
import os
from src.database import get_connection
from src.pdf_generator import NumberedCanvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io

def generate_procedimiento_pdf(codigo, nombre, version) -> bytes:
    """
    Genera un PDF genérico para un procedimiento oficial del SGC.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'SgcTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#EC2024"),
        spaceAfter=15,
        alignment=1 # Centered
    )
    
    body_style = ParagraphStyle(
        'SgcBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=10
    )
    
    bold_style = ParagraphStyle(
        'SgcBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    story.append(Paragraph("SISTEMA DE GESTIÓN DE CALIDAD - SIGRAMA", title_style))
    story.append(Paragraph(f"PROCEDIMIENTO OFICIAL: {nombre}", title_style))
    story.append(Spacer(1, 10))
    
    info_data = [
        [Paragraph("Código:", bold_style), Paragraph(codigo, body_style),
         Paragraph("Versión / Revisión:", bold_style), Paragraph(version, body_style)],
        [Paragraph("Fecha Emisión:", bold_style), Paragraph("19/06/2026", body_style),
         Paragraph("Clasificación:", bold_style), Paragraph("CONFIDENCIAL", body_style)]
    ]
    t_info = Table(info_data, colWidths=[90, 160, 110, 140])
    t_info.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("1. PROPÓSITO", ParagraphStyle('H2', parent=styles['Heading2'], textColor=colors.HexColor("#EC2024"))))
    story.append(Paragraph(f"Establecer los lineamientos y criterios obligatorios para el aseguramiento de calidad dimensional del componente '{nombre}' mediante control estadístico y calibración en piso.", body_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("2. ALCANCE", ParagraphStyle('H2', parent=styles['Heading2'], textColor=colors.HexColor("#EC2024"))))
    story.append(Paragraph("Aplica para todo el personal de Ingeniería, Operadores de Corte Láser, Operadores de Dobladora CNC y Auditores de Calidad involucrados en el proceso productivo.", body_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("3. RESPONSABILIDADES", ParagraphStyle('H2', parent=styles['Heading2'], textColor=colors.HexColor("#EC2024"))))
    story.append(Paragraph("• <b>Ingeniería de Diseño:</b> Alta de parámetros, SKU, y carga de archivos nativos de planos.<br/>"
                           "• <b>Operador de Planta:</b> Captura en tiempo real de mediciones físicas en subgrupos n=3.<br/>"
                           "• <b>Administrador de Calidad:</b> Liberación de primera pieza y auditorías de proceso.", body_style))
    
    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

def show_sgc():
    st.title("4. Sistema de Gestión de Calidad (SGC)")
    st.subheader("Control Documental de Procedimientos Oficiales de SIGRAMA")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    st.markdown("""
        Esta sección permite administrar y empatar los procedimientos oficiales del **Sistema de Gestión de Calidad (SGC)** de SIGRAMA.
        Las piezas capturadas en piso deben cumplir rigurosamente con los códigos de auditoría aquí cargados.
    """)
    
    # Check current SGC procedures in database
    df_sgc = pd.read_sql_query("SELECT * FROM procedimientos_sgc", conn)
    
    # Carga Inicial de documentos del SGC
    st.markdown("#### 📥 Cargar Procedimiento del SGC al Sistema")
    with st.form("form_sgc_upload"):
        col1, col2 = st.columns(2)
        with col1:
            sgc_code = st.text_input("Código del Documento SGC (Ej: SGC-PRC-01)")
            sgc_name = st.text_input("Nombre Oficial / Descripción (Ej: Procedimiento de Control Dimensional)")
        with col2:
            sgc_version = st.text_input("Versión Oficial (Ej: Rev. 2)")
            sgc_file = st.file_uploader("Subir Archivo de Procedimiento (PDF)", type=["pdf"])
            
        btn_upload_sgc = st.form_submit_button("Subir e Integrar Procedimiento", key="btn_sgc_upload_red")
        
        if btn_upload_sgc:
            if not sgc_code or not sgc_name or not sgc_version or not sgc_file:
                st.error("Error: Todos los campos del formulario y el archivo PDF son obligatorios.")
            else:
                # Save physical file
                sgc_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "SGC_Documents")
                os.makedirs(sgc_dir, exist_ok=True)
                dest_path = os.path.join(sgc_dir, f"{sgc_code}.pdf")
                with open(dest_path, "wb") as f:
                    f.write(sgc_file.read())
                    
                # Save to database
                try:
                    cursor.execute(
                        "INSERT INTO procedimientos_sgc (codigo, nombre, version, ruta_archivo) VALUES (?, ?, ?, ?)",
                        (sgc_code, sgc_name, sgc_version, dest_path)
                    )
                    conn.commit()
                    st.success(f"✅ Documento '{sgc_code}' cargado con éxito en el Sistema de Gestión de Calidad.")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error al registrar en base de datos: {str(ex)}")
                    
    st.markdown("---")
    st.markdown("#### 📋 Procedimientos Oficiales Activos")
    
    if len(df_sgc) == 0:
        st.info("💡 No hay procedimientos cargados por el usuario. Mostrando los documentos institucionales base de SIGRAMA:")
        
        # Default mock table showing default standard documents
        default_sgc = [
            {"Código": "SGC-PRC-01", "Nombre/Descripción": "Procedimiento General de Control Estadístico de Proceso", "Versión": "Rev. 1", "Estatus": "Activo"},
            {"Código": "SGC-CAL-03", "Nombre/Descripción": "Instrucción de Trabajo: Calibración y Calibres en Planta", "Versión": "Rev. 3", "Estatus": "Activo"},
            {"Código": "SGC-LIB-05", "Nombre/Descripción": "Criterio de Aceptación y Rechazo de Primeras Piezas", "Versión": "Rev. 0", "Estatus": "Activo"}
        ]
        st.table(pd.DataFrame(default_sgc))
        
        # Download buttons for mock procedures
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("**1. Procedimiento General (SGC-PRC-01)**")
            pdf1 = generate_procedimiento_pdf("SGC-PRC-01", "Procedimiento General de Control Estadístico de Proceso", "Rev. 1")
            st.download_button(
                label="📥 Descargar SGC-PRC-01 (PDF)",
                data=pdf1,
                file_name="SGC-PRC-01_Control_Estadistico.pdf",
                mime="application/pdf",
                key="btn_download_sgc_prc_01"
            )
        with col_m2:
            st.markdown("**2. Instrucción de Calibración (SGC-CAL-03)**")
            pdf2 = generate_procedimiento_pdf("SGC-CAL-03", "Instrucción de Trabajo: Calibración y Calibres en Planta", "Rev. 3")
            st.download_button(
                label="📥 Descargar SGC-CAL-03 (PDF)",
                data=pdf2,
                file_name="SGC-CAL-03_Instruccion_Calibracion.pdf",
                mime="application/pdf",
                key="btn_download_sgc_cal_03"
            )
    else:
        # Display registered SGC documents
        st.dataframe(df_sgc[["codigo", "nombre", "version", "fecha_carga"]], use_container_width=True)
        
        st.markdown("##### 📂 Descargar Procedimiento Registrado:")
        selected_sgc_code = st.selectbox("Seleccione el documento para descargar:", df_sgc["codigo"].tolist())
        
        if selected_sgc_code:
            row = df_sgc[df_sgc["codigo"] == selected_sgc_code].iloc[0]
            file_path = row["ruta_archivo"]
            
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                st.download_button(
                    label=f"📥 Descargar {selected_sgc_code} (PDF)",
                    data=file_bytes,
                    file_name=f"{selected_sgc_code}_Procedimiento.pdf",
                    mime="application/pdf",
                    key=f"btn_download_registered_sgc_{selected_sgc_code}"
                )
            else:
                st.error("El archivo físico no se encuentra en el servidor. Descargando copia de contingencia...")
                backup_pdf = generate_procedimiento_pdf(row["codigo"], row["nombre"], row["version"])
                st.download_button(
                    label=f"📥 Descargar Contingencia {selected_sgc_code} (PDF)",
                    data=backup_pdf,
                    file_name=f"{selected_sgc_code}_Contingencia.pdf",
                    mime="application/pdf",
                    key=f"btn_download_registered_sgc_cont_{selected_sgc_code}"
                )
                
    conn.close()
