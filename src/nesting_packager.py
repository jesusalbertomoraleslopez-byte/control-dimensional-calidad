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
