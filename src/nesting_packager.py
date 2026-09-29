import os
import zipfile
import io
import pandas as pd
from .database import get_connection

def generate_nesting_zip(excel_file_bytes) -> tuple[bytes, list[str]]:
    """
    Reads an Excel file representing the nesting list.
    Excel columns expected:
      - Item: sequential number (e.g. 1, 2, ...)
      - SKU: part SKU name (e.g. '12-A-6004-01-(16ga ANSI-61) - K48 - V3-R0')
      - Cantidad: integer quantity of parts (e.g. 25)
      
    It looks up the DXF files registered in the database, renames them,
    groups them into folders by material, and creates a ZIP package.
    
    Returns:
      (zip_bytes, logs_list)
    """
    logs = []
    
    # Read excel file
    try:
        df = pd.read_excel(io.BytesIO(excel_file_bytes))
    except Exception as e:
        return b"", [f"Error leyendo el archivo Excel: {str(e)}"]
    
    # Clean column names
    df.columns = [c.strip().upper() for c in df.columns]
    
    required_cols = {"ITEM", "SKU", "CANTIDAD"}
    missing = required_cols - set(df.columns)
    if missing:
        return b"", [f"Estructura de Excel inválida. Faltan columnas: {', '.join(missing)}. Las columnas requeridas son: ITEM, SKU, CANTIDAD"]
    
    conn = get_connection()
    cursor = conn.cursor()
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for idx, row in df.iterrows():
            item_raw = row["ITEM"]
            sku_raw = str(row["SKU"]).strip()
            qty_raw = row["CANTIDAD"]
            
            # Format item prefix to 4 digits e.g. 0001
            try:
                item_num = int(item_raw)
                item_prefix = f"{item_num:04d}"
            except Exception:
                item_prefix = str(item_raw).zfill(4)
                
            try:
                qty = int(qty_raw)
            except Exception:
                qty = str(qty_raw)
                
            # Search piece in database
            cursor.execute(
                "SELECT material, archivo_dxf FROM piezas WHERE nombre_sku = ? OR numero_pieza = ?",
                (sku_raw, sku_raw)
            )
            piece = cursor.fetchone()
            
            if not piece:
                logs.append(f"Fila {idx+2}: SKU '{sku_raw}' no registrado en el sistema. Se omite.")
                continue
                
            dxf_path = piece["archivo_dxf"]
            material = piece["material"] or "Otros"
            
            if not dxf_path or not os.path.exists(dxf_path):
                logs.append(f"Fila {idx+2}: SKU '{sku_raw}' no tiene un archivo DXF asociado o el archivo no existe en el servidor. Se omite.")
                continue
                
            # Construct the new filename inside the ZIP
            # Pattern: prefix item (0001) + original name + "[{qty}pz]".DXF
            # E.g. "0001_12-A-6004-01-(16ga ANSI-61) - K48 - V3-R0\"[25pz]\".DXF"
            # Since backslash or special quote might be restricted in ZIP file names, we will use double quotes
            # as requested: 'Y Al Final entre comillas la cantidad de piezas (25pz)' -> ..."[25pz]".DXF
            base_dxf_name = os.path.basename(dxf_path)
            # Remove extension for renaming
            name_no_ext, _ = os.path.splitext(base_dxf_name)
            
            new_filename = f"{item_prefix}_{name_no_ext}\"[#{qty}pz]\".dxf"
            
            # Place in folder structure grouped by material
            # E.g. "16ga/0001_piece\"[25pz]\".dxf"
            zip_entry_path = f"{material}/{new_filename}"
            
            try:
                zip_file.write(dxf_path, arcname=zip_entry_path)
                logs.append(f"Fila {idx+2}: SKU '{sku_raw}' empacado con éxito en '{zip_entry_path}'.")
            except Exception as ex:
                logs.append(f"Fila {idx+2}: Error al empacar el archivo DXF para '{sku_raw}': {str(ex)}")
                
    conn.close()
    
    zip_bytes = zip_buffer.getvalue()
    zip_buffer.close()
    
    return zip_bytes, logs

def generate_piece_documents_zip(piece_data: dict, is_full_engineering_pack: bool = False) -> tuple[bytes, str, list[str]]:
    """
    Genera un paquete ZIP descargable con toda la documentación oficial de una pieza:
    - Plano de Control (PDF)
    - Dibujo Técnico Original (PDF)
    - Archivo de Corte DXF
    - Modelo 3D STEP
    - Archivo Excel Resumen de Medidas
    - Ficha Técnica Oficial PDF autogenerada
    """
    logs = []
    num_pieza = str(piece_data.get("numero_pieza") or "PIEZA").strip().replace("/", "_").replace("\\", "_")
    sku = str(piece_data.get("nombre_sku") or num_pieza).strip().replace("/", "_").replace("\\", "_")
    tag = "INGENIERIA_COMPLETO" if is_full_engineering_pack else "COMPENDIO_DOCUMENTAL"
    zip_filename = f"{num_pieza}_{tag}.zip"

    zip_buffer = io.BytesIO()
    
    from src.services.gcs_storage import get_file_bytes
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 1. Plano de Control
        plano_path = piece_data.get("archivo_plano_control")
        if plano_path:
            b = get_file_bytes(plano_path)
            if b:
                ext = os.path.splitext(plano_path)[1] or ".pdf"
                zf.writestr(f"01_Planos/{num_pieza}_PLANO_CONTROL{ext}", b)
                logs.append("Plano de Control incluido con éxito.")
            else:
                logs.append(f"No se pudieron leer los bytes del Plano de Control: {plano_path}")

        # 2. Dibujo Original
        orig_path = piece_data.get("archivo_dibujo_original")
        if orig_path and orig_path != plano_path:
            b = get_file_bytes(orig_path)
            if b:
                ext = os.path.splitext(orig_path)[1] or ".pdf"
                zf.writestr(f"01_Planos/{num_pieza}_DIBUJO_ORIGINAL{ext}", b)
                logs.append("Dibujo Original incluido.")

        # 3. Archivo DXF
        dxf_path = piece_data.get("archivo_dxf")
        if dxf_path:
            b = get_file_bytes(dxf_path)
            if b:
                ext = os.path.splitext(dxf_path)[1] or ".dxf"
                zf.writestr(f"02_Manufactura_CNC/{num_pieza}_CORTE_LASER{ext}", b)
                logs.append("Archivo DXF de Corte incluido.")

        # 4. Modelo 3D STEP
        step_path = piece_data.get("archivo_step")
        if step_path:
            b = get_file_bytes(step_path)
            if b:
                ext = os.path.splitext(step_path)[1] or ".step"
                zf.writestr(f"03_Modelos_3D/{num_pieza}_CAD{ext}", b)
                logs.append("Modelo 3D STEP incluido.")

        # 5. Archivo Excel Resumen
        excel_path = piece_data.get("archivo_excel_resumen")
        if excel_path:
            b = get_file_bytes(excel_path)
            if b:
                ext = os.path.splitext(excel_path)[1] or ".xlsx"
                zf.writestr(f"04_Especificaciones/{num_pieza}_RESUMEN{ext}", b)
                logs.append("Excel de Resumen incluido.")

        # 6. Ficha Técnica Oficial PDF autogenerada
        try:
            from src.pdf_generator import generate_first_piece_pdf
            pdf_data = dict(piece_data)
            if not pdf_data.get("usuario_registro"):
                pdf_data["usuario_registro"] = "Ingeniería SIGRAMA"
            pdf_ficha = generate_first_piece_pdf(pdf_data)
            if pdf_ficha:
                zf.writestr(f"00_Ficha_Tecnica/{num_pieza}_FICHA_TECNICA.pdf", pdf_ficha)
                logs.append("Ficha Técnica Oficial PDF generada e integrada.")
        except Exception as e:
            logs.append(f"Aviso al generar ficha técnica PDF: {str(e)}")

        # 7. Manifiesto / README del paquete
        manifest_txt = f"""======================================================================
SIGRAMA METALES — PAQUETE TÉCNICO OFICIAL DE INGENIERÍA Y CALIDAD
======================================================================
Número de Pieza:  {piece_data.get('numero_pieza', 'N/D')}
Código SKU:       {piece_data.get('nombre_sku', 'N/D')}
Material:         {piece_data.get('material', 'N/D')}
Espesor Nominal:  {piece_data.get('espesor_materia_prima', 'N/D')} in
Acabado:          {piece_data.get('acabado_estandar', 'N/D')}
Factor K:         {piece_data.get('factor_k', 'N/D')}%
Versión / Rev:    {piece_data.get('version', 'V1')}-{piece_data.get('revision', 'R0')}
Fecha de Paquete: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
======================================================================
Archivos contenidos:
- 00_Ficha_Tecnica: Hoja de especificaciones de ingeniería y calibración.
- 01_Planos: Plano de control acotado y/o dibujo original de cliente.
- 02_Manufactura_CNC: Geometría plana desplegada para corte por láser (DXF).
- 03_Modelos_3D: Archivo tridimensional estándar (STEP).
- 04_Especificaciones: Tablas y resúmenes dimensionales complementarios.
======================================================================
Industria Sigrama S.A. de C.V. — Ingeniería que da resultados!!
"""
        zf.writestr(f"LEEME_{num_pieza}.txt", manifest_txt)

    zip_bytes = zip_buffer.getvalue()
    zip_buffer.close()
    return zip_bytes, zip_filename, logs

