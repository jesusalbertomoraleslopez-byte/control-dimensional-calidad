import io
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def generate_bulk_audit_excel(scanned_rows: list, source_path: str = '') -> bytes:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    
    color_header_fill = '111111'
    color_header_font = 'FFFFFF'
    color_brand_red = 'EC2024'
    color_border = 'D2D3D5'
    
    fill_ok = PatternFill(start_color='D4EDDA', end_color='D4EDDA', fill_type='solid')
    font_ok = Font(name='Arial', size=10, bold=True, color='155724')
    
    fill_err = PatternFill(start_color='F8D7DA', end_color='F8D7DA', fill_type='solid')
    font_err = Font(name='Arial', size=10, bold=True, color='721C24')
    
    fill_status_ok = PatternFill(start_color='C3E6CB', end_color='C3E6CB', fill_type='solid')
    font_status_ok = Font(name='Arial', size=10, bold=True, color='0F5132')
    
    fill_status_err = PatternFill(start_color='F5C6CB', end_color='F5C6CB', fill_type='solid')
    font_status_err = Font(name='Arial', size=10, bold=True, color='842029')
    
    thin_border = Border(
        left=Side(style='thin', color=color_border),
        right=Side(style='thin', color=color_border),
        top=Side(style='thin', color=color_border),
        bottom=Side(style='thin', color=color_border)
    )
    
    align_center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    align_left = Alignment(horizontal='left', vertical='center')
    
    total_folders = len(scanned_rows)
    ready_count = sum(1 for r in scanned_rows if r.get('ready'))
    pending_count = total_folders - ready_count
    pct_ready = (ready_count / total_folders * 100.0) if total_folders > 0 else 0.0
    now_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    headers = [
        ('No.', 6, align_center),
        ('Carpeta de Origen', 36, align_left),
        ('Número de Pieza', 18, align_left),
        ('Material', 12, align_center),
        ('Acabado', 14, align_center),
        ('Factor K', 10, align_center),
        ('Versión', 10, align_center),
        ('Revisión', 10, align_center),
        ('SKU Detectado', 42, align_left),
        ('Dibujo PDF', 15, align_center),
        ('Desplegado DXF', 15, align_center),
        ('Plano Control PDF', 18, align_center),
        ('Plano 3D (SLDDRW)', 18, align_center),
        ('Dibujo 2D (SLDPRT)', 18, align_center),
        ('Modelo STEP', 16, align_center),
        ('Excel Tolerancias', 18, align_center),
        ('Estatus General', 26, align_center),
        ('Detalle de Pendientes / Acción para Ingeniería', 48, align_left)
    ]
    
    sheets_config = [
        ('Auditoría General', scanned_rows, False),
        ('Solo Pendientes (Ingeniería)', [r for r in scanned_rows if not r.get('ready')], True)
    ]
    
    for sheet_title, rows_data, is_pending_only in sheets_config:
        ws = wb.create_sheet(title=sheet_title)
        ws.views.sheetView[0].showGridLines = True
        
        ws.merge_cells('A1:R1')
        top_cell = ws['A1']
        top_cell.value = 'INDUSTRIA SIGRAMA S.A. DE C.V.  |  CONTROL DIMENSIONAL DE CALIDAD'
        top_cell.font = Font(name='Arial', size=11, bold=True, color='FFFFFF')
        top_cell.fill = PatternFill(start_color=color_header_fill, end_color=color_header_fill, fill_type='solid')
        top_cell.alignment = Alignment(horizontal='left', vertical='center', indent=1)
        ws.row_dimensions[1].height = 26
        
        ws.merge_cells('A2:R2')
        title_cell = ws['A2']
        if is_pending_only:
            title_cell.value = 'PLAN DE TRABAJO - PIEZAS CON ARCHIVOS PENDIENTES DE INGENIERÍA'
        else:
            title_cell.value = 'REPORTE CONSOLIDADO DE AUDITORÍA DE ARCHIVOS DE INGENIERÍA'
        title_cell.font = Font(name='Arial', size=14, bold=True, color=color_brand_red)
        title_cell.alignment = Alignment(horizontal='left', vertical='center', indent=1)
        ws.row_dimensions[2].height = 28
        
        ws['A4'] = 'Fecha y Hora de Auditoría:'
        ws['A4'].font = Font(name='Arial', size=9, bold=True, color='4B5563')
        ws['C4'] = now_str
        ws['C4'].font = Font(name='Arial', size=9, bold=True)
        
        ws['A5'] = 'Carpeta / Origen Auditado:'
        ws['A5'].font = Font(name='Arial', size=9, bold=True, color='4B5563')
        ws['C5'] = source_path if source_path else 'Carga Local / Red / ZIP'
        ws['C5'].font = Font(name='Arial', size=9)
        
        ws['G4'] = 'Total Carpetas Analizadas:'
        ws['G4'].font = Font(name='Arial', size=9, bold=True, color='4B5563')
        ws['I4'] = total_folders
        ws['I4'].font = Font(name='Arial', size=10, bold=True)
        
        ws['G5'] = 'Diseños Completos (Listos):'
        ws['G5'].font = Font(name='Arial', size=9, bold=True, color='155724')
        ws['I5'] = ready_count
        ws['I5'].font = Font(name='Arial', size=10, bold=True, color='155724')
        
        ws['K4'] = 'Diseños con Pendientes:'
        ws['K4'].font = Font(name='Arial', size=9, bold=True, color='721C24')
        ws['M4'] = pending_count
        ws['M4'].font = Font(name='Arial', size=10, bold=True, color='721C24')
        
        ws['K5'] = 'Porcentaje de Integridad:'
        ws['K5'].font = Font(name='Arial', size=9, bold=True, color='0369A1')
        ws['M5'] = f'{pct_ready:.1f}%'
        ws['M5'].font = Font(name='Arial', size=10, bold=True, color='0369A1')
        
        if is_pending_only:
            ws['O4'] = 'Estado del Listado:'
            ws['O4'].font = Font(name='Arial', size=9, bold=True, color='721C24')
            ws['P4'] = f'{len(rows_data)} piezas por completar'
            ws['P4'].font = Font(name='Arial', size=9, bold=True, color='721C24')
            
        header_row = 7
        ws.row_dimensions[header_row].height = 28
        
        for col_idx, (col_name, col_w, col_align) in enumerate(headers, start=1):
            cell = ws.cell(row=header_row, column=col_idx, value=col_name)
            cell.font = Font(name='Arial', size=10, bold=True, color=color_header_font)
            cell.fill = PatternFill(start_color=color_header_fill, end_color=color_header_fill, fill_type='solid')
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.border = thin_border
            ws.column_dimensions[get_column_letter(col_idx)].width = col_w
            
        start_row = 8
        for r_idx, row_item in enumerate(rows_data, start=1):
            curr_row = start_row + r_idx - 1
            ws.row_dimensions[curr_row].height = 22
            
            parsed = row_item.get('parsed', {})
            files = row_item.get('files', {})
            is_ready = row_item.get('ready', False)
            status_text = row_item.get('Estatus', '')
            
            missing_items = []
            if not files.get('pdf_orig'): missing_items.append('Dibujo PDF')
            if not files.get('dxf'): missing_items.append('DXF')
            if not files.get('control_pdf'): missing_items.append('Plano Control')
            if not files.get('slddrw'): missing_items.append('Plano 3D (SLDDRW)')
            if not files.get('sldprt'): missing_items.append('Dibujo 2D (SLDPRT)')
            if not files.get('step'):
                missing_items.append('Modelo STEP')
            elif 'inválido' in str(row_item.get('Plano STEP', '')).lower():
                missing_items.append('STEP Inválido/Vacío')
            if not files.get('xlsx'):
                missing_items.append('Excel Tolerancias')
            elif 'sin corte' in str(row_item.get('Excel Resumen', '')).lower():
                missing_items.append('Excel sin hojas Corte/Doblez')
                
            if is_ready:
                detail_desc = '✔ Completo - Todos los archivos requeridos validados'
                clean_status = 'COMPLETO (Listo)'
            else:
                detail_desc = 'Falta: ' + ', '.join(missing_items) if missing_items else status_text.replace('🔴', '').strip()
                clean_status = 'PENDIENTE DE INGENIERÍA'
                
            row_vals = [
                (r_idx, align_center, None, None),
                (row_item.get('Carpeta', ''), align_left, None, None),
                (parsed.get('part_no', ''), align_left, None, None),
                (parsed.get('material', ''), align_center, None, None),
                (parsed.get('finish', ''), align_center, None, None),
                (parsed.get('k_factor', ''), align_center, None, None),
                (parsed.get('version', ''), align_center, None, None),
                (parsed.get('revision', ''), align_center, None, None),
                (row_item.get('SKU Detectado', ''), align_left, None, None),
                
                ('ENCONTRADO' if files.get('pdf_orig') else 'FALTANTE', align_center, fill_ok if files.get('pdf_orig') else fill_err, font_ok if files.get('pdf_orig') else font_err),
                ('ENCONTRADO' if files.get('dxf') else 'FALTANTE', align_center, fill_ok if files.get('dxf') else fill_err, font_ok if files.get('dxf') else font_err),
                ('ENCONTRADO' if files.get('control_pdf') else 'FALTANTE', align_center, fill_ok if files.get('control_pdf') else fill_err, font_ok if files.get('control_pdf') else font_err),
                ('ENCONTRADO' if files.get('slddrw') else 'FALTANTE', align_center, fill_ok if files.get('slddrw') else fill_err, font_ok if files.get('slddrw') else fill_err),
                ('ENCONTRADO' if files.get('sldprt') else 'FALTANTE', align_center, fill_ok if files.get('sldprt') else fill_err, font_ok if files.get('sldprt') else font_err),
                (
                    'ENCONTRADO' if 'encontrado' in str(row_item.get('Plano STEP', '')).lower() 
                    else ('INVÁLIDO' if 'inválido' in str(row_item.get('Plano STEP', '')).lower() else 'FALTANTE'),
                    align_center,
                    fill_ok if 'encontrado' in str(row_item.get('Plano STEP', '')).lower() else fill_err,
                    font_ok if 'encontrado' in str(row_item.get('Plano STEP', '')).lower() else font_err
                ),
                (
                    'ENCONTRADO' if 'encontrado' in str(row_item.get('Excel Resumen', '')).lower() 
                    else ('FORMATO INCORRECTO' if 'corte' in str(row_item.get('Excel Resumen', '')).lower() else 'FALTANTE'),
                    align_center,
                    fill_ok if 'encontrado' in str(row_item.get('Excel Resumen', '')).lower() else fill_err,
                    font_ok if 'encontrado' in str(row_item.get('Excel Resumen', '')).lower() else font_err
                ),
                (clean_status, align_center, fill_status_ok if is_ready else fill_status_err, font_status_ok if is_ready else font_status_err),
                (detail_desc, align_left, None, Font(name='Arial', size=9, bold=not is_ready, color='842029' if not is_ready else '155724'))
            ]
            
            for col_idx, (val, c_align, c_fill, c_font) in enumerate(row_vals, start=1):
                cell = ws.cell(row=curr_row, column=col_idx, value=val)
                cell.alignment = c_align
                cell.border = thin_border
                if c_fill:
                    cell.fill = c_fill
                else:
                    if curr_row % 2 == 0:
                        cell.fill = PatternFill(start_color='FAFBFB', end_color='FAFBFB', fill_type='solid')
                if c_font:
                    cell.font = c_font
                else:
                    cell.font = Font(name='Arial', size=9)
                    
        ws.freeze_panes = 'A8'
        last_row = start_row + len(rows_data) - 1 if rows_data else start_row
        ws.auto_filter.ref = f'A7:R{last_row}'
        
    buf = io.BytesIO()
    wb.save(buf)
    val = buf.getvalue()
    buf.close()
    return val
