import streamlit as st
import os
import pandas as pd
import openpyxl
from src.database import get_connection
from src.pdf_generator import generate_first_piece_pdf
from src.nesting_packager import generate_nesting_zip
from src.audit_excel import generate_bulk_audit_excel
from datetime import datetime
import io

def validate_excel_sheets(xlsx_path) -> bool:
    if not xlsx_path or not os.path.exists(xlsx_path):
        return False
    try:
        wb = openpyxl.load_workbook(xlsx_path, read_only=True, keep_links=False)
        sheets = [s.upper() for s in wb.sheetnames]
        wb.close()
        return "CORTE" in sheets and "DOBLEZ" in sheets
    except Exception:
        return False

def validate_step_file(step_path) -> bool:
    if not step_path or not os.path.exists(step_path):
        return False
    try:
        # Read the first 10MB to verify the file and avoid reading massive models into memory
        with open(step_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(1024 * 1024 * 10)
        
        if "ISO-10303-21" not in content:
            return False
        if "DATA;" not in content:
            return False
            
        geometry_keywords = ["ADVANCED_FACE", "MANIFOLD_SOLID_BREP", "FACE_BOUND", "CLOSED_SHELL", "SHELL_BASED_SURFACE_MODEL", "GEOMETRIC_REPRESENTATION"]
        has_geometry = any(kw in content for kw in geometry_keywords)
        return has_geometry
    except Exception:
        return False

def show_design_loader():
    st.title("3.2. Carga de Registros de Diseño e Ingeniería")
    st.subheader("Generación Automática de SKU, Creación de Directorios y Carga de Archivos Requeridos")
    
    # Use tabs for 1. Registro de Diseño, 2. Evidencia de Primera Pieza, 3. Generador de Paquetes (Nesteo), and 4. Importación Masiva
    tab_audit, tab1, tab2, tab3, tab4 = st.tabs([
        "🛡️ 3.2.1. Auditoría y Validación de Planos (Administrador)",
        "📁 3.2.2. Registro de Diseño e Ingeniería", 
        "✔ 3.2.3. Validación de Primera Pieza",
        "📦 3.2.4. Módulo Generador de Paquetes (Nesteo)",
        "⚡ 3.2.5. Importación Masiva"
    ])
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Fetch material thicknesses from database
    cursor.execute("SELECT material, espesor_nominal FROM materias_primas")
    materials_db = cursor.fetchall()
    mat_dict = {r["material"]: r["espesor_nominal"] for r in materials_db}
    material_options = list(mat_dict.keys())
    
    with tab_audit:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#111111 0%,#2A2A2A 100%);
                    border-left:5px solid #EC2024;
                    border-radius:10px;padding:1.2rem 1.5rem;margin-bottom:1.2rem;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
          <div style="color:#fff;font-weight:800;font-size:1.2rem;font-family:'Montserrat';">
            🛡️ Proceso Oficial de Validación y Auditoría de Planos
          </div>
          <div style="color:#D2D3D5;font-size:0.9rem;font-family:'Questrial';margin-top:0.3rem;">
            Verificación técnica de expedientes inyectados desde la red <b>Z:\\02 - INGENIERIA\\BASE DE DATOS PRODUCTOS</b> o cargados al Bucket.
            <b>Regla de Calidad:</b> Las piezas solo serán visibles en el <b>3.1. Visualizador 3D CAD</b> una vez que sean auditadas y aprobadas por el Administrador.
          </div>
        </div>
        """, unsafe_allow_html=True)

        # 1. KPIs de Auditoría en Tiempo Real
        c_kpi1, c_kpi2, c_kpi3 = st.columns(3)
        cursor.execute("SELECT COUNT(*) FROM piezas WHERE estatus_auditoria = 'Sin Auditar' OR estatus_auditoria IS NULL")
        cnt_sin_auditar = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM piezas WHERE estatus_auditoria = 'Auditada'")
        cnt_auditadas = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM piezas")
        cnt_total = cursor.fetchone()[0]

        with c_kpi1:
            st.metric("🔴 Piezas Sin Auditar", cnt_sin_auditar, help="Piezas pendientes de revisión. Bloqueadas para el Visor 3D CAD.")
        with c_kpi2:
            st.metric("🟢 Auditadas y Aprobadas", cnt_auditadas, help="Piezas aprobadas por el Administrador. Disponibles en el Visor 3D CAD.")
        with c_kpi3:
            st.metric("📦 Total de Piezas Registradas", cnt_total, help="Total en el catálogo de ingeniería.")

        cursor.execute("SELECT COUNT(*) FROM piezas WHERE (estatus_auditoria = 'Sin Auditar' OR estatus_auditoria IS NULL) AND documentos_completos = 1")
        cnt_completas_pendientes = cursor.fetchone()[0]

        with st.expander("⚡ Herramientas de Auditoría Masiva (Administrador)", expanded=False):
            st.markdown(f"""
            - **{cnt_completas_pendientes} piezas** cuentan con todos sus documentos técnicos indispensables (Plano PDF, DXF, Modelo 3D STEP y Hoja de Especificaciones).
            - Puede aprobarlas en lote para agilizar la habilitación en piso y en el Visor 3D CAD, o auditarlas individualmente con revisión técnica a continuación.
            """)
            col_b1, col_b2 = st.columns([1, 1])
            with col_b1:
                if st.button(f"🚀 Aprobar en Lote ({cnt_completas_pendientes} Piezas con Documentación Completa)", type="primary", disabled=(cnt_completas_pendientes == 0), key="btn_bulk_approve_complete"):
                    admin_name = st.session_state.get("nombre_completo", "Administrador de Calidad")
                    cursor.execute("""
                        UPDATE piezas SET
                            estatus_auditoria = 'Auditada',
                            fecha_auditoria = CURRENT_TIMESTAMP,
                            auditor_nombre = ?,
                            auditoria_notas = 'Aprobación masiva automática por expediente técnico completo'
                        WHERE (estatus_auditoria = 'Sin Auditar' OR estatus_auditoria IS NULL) AND documentos_completos = 1
                    """, (admin_name,))
                    conn.commit()
                    from src.database import save_database_to_gcs
                    save_database_to_gcs()
                    st.success(f"🎉 Se han auditado y aprobado {cnt_completas_pendientes} piezas con éxito.")
                    import time
                    time.sleep(1)
                    st.rerun()
            with col_b2:
                if st.button("🔄 Restablecer Todo el Catálogo a 'Sin Auditar'", key="btn_bulk_reset_all"):
                    cursor.execute("UPDATE piezas SET estatus_auditoria = 'Sin Auditar', fecha_auditoria = NULL, auditor_nombre = NULL")
                    conn.commit()
                    from src.database import save_database_to_gcs
                    save_database_to_gcs()
                    st.warning("Se restablecieron todas las piezas a 'Sin Auditar'.")
                    import time
                    time.sleep(1)
                    st.rerun()

        st.markdown("---")

        # 2. Filtros de Búsqueda y Selección
        fcol_stat, fcol_search = st.columns([1, 2])
        with fcol_stat:
            status_filter = st.selectbox(
                "Filtrar Catálogo:",
                [f"🔴 Sin Auditar ({cnt_sin_auditar})", f"🟢 Auditadas ({cnt_auditadas})", f"📋 Todas ({cnt_total})"],
                key="audit_status_filter"
            )
        with fcol_search:
            audit_search = st.text_input(
                "🔎 Buscar por Consecutivo ING, No. Pieza o SKU:",
                placeholder="Ej: ING0010 ó 12-A-6199 ó PP21340",
                key="audit_search_input"
            )

        # Construir consulta dinámica
        where_clauses = []
        params = []
        if "🔴 Sin Auditar" in status_filter:
            where_clauses.append("(estatus_auditoria = 'Sin Auditar' OR estatus_auditoria IS NULL)")
        elif "🟢 Auditadas" in status_filter:
            where_clauses.append("estatus_auditoria = 'Auditada'")

        if audit_search.strip():
            where_clauses.append("(consecutivo_ing LIKE ? OR numero_pieza LIKE ? OR nombre_sku LIKE ?)")
            q_like = f"%{audit_search.strip()}%"
            params.extend([q_like, q_like, q_like])

        query = "SELECT * FROM piezas"
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        query += " ORDER BY CASE WHEN consecutivo_ing IS NOT NULL AND consecutivo_ing != '' THEN 0 ELSE 1 END, consecutivo_ing, nombre_sku"

        cursor.execute(query, tuple(params))
        audit_rows = [dict(r) for r in cursor.fetchall()]

        if not audit_rows:
            st.info("ℹ️ No se encontraron piezas que coincidan con los filtros seleccionados.")
        else:
            def audit_label(p):
                ing = p.get("consecutivo_ing") or "S/C"
                status_icon = "🟢" if p.get("estatus_auditoria") == "Auditada" else "🔴"
                return f"{status_icon} [{ing}] {p['nombre_sku']}"

            audit_map = {audit_label(p): p for p in audit_rows}
            selected_audit_label = st.selectbox(
                f"Seleccione la Pieza a Auditar ({len(audit_rows)} mostradas):",
                list(audit_map.keys()),
                key="audit_selected_piece_box"
            )
            p_sel = audit_map[selected_audit_label]

            # Ficha de la pieza
            st.markdown(f"""
            <div style="background:#F8F9FA; border:1px solid #D2D3D5; border-radius:8px; padding:1.2rem; margin:1rem 0;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem;">
                    <span style="font-family:'Montserrat',sans-serif; font-size:1.3rem; font-weight:800; color:#111111;">
                        [{p_sel.get('consecutivo_ing') or 'S/C'}] {p_sel['nombre_sku']}
                    </span>
                    <span style="background:{'#16a34a' if p_sel.get('estatus_auditoria')=='Auditada' else '#dc2626'}; color:#fff; font-weight:bold; padding:4px 14px; border-radius:20px; font-size:0.85rem;">
                        {p_sel.get('estatus_auditoria', 'Sin Auditar')}
                    </span>
                </div>
                <div style="display:flex; flex-wrap:wrap; gap:1.5rem; font-size:0.9rem; color:#4B5563;">
                    <span>📌 <b>No. Pieza:</b> {p_sel['numero_pieza']}</span>
                    <span>🧱 <b>Material:</b> {p_sel['material']}</span>
                    <span>📏 <b>Espesor:</b> {p_sel['espesor_materia_prima']:.4f} in</span>
                    <span>📐 <b>Dimensiones:</b> {p_sel['largo_materia_prima']:.3f} x {p_sel['ancho_materia_prima']:.3f} in</span>
                    <span>🎨 <b>Acabado:</b> {p_sel['acabado_estandar']}</span>
                    <span>🔖 <b>Factor K:</b> {p_sel['factor_k']}</span>
                    <span>📋 <b>Versión:</b> {p_sel['version']}-{p_sel['revision']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Checklist de Documentos Requeridos
            st.markdown("##### 📋 Checklist de Documentación de Ingeniería")
            from src.services.gcs_storage import get_file_bytes, generate_secure_signed_url

            docs = [
                ("Plano de Control SIGRAMA (PDF)", p_sel.get("archivo_plano_control"), "application/pdf"),
                ("Plano Original del Cliente (PDF)", p_sel.get("archivo_dibujo_original"), "application/pdf"),
                ("Archivo de Corte Láser (DXF)", p_sel.get("archivo_dxf"), "application/dxf"),
                ("Modelo 3D de Intercambio (STEP)", p_sel.get("archivo_step"), "application/octet-stream"),
                ("Modelo 3D SolidWorks (SLDPRT)", p_sel.get("archivo_plano_nativo_3d"), "application/octet-stream"),
                ("Dibujo 2D SolidWorks (SLDDRW)", p_sel.get("archivo_dibujo_nativo_2d"), "application/octet-stream"),
                ("Especificaciones de Tolerancias (Excel)", p_sel.get("archivo_excel_resumen"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                ("VoBo / Primera Pieza", p_sel.get("documento_primera_pieza"), "application/pdf"),
            ]

            doc_cols = st.columns(4)
            for idx, (doc_name, doc_path, doc_mime) in enumerate(docs):
                c = doc_cols[idx % 4]
                with c:
                    has_doc = False
                    f_bytes = None
                    if doc_path:
                        f_bytes = get_file_bytes(doc_path)
                        if f_bytes:
                            has_doc = True
                    
                    if has_doc:
                        st.markdown(f"**✅ {doc_name}**")
                        clean_fn = os.path.basename(str(doc_path).replace('\\', '/').split('?')[0])
                        st.download_button(
                            label="📥 Descargar",
                            data=f_bytes,
                            file_name=clean_fn,
                            mime=doc_mime,
                            key=f"btn_dl_audit_{idx}_{p_sel['id']}",
                            use_container_width=True
                        )
                    else:
                        st.markdown(f"**❌ {doc_name}**")
                        st.caption("No registrado")

            st.markdown("---")

            # Vista Previa del Plano de Control
            st.markdown("##### 📄 Vista Previa del Plano de Control")
            preview_pdf_path = p_sel.get("archivo_plano_control") or p_sel.get("archivo_dibujo_original")
            preview_bytes = get_file_bytes(preview_pdf_path) if preview_pdf_path else None

            if preview_bytes:
                import base64
                pdf_b64 = base64.b64encode(preview_bytes).decode("utf-8")
                pdfjs_audit_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                  <meta charset="utf-8">
                  <style>
                    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
                    body {{ background: #525659; overflow-y: auto; height: 420px; }}
                    #pdf-wrapper {{ display: flex; flex-direction: column; align-items: center; padding: 10px; gap: 10px; }}
                    canvas {{ display: block; box-shadow: 0 2px 8px rgba(0,0,0,0.5); max-width: 100%; }}
                    #pdf-loading {{ color: #94a3b8; font-size: 14px; padding: 2rem; text-align: center; }}
                  </style>
                  <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
                </head>
                <body>
                  <div id="pdf-wrapper"><div id="pdf-loading">⏳ Cargando plano de control...</div></div>
                  <script>
                    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
                    const raw = atob("{pdf_b64}");
                    const uint8 = new Uint8Array(raw.length);
                    for (let i = 0; i < raw.length; i++) uint8[i] = raw.charCodeAt(i);
                    pdfjsLib.getDocument({{ data: uint8 }}).promise.then(pdf => {{
                      document.getElementById('pdf-loading').remove();
                      const renderPage = (num) => {{
                        pdf.getPage(num).then(page => {{
                          const vp0 = page.getViewport({{ scale: 1 }});
                          const wrapper = document.getElementById('pdf-wrapper');
                          const scale = (wrapper.clientWidth - 20) / vp0.width;
                          const viewport = page.getViewport({{ scale }});
                          const canvas = document.createElement('canvas');
                          canvas.width = viewport.width; canvas.height = viewport.height;
                          wrapper.appendChild(canvas);
                          page.render({{ canvasContext: canvas.getContext('2d'), viewport }});
                          if (num < pdf.numPages) renderPage(num + 1);
                        }});
                      }};
                      renderPage(1);
                    }});
                  </script>
                </body>
                </html>
                """
                components.html(pdfjs_audit_html, height=440, scrolling=False)
            else:
                st.warning("⚠️ No se encontró el archivo PDF del plano para generar vista previa.")

            st.markdown("---")

            # Formulario de Dictamen del Administrador
            st.markdown("##### ✍️ Dictamen y Aprobación del Administrador")
            audit_notes = st.text_area(
                "Notas u Observaciones de la Auditoría:",
                value=p_sel.get("auditoria_notas") or "",
                placeholder="Indique si el plano cumple tolerancias, especificaciones de corte y doblez, o motivos de rechazo.",
                key=f"notes_audit_{p_sel['id']}"
            )

            col_act1, col_act2, col_act3 = st.columns([2, 1, 1])
            with col_act1:
                btn_approve = st.button(
                    "✅ Auditar y Aprobar Pieza (Habilitar en Visor 3D CAD)",
                    type="primary",
                    use_container_width=True,
                    key=f"btn_approve_audit_{p_sel['id']}"
                )
            with col_act2:
                btn_reject = st.button(
                    "⚠️ Rechazar / Observaciones",
                    use_container_width=True,
                    key=f"btn_reject_audit_{p_sel['id']}"
                )
            with col_act3:
                btn_reset = st.button(
                    "🔄 Marcar 'Sin Auditar'",
                    use_container_width=True,
                    key=f"btn_reset_audit_{p_sel['id']}"
                )

            if btn_approve:
                admin_name = st.session_state.get("nombre_completo", "Administrador de Calidad")
                cursor.execute("""
                    UPDATE piezas SET
                        estatus_auditoria = 'Auditada',
                        fecha_auditoria = CURRENT_TIMESTAMP,
                        auditor_nombre = ?,
                        auditoria_notas = ?
                    WHERE id = ?
                """, (admin_name, audit_notes, p_sel["id"]))
                conn.commit()
                from src.database import save_database_to_gcs
                save_database_to_gcs()
                st.success(f"🎉 ¡Pieza '[{p_sel.get('consecutivo_ing')}] {p_sel['nombre_sku']}' auditada y aprobada con éxito! Ahora está disponible en el 3.1. Visualizador 3D CAD.")
                import time
                time.sleep(1)
                st.rerun()

            elif btn_reject:
                admin_name = st.session_state.get("nombre_completo", "Administrador de Calidad")
                cursor.execute("""
                    UPDATE piezas SET
                        estatus_auditoria = 'Rechazada',
                        fecha_auditoria = CURRENT_TIMESTAMP,
                        auditor_nombre = ?,
                        auditoria_notas = ?
                    WHERE id = ?
                """, (admin_name, audit_notes, p_sel["id"]))
                conn.commit()
                from src.database import save_database_to_gcs
                save_database_to_gcs()
                st.warning(f"⚠️ Pieza '[{p_sel.get('consecutivo_ing')}] {p_sel['nombre_sku']}' marcada como Rechazada con observaciones.")
                import time
                time.sleep(1)
                st.rerun()

            elif btn_reset:
                cursor.execute("""
                    UPDATE piezas SET
                        estatus_auditoria = 'Sin Auditar',
                        fecha_auditoria = NULL,
                        auditor_nombre = NULL
                    WHERE id = ?
                """, (p_sel["id"],))
                conn.commit()
                from src.database import save_database_to_gcs
                save_database_to_gcs()
                st.info(f"Pieza restablecida a 'Sin Auditar'.")
                import time
                time.sleep(1)
                st.rerun()

    with tab1:
        st.markdown("#### Registro de Nueva Pieza")
        
        # Guía Visual de Concatenación del SKU de SIGRAMA
        guide_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sku_guide.png")
        if os.path.exists(guide_path):
            st.image(guide_path, caption="Estructura de Concatenación Oficial y Variables de Diseño de SIGRAMA", use_container_width=True)
        
        
        # Initialize state values if they don't exist
        if "part_number" not in st.session_state:
            st.session_state["part_number"] = "12-A-6004-01"
        if "material" not in st.session_state:
            st.session_state["material"] = "16ga"
        if "finish" not in st.session_state:
            st.session_state["finish"] = "ANSI-61"
        if "factor_k" not in st.session_state:
            st.session_state["factor_k"] = 48
        if "version" not in st.session_state:
            st.session_state["version"] = "V3"
        if "revision" not in st.session_state:
            st.session_state["revision"] = "R0"
        if "component_name" not in st.session_state:
            st.session_state["component_name"] = "END_FILLER"
            
        # Form Inputs
        col1, col2 = st.columns(2)
        with col1:
            part_no = st.text_input("Número de Pieza (D)", value=st.session_state["part_number"])
            comp_name = st.text_input("Nombre de la Pieza / Componente (Ej: END_FILLER)", value=st.session_state["component_name"])
            material = st.selectbox("Material (G)", material_options, index=material_options.index(st.session_state["material"]) if st.session_state["material"] in material_options else 0)
            finish = st.text_input("Acabado / Estándar (H)", value=st.session_state["finish"])
        with col2:
            factor_k = st.number_input("Factor K (O) - Entero", value=int(st.session_state["factor_k"]), min_value=0, max_value=100)
            version = st.selectbox("Versión (E)", ["V0", "V1", "V2", "V3", "V4", "V5"], index=["V0", "V1", "V2", "V3", "V4", "V5"].index(st.session_state["version"]))
            revision = st.selectbox("Revisión (M)", ["R0", "R1", "R2", "R3"], index=["R0", "R1", "R2", "R3"].index(st.session_state["revision"]))
            
        # Update Session State
        st.session_state["part_number"] = part_no
        st.session_state["component_name"] = comp_name
        st.session_state["material"] = material
        st.session_state["finish"] = finish
        st.session_state["factor_k"] = factor_k
        st.session_state["version"] = version
        st.session_state["revision"] = revision
        
        # Real-time SKU Concatenation Lógica
        # Formula: {Número de Pieza}-({Material} {Acabado/Estándar}) - K{Factor K} - {Versión}-{Revisión}
        sku_generated = f"{part_no}-({material} {finish}) - K{factor_k} - {version}-{revision}"
        st.session_state["nombre_sku"] = sku_generated
        
        # Display SKU (3 veces más grande con estilos premium)
        st.markdown(
            f'<div style="background-color: #e0f2fe; border-left: 6px solid #0284c7; padding: 1.5rem; '
            f'border-radius: 8px; margin-bottom: 1.5rem; box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);">'
            f'<span style="color: #0369a1; font-weight: bold; font-size: 1.1rem; text-transform: uppercase; '
            f'letter-spacing: 0.5px;">Nombre SKU Generado:</span><br/>'
            f'<span style="color: #0c4a6e; font-weight: 800; font-size: 2.2rem; font-family: monospace; '
            f'word-break: break-all; line-height: 1.2;">{sku_generated}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        
        # Download template layout for Engineering
        st.markdown("##### 📥 Plantilla Excel de Resumen de Dimensiones")
        st.markdown("Descargue la plantilla de Excel oficial para rellenar con las especificaciones de diseño (tolerancias y nominales):")
        
        def generate_eng_excel_template():
            corte_cols = {
                "No.": [1, 2, 3],
                "RESP": ["LASER", "LASER", "LASER"],
                "DIM": [19.000, 3.527, 0.312],
                "LIM.I": [18.985, 3.512, 0.297],
                "LIM.S": [19.015, 3.542, 0.327]
            }
            doblez_cols = {
                "MEDIDA": ["A", "B", "C", "D", "E"],
                "DIMENSION": [0.630, 1.250, 1.880, 0.380, 18.630],
                "LIM.I": [0.615, 1.235, 1.865, 0.365, 18.615],
                "LIM.S": [0.645, 1.265, 1.895, 0.395, 18.645]
            }
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                pd.DataFrame(corte_cols).to_excel(writer, sheet_name="CORTE", index=False)
                pd.DataFrame(doblez_cols).to_excel(writer, sheet_name="DOBLEZ", index=False)
            return buffer.getvalue()
            
        eng_template_bytes = generate_eng_excel_template()
        st.download_button(
            label="📥 Descargar Plantilla Excel de Diseño (Especificaciones)",
            data=eng_template_bytes,
            file_name="Plantilla_Diseno_Dimensiones.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="btn_download_eng_template_blue"
        )
        st.markdown("---")
        
        # File Uploaders
        st.markdown("##### 📁 Archivos de Diseño Requeridos (Obligatorios)")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            file_pdf_orig = st.file_uploader("1. Dibujo Original Cliente (.PDF)", type=["pdf"], key="file_pdf_orig")
            file_dxf = st.file_uploader("2. Desplegado DXF (.DXF)", type=["dxf"], key="file_dxf")
            file_control_pdf = st.file_uploader("3. Plano de Control PDF (.PDF)", type=["pdf"], key="file_control_pdf")
        with f_col2:
            file_slddrw = st.file_uploader("4. Plano Nativo diseño 3D (.SLDDRW)", type=["slddrw"], key="file_slddrw")
            file_sldprt = st.file_uploader("5. Dibujo Nativo diseño 2D (.SLDPRT)", type=["sldprt"], key="file_sldprt")
            file_xlsx = st.file_uploader("6. Excel con resumen de Dimensiones (.XLSX)", type=["xlsx"], key="file_xlsx")
            file_step = st.file_uploader("7. Archivo STEP para Visor 3D (.STEP, .STP) - Opcional", type=["step", "stp"], key="file_step")
            
        # Programmatic material dimensions defaults
        mat_espesor = float(mat_dict.get(material, 0.060))
        mat_ancho = 0.0
        mat_largo = 0.0
        
        if file_xlsx is not None:
            try:
                df_c = pd.read_excel(file_xlsx, sheet_name="CORTE")
                df_c.columns = [c.strip().upper() for c in df_c.columns]
                if "DIM" in df_c.columns and len(df_c) >= 2:
                    mat_largo = float(df_c["DIM"].iloc[0])
                    mat_ancho = float(df_c["DIM"].iloc[1])
            except Exception:
                pass
            
        # Register Action button (Blue)
        if st.button("💾 Guardar Registro y Crear Carpetas", key="btn_save_design_blue"):
            # Validations
            if not part_no:
                st.error("Error: El campo 'Número de Pieza' no puede estar vacío.")
            elif not comp_name:
                st.error("Error: El campo 'Nombre de Pieza / Componente' no puede estar vacío.")
            elif not (file_pdf_orig and file_dxf and file_control_pdf and file_slddrw and file_sldprt and file_xlsx):
                st.error("Error: Debe cargar obligatoriamente los 6 archivos de diseño requeridos (.PDF original, .DXF desplegado, .PDF plano de control, .SLDDRW nativo 3D, .SLDPRT nativo 2D, .XLSX de dimensiones).")
            else:
                # 1. Define folder path
                # Path: /Proyectos/[Nombre_Pieza]/Rev_[Revision]/FactorK_[Valor_K]/Espesor_[Valor_Espesor]/
                # We save inside our scratch workspace path for persistence
                project_base = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Proyectos")
                dest_dir = os.path.join(
                    project_base,
                    comp_name,
                    f"Rev_{revision}",
                    f"FactorK_{factor_k}",
                    f"Espesor_{mat_espesor:.3f}"
                )
                
                os.makedirs(dest_dir, exist_ok=True)
                
                # 2. Save files physically in the created directories
                saved_paths = {}
                uploaded_files = {
                    "pdf_orig": (file_pdf_orig, f"{comp_name}_Original.pdf"),
                    "dxf": (file_dxf, f"{sku_generated}.dxf"),
                    "control_pdf": (file_control_pdf, f"{sku_generated}.pdf"),
                    "slddrw": (file_slddrw, f"{sku_generated}.slddrw"),
                    "sldprt": (file_sldprt, f"{sku_generated}.sldprt"),
                    "xlsx": (file_xlsx, f"{sku_generated}.xlsx"),
                    "step": (file_step, f"{sku_generated}.step") if file_step else (None, "")
                }
                
                from src.services.gcs_storage import is_gcs_available, upload_file_to_gcs
                gcs_ready = is_gcs_available()

                for file_key, (file_obj, filename) in uploaded_files.items():
                    if file_obj is not None:
                        file_path = os.path.join(dest_dir, filename)
                        with open(file_path, "wb") as f:
                            f.write(file_obj.getbuffer())
                        if gcs_ready:
                            rel_blob = f"Proyectos/{part_no}/Rev_{revision}/FactorK_{factor_k}/Espesor_{mat_espesor:.3f}/{filename}"
                            ok_gcs, gcs_uri = upload_file_to_gcs(file_path, rel_blob)
                            saved_paths[file_key] = gcs_uri if ok_gcs else file_path
                        else:
                            saved_paths[file_key] = file_path
                        
                # 3. Save details to SQLite Database
                try:
                    cursor.execute(
                        """
                        INSERT INTO piezas (
                            numero_pieza, material, acabado_estandar, factor_k, version, revision, nombre_sku,
                            espesor_materia_prima, ancho_materia_prima, largo_materia_prima, ruta_almacenamiento,
                            archivo_dibujo_original, archivo_dxf, archivo_plano_control, archivo_plano_nativo_3d,
                            archivo_dibujo_nativo_2d, archivo_excel_resumen, archivo_step, usuario_registro
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            part_no, material, finish, factor_k, version, revision, sku_generated,
                            mat_espesor, mat_ancho, mat_largo, dest_dir,
                            saved_paths.get("pdf_orig"), saved_paths.get("dxf"), saved_paths.get("control_pdf"),
                            saved_paths.get("slddrw"), saved_paths.get("sldprt"), saved_paths.get("xlsx"),
                            saved_paths.get("step"), st.session_state["nombre_completo"]
                        )
                    )
                    conn.commit()
                    
                    # 4. Automatic Backup Report (PDF of movement/registration)
                    cursor.execute("SELECT id FROM piezas WHERE nombre_sku = ?", (sku_generated,))
                    p_id = cursor.fetchone()[0]
                    
                    # Fetch stored piece details to generate backup
                    piece_record = {
                        "id": p_id,
                        "numero_pieza": part_no,
                        "material": material,
                        "acabado_estandar": finish,
                        "factor_k": factor_k,
                        "version": version,
                        "revision": revision,
                        "nombre_sku": sku_generated,
                        "espesor_materia_prima": mat_espesor,
                        "ancho_materia_prima": mat_ancho,
                        "largo_materia_prima": mat_largo,
                        "ruta_almacenamiento": dest_dir,
                        "archivo_dibujo_original": saved_paths.get("pdf_orig"),
                        "archivo_dxf": saved_paths.get("dxf"),
                        "archivo_plano_control": saved_paths.get("control_pdf"),
                        "archivo_plano_nativo_3d": saved_paths.get("slddrw"),
                        "archivo_dibujo_nativo_2d": saved_paths.get("sldprt"),
                        "archivo_excel_resumen": saved_paths.get("xlsx"),
                        "archivo_step": saved_paths.get("step"),
                        "usuario_registro": st.session_state["nombre_completo"]
                    }
                    
                    backup_pdf_bytes = generate_first_piece_pdf(piece_record)
                    backup_pdf_path = os.path.join(dest_dir, f"Backup_Registro_{sku_generated}.pdf")
                    with open(backup_pdf_path, "wb") as f:
                        f.write(backup_pdf_bytes)
                        
                    st.success(f"✅ ¡Registro de Pieza '{sku_generated}' creado con éxito!")
                    st.info(f"📂 Carpetas creadas físicamente en: `{dest_dir}`")
                    st.info(f"📄 Respaldo del movimiento generado en PDF: `Backup_Registro_{sku_generated}.pdf`")
                    
                    # Download backup right away
                    st.download_button(
                        label="📥 Descargar Respaldo de Registro (PDF)",
                        data=backup_pdf_bytes,
                        file_name=f"Respaldo_Registro_{sku_generated}.pdf",
                        mime="application/pdf",
                        key="btn_download_backup_reg_pdf"
                    )
                except Exception as ex:
                    err_msg = str(ex)
                    if "UNIQUE constraint failed" in err_msg and "nombre_sku" in err_msg:
                        st.error(
                            f"⚠️ **Error de Registro:** El SKU `{sku_generated}` ya se encuentra registrado "
                            f"en el sistema. No se pueden duplicar piezas con el mismo número, versión y revisión.\n\n"
                            f"Si necesita subir nuevos archivos para esta pieza, por favor pida al Administrador de Calidad "
                            f"eliminar el registro previo en la sección **8. Área de Mantenimiento** e inténtelo nuevamente."
                        )
                    else:
                        st.error(f"Error al guardar el registro en la Base de Datos: {err_msg}")
                    
    with tab2:
        st.markdown("#### Validación y Liberación de Primera Pieza")
        st.markdown("""
            Para habilitar una pieza en las estaciones de producción, es obligatorio subir la evidencia escaneada del **Plano Validado Impreso**
            y contrastar las cotas dimensionales de la primera pieza calibrada contra el Excel de diseño.
        """)
        
        # Select registered piece to validate
        cursor.execute("SELECT id, nombre_sku, ruta_almacenamiento, plano_validado_impreso, documento_primera_pieza FROM piezas")
        registered_pieces = cursor.fetchall()
        
        if not registered_pieces:
            st.warning("No hay piezas registradas en el sistema. Registre una pieza en la primera pestaña antes de validar.")
        else:
            piece_options = {r["nombre_sku"]: r for r in registered_pieces}
            selected_piece_sku = st.selectbox("Seleccione la Pieza a Validar:", list(piece_options.keys()))
            sku = selected_piece_sku
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; justify-content: space-between; 
                            background-color: #F8F9FA; border: 1px solid #D2D3D5; border-radius: 6px; 
                            padding: 0.5rem 1rem; margin-bottom: 0.8rem; font-family: 'Questrial', sans-serif;">
                    <span style="font-family: 'Montserrat', sans-serif; font-weight: bold; font-size: 1.1rem; color: #111111;">
                        {sku}
                    </span>
                    <button onclick="navigator.clipboard.writeText('{sku}').then(() => {{
                        const btn = document.getElementById('copy-btn-design');
                        btn.innerHTML = '✅ Copiado!';
                        btn.style.backgroundColor = '#16a34a';
                        setTimeout(() => {{
                            btn.innerHTML = '📋 Copiar SKU';
                            btn.style.backgroundColor = '#EC2024';
                        }}, 2000);
                    }})" id="copy-btn-design" style="
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
            piece_sel = piece_options[selected_piece_sku]
            
            st.markdown(f"**Estatus de Validación Actual:** " + 
                        ("🟢 LIBERADA" if piece_sel["documento_primera_pieza"] else "🔴 PENDIENTE DE VALIDACIÓN"))
            
            # Show download options if already validated/liberated
            if piece_sel["documento_primera_pieza"] or piece_sel["plano_validado_impreso"]:
                st.markdown("##### 📥 Documentos de Validación Existentes:")
                from src.services.gcs_storage import get_file_bytes, generate_secure_signed_url
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    path_vobo = piece_sel["documento_primera_pieza"]
                    vobo_bytes = get_file_bytes(path_vobo) if path_vobo else None
                    if vobo_bytes:
                        clean_vobo_name = os.path.basename(str(path_vobo).replace("\\", "/").split("?")[0])
                        st.download_button(
                            label="📥 Descargar PDF VoBo Subido",
                            data=vobo_bytes,
                            file_name=clean_vobo_name,
                            mime="application/pdf",
                            key="btn_dl_existing_vobo_blue",
                            use_container_width=True
                        )
                with col_dl2:
                    path_plano = piece_sel["plano_validado_impreso"]
                    plano_bytes = get_file_bytes(path_plano) if path_plano else None
                    if plano_bytes:
                        clean_plano_name = os.path.basename(str(path_plano).replace("\\", "/").split("?")[0])
                        st.download_button(
                            label="📥 Descargar Plano Validado Impreso",
                            data=plano_bytes,
                            file_name=clean_plano_name,
                            mime="application/pdf",
                            key="btn_dl_existing_plano_blue",
                            use_container_width=True
                        )
                st.markdown("---")
            
            st.markdown("##### Cargar o Actualizar Documentos de Validación:")
            # Form to upload validation proof
            with st.form("validation_form"):
                file_plano_val = st.file_uploader("1. Cargar Plano Validado Impreso (Escaneado en PDF)", type=["pdf"])
                file_vobo_val = st.file_uploader("2. Cargar PDF de Primera Pieza VoBo (Visto Bueno)", type=["pdf"])
                accept_verification = st.checkbox("Confirmo que las medidas físicas de la primera pieza coinciden dentro de tolerancias con el Excel de Dimensiones.")
                
                btn_validate = st.form_submit_button("Liberar Componente y Registrar Evidencias", key="btn_validate_piece_blue")
                
                if btn_validate:
                    if not file_plano_val:
                        st.error("Error: Debe subir el plano validado en PDF para autorizar la liberación.")
                    elif not file_vobo_val:
                        st.error("Error: Debe subir el PDF de primera pieza VoBo para autorizar la liberación.")
                    elif not accept_verification:
                        st.error("Error: Debe confirmar la validación dimensional visual del reporte contra el físico.")
                    else:
                        storage_path = piece_sel["ruta_almacenamiento"]
                        val_filename = f"Plano_Validado_{piece_sel['nombre_sku']}.pdf"
                        vobo_filename = f"VoBo_Primera_Pieza_{piece_sel['nombre_sku']}.pdf"
                        
                        file_plano_val.seek(0)
                        val_bytes = file_plano_val.read()
                        file_vobo_val.seek(0)
                        vobo_bytes = file_vobo_val.read()

                        from src.services.gcs_storage import is_gcs_available, upload_file_to_gcs, normalize_blob_name
                        val_db_path = None
                        vobo_db_path = None
                        
                        if is_gcs_available():
                            blob_base = normalize_blob_name(storage_path)
                            ok1, uri1 = upload_file_to_gcs(val_bytes, f"{blob_base}/{val_filename}")
                            if ok1: val_db_path = uri1
                            ok2, uri2 = upload_file_to_gcs(vobo_bytes, f"{blob_base}/{vobo_filename}")
                            if ok2: vobo_db_path = uri2
                            
                        # Respaldo local si no se conectó a GCS
                        if not val_db_path or not vobo_db_path:
                            local_dest = storage_path if not str(storage_path).startswith("gs://") else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Proyectos", piece_sel["nombre_sku"])
                            os.makedirs(local_dest, exist_ok=True)
                            val_local = os.path.join(local_dest, val_filename)
                            with open(val_local, "wb") as f:
                                f.write(val_bytes)
                            vobo_local = os.path.join(local_dest, vobo_filename)
                            with open(vobo_local, "wb") as f:
                                f.write(vobo_bytes)
                            if not val_db_path: val_db_path = val_local
                            if not vobo_db_path: vobo_db_path = vobo_local

                        # 3. Update Database
                        cursor.execute(
                            "UPDATE piezas SET plano_validado_impreso = ?, documento_primera_pieza = ? WHERE id = ?",
                            (val_db_path, vobo_db_path, piece_sel["id"])
                        )
                        conn.commit()
                        
                        st.success(f"✅ ¡Componente '{selected_piece_sku}' liberado con éxito en producción!")
                        st.rerun()
                        
    with tab3:
        st.markdown("#### Generador de Paquetes ZIP para Nesteo (ProNest)")
        st.markdown("""
            Suba un archivo Excel que contenga la lista de cantidades requeridas. El sistema agrupará automáticamente
            los archivos DXF de corte en subcarpetas por material, renombrará cada DXF con su prefijo de ítem de nido y cantidad al final,
            y empacará todo en un archivo comprimido listo para su carga en **ProNest**.
        """)
        
        # Download template layout
        st.markdown("📥 **Plantilla del Excel de Nesteo requerida:**")
        
        # Create sample excel bytes
        template_df = pd.DataFrame([
            {"ITEM": 1, "SKU": "12-A-6004-01-(16ga ANSI-61) - K48 - V3-R0", "CANTIDAD": 25},
            {"ITEM": 2, "SKU": "12-A-6004-01-(16ga ANSI-61) - K48 - V3-R0", "CANTIDAD": 12}
        ])
        template_buffer = io.BytesIO()
        template_df.to_excel(template_buffer, index=False)
        st.download_button(
            label="📥 Descargar Plantilla Excel de Nesteo",
            data=template_buffer.getvalue(),
            file_name="Plantilla_Lista_Nesteo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="btn_download_nesting_template_blue"
        )
        
        st.markdown("---")
        
        nesting_excel = st.file_uploader("Cargar Lista de Nesteo en Excel (.XLSX)", type=["xlsx"])
        
        if nesting_excel:
            st.success("Lista cargada. Presione el botón de abajo para generar el paquete.")
            
            if st.button("📦 Procesar y Generar ZIP de Nesteo", key="btn_generate_nesting_zip_blue"):
                zip_bytes, logs = generate_nesting_zip(nesting_excel.read())
                
                if zip_bytes:
                    st.success("✅ ¡Paquete ZIP de Nesteo generado con éxito!")
                    st.download_button(
                        label="📥 Descargar Paquete ZIP de DXFs para ProNest",
                        data=zip_bytes,
                        file_name=f"Paquete_Nesteo_SIGRAMA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip",
                        key="btn_download_nesting_zip_blue"
                    )
                else:
                    st.error("Error al procesar el paquete ZIP. Revise los detalles abajo.")
                    
                # Show logs/detail
                with st.expander("📝 Bitácora de Procesamiento de Nesteo"):
                    for log in logs:
                        st.text(log)
                        
    with tab4:
        st.markdown("#### Importación Masiva de Piezas e Ingeniería")
        st.markdown("""
            Indique la ruta de la carpeta de red o local donde Ingeniería prepara los archivos de las piezas.
            El sistema analizará las subcarpetas, validará los archivos requeridos y le permitirá seleccionar cuáles importar de forma masiva.
        """)
        
        import_method = st.radio(
            "Método de Carga:",
            ["Escanear Carpeta Local/Red (Requiere ejecutar en Localhost)", "Cargar Archivo Comprimido (.ZIP / .RAR)"],
            horizontal=True,
            key="import_method_radio"
        )
        
        default_official_path = "Z:\\02 - INGENIERIA\\BASE DE DATOS PRODUCTOS"
        if "bulk_import_path" not in st.session_state:
            st.session_state["bulk_import_path"] = default_official_path if os.path.exists(default_official_path) else ""
            
        import_path = ""
        zip_file = None
        
        if import_method == "Escanear Carpeta Local/Red (Requiere ejecutar en Localhost)":
            if not os.path.exists("Z:\\") and os.name != "nt":
                st.info("☁️ **Estás navegando en la versión en la Nube (Streamlit Cloud):** Los servidores remotos no pueden acceder directamente a la unidad física `Z:\\` de tu red local. Para importar nuevos diseños desde la nube, utiliza la opción **'Cargar Archivo Comprimido (.ZIP / .RAR)'** o ejecuta la aplicación desde tu computadora local / Concentradora.")

            col_in, col_browse, col_def = st.columns([3.2, 1.2, 1.2])
            with col_in:
                import_path = st.text_input(
                    "Ruta de la Carpeta de Ingeniería:", 
                    value=st.session_state.get("bulk_import_path", default_official_path if os.path.exists(default_official_path) else ""),
                    placeholder="Ej: Z:\\02 - INGENIERIA\\BASE DE DATOS PRODUCTOS",
                    key="txt_bulk_import_path"
                )
                st.session_state["bulk_import_path"] = import_path
                if import_path:
                    import_path = import_path.strip().strip('"').strip("'")
            with col_browse:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                btn_browse = st.button("📁 Examinar...", help="Abre una ventana para buscar y seleccionar la carpeta desde tu computadora", key="btn_browse_folder")
                if btn_browse:
                    try:
                        import tkinter as tk
                        from tkinter import filedialog
                        root = tk.Tk()
                        root.withdraw()
                        root.wm_attributes('-topmost', 1)
                        curr_dir = import_path if (import_path and os.path.exists(import_path)) else ("Z:\\" if os.path.exists("Z:\\") else None)
                        selected_dir = filedialog.askdirectory(title="Seleccionar Carpeta de Base de Datos de Ingeniería SIGRAMA", initialdir=curr_dir)
                        root.destroy()
                        if selected_dir:
                            st.session_state["bulk_import_path"] = os.path.normpath(selected_dir)
                            st.rerun()
                    except Exception as e:
                        st.warning(f"No se pudo abrir el explorador de carpetas en este entorno ({str(e)}). Ingrese la ruta manualmente o use la versión local.")
            with col_def:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                if st.button("⚡ Ruta Z:\\ Oficial", help="Cargar automáticamente la ruta oficial de Ingeniería SIGRAMA", key="btn_official_z_path"):
                    st.session_state["bulk_import_path"] = default_official_path
                    st.rerun()
        else:
            zip_file = st.file_uploader("Cargar Archivo Comprimido (.ZIP o .RAR) con Estructura de Ingeniería", type=["zip", "rar"])
        
        # We use session state to persist scan results between data editor interactions
        if "bulk_scan_results" not in st.session_state:
            st.session_state["bulk_scan_results"] = None
        if "last_scanned_path" not in st.session_state:
            st.session_state["last_scanned_path"] = ""
            
        col_scan1, col_scan2 = st.columns([1, 4])
        with col_scan1:
            btn_scan = st.button("🔍 Escanear Carpeta", key="btn_import_scan_red")
            
        run_scan = False
        if btn_scan:
            if import_method == "Escanear Carpeta Local/Red (Requiere ejecutar en Localhost)":
                if not import_path:
                    st.error("Error: Debe ingresar una ruta de carpeta válida.")
                elif not os.path.exists(import_path):
                    st.error(f"❌ La ruta especificada no existe o no es accesible: '{import_path}'")
                else:
                    st.session_state["bulk_scan_results"] = None
                    st.session_state["last_scanned_path"] = import_path
                    run_scan = True
            else:
                if zip_file is None:
                    st.error("Error: Debe cargar un archivo ZIP o RAR válido.")
                else:
                    import zipfile
                    import shutil
                    import subprocess
                    
                    temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "temp_bulk_import")
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    try:
                        archive_name = getattr(zip_file, "name", "archivo_comprimido.rar")
                        raw_archive_path = os.path.join(temp_dir, archive_name)
                        
                        # Guardar archivo en disco físico por bloques para evitar desbordes de memoria y errores de buffer en rarfile
                        zip_file.seek(0)
                        with open(raw_archive_path, "wb") as f_out:
                            while True:
                                chunk = zip_file.read(1024 * 1024 * 8)
                                if not chunk:
                                    break
                                f_out.write(chunk)
                                
                        file_name_lower = archive_name.lower()
                        extracted = False
                        err_details = []
                        
                        # 1. Intentar descompresión ZIP si termina en .zip
                        if file_name_lower.endswith(".zip"):
                            try:
                                with zipfile.ZipFile(raw_archive_path) as z:
                                    z.extractall(temp_dir)
                                extracted = True
                            except Exception as e_zip:
                                err_details.append(f"ZipFile: {e_zip}")
                                
                        # 2. Descompresión RAR y multiformato
                        if not extracted:
                            # 2.1 unar CLI (Linux Streamlit Cloud o si existe en PATH)
                            unar_bin = shutil.which("unar")
                            if unar_bin:
                                try:
                                    res_unar = subprocess.run([unar_bin, "-o", temp_dir, "-f", raw_archive_path], capture_output=True, text=True)
                                    if res_unar.returncode == 0:
                                        extracted = True
                                    else:
                                        err_details.append(f"unar CLI: {res_unar.stderr.strip() or res_unar.stdout.strip()}")
                                except Exception as e_u:
                                    err_details.append(f"unar error: {e_u}")
                                    
                            # 2.2 UnRAR.exe / WinRAR.exe (Windows)
                            if not extracted:
                                winrar_candidates = [
                                    shutil.which("UnRAR"),
                                    shutil.which("unrar"),
                                    r"C:\Program Files\WinRAR\UnRAR.exe",
                                    r"C:\Program Files (x86)\WinRAR\UnRAR.exe",
                                    r"C:\Program Files\WinRAR\WinRAR.exe",
                                    r"C:\Program Files (x86)\WinRAR\WinRAR.exe",
                                ]
                                for candidate in winrar_candidates:
                                    if candidate and os.path.exists(candidate):
                                        try:
                                            dest_arg = temp_dir.rstrip(os.sep) + os.sep
                                            res_unrar = subprocess.run([candidate, "x", "-y", "-o+", raw_archive_path, dest_arg], capture_output=True, text=True)
                                            if res_unrar.returncode == 0:
                                                extracted = True
                                                break
                                            else:
                                                err_details.append(f"WinRAR: {res_unrar.stderr.strip() or res_unrar.stdout.strip()}")
                                        except Exception as e_w:
                                            err_details.append(f"WinRAR error: {e_w}")
                                            
                            # 2.3 7-Zip CLI (si existe)
                            if not extracted:
                                sz_candidates = [
                                    shutil.which("7z"),
                                    shutil.which("7za"),
                                    r"C:\Program Files\7-Zip\7z.exe",
                                    r"C:\Program Files (x86)\7-Zip\7z.exe",
                                ]
                                for sz in sz_candidates:
                                    if sz and os.path.exists(sz):
                                        try:
                                            res_sz = subprocess.run([sz, "x", "-y", f"-o{temp_dir}", raw_archive_path], capture_output=True, text=True)
                                            if res_sz.returncode == 0:
                                                extracted = True
                                                break
                                        except Exception as e_7:
                                            err_details.append(f"7z error: {e_7}")

                            # 2.4 Biblioteca Python rarfile
                            if not extracted:
                                try:
                                    import rarfile
                                    for tool_cand in [
                                        r"C:\Program Files\WinRAR\UnRAR.exe",
                                        r"C:\Program Files (x86)\WinRAR\UnRAR.exe",
                                        shutil.which("unar"),
                                        shutil.which("unrar")
                                    ]:
                                        if tool_cand and os.path.exists(tool_cand):
                                            rarfile.UNRAR_TOOL = tool_cand
                                            break
                                    with rarfile.RarFile(raw_archive_path) as rf:
                                        rf.extractall(temp_dir)
                                    extracted = True
                                except Exception as e_rf:
                                    err_details.append(f"rarfile: {e_rf}")

                            # 2.5 Fallback por si era archivo ZIP con otra extensión
                            if not extracted:
                                try:
                                    with zipfile.ZipFile(raw_archive_path) as z:
                                        z.extractall(temp_dir)
                                    extracted = True
                                except Exception:
                                    pass

                        # Eliminar el archivo contenedor temporal del directorio
                        try:
                            if os.path.exists(raw_archive_path):
                                os.remove(raw_archive_path)
                        except Exception:
                            pass
                            
                        if not extracted:
                            msg_det = " | ".join(err_details) if err_details else "Verifique que el archivo no esté dañado ni protegido por contraseña."
                            raise Exception(f"No se pudo descomprimir el archivo '{archive_name}'. Detalle: {msg_det}")

                        # Localizar la carpeta que contiene las subcarpetas ING...
                        scan_root = temp_dir
                        import re
                        for _ in range(6):
                            dir_items = [c for c in os.listdir(scan_root) if os.path.isdir(os.path.join(scan_root, c)) and not c.startswith(".")]
                            has_ing = any(re.match(r"ING\d+", c, re.IGNORECASE) for c in dir_items)
                            if has_ing:
                                break
                            if len(dir_items) == 1:
                                scan_root = os.path.join(scan_root, dir_items[0])
                            else:
                                break
                                
                        import_path = scan_root
                        st.session_state["bulk_scan_results"] = None
                        st.session_state["last_scanned_path"] = import_path
                        run_scan = True
                    except Exception as e:
                        st.error(f"❌ Error al descomprimir el archivo: {str(e)}")
                        run_scan = False
                        
        if run_scan:
            with st.spinner("Escaneando subcarpetas de Ingeniería..."):
                    import re
                    
                    def parse_folder_name(folder_name):
                        pattern = r"ING\d+\s*-\s*(?P<part_no>.+?)-\((?P<material>[a-zA-Z0-9]+)\s+(?P<finish>.+?)\)\s*-\s*K(?P<k_factor>\d+)\s*-\s*(?P<version>V\d+)-(?P<revision>R\d+)"
                        match = re.match(pattern, folder_name.strip())
                        if match:
                            return match.groupdict()
                        return None
                        
                    def scan_files_in_folder(folder_path):
                        if not os.path.isdir(folder_path):
                            return None
                        files = os.listdir(folder_path)
                        classified = {
                            "pdf_orig": None, "dxf": None, "control_pdf": None,
                            "slddrw": None, "sldprt": None, "xlsx": None, "step": None,
                            "plano_validado": None, "vobo_pdf": None
                        }
                        pdf_files = []
                        for f in files:
                            f_lower = f.lower()
                            full_p = os.path.join(folder_path, f)
                            if not os.path.isfile(full_p) or f.startswith("."):
                                continue
                            if f_lower.endswith(".dxf"):
                                classified["dxf"] = full_p
                            elif f_lower.endswith(".slddrw"):
                                classified["slddrw"] = full_p
                            elif f_lower.endswith(".sldprt"):
                                classified["sldprt"] = full_p
                            elif f_lower.endswith(".xlsx"):
                                if not f.startswith("~$"):
                                    classified["xlsx"] = full_p
                            elif f_lower.endswith(".step") or f_lower.endswith(".stp"):
                                classified["step"] = full_p
                            elif f_lower.endswith(".pdf"):
                                if "validado" in f_lower:
                                    classified["plano_validado"] = full_p
                                elif "vobo" in f_lower or "primera" in f_lower:
                                    classified["vobo_pdf"] = full_p
                                else:
                                    pdf_files.append(full_p)
                                    
                        if len(pdf_files) == 1:
                            classified["pdf_orig"] = pdf_files[0]
                            classified["control_pdf"] = pdf_files[0]
                        elif len(pdf_files) >= 2:
                            orig_pdf, ctrl_pdf = None, None
                            for pdf in pdf_files:
                                pdf_name = os.path.basename(pdf).lower()
                                if any(x in pdf_name for x in ["original", "orig", "cliente", "dibujo"]):
                                    orig_pdf = pdf
                                elif any(x in pdf_name for x in ["control", "plano"]):
                                    ctrl_pdf = pdf
                            if not orig_pdf and not ctrl_pdf:
                                pdf_files.sort()
                                orig_pdf = pdf_files[0]
                                ctrl_pdf = pdf_files[1]
                            elif orig_pdf and not ctrl_pdf:
                                remaining = [p for p in pdf_files if p != orig_pdf]
                                ctrl_pdf = remaining[0]
                            elif ctrl_pdf and not orig_pdf:
                                remaining = [p for p in pdf_files if p != ctrl_pdf]
                                orig_pdf = remaining[0]
                            classified["pdf_orig"] = orig_pdf
                            classified["control_pdf"] = ctrl_pdf
                            
                        return classified
                        
                    scanned_rows = []
                    try:
                        subdirs = sorted(os.listdir(import_path))
                    except Exception as e:
                        st.error(f"❌ Error al listar directorio: {str(e)}")
                        subdirs = []
                        
                    for sdir in subdirs:
                        full_subdir_path = os.path.join(import_path, sdir)
                        if not os.path.isdir(full_subdir_path):
                            continue
                        parsed = parse_folder_name(sdir)
                        if not parsed:
                            continue
                        classified = scan_files_in_folder(full_subdir_path)
                        if not classified:
                            continue
                            
                        mandatory_keys = ["pdf_orig", "dxf", "control_pdf", "slddrw", "sldprt", "xlsx"]
                        present_count = sum(1 for k in mandatory_keys if classified[k] is not None)
                        
                        xlsx_valid = False
                        if classified["xlsx"]:
                            xlsx_valid = validate_excel_sheets(classified["xlsx"])
                            
                        step_valid = False
                        if classified["step"]:
                            step_valid = validate_step_file(classified["step"])
                            
                        sku = f"{parsed['part_no']}-({parsed['material']} {parsed['finish']}) - K{parsed['k_factor']} - {parsed['version']}-{parsed['revision']}"
                        
                        errors_list = []
                        if present_count < 6 or not classified["step"]:
                            missing_list = []
                            for k in mandatory_keys:
                                if not classified[k]:
                                    missing_list.append(k.upper())
                            if not classified["step"]:
                                missing_list.append("STEP")
                            errors_list.append(f"Incompleto (Falta: {', '.join(missing_list)})")
                        
                        if classified["xlsx"] and not xlsx_valid:
                            errors_list.append("Excel s/Corte o Doblez")
                        if classified["step"] and not step_valid:
                            errors_list.append("STEP vacío/inválido")
                            
                        ready_to_import = (present_count == 6) and (classified["step"] is not None) and xlsx_valid and step_valid
                        
                        if not errors_list:
                            status_desc = "Listo"
                        else:
                            status_desc = "🔴 " + " | ".join(errors_list)
                            
                        has_validation = (classified["plano_validado"] is not None and classified["vobo_pdf"] is not None)
                        if has_validation and ready_to_import:
                            status_desc += " + Auto-Liberar 🟢"
                            
                        scanned_rows.append({
                            "Seleccionar": ready_to_import,
                            "Carpeta": sdir,
                            "SKU Detectado": sku,
                            "Dibujo PDF": "🟢 Encontrado" if classified["pdf_orig"] else "🔴 Faltante",
                            "DXF": "🟢 Encontrado" if classified["dxf"] else "🔴 Faltante",
                            "Plano Control": "🟢 Encontrado" if classified["control_pdf"] else "🔴 Faltante",
                            "Plano 3D": "🟢 Encontrado" if classified["slddrw"] else "🔴 Faltante",
                            "Dibujo 2D": "🟢 Encontrado" if classified["sldprt"] else "🔴 Faltante",
                            "Plano STEP": "🟢 Encontrado" if step_valid else ("🔴 Sin pieza/inválido" if classified["step"] else "🔴 Faltante"),
                            "Excel Resumen": "🟢 Encontrado" if xlsx_valid else ("🔴 Sin Corte/Doblez" if classified["xlsx"] else "🔴 Faltante"),
                            "Estatus": status_desc,
                            "ready": ready_to_import,
                            "parsed": parsed,
                            "files": classified
                        })
                        
                    if not scanned_rows:
                        st.warning("⚠️ No se encontraron carpetas válidas que coincidan con la nomenclatura esperada (ej: INGXXXX - SKU).")
                    else:
                        st.session_state["bulk_scan_results"] = scanned_rows
                        st.success(f"🔍 Escaneo completado. Se detectaron {len(scanned_rows)} carpetas con nomenclatura de Ingeniería válida.")
                        
        if st.session_state["bulk_scan_results"] is not None:
            scanned_rows = st.session_state["bulk_scan_results"]
            
            # ── Calculate Audit Metrics ──
            total_detected = len(scanned_rows)
            total_ready = sum(1 for r in scanned_rows if r.get("ready"))
            total_pending = total_detected - total_ready
            pct_ready = (total_ready / total_detected * 100.0) if total_detected > 0 else 0.0
            
            # Generate Excel Audit file with colors (openpyxl)
            audit_source = st.session_state.get("last_scanned_path", import_path)
            audit_excel_bytes = generate_bulk_audit_excel(scanned_rows, audit_source)
            audit_filename = f"Auditoria_Ingenieria_Pendientes_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            
            st.markdown("---")
            st.markdown("##### 📋 Listado de Diseños Detectados en Carpeta y Auditoría")
            
            # ── KPI Cards ──
            k_col1, k_col2, k_col3, k_col4 = st.columns(4)
            with k_col1:
                st.metric("Total Diseños Analizados", f"{total_detected}")
            with k_col2:
                st.metric("Diseños Completos", f"{total_ready}", delta="Listos para Importar", delta_color="normal")
            with k_col3:
                st.metric("Con Información Pendiente", f"{total_pending}", delta="Requiere Ingeniería", delta_color="inverse")
            with k_col4:
                st.metric("Índice de Integridad", f"{pct_ready:.1f}%")
                
            # ── Explanatory Banner & Top Download Button ──
            top_dl_col1, top_dl_col2 = st.columns([2.5, 1])
            with top_dl_col1:
                st.markdown("""
                <div style="background-color: #F8F9FA; border-left: 5px solid #EC2024; border: 1px solid #D2D3D5; border-radius: 6px; padding: 0.6rem 1rem;">
                    <span style="font-family: 'Montserrat', sans-serif; font-weight: bold; color: #111111; font-size: 0.95rem;">
                        📊 Reporte de Auditoría para Ingeniería (Excel a Color)
                    </span>
                    <p style="font-family: 'Questrial', sans-serif; font-size: 0.85rem; color: #64748b; margin: 0.2rem 0 0 0;">
                        Descarga el informe completo con colores (🟢 Verde = Encontrado, 🔴 Rojo = Faltante) y la pestaña exclusiva <b>'Solo Pendientes'</b> para que el equipo de Ingeniería complete los archivos faltantes.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            with top_dl_col2:
                st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
                st.download_button(
                    label="📥 Descargar Auditoría en Excel",
                    data=audit_excel_bytes,
                    file_name=audit_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Descargar archivo Excel con formato de colores de la auditoría actual",
                    key="btn_dl_audit_excel_top"
                )
                
            st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
            st.markdown("Seleccione individualmente los registros válidos que desea registrar en la base de datos:")
            
            df_display = pd.DataFrame([
                {
                    "Seleccionar": r["Seleccionar"],
                    "Carpeta": r["Carpeta"],
                    "SKU Detectado": r["SKU Detectado"],
                    "Dibujo PDF": r["Dibujo PDF"],
                    "DXF": r["DXF"],
                    "Plano Control": r["Plano Control"],
                    "Plano 3D": r["Plano 3D"],
                    "Dibujo 2D": r["Dibujo 2D"],
                    "Plano STEP": r["Plano STEP"],
                    "Excel Resumen": r["Excel Resumen"],
                    "Estatus": r["Estatus"]
                }
                for r in scanned_rows
            ])
            
            edited_df = st.data_editor(
                df_display,
                column_config={
                    "Seleccionar": st.column_config.CheckboxColumn(
                        "¿Importar?",
                        help="Marque para incluir este diseño en la importación",
                        default=False
                    )
                },
                disabled=[col for col in df_display.columns if col != "Seleccionar"],
                use_container_width=True,
                key="bulk_import_data_editor"
            )
            
            # Sync edited selection back to session_state scan results
            for idx, sel_val in enumerate(edited_df["Seleccionar"].tolist()):
                st.session_state["bulk_scan_results"][idx]["Seleccionar"] = sel_val
                
            selected_indices = edited_df[edited_df["Seleccionar"] == True].index.tolist()
            st.info(f"📍 Diseños seleccionados para importar definitivamente: **{len(selected_indices)}** de **{len(scanned_rows)}**")
            
            # Action Buttons: Import and Download Excel
            bot_act1, bot_act2 = st.columns([1, 1])
            with bot_act1:
                btn_import_clicked = st.button("🚀 Importar Selección Confirmada", key="btn_import_execute_red")
            with bot_act2:
                st.download_button(
                    label="📊 Descargar Reporte de Auditoría (Excel a Color)",
                    data=audit_excel_bytes,
                    file_name=audit_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Descargar archivo Excel con formato de colores de la auditoría actual",
                    key="btn_dl_audit_excel_bottom"
                )
                
            if btn_import_clicked:
                if not selected_indices:
                    st.error("Error: No ha seleccionado ningún registro viable para importar.")
                else:
                    import shutil
                    
                    def get_or_create_material(material_name, cursor):
                        cursor.execute("SELECT espesor_nominal FROM materias_primas WHERE material = ?", (material_name,))
                        row = cursor.fetchone()
                        if row:
                            return row[0]
                        
                        thickness = 0.060
                        m_lower = material_name.lower()
                        if "16ga" in m_lower:
                            thickness = 0.0598
                        elif "18ga" in m_lower:
                            thickness = 0.0478
                        elif "20ga" in m_lower:
                            thickness = 0.0359
                        elif "14ga" in m_lower:
                            thickness = 0.0747
                        elif "12ga" in m_lower:
                            thickness = 0.1046
                        elif "10ga" in m_lower:
                            thickness = 0.1345
                        else:
                            import re
                            nums = re.findall(r"\d+", material_name)
                            if nums:
                                val = int(nums[0])
                                if "al" in m_lower:
                                    thickness = val / 1000.0
                                else:
                                    thickness = val / 100.0
                        cursor.execute("INSERT INTO materias_primas (material, espesor_nominal) VALUES (?, ?)", (material_name, thickness))
                        return thickness
                        
                    import_count = 0
                    errors = 0
                    total_import = len(selected_indices)
                    progress_bar = st.progress(0.0)
                    log_area = st.empty()
                    logs_output = []
                    
                    for idx, index_val in enumerate(selected_indices):
                        orig_row = scanned_rows[index_val]
                        parsed = orig_row["parsed"]
                        files = orig_row["files"]
                        sku = orig_row["SKU Detectado"]
                        
                        if not orig_row["ready"]:
                            logs_output.append(f"⚠️ Ignorado {sku}: No cuenta con los 6 archivos requeridos.")
                            errors += 1
                            continue
                            
                        try:
                            mat_espesor = get_or_create_material(parsed["material"], cursor)
                            
                            # Parse nominal dimensions from Excel resume
                            mat_ancho = 0.0
                            mat_largo = 0.0
                            xlsx_path = files.get("xlsx")
                            if xlsx_path and os.path.exists(xlsx_path):
                                try:
                                    df_c = pd.read_excel(xlsx_path, sheet_name="CORTE")
                                    df_c.columns = [c.strip().upper() for c in df_c.columns]
                                    if "DIM" in df_c.columns and len(df_c) >= 2:
                                        mat_largo = float(df_c["DIM"].iloc[0])
                                        mat_ancho = float(df_c["DIM"].iloc[1])
                                except Exception:
                                    pass
                                    
                            project_base = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Proyectos")
                            dest_dir = os.path.join(
                                project_base,
                                parsed["part_no"],
                                f"Rev_{parsed['revision']}",
                                f"FactorK_{parsed['k_factor']}",
                                f"Espesor_{mat_espesor:.3f}"
                            )
                            os.makedirs(dest_dir, exist_ok=True)
                            
                            saved_paths = {}
                            from src.services.gcs_storage import is_gcs_available, upload_file_to_gcs
                            gcs_ready = is_gcs_available()

                            for file_key, src_path in files.items():
                                if src_path is not None:
                                    ext = os.path.splitext(src_path)[1]
                                    if file_key == "pdf_orig":
                                        filename = f"{parsed['part_no']}_Original{ext}"
                                    elif file_key == "plano_validado":
                                        filename = f"Plano_Validado_{sku}{ext}"
                                    elif file_key == "vobo_pdf":
                                        filename = f"VoBo_Primera_Pieza_{sku}{ext}"
                                    else:
                                        filename = f"{sku}{ext}"
                                    dest_path = os.path.join(dest_dir, filename)
                                    shutil.copy2(src_path, dest_path)

                                    if gcs_ready:
                                        rel_blob = f"Proyectos/{parsed['part_no']}/Rev_{parsed['revision']}/FactorK_{parsed['k_factor']}/Espesor_{mat_espesor:.3f}/{filename}"
                                        ok_g, gcs_uri = upload_file_to_gcs(dest_path, rel_blob)
                                        saved_paths[file_key] = gcs_uri if ok_g else dest_path
                                    else:
                                        saved_paths[file_key] = dest_path

                            db_storage_path = f"gs://sigrama-planos-calidad-2026/Proyectos/{parsed['part_no']}/Rev_{parsed['revision']}/FactorK_{parsed['k_factor']}/Espesor_{mat_espesor:.3f}" if gcs_ready else dest_dir

                            cursor.execute(
                                """
                                INSERT OR REPLACE INTO piezas (
                                    numero_pieza, material, acabado_estandar, factor_k, version, revision, nombre_sku,
                                    espesor_materia_prima, ancho_materia_prima, largo_materia_prima, ruta_almacenamiento,
                                    archivo_dibujo_original, archivo_dxf, archivo_plano_control, archivo_plano_nativo_3d,
                                    archivo_dibujo_nativo_2d, archivo_excel_resumen, archivo_step,
                                    plano_validado_impreso, documento_primera_pieza, usuario_registro
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    parsed["part_no"], parsed["material"], parsed["finish"], int(parsed["k_factor"]), parsed["version"], parsed["revision"], sku,
                                    mat_espesor, mat_ancho, mat_largo, db_storage_path,
                                    saved_paths.get("pdf_orig"), saved_paths.get("dxf"), saved_paths.get("control_pdf"),
                                    saved_paths.get("slddrw"), saved_paths.get("sldprt"), saved_paths.get("xlsx"), saved_paths.get("step"),
                                    saved_paths.get("plano_validado"), saved_paths.get("vobo_pdf"), st.session_state["nombre_completo"]
                                )
                            )
                            
                            cursor.execute("SELECT id FROM piezas WHERE nombre_sku = ?", (sku,))
                            inserted_piece_id = cursor.fetchone()[0]
                            
                            piece_record = {
                                "id": inserted_piece_id,
                                "numero_pieza": parsed["part_no"],
                                "material": parsed["material"],
                                "acabado_estandar": parsed["finish"],
                                "factor_k": int(parsed["k_factor"]),
                                "version": parsed["version"],
                                "revision": parsed["revision"],
                                "nombre_sku": sku,
                                "espesor_materia_prima": mat_espesor,
                                "ancho_materia_prima": mat_ancho,
                                "largo_materia_prima": mat_largo,
                                "ruta_almacenamiento": dest_dir,
                                "archivo_dibujo_original": saved_paths.get("pdf_orig"),
                                "archivo_dxf": saved_paths.get("dxf"),
                                "archivo_plano_control": saved_paths.get("control_pdf"),
                                "archivo_plano_nativo_3d": saved_paths.get("slddrw"),
                                "archivo_dibujo_nativo_2d": saved_paths.get("sldprt"),
                                "archivo_excel_resumen": saved_paths.get("xlsx"),
                                "archivo_step": saved_paths.get("step"),
                                "usuario_registro": st.session_state["nombre_completo"]
                            }
                            backup_pdf_bytes = generate_first_piece_pdf(piece_record)
                            backup_pdf_path = os.path.join(dest_dir, f"Backup_Registro_{sku}.pdf")
                            with open(backup_pdf_path, "wb") as f:
                                f.write(backup_pdf_bytes)
                                
                            conn.commit()
                            import_count += 1
                            logs_output.append(f"✅ Importado con éxito: {sku}")
                        except Exception as ex:
                            conn.rollback()
                            errors += 1
                            logs_output.append(f"❌ Error al importar {sku}: {str(ex)}")
                            
                        progress_bar.progress((idx + 1) / total_import)
                        log_area.text("\n".join(logs_output[-5:]))
                        
                    st.success(f"🎉 Importación finalizada con éxito. Importados: {import_count}, Errores/Ignorados: {errors}")
                    st.session_state["bulk_scan_results"] = None # Clear scan results to force fresh scan
                    
                    # Clean up temporary directory if it exists
                    temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "temp_bulk_import")
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    
                    with st.expander("📝 Registro Completo de Eventos (Log)"):
                        st.text("\n".join(logs_output))
                        
    conn.close()

from datetime import datetime
import io
