import streamlit as st
import pandas as pd
import io
import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from src.pdf_generator import NumberedCanvas
from src.database import get_connection

def generate_glossary_docx(codigo, nombre, asociado) -> bytes:
    doc = docx.Document()
    
    # Page setup (Margins)
    section = doc.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    
    # Pantone Colors
    # Rojo Corporativo: #EC2024 (Pantone 485 C) -> RGB 236, 32, 36
    c_red = RGBColor(236, 32, 36)
    c_black = RGBColor(17, 17, 17)
    c_gray = RGBColor(100, 100, 100)
    
    # Header Slogan
    p_header = doc.add_paragraph()
    r_header = p_header.add_run("SISTEMA DE GESTIÓN DE CALIDAD - SIGRAMA")
    r_header.font.name = 'Arial'
    r_header.font.size = Pt(9)
    r_header.font.bold = True
    r_header.font.color.rgb = c_gray
    p_header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    p_title = doc.add_paragraph()
    r_title = p_title.add_run(f"PLANTILLA DE DOCUMENTO: {nombre}")
    r_title.font.name = 'Arial'
    r_title.font.size = Pt(14)
    r_title.font.bold = True
    r_title.font.color.rgb = c_red
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph().add_run("").font.size = Pt(10) # spacer
    
    # Info table
    table = doc.add_table(rows=2, cols=2)
    table.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    
    # Style table cells (Borders & Padding)
    for row in table.rows:
        for cell in row.cells:
            tcPr = cell._tc.get_or_add_tcPr()
            tcBorders = parse_xml(r'<w:tcBorders %s><w:top w:val="single" w:sz="4" w:space="0" w:color="D2D3D5"/><w:left w:val="none"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="D2D3D5"/><w:right w:val="none"/></w:tcBorders>' % nsdecls('w'))
            tcPr.append(tcBorders)
            
    # Row 0
    cell_0_0 = table.cell(0, 0)
    p_0_0 = cell_0_0.paragraphs[0]
    p_0_0.add_run("Código Temporal: ").bold = True
    p_0_0.add_run(codigo)
    p_0_0.runs[0].font.name = 'Arial'
    p_0_0.runs[1].font.name = 'Arial'
    
    cell_0_1 = table.cell(0, 1)
    p_0_1 = cell_0_1.paragraphs[0]
    p_0_1.add_run("Asociado a: ").bold = True
    p_0_1.add_run(asociado)
    p_0_1.runs[0].font.name = 'Arial'
    p_0_1.runs[1].font.name = 'Arial'
    
    # Row 1
    cell_1_0 = table.cell(1, 0)
    p_1_0 = cell_1_0.paragraphs[0]
    p_1_0.add_run("Fecha de Generación: ").bold = True
    p_1_0.add_run("26/06/2026")
    p_1_0.runs[0].font.name = 'Arial'
    p_1_0.runs[1].font.name = 'Arial'
    
    cell_1_1 = table.cell(1, 1)
    p_1_1 = cell_1_1.paragraphs[0]
    p_1_1.add_run("Estatus: ").bold = True
    p_1_1.add_run("BORRADOR EN REVISIÓN (SGC)")
    p_1_1.runs[0].font.name = 'Arial'
    p_1_1.runs[1].font.name = 'Arial'
    
    doc.add_paragraph().add_run("").font.size = Pt(15) # spacer
    
    # Section 1
    h1 = doc.add_paragraph()
    r_h1 = h1.add_run("1. OBJETIVO Y PROPÓSITO")
    r_h1.font.name = 'Arial'
    r_h1.font.size = Pt(11)
    r_h1.font.bold = True
    r_h1.font.color.rgb = c_red
    
    p_body1 = doc.add_paragraph()
    r_b1 = p_body1.add_run(f"Establecer la estructura base y lineamientos para el control, archivo y visualización del documento referenciado como '{nombre}' de acuerdo con los criterios del Sistema de Gestión de Calidad (SGC) de SIGRAMA.")
    r_b1.font.name = 'Arial'
    r_b1.font.size = Pt(10)
    
    # Section 2
    h2 = doc.add_paragraph()
    r_h2 = h2.add_run("2. LINEAMIENTES GENERALES")
    r_h2.font.name = 'Arial'
    r_h2.font.size = Pt(11)
    r_h2.font.bold = True
    r_h2.font.color.rgb = c_red
    
    p_body2 = doc.add_paragraph()
    r_b2 = p_body2.add_run(f"Este documento sirve como plantilla oficial nativa y debe ser resguardado y distribuido únicamente a personal autorizado del área de {asociado}. Cualquier cambio en la estructura debe ser notificado al departamento de Calidad.")
    r_b2.font.name = 'Arial'
    r_b2.font.size = Pt(10)
    
    # Section 3
    h3 = doc.add_paragraph()
    r_h3 = h3.add_run("3. FIRMA INSTITUCIONAL Y CIERRE")
    r_h3.font.name = 'Arial'
    r_h3.font.size = Pt(11)
    r_h3.font.bold = True
    r_h3.font.color.rgb = c_red
    
    p_footer = doc.add_paragraph()
    r_f = p_footer.add_run("Ingeniería que da resultados!!")
    r_f.font.name = 'Arial'
    r_f.font.italic = True
    r_f.font.bold = True
    r_f.font.color.rgb = c_red
    p_footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    # Save to buffer
    buf = io.BytesIO()
    doc.save(buf)
    docx_bytes = buf.getvalue()
    buf.close()
    return docx_bytes

def generate_glossary_pdf(codigo, nombre, asociado) -> bytes:
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
        'GlossaryTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#EC2024"),
        spaceAfter=15,
        alignment=1 # Centered
    )
    
    body_style = ParagraphStyle(
        'GlossaryBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#111111"),
        spaceAfter=10
    )
    
    bold_style = ParagraphStyle(
        'GlossaryBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    story.append(Paragraph("SISTEMA DE GESTIÓN DE CALIDAD - SIGRAMA", title_style))
    story.append(Paragraph(f"PLANTILLA DE DOCUMENTO: {nombre}", title_style))
    story.append(Spacer(1, 10))
    
    info_data = [
        [Paragraph("Código Temporal:", bold_style), Paragraph(codigo, body_style),
         Paragraph("Asociado a:", bold_style), Paragraph(asociado, body_style)],
        [Paragraph("Fecha Generación:", bold_style), Paragraph("26/06/2026", body_style),
         Paragraph("Estatus:", bold_style), Paragraph("BORRADOR EN REVISIÓN (SGC)", body_style)]
    ]
    t_info = Table(info_data, colWidths=[110, 140, 90, 160])
    t_info.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D2D3D5")),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8F9FA")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("1. OBJETIVO Y PROPÓSITO", ParagraphStyle('H2', parent=styles['Heading2'], textColor=colors.HexColor("#EC2024"))))
    story.append(Paragraph(f"Establecer la estructura base y lineamientos para el control, archivo y visualización del documento referenciado como '{nombre}' de acuerdo con los criterios del Sistema de Gestión de Calidad (SGC) de SIGRAMA.", body_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("2. LINEAMIENTES GENERALES", ParagraphStyle('H2', parent=styles['Heading2'], textColor=colors.HexColor("#EC2024"))))
    story.append(Paragraph(f"Este documento sirve como plantilla oficial nativa y debe ser resguardado y distribuido únicamente a personal autorizado del área de {asociado}. Cualquier cambio en la estructura debe ser notificado al departamento de Calidad.", body_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("3. FIRMA INSTITUCIONAL Y CIERRE", ParagraphStyle('H2', parent=styles['Heading2'], textColor=colors.HexColor("#EC2024"))))
    story.append(Spacer(1, 5))
    story.append(Paragraph("<u>Ingeniería que da resultados!!</u>", ParagraphStyle('FooterStyle', parent=body_style, fontName='Helvetica-Oblique-Bold', textColor=colors.HexColor("#EC2024"), alignment=2)))
    
    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

def show_glossary():
    st.title("Glosario de Documentación de Calidad")
    st.subheader("Borradores en Revisión por el SGC (Códigos Pendientes de Asignación)")
    
    st.markdown("""
        > [!IMPORTANT]
        > El presente glosario ha sido enviado a revisión al **SGC** para la asignación oficial de códigos. 
        > Por tal motivo, los códigos no cuentan con numeración definitiva y se muestran como **`[Por asignar]`**. 
        > Cada documento puede ser descargado en formato **WORD nativo** (con el mismo diseño del PDF) o en **PDF** para su revisión.
    """)
    
    conn = get_connection()
    df_glossary = pd.read_sql_query("SELECT * FROM glosario_documentos", conn)
    conn.close()
    
    # Custom CSS Table Header
    st.markdown("#### 📋 Matriz de Control Documental (Borradores)")
    
    h_col1, h_col2, h_col3, h_col4, h_col5 = st.columns([1.5, 3.5, 2.5, 1.5, 1.5])
    with h_col1:
        st.markdown("**Código Documento**")
    with h_col2:
        st.markdown("**Descripción / Nombre Oficial**")
    with h_col3:
        st.markdown("**Asociado a**")
    with h_col4:
        st.markdown("**Formato WORD**")
    with h_col5:
        st.markdown("**Formato PDF**")
        
    st.markdown("<hr style='border-top: 2px solid #EC2024; margin: 0.2rem 0 0.8rem 0;'>", unsafe_allow_html=True)
    
    # Render rows
    for i, row in df_glossary.iterrows():
        db_code = row['codigo_documento']
        nombre = row['nombre_oficial']
        asociado = row['asociado_a']
        
        # Mask code for SGC assignment
        ui_code = "[Por asignar]"
        
        r_col1, r_col2, r_col3, r_col4, r_col5 = st.columns([1.5, 3.5, 2.5, 1.5, 1.5])
        with r_col1:
            st.markdown(f"<span style='color: #64748b; font-family: monospace; font-weight: bold;'>{ui_code}</span>", unsafe_allow_html=True)
        with r_col2:
            st.markdown(f"**{nombre}**")
        with r_col3:
            st.markdown(f"<span style='font-size: 13px; color: #475569;'>{asociado}</span>", unsafe_allow_html=True)
        with r_col4:
            # Generate Word doc bytes
            word_bytes = generate_glossary_docx(db_code, nombre, asociado)
            st.download_button(
                label="📝 Word",
                data=word_bytes,
                file_name=f"Boceto_Word_{db_code}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"btn_dl_word_{db_code}"
            )
        with r_col5:
            # Generate PDF doc bytes
            pdf_bytes = generate_glossary_pdf(db_code, nombre, asociado)
            st.download_button(
                label="📄 PDF",
                data=pdf_bytes,
                file_name=f"Boceto_PDF_{db_code}.pdf",
                mime="application/pdf",
                key=f"btn_dl_pdf_{db_code}"
            )
        st.markdown("<hr style='border-top: 1px solid #E2E8F0; margin: 0.3rem 0;'>", unsafe_allow_html=True)
        
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Slogan of Results
    st.markdown("""
        <div style="text-align: right; margin-top: 2rem;">
            <p style="font-family: 'Montserrat', sans-serif; font-style: italic; font-weight: bold; color: #EC2024; font-size: 1.1rem; margin: 0;">
                Ingeniería que da resultados!!
            </p>
            <hr style="border: 0; border-top: 2px solid #EC2024; width: 100px; margin: 0.3rem 0 0 auto;">
        </div>
    """, unsafe_allow_html=True)
