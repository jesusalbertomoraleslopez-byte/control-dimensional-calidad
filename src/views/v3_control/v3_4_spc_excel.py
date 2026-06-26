import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import io
import os
from datetime import datetime
from src.database import get_connection
from src.utils import calculate_spc_stats, generate_gauss_chart
from src.pdf_generator import generate_excel_spc_report_pdf
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side, Protection
from openpyxl.formatting.rule import CellIsRule
from openpyxl.utils import get_column_letter

def format_tolerance(nominal, li, ls):
    """
    Calcula y formatea la tolerancia bilateral o unilateral.
    """
    try:
        nominal = float(nominal)
        li = float(li)
        ls = float(ls)
        upper_tol = ls - nominal
        lower_tol = nominal - li
        if abs(upper_tol - lower_tol) < 1e-6:
            return f"±{upper_tol:.4f}"
        else:
            return f"+{upper_tol:.4f} / -{lower_tol:.4f}"
    except Exception:
        return "N/A"

def apply_excel_template_styling(workbook, num_rows_corte, num_rows_doblez):
    from openpyxl.styles import Protection
    
    # Styling variables
    header_fill = PatternFill(start_color="B30000", end_color="B30000", fill_type="solid") # Dark red like Pantone 485C
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    border_side = Side(border_style="thin", color="D3D3D3")
    cell_border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)
    
    even_fill = PatternFill(start_color="F2F6F9", end_color="F2F6F9", fill_type="solid") # light blue-gray
    odd_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    
    # Conditional formatting colors (soft green/red for readability)
    green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    green_font = Font(name="Calibri", size=11, color="006100", bold=True)
    red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    red_font = Font(name="Calibri", size=11, color="9C0006", bold=True)
    
    # 1. Sheet CORTE
    if "CORTE" in workbook.sheetnames:
        ws = workbook["CORTE"]
        ws.protection.sheet = True # Enable protection
        
        # Style header
        for col in range(1, 10): # A to I
            cell = ws.cell(row=1, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center_align
            cell.border = cell_border
            cell.protection = Protection(locked=True)
            
        # Format rows and set formulas
        for r in range(2, num_rows_corte + 2):
            row_fill = even_fill if r % 2 == 0 else odd_fill
            
            # Formulas for VoBo columns:
            # G is VoBo MFG, checking F (VALOR MFG) against D (LIM.I) and E (LIM.S)
            ws.cell(row=r, column=7, value=f'=IF(F{r}="", "", IF(AND(F{r}>=D{r}, F{r}<=E{r}), "Aprobado", "Fuera de Tolerancia"))')
            # I is VoBo CAL, checking H (VALOR CAL) against D (LIM.I) and E (LIM.S)
            ws.cell(row=r, column=9, value=f'=IF(H{r}="", "", IF(AND(H{r}>=D{r}, H{r}<=E{r}), "Aprobado", "Fuera de Tolerancia"))')
            
            for col in range(1, 10):
                cell = ws.cell(row=r, column=col)
                cell.border = cell_border
                cell.alignment = center_align
                cell.fill = row_fill
                
                # Bold and unlock for measurement inputs (F and H)
                if col in [6, 8]:
                    cell.font = Font(name="Calibri", size=11, bold=True)
                    cell.protection = Protection(locked=False) # Unlock VALOR MFG (col 6) & VALOR CAL (col 8)
                else:
                    cell.font = Font(name="Calibri", size=11)
                    cell.protection = Protection(locked=True) # Lock A-E and G, I (VoBo columns)
                    
        # Apply conditional formatting
        if num_rows_corte > 0:
            ws.conditional_formatting.add(
                f"G2:G{num_rows_corte + 1}",
                CellIsRule(operator="equal", formula=['"Aprobado"'], stopIfTrue=True, fill=green_fill, font=green_font)
            )
            ws.conditional_formatting.add(
                f"G2:G{num_rows_corte + 1}",
                CellIsRule(operator="equal", formula=['"Fuera de Tolerancia"'], stopIfTrue=True, fill=red_fill, font=red_font)
            )
            ws.conditional_formatting.add(
                f"I2:I{num_rows_corte + 1}",
                CellIsRule(operator="equal", formula=['"Aprobado"'], stopIfTrue=True, fill=green_fill, font=green_font)
            )
            ws.conditional_formatting.add(
                f"I2:I{num_rows_corte + 1}",
                CellIsRule(operator="equal", formula=['"Fuera de Tolerancia"'], stopIfTrue=True, fill=red_fill, font=red_font)
            )
        
        # Set column widths
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            # VoBo MFG (G, col 7) and VoBo CAL (I, col 9) are set to exactly 25 points
            if col[0].column in [7, 9]:
                ws.column_dimensions[col_letter].width = 25
            else:
                max_len = 0
                for cell in col:
                    val_str = str(cell.value or '')
                    # If it's a formula, don't use the formula length for width
                    if val_str.startswith('='):
                        val_str = "Fuera de Tolerancia"
                    max_len = max(max_len, len(val_str))
                ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
            
    # 2. Sheet DOBLEZ
    if "DOBLEZ" in workbook.sheetnames:
        ws = workbook["DOBLEZ"]
        ws.protection.sheet = True # Enable protection
        
        # Style header
        for col in range(1, 9): # A to H
            cell = ws.cell(row=1, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center_align
            cell.border = cell_border
            cell.protection = Protection(locked=True)
            
        # Format rows and set formulas
        for r in range(2, num_rows_doblez + 2):
            row_fill = even_fill if r % 2 == 0 else odd_fill
            
            # Formulas for VoBo columns:
            # F is VoBo MFG, checking E (VALOR MFG) against C (LIM.I) and D (LIM.S)
            ws.cell(row=r, column=6, value=f'=IF(E{r}="", "", IF(AND(E{r}>=C{r}, E{r}<=D{r}), "Aprobado", "Fuera de Tolerancia"))')
            # H is VoBo CAL, checking G (VALOR CAL) against C (LIM.I) and D (LIM.S)
            ws.cell(row=r, column=8, value=f'=IF(G{r}="", "", IF(AND(G{r}>=C{r}, G{r}<=D{r}), "Aprobado", "Fuera de Tolerancia"))')
            
            for col in range(1, 9):
                cell = ws.cell(row=r, column=col)
                cell.border = cell_border
                cell.alignment = center_align
                cell.fill = row_fill
                
                # Bold and unlock for measurement inputs (E and G)
                if col in [5, 7]:
                    cell.font = Font(name="Calibri", size=11, bold=True)
                    cell.protection = Protection(locked=False) # Unlock VALOR MFG (col 5) & VALOR CAL (col 7)
                else:
                    cell.font = Font(name="Calibri", size=11)
                    cell.protection = Protection(locked=True) # Lock A-D and F, H (VoBo columns)
                    
        # Apply conditional formatting
        if num_rows_doblez > 0:
            ws.conditional_formatting.add(
                f"F2:F{num_rows_doblez + 1}",
                CellIsRule(operator="equal", formula=['"Aprobado"'], stopIfTrue=True, fill=green_fill, font=green_font)
            )
            ws.conditional_formatting.add(
                f"F2:F{num_rows_doblez + 1}",
                CellIsRule(operator="equal", formula=['"Fuera de Tolerancia"'], stopIfTrue=True, fill=red_fill, font=red_font)
            )
            ws.conditional_formatting.add(
                f"H2:H{num_rows_doblez + 1}",
                CellIsRule(operator="equal", formula=['"Aprobado"'], stopIfTrue=True, fill=green_fill, font=green_font)
            )
            ws.conditional_formatting.add(
                f"H2:H{num_rows_doblez + 1}",
                CellIsRule(operator="equal", formula=['"Fuera de Tolerancia"'], stopIfTrue=True, fill=red_fill, font=red_font)
            )
        
        # Set column widths
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            # VoBo MFG (F, col 6) and VoBo CAL (H, col 8) are set to exactly 25 points
            if col[0].column in [6, 8]:
                ws.column_dimensions[col_letter].width = 25
            else:
                max_len = 0
                for cell in col:
                    val_str = str(cell.value or '')
                    # If it's a formula, don't use the formula length for width
                    if val_str.startswith('='):
                        val_str = "Fuera de Tolerancia"
                    max_len = max(max_len, len(val_str))
                ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

def generate_excel_template_empty():
    """
    Genera un archivo de plantilla Excel con las hojas CORTE y DOBLEZ con especificaciones por defecto pero sin mediciones.
    """
    corte_data = {
        "No.": [1, 2, 3],
        "RESP": ["LASER", "LASER", "LASER"],
        "DIM": [19.000, 3.527, 0.312],
        "LIM.I": [18.985, 3.512, 0.297],
        "LIM.S": [19.015, 3.542, 0.327],
        "VALOR MFG": [np.nan, np.nan, np.nan],
        "VoBo MFG": [np.nan, np.nan, np.nan],
        "VALOR CAL": [np.nan, np.nan, np.nan],
        "VoBo CAL": [np.nan, np.nan, np.nan]
    }
    
    doblez_data = {
        "MEDIDA": ["A", "B", "C", "D", "E"],
        "DIMENSION": [0.630, 1.250, 1.880, 0.380, 18.630],
        "LIM.I": [0.615, 1.235, 1.865, 0.365, 18.615],
        "LIM.S": [0.645, 1.265, 1.895, 0.395, 18.645],
        "VALOR MFG": [np.nan, np.nan, np.nan, np.nan, np.nan],
        "VoBo MFG": [np.nan, np.nan, np.nan, np.nan, np.nan],
        "VALOR CAL": [np.nan, np.nan, np.nan, np.nan, np.nan],
        "VoBo CAL": [np.nan, np.nan, np.nan, np.nan, np.nan]
    }
    
    df_corte = pd.DataFrame(corte_data)
    df_doblez = pd.DataFrame(doblez_data)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_corte.to_excel(writer, sheet_name="CORTE", index=False)
        df_doblez.to_excel(writer, sheet_name="DOBLEZ", index=False)
        
        workbook = writer.book
        apply_excel_template_styling(workbook, len(df_corte), len(df_doblez))
        
    return buffer.getvalue()

def generate_custom_excel_template(file_path):
    """
    Lee las especificaciones desde el Excel de diseño y las devuelve como plantilla vacía para medición.
    Asegura las columnas de proceso vacías.
    """
    xls = pd.ExcelFile(file_path)
    sheets = xls.sheet_names
    
    num_rows_corte = 0
    num_rows_doblez = 0
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        if "CORTE" in sheets:
            df_c = pd.read_excel(file_path, sheet_name="CORTE")
            df_c.columns = [c.strip().upper() for c in df_c.columns]
            required = ["NO.", "RESP", "DIM", "LIM.I", "LIM.S"]
            for col in required:
                if col not in df_c.columns:
                    df_c[col] = np.nan
            
            df_template = pd.DataFrame()
            df_template["No."] = df_c["NO."]
            df_template["RESP"] = df_c["RESP"] if "RESP" in df_c.columns else "LASER"
            df_template["DIM"] = df_c["DIM"]
            df_template["LIM.I"] = df_c["LIM.I"]
            df_template["LIM.S"] = df_c["LIM.S"]
            df_template["VALOR MFG"] = np.nan
            df_template["VoBo MFG"] = np.nan
            df_template["VALOR CAL"] = np.nan
            df_template["VoBo CAL"] = np.nan
            df_template.to_excel(writer, sheet_name="CORTE", index=False)
            num_rows_corte = len(df_template)
            
        if "DOBLEZ" in sheets:
            df_d = pd.read_excel(file_path, sheet_name="DOBLEZ")
            df_d.columns = [c.strip().upper() for c in df_d.columns]
            required = ["MEDIDA", "DIMENSION", "LIM.I", "LIM.S"]
            for col in required:
                if col not in df_d.columns:
                    df_d[col] = np.nan
                    
            df_template = pd.DataFrame()
            df_template["MEDIDA"] = df_d["MEDIDA"]
            df_template["DIMENSION"] = df_d["DIMENSION"]
            df_template["LIM.I"] = df_d["LIM.I"]
            df_template["LIM.S"] = df_d["LIM.S"]
            df_template["VALOR MFG"] = np.nan
            df_template["VoBo MFG"] = np.nan
            df_template["VALOR CAL"] = np.nan
            df_template["VoBo CAL"] = np.nan
            df_template.to_excel(writer, sheet_name="DOBLEZ", index=False)
            num_rows_doblez = len(df_template)
            
        workbook = writer.book
        apply_excel_template_styling(workbook, num_rows_corte, num_rows_doblez)
            
    return buffer.getvalue()

def show_spc_excel():
    st.title("3.4. Control Estadístico de Proceso (SPC) desde Excel")
    st.subheader("Carga e Importación Dinámica de Mediciones de Corte Láser y Doblez")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Select registered piece SKU
    cursor.execute("SELECT id, nombre_sku, ruta_almacenamiento, archivo_excel_resumen FROM piezas")
    pieces = cursor.fetchall()
    
    fallback_sku = "12-A-6004-01-(16ga ANSI-61) - K48 - V3-R0"
    
    if not pieces:
        st.warning("⚠️ No hay piezas registradas en el sistema. Trabajando en Modo Demostración.")
        sku_selected = fallback_sku
        piece_id = 1
        dest_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Proyectos", "END_FILLER", "Rev_R0", "FactorK_48", "Espesor_0.060")
        archivo_excel_resumen = None
    else:
        piece_options = [r["nombre_sku"] for r in pieces]
        sku_selected = st.selectbox("Seleccione el SKU asociado:", piece_options)
        piece_row = [r for r in pieces if r["nombre_sku"] == sku_selected][0]
        piece_id = piece_row["id"]
        dest_dir = piece_row["ruta_almacenamiento"]
        archivo_excel_resumen = piece_row["archivo_excel_resumen"]
        
    sku = sku_selected
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: space-between; 
                    background-color: #F8F9FA; border: 1px solid #D2D3D5; border-radius: 6px; 
                    padding: 0.5rem 1rem; margin-bottom: 0.8rem; font-family: 'Questrial', sans-serif;">
            <span style="font-family: 'Montserrat', sans-serif; font-weight: bold; font-size: 1.1rem; color: #111111;">
                {sku}
            </span>
            <button onclick="navigator.clipboard.writeText('{sku}').then(() => {{
                const btn = document.getElementById('copy-btn-spc');
                btn.innerHTML = '✅ Copiado!';
                btn.style.backgroundColor = '#16a34a';
                setTimeout(() => {{
                    btn.innerHTML = '📋 Copiar SKU';
                    btn.style.backgroundColor = '#EC2024';
                }}, 2000);
            }})" id="copy-btn-spc" style="
                background-color: #EC2024;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
                font-weight: bold;
                font-family: 'Questrial', sans-serif;
                cursor: pointer;
                transition: all 0.2s ease;
            " onmouseover="this.style.backgroundColor='#111111'" onmouseout="if(this.innerHTML!=='✅ Copiado!') this.style.backgroundColor='#EC2024'">
                📋 Copiar SKU
            </button>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Operator and metadata setup
    st.markdown("#### 👤 Datos de Control")
    col_meta1, col_meta2 = st.columns(2)
    with col_meta1:
        operator_name = st.text_input("Operador/Inspector de Calidad", value=st.session_state.get("nombre_completo", "Inspector Calidad"))
    with col_meta2:
        shift_name = st.selectbox("Turno", ["Turno 1", "Turno 2", "Turno 3"])
        
    st.markdown("---")
    
    # Template download action
    st.markdown("##### 📥 Descarga de Plantilla oficial para Capturas")
    st.markdown("Descargue la plantilla de Excel oficial para rellenar con las medidas de Corte Láser y Doblez en piso de producción:")
    
    # Check if the Excel from Engineering exists
    has_design_excel = False
    if archivo_excel_resumen and os.path.exists(archivo_excel_resumen):
        has_design_excel = True
        
    if has_design_excel:
        st.success(f"✅ Formato de medición personalizado disponible para esta pieza (cargado por Ingeniería).")
        excel_tpl_bytes = generate_custom_excel_template(archivo_excel_resumen)
    else:
        st.warning("⚠️ Esta pieza no cuenta con un Excel de especificaciones cargado por Ingeniería. Cargando plantilla genérica de demostración.")
        excel_tpl_bytes = generate_excel_template_empty()
        
    template_filename = f"Plantilla_Medicion_SPC_{sku_selected}.xlsx"
    
    st.download_button(
        label=f"📥 Descargar Formato de Medición para {sku_selected}",
        data=excel_tpl_bytes,
        file_name=template_filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="btn_download_spc_template_red"
    )
    
    st.markdown("---")
    
    # 2. Excel File Upload
    st.markdown("##### 📁 Cargar Mediciones Dimensionales de Excel")
    uploaded_file = st.file_uploader("Cargar Archivo Excel de SPC (.XLSX)", type=["xlsx"])
    
    corte_rows_data = []
    doblez_rows_data = []
    file_processed = False
    excel_name = ""
    
    if uploaded_file:
        excel_name = uploaded_file.name
        try:
            # Read sheets
            xls = pd.ExcelFile(uploaded_file)
            sheets = xls.sheet_names
            
            if "CORTE" not in sheets or "DOBLEZ" not in sheets:
                st.error("❌ El archivo Excel debe contener obligatoriamente las hojas de trabajo con nombres exactos: 'CORTE' y 'DOBLEZ'.")
            else:
                df_corte_raw = pd.read_excel(uploaded_file, sheet_name="CORTE")
                df_doblez_raw = pd.read_excel(uploaded_file, sheet_name="DOBLEZ")
                
                # Check columns case insensitively & trim spaces
                df_corte_raw.columns = [c.strip().upper() for c in df_corte_raw.columns]
                df_doblez_raw.columns = [c.strip().upper() for c in df_doblez_raw.columns]
                
                corte_required = ["NO.", "RESP", "DIM", "LIM.I", "LIM.S"]
                doblez_required = ["MEDIDA", "DIMENSION", "LIM.I", "LIM.S"]
                
                missing_corte = [col for col in corte_required if col not in df_corte_raw.columns]
                missing_doblez = [col for col in doblez_required if col not in df_doblez_raw.columns]
                
                if missing_corte:
                    st.error(f"❌ La hoja 'CORTE' no contiene todas las columnas requeridas: {missing_corte}")
                elif missing_doblez:
                    st.error(f"❌ La hoja 'DOBLEZ' no contiene todas las columnas requeridas: {missing_doblez}")
                else:
                    file_processed = True
                    
                    # Process Corte
                    st.markdown("### ⚡ Resumen de Dimensiones - Corte Láser")
                    corte_list = []
                    for idx, row in df_corte_raw.iterrows():
                        dim_name = f"Corte - No. {int(row['NO.'])}"
                        nominal = float(row["DIM"])
                        li = float(row["LIM.I"])
                        ls = float(row["LIM.S"])
                        
                        val_mfg = float(row["VALOR MFG"]) if "VALOR MFG" in row and not pd.isna(row["VALOR MFG"]) else None
                        val_cal = float(row["VALOR CAL"]) if "VALOR CAL" in row and not pd.isna(row["VALOR CAL"]) else None
                        
                        vobo_mfg = str(row["VOBO MFG"]) if "VOBO MFG" in row and not pd.isna(row["VOBO MFG"]) else "N/A"
                        vobo_cal = str(row["VOBO CAL"]) if "VOBO CAL" in row and not pd.isna(row["VOBO CAL"]) else "N/A"
                        
                        tol_formatted = format_tolerance(nominal, li, ls)
                        
                        dev_mfg = val_mfg - nominal if val_mfg is not None else None
                        dev_cal = val_cal - nominal if val_cal is not None else None
                        
                        est_mfg = "🟢 PASA" if val_mfg is not None and li <= val_mfg <= ls else "🔴 FUERA" if val_mfg is not None else "N/D"
                        est_cal = "🟢 PASA" if val_cal is not None and li <= val_cal <= ls else "🔴 FUERA" if val_cal is not None else "N/D"
                        
                        corte_list.append({
                            "No.": int(row["NO."]),
                            "RESP": str(row["RESP"]),
                            "DIM": nominal,
                            "LIM.I": li,
                            "LIM.S": ls,
                            "TOLERANCIA": tol_formatted,
                            "VALOR MFG": val_mfg,
                            "DEV. MFG": f"{dev_mfg:+.4f}" if dev_mfg is not None else "N/A",
                            "ESTATUS_MFG": est_mfg,
                            "VALOR CAL": val_cal,
                            "DEV. CAL": f"{dev_cal:+.4f}" if dev_cal is not None else "N/A",
                            "ESTATUS_CAL": est_cal,
                            "VOBO MFG": vobo_mfg,
                            "VOBO CAL": vobo_cal,
                            "DIM_NAME": dim_name
                        })
                    
                    corte_rows_data = corte_list
                    df_corte_show = pd.DataFrame(corte_list)
                    st.table(df_corte_show[["No.", "RESP", "DIM", "TOLERANCIA", "VALOR MFG", "DEV. MFG", "ESTATUS_MFG", "VALOR CAL", "DEV. CAL", "ESTATUS_CAL"]])
                    
                    # Process Doblez
                    st.markdown("### 📐 Resumen de Dimensiones - Doblez")
                    doblez_list = []
                    for idx, row in df_doblez_raw.iterrows():
                        dim_name = f"Doblez - {str(row['MEDIDA'])}"
                        nominal = float(row["DIMENSION"])
                        li = float(row["LIM.I"])
                        ls = float(row["LIM.S"])
                        
                        val_mfg = float(row["VALOR MFG"]) if "VALOR MFG" in row and not pd.isna(row["VALOR MFG"]) else None
                        val_cal = float(row["VALOR CAL"]) if "VALOR CAL" in row and not pd.isna(row["VALOR CAL"]) else None
                        
                        vobo_mfg = str(row["VOBO MFG"]) if "VOBO MFG" in row and not pd.isna(row["VOBO MFG"]) else "N/A"
                        vobo_cal = str(row["VOBO CAL"]) if "VOBO CAL" in row and not pd.isna(row["VOBO CAL"]) else "N/A"
                        
                        tol_formatted = format_tolerance(nominal, li, ls)
                        
                        dev_mfg = val_mfg - nominal if val_mfg is not None else None
                        dev_cal = val_cal - nominal if val_cal is not None else None
                        
                        est_mfg = "🟢 PASA" if val_mfg is not None and li <= val_mfg <= ls else "🔴 FUERA" if val_mfg is not None else "N/D"
                        est_cal = "🟢 PASA" if val_cal is not None and li <= val_cal <= ls else "🔴 FUERA" if val_cal is not None else "N/D"
                        
                        doblez_list.append({
                            "MEDIDA": str(row["MEDIDA"]),
                            "DIMENSION": nominal,
                            "LIM.I": li,
                            "LIM.S": ls,
                            "TOLERANCIA": tol_formatted,
                            "VALOR MFG": val_mfg,
                            "DEV. MFG": f"{dev_mfg:+.4f}" if dev_mfg is not None else "N/A",
                            "ESTATUS_MFG": est_mfg,
                            "VALOR CAL": val_cal,
                            "DEV. CAL": f"{dev_cal:+.4f}" if dev_cal is not None else "N/A",
                            "ESTATUS_CAL": est_cal,
                            "VOBO MFG": vobo_mfg,
                            "VOBO CAL": vobo_cal,
                            "DIM_NAME": dim_name
                        })
                    
                    doblez_rows_data = doblez_list
                    df_doblez_show = pd.DataFrame(doblez_list)
                    st.table(df_doblez_show[["MEDIDA", "DIMENSION", "TOLERANCIA", "VALOR MFG", "DEV. MFG", "ESTATUS_MFG", "VALOR CAL", "DEV. CAL", "ESTATUS_CAL"]])
                    
                    # 3. Save to DB Button (Blue)
                    st.markdown("##### 💾 Registrar mediciones")
                    if st.button("💾 Guardar Mediciones en Base de Datos", key="btn_save_excel_spc_blue"):
                        try:
                            # 1. Save Corte Laser
                            for r in corte_list:
                                cursor.execute(
                                    """
                                    INSERT INTO mediciones_excel (
                                        pieza_id, excel_nombre, estacion, dimension_nombre, nominal,
                                        limite_inferior, limite_superior, valor_mfg, vobo_mfg, valor_cal, vobo_cal
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (
                                        piece_id, excel_name, "Corte Láser", r["DIM_NAME"], r["DIM"],
                                        r["LIM.I"], r["LIM.S"], r["VALOR MFG"], r["VOBO MFG"], r["VALOR CAL"], r["VOBO CAL"]
                                    )
                                )
                            # 2. Save Doblez
                            for r in doblez_list:
                                cursor.execute(
                                    """
                                    INSERT INTO mediciones_excel (
                                        pieza_id, excel_nombre, estacion, dimension_nombre, nominal,
                                        limite_inferior, limite_superior, valor_mfg, vobo_mfg, valor_cal, vobo_cal
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (
                                        piece_id, excel_name, "Doblez", r["DIM_NAME"], r["DIMENSION"],
                                        r["LIM.I"], r["LIM.S"], r["VALOR MFG"], r["VOBO MFG"], r["VALOR CAL"], r["VOBO CAL"]
                                    )
                                )
                            conn.commit()
                            st.success(f"✅ ¡Mediciones del archivo '{excel_name}' cargadas y guardadas exitosamente en la Base de Datos!")
                            
                        except Exception as ex:
                            st.error(f"Error al guardar datos: {str(ex)}")
                            
        except Exception as e:
            st.error(f"Error al procesar el archivo Excel: {str(e)}")
            
    st.markdown("---")
    
    # 4. Simulation Tool for Demo/Testing
    st.markdown("##### 🧪 Generar Lotes Simulados de Calidad (Para Análisis SPC)")
    st.markdown("""
        Los cálculos de capacidad de proceso ($C_p$/$C_{pk}$) e histogramas requieren muestras de múltiples piezas cargadas históricamente.
        Presione el botón de abajo para simular e insertar **25 reportes de control dimensional** con variación aleatoria real alrededor del nominal.
    """)
    if st.button("🧪 Generar e Insertar 25 Lotes de Prueba en BD", key="btn_generate_sim_spc_blue"):
        try:
            sim_corte_spec = [
                {"name": "Corte - No. 1", "nominal": 19.000, "li": 18.985, "ls": 19.015, "std": 0.0035},
                {"name": "Corte - No. 2", "nominal": 3.527, "li": 3.512, "ls": 3.542, "std": 0.0040},
                {"name": "Corte - No. 3", "nominal": 0.312, "li": 0.297, "ls": 0.327, "std": 0.0030}
            ]
            sim_doblez_spec = [
                {"name": "Doblez - A", "nominal": 0.630, "li": 0.615, "ls": 0.645, "std": 0.0045},
                {"name": "Doblez - B", "nominal": 1.250, "li": 1.235, "ls": 1.265, "std": 0.0050},
                {"name": "Doblez - C", "nominal": 1.880, "li": 1.865, "ls": 1.895, "std": 0.0045},
                {"name": "Doblez - D", "nominal": 0.380, "li": 0.365, "ls": 0.395, "std": 0.0055},
                {"name": "Doblez - E", "nominal": 18.630, "li": 18.615, "ls": 18.645, "std": 0.0060}
            ]
            
            # Generate 25 records
            for run_idx in range(1, 26):
                sim_filename = f"Reporte_Piso_Simulado_Pieza_{run_idx}.xlsx"
                
                # Corte Laser
                for c_spec in sim_corte_spec:
                    mfg_val = float(np.random.normal(c_spec["nominal"] + 0.001, c_spec["std"]))
                    cal_val = float(np.random.normal(c_spec["nominal"] - 0.0005, c_spec["std"] * 0.9))
                    cursor.execute(
                        """
                        INSERT INTO mediciones_excel (
                            pieza_id, excel_nombre, estacion, dimension_nombre, nominal,
                            limite_inferior, limite_superior, valor_mfg, vobo_mfg, valor_cal, vobo_cal
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            piece_id, sim_filename, "Corte Láser", c_spec["name"], c_spec["nominal"],
                            c_spec["li"], c_spec["ls"], mfg_val, "Aprobado", cal_val, "Aprobado"
                        )
                    )
                    
                # Doblez
                for d_spec in sim_doblez_spec:
                    mfg_val = float(np.random.normal(d_spec["nominal"] + 0.0015, d_spec["std"]))
                    cal_val = float(np.random.normal(d_spec["nominal"] - 0.0002, d_spec["std"] * 0.85))
                    cursor.execute(
                        """
                        INSERT INTO mediciones_excel (
                            pieza_id, excel_nombre, estacion, dimension_nombre, nominal,
                            limite_inferior, limite_superior, valor_mfg, vobo_mfg, valor_cal, vobo_cal
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            piece_id, sim_filename, "Doblez", d_spec["name"], d_spec["nominal"],
                            d_spec["li"], d_spec["ls"], mfg_val, "Aprobado", cal_val, "Aprobado"
                        )
                    )
            
            conn.commit()
            st.success("✅ ¡25 lotes simulados insertados con éxito en la base de datos para el SKU seleccionado!")
            
        except Exception as e_sim:
            st.error(f"Error al generar lotes simulados: {str(e_sim)}")
            
    st.markdown("---")
    
    # 5. Historical SPC Analysis & Visualizations
    st.markdown("### 📈 Análisis de Habilidad y Capacidad de Proceso Histórico (SPC)")
    
    # Load all unique dimensions in DB for this SKU
    cursor.execute(
        """
        SELECT DISTINCT dimension_nombre, estacion 
        FROM mediciones_excel 
        WHERE pieza_id = ?
        ORDER BY estacion, dimension_nombre
        """, (piece_id,)
    )
    dimensions_available = cursor.fetchall()
    
    if not dimensions_available:
        st.info("💡 No hay historial de mediciones de Excel guardado para esta pieza. Suba un archivo de Excel y regístrelo, o genere lotes simulados para habilitar los gráficos y reportes SPC.")
    else:
        dim_options = [f"{r['estacion']} - {r['dimension_nombre']}" for r in dimensions_available]
        selected_dim_opt = st.selectbox("Seleccione la dimensión a analizar:", dim_options)
        
        selected_est = selected_dim_opt.split(" - ")[0]
        selected_dim = selected_dim_opt.split(" - ")[1]
        
        # Load measurements history for this dimension
        df_hist = pd.read_sql_query(
            """
            SELECT excel_nombre, valor_mfg, valor_cal, nominal, limite_inferior, limite_superior, fecha_registro
            FROM mediciones_excel
            WHERE pieza_id = ? AND estacion = ? AND dimension_nombre = ?
            ORDER BY fecha_registro ASC
            """,
            conn,
            params=(piece_id, selected_est, selected_dim)
        )
        
        if len(df_hist) > 0:
            st.markdown(f"**Registros encontrados:** {len(df_hist)}")
            
            nominal = float(df_hist["nominal"].iloc[0])
            li = float(df_hist["limite_inferior"].iloc[0])
            ls = float(df_hist["limite_superior"].iloc[0])
            tol_str = format_tolerance(nominal, li, ls)
            
            # Show summary stats
            st.markdown("##### 📊 Indicadores de Capacidad de Proceso (SPC) - VALOR CAL (Calibración)")
            
            cal_values = df_hist["valor_cal"].dropna().tolist()
            mfg_values = df_hist["valor_mfg"].dropna().tolist()
            
            stats_cal = calculate_spc_stats(cal_values, nominal, li, ls)
            stats_mfg = calculate_spc_stats(mfg_values, nominal, li, ls)
            
            sc_col1, sc_col2, sc_col3, sc_col4 = st.columns(4)
            with sc_col1:
                st.metric("Nominal / Tolerancia", f"{nominal:.4f} ({tol_str})")
            with sc_col2:
                st.metric("Media Muestral (X-barra)", f"{stats_cal['mean']:.4f}")
            with sc_col3:
                st.metric("Capacidad Cp", f"{stats_cal['cp']:.2f}" if stats_cal['cp'] is not None else "N/A")
            with sc_col4:
                status_color = "normal" if stats_cal['pasa'] else "inverse"
                st.metric("Habilidad Cpk", f"{stats_cal['cpk']:.2f}" if stats_cal['cpk'] is not None else "N/A", 
                          delta=stats_cal['status_desc'], delta_color=status_color)
                
            # Gauss Chart
            st.markdown("##### 🔔 Distribución Normal (Campana de Gauss) vs Tolerancias (Calidad)")
            fig_gauss = generate_gauss_chart(cal_values, nominal, li, ls, f"Distribución Normal - {selected_dim}")
            st.plotly_chart(fig_gauss, use_container_width=True)
            
            # Trend / Control Chart
            st.markdown("##### 📈 Gráfico de Tendencia y Control de Proceso (Corrida de Muestras)")
            fig_trend = go.Figure()
            
            # Add Limits
            fig_trend.add_hline(y=nominal, line_color="#10b981", line_width=2, annotation_text="Nominal", annotation_position="top left")
            fig_trend.add_hline(y=li, line_color="#ef4444", line_dash="dash", line_width=2, annotation_text="L.I.", annotation_position="bottom left")
            fig_trend.add_hline(y=ls, line_color="#ef4444", line_dash="dash", line_width=2, annotation_text="L.S.", annotation_position="top left")
            
            indices = list(range(1, len(df_hist) + 1))
            
            # Plot MFG
            fig_trend.add_trace(go.Scatter(
                x=indices, y=df_hist["valor_mfg"],
                mode='lines+markers',
                name='VALOR MFG (Manufactura)',
                line=dict(color='#f59e0b', width=2),
                marker=dict(size=6)
            ))
            
            # Plot CAL
            fig_trend.add_trace(go.Scatter(
                x=indices, y=df_hist["valor_cal"],
                mode='lines+markers',
                name='VALOR CAL (Calibración)',
                line=dict(color='#0056b3', width=2.5),
                marker=dict(size=7)
            ))
            
            fig_trend.update_layout(
                title=f"Gráfica de Tendencia - {selected_dim}",
                xaxis_title="Corridas / Piezas Cargadas",
                yaxis_title="Dimensión Medida (in)",
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=40, r=40, t=50, b=40),
                xaxis=dict(gridcolor='#f1f5f9', tickmode='linear'),
                yaxis=dict(gridcolor='#f1f5f9')
            )
            st.plotly_chart(fig_trend, use_container_width=True)
            
            # 6. Report PDF Export (if file was uploaded)
            st.markdown("##### 📄 Exportar Reporte de Resultados en PDF")
            st.markdown("Haga clic abajo para generar y descargar un informe formal del análisis SPC de las dimensiones importadas:")
            
            # Prepare data list for PDF summary if file was uploaded or from DB
            # We will use active data from the uploaded file if available, or fetch current DB values for report
            active_corte = []
            active_doblez = []
            
            if file_processed:
                active_corte = corte_rows_data
                active_doblez = doblez_rows_data
            else:
                # Retrieve latest file's data from DB
                cursor.execute(
                    """
                    SELECT DISTINCT excel_nombre 
                    FROM mediciones_excel 
                    WHERE pieza_id = ? 
                    ORDER BY fecha_registro DESC 
                    LIMIT 1
                    """, (piece_id,)
                )
                last_excel = cursor.fetchone()
                if last_excel:
                    excel_name = last_excel["excel_nombre"]
                    
                    df_c_db = pd.read_sql_query(
                        "SELECT * FROM mediciones_excel WHERE pieza_id = ? AND excel_nombre = ? AND estacion = 'Corte Láser'",
                        conn, params=(piece_id, excel_name)
                    )
                    df_d_db = pd.read_sql_query(
                        "SELECT * FROM mediciones_excel WHERE pieza_id = ? AND excel_nombre = ? AND estacion = 'Doblez'",
                        conn, params=(piece_id, excel_name)
                    )
                    
                    for idx, row in df_c_db.iterrows():
                        tol_f = format_tolerance(row["nominal"], row["limite_inferior"], row["limite_superior"])
                        est_m = "🟢 PASA" if row["valor_mfg"] is not None and row["limite_inferior"] <= row["valor_mfg"] <= row["limite_superior"] else "🔴 FUERA"
                        est_c = "🟢 PASA" if row["valor_cal"] is not None and row["limite_inferior"] <= row["valor_cal"] <= row["limite_superior"] else "🔴 FUERA"
                        active_corte.append({
                            "No.": idx + 1, "RESP": "LASER", "DIM": row["nominal"], "TOLERANCIA": tol_f,
                            "VALOR MFG": row["valor_mfg"], "ESTATUS_MFG": est_m, "VALOR CAL": row["valor_cal"], "ESTATUS_CAL": est_c
                        })
                        
                    for idx, row in df_d_db.iterrows():
                        tol_f = format_tolerance(row["nominal"], row["limite_inferior"], row["limite_superior"])
                        est_m = "🟢 PASA" if row["valor_mfg"] is not None and row["limite_inferior"] <= row["valor_mfg"] <= row["limite_superior"] else "🔴 FUERA"
                        est_c = "🟢 PASA" if row["valor_cal"] is not None and row["limite_inferior"] <= row["valor_cal"] <= row["limite_superior"] else "🔴 FUERA"
                        active_doblez.append({
                            "MEDIDA": row["dimension_nombre"].replace("Doblez - ", ""),
                            "DIMENSION": row["nominal"],
                            "TOLERANCIA": tol_f,
                            "VALOR MFG": row["valor_mfg"],
                            "ESTATUS_MFG": est_m,
                            "VALOR CAL": row["valor_cal"],
                            "ESTATUS_CAL": est_c
                        })
            
            # Prepare overall stats list for the report
            hist_stats = []
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
            
            if active_corte or active_doblez:
                rep_pdf_bytes = generate_excel_spc_report_pdf(sku_selected, excel_name or "Historial_Guardado.xlsx", active_corte, active_doblez, hist_stats)
                st.download_button(
                    label="📥 Descargar Reporte SPC Excel (PDF)",
                    data=rep_pdf_bytes,
                    file_name=f"Reporte_SPC_Excel_{sku_selected.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    key="btn_download_excel_spc_pdf_blue"
                )
            
    conn.close()
