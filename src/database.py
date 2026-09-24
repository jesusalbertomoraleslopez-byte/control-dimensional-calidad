import os
import sqlite3
import hashlib
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "sigrama_calidad.db")

def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=60.0)
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 60000;")
    except Exception:
        pass
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 1. Usuarios Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('Administrador', 'Operador')),
        nombre_completo TEXT NOT NULL,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 2. Materias Primas Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materias_primas (
        material TEXT PRIMARY KEY,
        espesor_nominal REAL NOT NULL
    );
    """)
    
    # 3. Piezas Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS piezas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        consecutivo_ing TEXT,
        numero_pieza TEXT NOT NULL,
        material TEXT NOT NULL REFERENCES materias_primas(material),
        acabado_estandar TEXT NOT NULL,
        factor_k INTEGER NOT NULL,
        version TEXT NOT NULL,
        revision TEXT NOT NULL,
        nombre_sku TEXT UNIQUE NOT NULL,
        espesor_materia_prima REAL NOT NULL,
        ancho_materia_prima REAL NOT NULL,
        largo_materia_prima REAL NOT NULL,
        ruta_almacenamiento TEXT NOT NULL,
        -- Design files
        archivo_dibujo_original TEXT,
        archivo_dxf TEXT,
        archivo_plano_control TEXT,
        archivo_plano_nativo_3d TEXT,
        archivo_dibujo_nativo_2d TEXT,
        archivo_excel_resumen TEXT,
        archivo_step TEXT,
        -- First piece validation evidence
        plano_validado_impreso TEXT,
        documento_primera_pieza TEXT,
        -- Audit tracking
        estatus_auditoria TEXT DEFAULT 'Sin Auditar',
        fecha_auditoria TIMESTAMP,
        auditor_nombre TEXT,
        auditoria_notas TEXT,
        documentos_completos INTEGER DEFAULT 0,
        usuario_registro TEXT NOT NULL,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Dynamic migrations for existing databases
    cursor.execute("PRAGMA table_info(piezas)")
    existing_cols = [c[1] for c in cursor.fetchall()]
    new_cols = [
        ("consecutivo_ing", "TEXT"),
        ("estatus_auditoria", "TEXT DEFAULT 'Sin Auditar'"),
        ("fecha_auditoria", "TIMESTAMP"),
        ("auditor_nombre", "TEXT"),
        ("auditoria_notas", "TEXT"),
        ("documentos_completos", "INTEGER DEFAULT 0")
    ]
    for col_name, col_def in new_cols:
        if col_name not in existing_cols:
            try:
                cursor.execute(f"ALTER TABLE piezas ADD COLUMN {col_name} {col_def};")
            except Exception:
                pass
    
    # 4. Lotes Control Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lotes_control (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pieza_id INTEGER NOT NULL REFERENCES piezas(id),
        operador TEXT NOT NULL,
        turno TEXT NOT NULL CHECK (turno IN ('Turno 1', 'Turno 2', 'Turno 3')),
        estacion TEXT NOT NULL CHECK (estacion IN ('Corte Láser', 'Doblez')),
        estatus TEXT DEFAULT 'Pendiente' CHECK (estatus IN ('Aprobado', 'Rechazado', 'Pendiente')),
        v_dobladura REAL DEFAULT 10.0,
        gauge_perfil TEXT CHECK (gauge_perfil IN ('Embona', 'No Embona', 'N/A')),
        fecha_captura TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 5. Mediciones Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mediciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lote_id INTEGER NOT NULL REFERENCES lotes_control(id) ON DELETE CASCADE,
        muestra_numero INTEGER NOT NULL CHECK (muestra_numero BETWEEN 1 AND 3),
        -- Laser Measurements
        laser_largo REAL,
        laser_ancho REAL,
        laser_diametro REAL,
        -- Bender Measurements (A to J)
        cota_a REAL,
        cota_b REAL,
        cota_c REAL,
        cota_d REAL,
        cota_e REAL,
        cota_f REAL,
        cota_g REAL,
        cota_h REAL,
        cota_i REAL,
        cota_j REAL
    );
    """)
    
    # 6. Glosario de Documentos Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS glosario_documentos (
        codigo_documento TEXT PRIMARY KEY,
        nombre_oficial TEXT NOT NULL,
        asociado_a TEXT NOT NULL,
        ruta_plantilla_muestra TEXT NOT NULL
    );
    """)
    
    # 7. Procedimientos SGC
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS procedimientos_sgc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,
        nombre TEXT NOT NULL,
        version TEXT NOT NULL,
        fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ruta_archivo TEXT NOT NULL
    );
    """)
    
    # 8. Mediciones Excel Table (flexible schema for dynamic dimensions loaded from Excel)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mediciones_excel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pieza_id INTEGER NOT NULL REFERENCES piezas(id),
        excel_nombre TEXT NOT NULL,
        estacion TEXT NOT NULL, -- 'Corte Láser' o 'Doblez'
        dimension_nombre TEXT NOT NULL,
        nominal REAL NOT NULL,
        limite_inferior REAL NOT NULL,
        limite_superior REAL NOT NULL,
        valor_mfg REAL,
        vobo_mfg TEXT,
        valor_cal REAL,
        vobo_cal TEXT,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 9. Inspecciones Table (new table for QC movements & history)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inspecciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_inspeccion TEXT UNIQUE NOT NULL,
        pieza_id INTEGER NOT NULL REFERENCES piezas(id),
        fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        operador TEXT NOT NULL,
        turno TEXT NOT NULL,
        excel_nombre TEXT NOT NULL,
        estatus_general TEXT NOT NULL,
        calibre TEXT
    );
    """)
    
    # Add inspeccion_id to mediciones_excel if it doesn't exist
    cursor.execute("PRAGMA table_info(mediciones_excel);")
    columns = [row[1] for row in cursor.fetchall()]
    if "inspeccion_id" not in columns:
        cursor.execute("ALTER TABLE mediciones_excel ADD COLUMN inspeccion_id INTEGER REFERENCES inspecciones(id) ON DELETE CASCADE;")
    
    # Insert Default Users
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        admin_pass = hash_password("admin123")
        op_pass = hash_password("operador123")
        cursor.execute("INSERT INTO usuarios (username, password_hash, role, nombre_completo) VALUES (?, ?, ?, ?)",
                       ("admin", admin_pass, "Administrador", "Administrador de Calidad"))
        cursor.execute("INSERT INTO usuarios (username, password_hash, role, nombre_completo) VALUES (?, ?, ?, ?)",
                       ("operador", op_pass, "Operador", "Operador de Planta"))
        
    # Insert Default Materials and Nominal Thicknesses
    cursor.execute("SELECT COUNT(*) FROM materias_primas")
    if cursor.fetchone()[0] == 0:
        materials = [
            ("10gacr", 0.1345),
            ("12gacr", 0.1046),
            ("14gacr", 0.0747),
            ("10ga", 0.1345),
            ("12ga", 0.1046),
            ("14ga", 0.0747),
            ("16ga", 0.0598), # ~0.060 as in example
            ("250Al", 0.250),
            ("375Al", 0.375)
        ]
        cursor.executemany("INSERT INTO materias_primas (material, espesor_nominal) VALUES (?, ?)", materials)
        
    # Insert Default Glossary rows
    cursor.execute("SELECT COUNT(*) FROM glosario_documentos")
    if cursor.fetchone()[0] == 0:
        glossary_items = [
            ("DOC-CAD-01", "Dibujo Original del Cliente (PDF)", "3.2 Registro de Diseño", "muestras/DOC-CAD-01-muestra.pdf"),
            ("DOC-DXF-02", "Desplegado DXF para Corte Láser", "3.2 Registro de Diseño y Nesteo", "muestras/DOC-DXF-02-muestra.dxf"),
            ("DOC-PLN-03", "Plano de Control Dimensional (PDF)", "3.2 Registro de Diseño y Piso", "muestras/DOC-PLN-03-muestra.pdf"),
            ("DOC-3DN-04", "Plano Nativo Diseño 3D (SLDDRW)", "3.2 Registro de Diseño (SolidWorks)", "muestras/DOC-3DN-04-muestra.slddrw"),
            ("DOC-2DN-05", "Dibujo Nativo Diseño 2D (SLDPRT)", "3.2 Registro de Diseño (SolidWorks)", "muestras/DOC-2DN-05-muestra.sldprt"),
            ("DOC-XLS-06", "Excel con Resumen de Dimensiones", "3.2 / 3.3 Validaciones y Captura", "muestras/DOC-XLS-06-muestra.xlsx"),
            ("DOC-STP-07", "Archivo CAD 3D Generales (.STEP)", "3.1 Visualizador CAD 3D", "muestras/DOC-STP-07-muestra.step"),
            ("DOC-VAL-08", "Plano Validado Impreso (PDF Escaneado)", "3.2 Evidencia de Primera Pieza", "muestras/DOC-VAL-08-muestra.pdf"),
            ("DOC-REP-09", "Reporte Final de Primera Pieza Válida (PDF)", "3.2 Registro de Diseño (Salida)", "muestras/DOC-REP-09-muestra.pdf"),
            ("DOC-SPC-10", "Reporte Control Estadístico de Lote", "3.3 Captura en Piso (Salida)", "muestras/DOC-SPC-10-muestra.pdf"),
            ("SGC-PRC-01", "Procedimiento de Control Dimensional (SGC)", "4. Sistema de Gestión de Calidad", "muestras/SGC-PRC-01-muestra.pdf"),
            ("MAN-OPE-01", "Manual de Operación de Calidad (PDF)", "7. Manual de Operación", "muestras/MAN-OPE-01-muestra.pdf")
        ]
        cursor.executemany("INSERT INTO glosario_documentos (codigo_documento, nombre_oficial, asociado_a, ruta_plantilla_muestra) VALUES (?, ?, ?, ?)", glossary_items)
        
    # Auto-sync existing parts from src/Proyectos directory into piezas table (only if empty)
    try:
        cursor.execute("SELECT COUNT(*) FROM piezas")
        piezas_existentes = cursor.fetchone()[0]
    except Exception:
        piezas_existentes = 0

    if piezas_existentes == 0:
        seed_path = os.path.join(DB_DIR, "seed_piezas.json")
        if os.path.exists(seed_path):
            import json
            try:
                with open(seed_path, "r", encoding="utf-8") as f:
                    seed_data = json.load(f)
                for item in seed_data:
                    mat = item.get("material") or "16ga"
                    esp = float(item.get("espesor_materia_prima") or 0.060)
                    cursor.execute("INSERT OR IGNORE INTO materias_primas (material, espesor_nominal) VALUES (?, ?)", (mat, esp))
                    cursor.execute("""
                    INSERT OR IGNORE INTO piezas (
                        consecutivo_ing, numero_pieza, material, acabado_estandar, factor_k, version, revision, nombre_sku,
                        espesor_materia_prima, ancho_materia_prima, largo_materia_prima, ruta_almacenamiento,
                        archivo_dibujo_original, archivo_dxf, archivo_plano_control, archivo_plano_nativo_3d,
                        archivo_dibujo_nativo_2d, archivo_excel_resumen, archivo_step,
                        plano_validado_impreso, documento_primera_pieza,
                        estatus_auditoria, fecha_auditoria, auditor_nombre, auditoria_notas,
                        documentos_completos, usuario_registro, fecha_registro
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item.get("consecutivo_ing"), item.get("numero_pieza"), item.get("material"), item.get("acabado_estandar"),
                        item.get("factor_k"), item.get("version"), item.get("revision"), item.get("nombre_sku"),
                        item.get("espesor_materia_prima", 0.0), item.get("ancho_materia_prima", 0.0), item.get("largo_materia_prima", 0.0),
                        item.get("ruta_almacenamiento"), item.get("archivo_dibujo_original"), item.get("archivo_dxf"),
                        item.get("archivo_plano_control"), item.get("archivo_plano_nativo_3d"), item.get("archivo_dibujo_nativo_2d"),
                        item.get("archivo_excel_resumen"), item.get("archivo_step"), item.get("plano_validado_impreso"),
                        item.get("documento_primera_pieza"), item.get("estatus_auditoria", "Sin Auditar"),
                        item.get("fecha_auditoria"), item.get("auditor_nombre"), item.get("auditoria_notas"),
                        item.get("documentos_completos", 0), item.get("usuario_registro", "Sistema"),
                        item.get("fecha_registro")
                    ))
            except Exception:
                pass

        proyectos_dir = os.path.join(os.path.dirname(__file__), "Proyectos")
        if os.path.exists(proyectos_dir):
            import re
            pattern = r"(?P<part_no>.+?)-\((?P<material>[a-zA-Z0-9]+)\s+(?P<finish>.+?)\)\s*-\s*K(?P<k_factor>\d+)\s*-\s*(?P<version>V\d+)-(?P<revision>R\d+)"
            for root, dirs, files in os.walk(proyectos_dir):
                step_files = [f for f in files if f.lower().endswith(('.step', '.stp'))]
                if step_files:
                    sku_candidate = os.path.splitext(step_files[0])[0]
                    m = re.search(pattern, sku_candidate)
                    if m:
                        p = m.groupdict()
                        full_sku = f"{p['part_no']}-({p['material']} {p['finish']}) - K{p['k_factor']} - {p['version']}-{p['revision']}"
                        
                        dxf = next((os.path.join(root, f) for f in files if f.lower().endswith('.dxf')), None)
                        step = os.path.join(root, step_files[0])
                        xlsx = next((os.path.join(root, f) for f in files if f.lower().endswith('.xlsx')), None)
                        slddrw = next((os.path.join(root, f) for f in files if f.lower().endswith('.slddrw')), None)
                        sldprt = next((os.path.join(root, f) for f in files if f.lower().endswith('.sldprt')), None)
                        ctrl_pdf = next((os.path.join(root, f) for f in files if f.lower().endswith('.pdf') and not f.lower().startswith('backup') and 'original' not in f.lower()), None)
                        orig_pdf = next((os.path.join(root, f) for f in files if 'original' in f.lower() or f.lower().endswith('.pdf')), None)
                        
                        esp_match = re.search(r"Espesor_([0-9.]+)", root)
                        esp = float(esp_match.group(1)) if esp_match else 0.060
                        
                        try:
                            cursor.execute("INSERT OR IGNORE INTO materias_primas (material, espesor_nominal) VALUES (?, ?)", (p['material'], esp))
                            cursor.execute("""
                            INSERT OR IGNORE INTO piezas (
                                numero_pieza, material, acabado_estandar, factor_k, version, revision, nombre_sku,
                                espesor_materia_prima, ancho_materia_prima, largo_materia_prima, ruta_almacenamiento,
                                archivo_dibujo_original, archivo_dxf, archivo_plano_control, archivo_plano_nativo_3d,
                                archivo_dibujo_nativo_2d, archivo_excel_resumen, archivo_step, usuario_registro
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                p['part_no'], p['material'], p['finish'], int(p['k_factor']), p['version'], p['revision'], full_sku,
                                esp, 0.0, 0.0, root,
                                orig_pdf, dxf, ctrl_pdf, slddrw, sldprt, xlsx, step, 'Sistema (Auto-Sync)'
                            ))
                        except Exception:
                            pass
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_database()
