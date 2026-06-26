import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
import io

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Draw running header (except on first page, or on all if desired)
        self.drawString(54, 750, "SIGRAMA - CONTROL DIMENSIONAL DE CALIDAD")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 742, 612 - 54, 742)
        
        # Draw running footer
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(612 - 54, 36, page_text)
        self.drawString(54, 36, "CONFIDENCIAL - PROPIEDAD DE SIGRAMA S.A. DE C.V.")
        self.line(54, 48, 612 - 54, 48)
        self.restoreState()

def generate_first_piece_pdf(piece_data) -> bytes:
    """
    Genera un PDF con el registro de validación de primera pieza.
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
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0056b3"),
        alignment=0, # Left
        spaceAfter=15
    )
    
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=12,
        spaceAfter=6
    )
    
    normal_style = ParagraphStyle(
        'DocNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155")
    )
    
    bold_style = ParagraphStyle(
        'DocBold',
        parent=normal_style,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # Title
    story.append(Paragraph("REPORTE DE LIBERACIÓN DE PRIMERA PIEZA", title_style))
    story.append(Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
    story.append(Spacer(1, 15))
    
    # Metadata Table
    story.append(Paragraph("1. INFORMACIÓN GENERAL DEL COMPONENTE", section_title))
    metadata_data = [
        [Paragraph("SKU Concatenado:", bold_style), Paragraph(piece_data.get("nombre_sku", ""), normal_style)],
        [Paragraph("Número de Pieza:", bold_style), Paragraph(piece_data.get("numero_pieza", ""), normal_style)],
        [Paragraph("Material / Espesor:", bold_style), Paragraph(f"{piece_data.get('material', '')} ({piece_data.get('espesor_materia_prima', '')}\")", normal_style)],
        [Paragraph("Acabado / Estándar:", bold_style), Paragraph(piece_data.get("acabado_estandar", ""), normal_style)],
        [Paragraph("Factor K / Versión:", bold_style), Paragraph(f"K{piece_data.get('factor_k', '')} / {piece_data.get('version', '')}", normal_style)],
        [Paragraph("Revisión:", bold_style), Paragraph(piece_data.get("revision", ""), normal_style)],
        [Paragraph("Espesor Nominal (in):", bold_style), Paragraph(str(piece_data.get("espesor_materia_prima", "")), normal_style)],
        [Paragraph("Dimensiones Mat. Prima:", bold_style), Paragraph(f"{piece_data.get('ancho_materia_prima', '')} x {piece_data.get('largo_materia_prima', '')} in", normal_style)],
        [Paragraph("Ruta Física Servidor:", bold_style), Paragraph(piece_data.get("ruta_almacenamiento", ""), normal_style)],
        [Paragraph("Registrado por:", bold_style), Paragraph(piece_data.get("usuario_registro", ""), normal_style)]
    ]
    
    t_meta = Table(metadata_data, colWidths=[150, 350])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    # Validation Checklist
    story.append(Paragraph("2. REGISTROS Y ENTRADAS ASOCIADAS", section_title))
    checklist_data = [
        [Paragraph("Documento Requerido", bold_style), Paragraph("Estado en Sistema", bold_style)],
        [Paragraph("Dibujo Original Cliente (.PDF)", normal_style), Paragraph("Cargado ✔" if piece_data.get("archivo_dibujo_original") else "No Cargado ✘", normal_style)],
        [Paragraph("Desplegado DXF (.DXF)", normal_style), Paragraph("Cargado ✔" if piece_data.get("archivo_dxf") else "No Cargado ✘", normal_style)],
        [Paragraph("Plano de Control PDF (.PDF)", normal_style), Paragraph("Cargado ✔" if piece_data.get("archivo_plano_control") else "No Cargado ✘", normal_style)],
        [Paragraph("Plano Nativo Diseño 3D (.SLDDRW)", normal_style), Paragraph("Cargado ✔" if piece_data.get("archivo_plano_nativo_3d") else "No Cargado ✘", normal_style)],
        [Paragraph("Dibujo Nativo Diseño 2D (.SLDPRT)", normal_style), Paragraph("Cargado ✔" if piece_data.get("archivo_dibujo_native_2d") or piece_data.get("archivo_dibujo_nativo_2d") else "No Cargado ✘", normal_style)],
        [Paragraph("Excel Resumen de Dimensiones (.XLSX)", normal_style), Paragraph("Cargado ✔" if piece_data.get("archivo_excel_resumen") else "No Cargado ✘", normal_style)],
        [Paragraph("Archivo STEP (.STEP)", normal_style), Paragraph("Cargado ✔" if piece_data.get("archivo_step") else "No Cargado ✘", normal_style)],
    ]
    t_check = Table(checklist_data, colWidths=[280, 220])
    t_check.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor("#0056b3")),
        ('TEXTCOLOR', (0,0), (1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_check)
    story.append(Spacer(1, 15))
    
    # First Piece Verification Status
    story.append(Paragraph("3. ESTATUS DE LIBERACIÓN DE PRIMERA PIEZA", section_title))
    status_data = [
        [Paragraph("Variable de Validación", bold_style), Paragraph("Estatus / Detalle", bold_style)],
        [Paragraph("Plano Validado Impreso Escaneado:", normal_style), Paragraph("Cargado ✔" if piece_data.get("plano_validado_impreso") else "Pendiente ✘", normal_style)],
        [Paragraph("Estatus de Validación Dimensional:", normal_style), Paragraph("APROBADO - Primera Pieza Válida ✔" if piece_data.get("documento_primera_pieza") else "PENDIENTE DE VALIDACIÓN ✘", bold_style)],
    ]
    t_status = Table(status_data, colWidths=[220, 280])
    t_status.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_status)
    story.append(Spacer(1, 20))
    
    # Signatures
    sig_data = [
        [Paragraph("_____________________________<br/>Firma Operador de Captura", normal_style), 
         Paragraph("_____________________________<br/>Firma Administrador de Calidad / Auditor", normal_style)]
    ]
    t_sig = Table(sig_data, colWidths=[250, 250])
    t_sig.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    
    story.append(KeepTogether([t_sig]))
    
    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

def generate_spc_lote_pdf(lote_data, measurements, stats=None) -> bytes:
    """
    Generates a PDF report for a captured batch/lote, including dimensional measurements.
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
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0056b3"),
        spaceAfter=12
    )
    
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=5
    )
    
    normal_style = ParagraphStyle(
        'DocNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#334155")
    )
    
    bold_style = ParagraphStyle(
        'DocBold',
        parent=normal_style,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # Title
    story.append(Paragraph(f"REPORTE DE CONTROL ESTADÍSTICO DE PROCESO (SPC) - {lote_data['estacion'].upper()}", title_style))
    story.append(Paragraph(f"Fecha de Reporte: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
    story.append(Spacer(1, 10))
    
    # Lote Info
    info_data = [
        [Paragraph("Lote ID:", bold_style), Paragraph(str(lote_data.get("id")), normal_style),
         Paragraph("Fecha Captura:", bold_style), Paragraph(str(lote_data.get("fecha_captura")), normal_style)],
        [Paragraph("Pieza SKU:", bold_style), Paragraph(str(lote_data.get("nombre_sku")), normal_style),
         Paragraph("Estación:", bold_style), Paragraph(str(lote_data.get("estacion")), normal_style)],
        [Paragraph("Operador:", bold_style), Paragraph(str(lote_data.get("operador")), normal_style),
         Paragraph("Turno:", bold_style), Paragraph(str(lote_data.get("turno")), normal_style)],
        [Paragraph("Estatus Lote:", bold_style), Paragraph(str(lote_data.get("estatus")), bold_style),
         Paragraph("V Doble / Gauge:", bold_style), Paragraph(f"V: {lote_data.get('v_dobladura')}mm / Gauge: {lote_data.get('gauge_perfil') or 'N/A'}", normal_style)]
    ]
    t_info = Table(info_data, colWidths=[80, 170, 90, 160])
    t_info.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 10))
    
    # Measurements Table
    story.append(Paragraph("DETALLE DE MEDICIONES CAPTURADAS (Subgrupo n=3)", section_title))
    
    if lote_data['estacion'] == 'Corte Láser':
        meas_header = ["Dimensión / Tolerancia", "Muestra 1", "Muestra 2", "Muestra 3", "Media (X-barra)", "Rango (R)", "Estatus"]
        meas_rows = []
        
        # Dimensions definitions: Nom, LI, LS
        dims = {
            "Largo (Nom: 19.000 ±0.015)": "laser_largo",
            "Ancho (Nom: 3.527 ±0.015)": "laser_ancho",
            "Diámetro Φ (Nom: 0.312 ±0.015)": "laser_diametro"
        }
        
        for name, key in dims.items():
            vals = [m[key] for m in measurements if m[key] is not None]
            if len(vals) == 3:
                x_bar = sum(vals)/3.0
                r = max(vals) - min(vals)
                # determine limits
                if "Largo" in name:
                    li, ls = 18.985, 19.015
                elif "Ancho" in name:
                    li, ls = 3.512, 3.542
                else:
                    li, ls = 0.297, 0.327
                
                status_str = "PASA ✔" if all(li <= v <= ls for v in vals) else "FUERA ✘"
                meas_rows.append([
                    Paragraph(name, normal_style),
                    Paragraph(f"{vals[0]:.4f}", normal_style),
                    Paragraph(f"{vals[1]:.4f}", normal_style),
                    Paragraph(f"{vals[2]:.4f}", normal_style),
                    Paragraph(f"{x_bar:.4f}", bold_style),
                    Paragraph(f"{r:.4f}", normal_style),
                    Paragraph(status_str, bold_style)
                ])
            else:
                meas_rows.append([Paragraph(name, normal_style), "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"])
                
        t_meas = Table([meas_header] + meas_rows, colWidths=[170, 55, 55, 55, 65, 50, 50])
        t_meas.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0056b3")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 4),
            ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ]))
        story.append(t_meas)
        
    else: # Doblez
        meas_header = ["Cota [Nom (LI - LS)]", "M1", "M2", "M3", "Media", "Rango", "Estatus"]
        meas_rows = []
        
        doblez_tolerancias = {
            "cota_a": ("A", 0.630, 0.615, 0.645),
            "cota_b": ("B", 1.250, 1.235, 1.265),
            "cota_c": ("C", 1.880, 1.865, 1.895),
            "cota_d": ("D", 0.380, 0.365, 0.395),
            "cota_e": ("E", 18.630, 18.615, 18.645),
            "cota_f": ("F", 18.130, 18.115, 18.145),
            "cota_g": ("G", 0.880, 0.865, 0.895),
            "cota_h": ("H", 0.630, 0.615, 0.645),
            "cota_i": ("I", 0.380, 0.365, 0.395),
            "cota_j": ("J", 0.031, 0.016, 0.046),
        }
        
        for key, (letter_cota, nom, li, ls) in doblez_tolerancias.items():
            vals = [m[key] for m in measurements if m[key] is not None]
            if len(vals) == 3:
                x_bar = sum(vals)/3.0
                r = max(vals) - min(vals)
                status_str = "PASA ✔" if all(li <= v <= ls for v in vals) else "FUERA ✘"
                meas_rows.append([
                    Paragraph(f"Cota {letter_cota} [{nom:.3f} ({li:.3f} - {ls:.3f})]", normal_style),
                    Paragraph(f"{vals[0]:.3f}", normal_style),
                    Paragraph(f"{vals[1]:.3f}", normal_style),
                    Paragraph(f"{vals[2]:.3f}", normal_style),
                    Paragraph(f"{x_bar:.3f}", bold_style),
                    Paragraph(f"{r:.3f}", normal_style),
                    Paragraph(status_str, bold_style)
                ])
            else:
                meas_rows.append([Paragraph(f"Cota {letter_cota} [{nom:.3f}]", normal_style), "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"])
                
        t_meas = Table([meas_header] + meas_rows, colWidths=[170, 55, 55, 55, 65, 50, 50])
        t_meas.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0056b3")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 4),
            ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ]))
        story.append(t_meas)
        
    story.append(Spacer(1, 15))
    
    # Statistical validation section (Cp/Cpk summary if provided)
    if stats:
        story.append(Paragraph("ANÁLISIS DE CAPACIDAD DE PROCESO (SPC)", section_title))
        stats_header = ["Cota / Característica", "Media (X-barra)", "Desv. Est. (σ)", "Cp", "Cpk", "Capacidad de Proceso"]
        stats_rows = []
        for s in stats:
            stats_rows.append([
                Paragraph(s['name'], normal_style),
                Paragraph(f"{s['mean']:.4f}", normal_style),
                Paragraph(f"{s['std']:.4f}", normal_style),
                Paragraph(f"{s['cp']:.2f}" if s['cp'] is not None else "N/D", normal_style),
                Paragraph(f"{s['cpk']:.2f}" if s['cpk'] is not None else "N/D", bold_style),
                Paragraph(s['status_desc'], normal_style)
            ])
        t_stats = Table([stats_header] + stats_rows, colWidths=[150, 80, 80, 50, 50, 90])
        t_stats.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#64748b")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_stats)
        story.append(Spacer(1, 15))
    
    # Signatures
    sig_data = [
        [Paragraph("_____________________________<br/>Firma Operador de Turno", normal_style), 
         Paragraph("_____________________________<br/>Firma Calidad / Supervisor", normal_style)]
    ]
    t_sig = Table(sig_data, colWidths=[250, 250])
    t_sig.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(KeepTogether([t_sig]))
    
    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

from datetime import datetime

def generate_excel_spc_report_pdf(sku_selected, excel_name, corte_data, doblez_data, stats_list=None,
                                  insp_code=None, insp_date=None, operator=None, shift=None) -> bytes:
    """
    Genera un reporte PDF formal del análisis SPC realizado a partir de la importación de Excel.
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
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#EC2024"), # Corporate Red
        spaceAfter=10
    )
    
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=12,
        spaceAfter=6
    )
    
    normal_style = ParagraphStyle(
        'DocNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#334155")
    )
    
    bold_style = ParagraphStyle(
        'DocBold',
        parent=normal_style,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # Title
    story.append(Paragraph("REPORTE DE CONTROL ESTADÍSTICO DE PROCESO (SPC) DESDE EXCEL", title_style))
    story.append(Paragraph(f"Fecha de Generación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
    story.append(Spacer(1, 10))
    
    # Info Section
    if insp_code:
        info_data = [
            [
                Paragraph("Código Inspección:", bold_style), Paragraph(insp_code, bold_style),
                Paragraph("Fecha Inspección:", bold_style), Paragraph(insp_date if insp_date else datetime.now().strftime('%d/%m/%Y %H:%M'), normal_style)
            ],
            [
                Paragraph("Pieza SKU:", bold_style), Paragraph(sku_selected, normal_style),
                Paragraph("Archivo Origen:", bold_style), Paragraph(excel_name, normal_style)
            ],
            [
                Paragraph("Operador:", bold_style), Paragraph(operator if operator else "N/A", normal_style),
                Paragraph("Turno:", bold_style), Paragraph(shift if shift else "N/A", normal_style)
            ]
        ]
        t_info = Table(info_data, colWidths=[95, 155, 90, 160])
    else:
        info_data = [
            [Paragraph("Pieza SKU:", bold_style), Paragraph(sku_selected, normal_style),
             Paragraph("Archivo Origen:", bold_style), Paragraph(excel_name, normal_style)],
            [Paragraph("Estatus General:", bold_style), Paragraph("Evaluado ✔", bold_style),
             Paragraph("Importación:", bold_style), Paragraph("Hojas CORTE y DOBLEZ", normal_style)]
        ]
        t_info = Table(info_data, colWidths=[90, 160, 90, 160])
        
    t_info.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 12))
    
    # Corte Table
    if corte_data:
        story.append(Paragraph("1. RESUMEN DE DIMENSIONES - CORTE LÁSER", section_title))
        corte_header = ["No.", "RESP", "Nominal", "Tolerancia", "VALOR MFG", "Est. MFG", "VALOR CAL", "Est. CAL"]
        corte_rows = []
        for r in corte_data:
            corte_rows.append([
                Paragraph(str(r.get("No.", "")), normal_style),
                Paragraph(str(r.get("RESP", "")), normal_style),
                Paragraph(f"{float(r.get('DIM', 0)):.4f}", normal_style),
                Paragraph(str(r.get("TOLERANCIA", "")), normal_style),
                Paragraph(f"{float(r.get('VALOR MFG', 0)):.4f}" if r.get('VALOR MFG') is not None else "N/A", normal_style),
                Paragraph(str(r.get("ESTATUS_MFG", "")), bold_style),
                Paragraph(f"{float(r.get('VALOR CAL', 0)):.4f}" if r.get('VALOR CAL') is not None else "N/A", normal_style),
                Paragraph(str(r.get("ESTATUS_CAL", "")), bold_style)
            ])
        t_corte = Table([corte_header] + corte_rows, colWidths=[40, 50, 60, 80, 65, 65, 65, 75])
        t_corte.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0056b3")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 4),
            ('ALIGN', (2,1), (-1,-1), 'CENTER'),
        ]))
        story.append(t_corte)
        story.append(Spacer(1, 12))
        
    # Doblez Table
    if doblez_data:
        story.append(Paragraph("2. RESUMEN DE DIMENSIONES - ESTACIÓN DOBLEZ", section_title))
        doblez_header = ["MEDIDA", "Nominal", "Tolerancia", "VALOR MFG", "Est. MFG", "VALOR CAL", "Est. CAL"]
        doblez_rows = []
        for r in doblez_data:
            doblez_rows.append([
                Paragraph(str(r.get("MEDIDA", "")), normal_style),
                Paragraph(f"{float(r.get('DIMENSION', 0)):.4f}", normal_style),
                Paragraph(str(r.get("TOLERANCIA", "")), normal_style),
                Paragraph(f"{float(r.get('VALOR MFG', 0)):.4f}" if r.get('VALOR MFG') is not None else "N/A", normal_style),
                Paragraph(str(r.get("ESTATUS_MFG", "")), bold_style),
                Paragraph(f"{float(r.get('VALOR CAL', 0)):.4f}" if r.get('VALOR CAL') is not None else "N/A", normal_style),
                Paragraph(str(r.get("ESTATUS_CAL", "")), bold_style)
            ])
        t_doblez = Table([doblez_header] + doblez_rows, colWidths=[60, 70, 90, 70, 70, 70, 70])
        t_doblez.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f59e0b")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 4),
            ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ]))
        story.append(t_doblez)
        story.append(Spacer(1, 12))
        
    # Hist Stats Section
    if stats_list:
        story.append(Paragraph("3. HISTORIAL DE CAPACIDAD DE PROCESO (SPC - Cp/Cpk)", section_title))
        stats_header = ["Dimensión", "Muestras", "Promedio", "Desv. Est. (σ)", "Cp", "Cpk", "Evaluación SPC"]
        stats_rows = []
        for s in stats_list:
            stats_rows.append([
                Paragraph(s['name'], normal_style),
                Paragraph(str(s['samples']), normal_style),
                Paragraph(f"{s['mean']:.4f}", normal_style),
                Paragraph(f"{s['std']:.4f}", normal_style),
                Paragraph(f"{s['cp']:.2f}" if s['cp'] is not None else "N/D", normal_style),
                Paragraph(f"{s['cpk']:.2f}" if s['cpk'] is not None else "N/D", bold_style),
                Paragraph(s['status_desc'], normal_style)
            ])
        t_stats = Table([stats_header] + stats_rows, colWidths=[130, 50, 65, 65, 50, 50, 90])
        t_stats.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#64748b")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_stats)
        story.append(Spacer(1, 15))
        
    # Signatures
    sig_data = [
        [Paragraph("_____________________________<br/>Firma Operador de Turno", normal_style), 
         Paragraph("_____________________________<br/>Firma Calidad / Supervisor", normal_style)]
    ]
    t_sig = Table(sig_data, colWidths=[250, 250])
    t_sig.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(KeepTogether([t_sig]))
    
    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_remision_pdf(remision_code, date_str, piece_sku, inspections_list, consolidated_stats) -> bytes:
    """
    Genera un reporte PDF consolidado de remisión diaria y liberación de embarque,
    incluyendo el análisis estadístico SPC agrupado.
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
    
    # Custom styles
    title_style = ParagraphStyle(
        'RemisionTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#EC2024"), # Corporate Red
        spaceAfter=10
    )
    
    section_title = ParagraphStyle(
        'RemisionSection',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#111111"),
        spaceBefore=12,
        spaceAfter=5
    )
    
    normal_style = ParagraphStyle(
        'RemisionNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#334155")
    )
    
    bold_style = ParagraphStyle(
        'RemisionBold',
        parent=normal_style,
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'RemisionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=0
    )
    
    header_style_center = ParagraphStyle(
        'RemisionHeaderCenter',
        parent=header_style,
        alignment=1
    )
    
    story = []
    
    # Header Title
    story.append(Paragraph("REPORTE CONSOLIDADO DE REMISIÓN Y LIBERACIÓN DE EMBARQUE", title_style))
    story.append(Paragraph(f"Fecha de Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
    story.append(Spacer(1, 10))
    
    # Check if all inspections are approved to set overall status
    all_ok = all(insp.get("status", "") == "Aprobado" for insp in inspections_list)
    estatus_remision = "LIBERADO (APROBADO) ✔" if all_ok else "RETENIDO (EN REVISIÓN) ✘"
    estatus_color = "#16a34a" if all_ok else "#dc2626"
    
    # Metadata Table
    info_data = [
        [
            Paragraph("Código Remisión:", bold_style), Paragraph(remision_code, bold_style),
            Paragraph("Fecha Embarque:", bold_style), Paragraph(date_str, normal_style)
        ],
        [
            Paragraph("Pieza SKU:", bold_style), Paragraph(piece_sku, normal_style),
            Paragraph("Cant. Inspeccionada:", bold_style), Paragraph(f"{len(inspections_list)} piezas", normal_style)
        ],
        [
            Paragraph("Estatus Embarque:", bold_style), 
            Paragraph(f"<font color='{estatus_color}'><b>{estatus_remision}</b></font>", normal_style),
            Paragraph("Tipo Reporte:", bold_style), Paragraph("Consolidado Diario SPC", normal_style)
        ]
    ]
    t_info = Table(info_data, colWidths=[105, 145, 105, 145])
    t_info.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 12))
    
    # Inspections List Table
    story.append(Paragraph("1. RELACIÓN DE PIEZAS INSPECCIONADAS Y EVALUADAS", section_title))
    insp_header = [
        Paragraph("No.", header_style),
        Paragraph("Código de Inspección", header_style),
        Paragraph("Hora Registro", header_style),
        Paragraph("Operador / Inspector", header_style),
        Paragraph("Turno", header_style),
        Paragraph("Estatus General", header_style_center)
    ]
    
    insp_rows = []
    for idx, r in enumerate(inspections_list, 1):
        status_text = r.get("status", "")
        status_style_str = f"<font color='#16a34a'><b>{status_text}</b></font>" if status_text == "Aprobado" else f"<font color='#dc2626'><b>{status_text}</b></font>"
        insp_rows.append([
            Paragraph(str(idx), normal_style),
            Paragraph(r.get("code", ""), bold_style),
            Paragraph(r.get("time", ""), normal_style),
            Paragraph(r.get("operator", ""), normal_style),
            Paragraph(r.get("shift", ""), normal_style),
            Paragraph(status_style_str, normal_style)
        ])
    t_insp = Table([insp_header] + insp_rows, colWidths=[30, 100, 70, 130, 70, 104])
    t_insp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#111111")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (5,1), (5,-1), 'CENTER'),
    ]))
    story.append(t_insp)
    story.append(Spacer(1, 12))
    
    # Consolidated SPC Table
    story.append(Paragraph("2. ANÁLISIS ESTADÍSTICO DE PROCESO (SPC) CONSOLIDADO", section_title))
    stats_header = [
        Paragraph("Característica / Cota", header_style),
        Paragraph("Piezas", header_style_center),
        Paragraph("Promedio", header_style_center),
        Paragraph("Desv. Est. (σ)", header_style_center),
        Paragraph("Cp", header_style_center),
        Paragraph("Cpk", header_style_center),
        Paragraph("Evaluación de Habilidad", header_style_center)
    ]
    
    stats_rows = []
    for s in consolidated_stats:
        cp_val = s.get("cp")
        cpk_val = s.get("cpk")
        cp_str = f"{cp_val:.2f}" if cp_val is not None else "N/D"
        cpk_str = f"{cpk_val:.2f}" if cpk_val is not None else "N/D"
        
        stats_rows.append([
            Paragraph(s.get("name", ""), normal_style),
            Paragraph(str(s.get("samples", 0)), normal_style),
            Paragraph(f"{s.get('mean', 0.0):.4f}", normal_style),
            Paragraph(f"{s.get('std', 0.0):.4f}" if s.get('std', 0.0) > 0 else "N/D", normal_style),
            Paragraph(cp_str, normal_style),
            Paragraph(cpk_str, bold_style),
            Paragraph(s.get("status_desc", ""), normal_style)
        ])
    t_stats = Table([stats_header] + stats_rows, colWidths=[140, 45, 65, 65, 45, 45, 99])
    t_stats.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EC2024")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
    ]))
    story.append(t_stats)
    story.append(Spacer(1, 20))
    
    # Signatures
    sig_data = [
        [
            Paragraph("<b>VALIDADO POR PRODUCCIÓN</b><br/><br/><br/>_____________________________<br/>Supervisor de Turno / Producción", normal_style), 
            Paragraph("<b>LIBERADO POR CALIDAD</b><br/><br/><br/>_____________________________<br/>Auditor de Calidad / VoBo Calidad", normal_style)
        ]
    ]
    t_sig = Table(sig_data, colWidths=[250, 250])
    t_sig.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(KeepTogether([t_sig]))
    
    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

