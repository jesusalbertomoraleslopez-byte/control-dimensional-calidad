import os
import sqlite3
import hashlib
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "sigrama_calidad.db")

def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
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
        usuario_registro TEXT NOT NULL,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
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
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_database()
