import streamlit as st
import pandas as pd
import sqlite3
import os
import io
from src.database import get_connection
import src.views.v3_control.v3_1_cad_viewer as cad_view
import zipfile

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

from src.pdf_generator import generate_first_piece_pdf
from src.services.gcs_storage import get_file_bytes, generate_secure_signed_url

def render_header_back_to_hub(current_section=""):
    """
    Componente de barra de navegación superior universal.
    Permite al usuario volver a la Página Principal (Centro de Control) desde cualquier submódulo con 1 clic.
    """
    col_back, col_space = st.columns([1.5, 5])
    with col_back:
        if st.button("🔙 Volver a Página Principal", key=f"btn_global_hub_back_{current_section}", use_container_width=True):
            st.session_state["nav_menu_selection"] = "1. Página Principal (Centro de Control)"
            st.session_state["redirect_to_page"] = "1. Página Principal (Centro de Control)"
            st.rerun()

def show_hub():
    # ── ESTILOS INDUSTRIALES EXACTOS SEGÚN DIAGRAMA (PANTALLA LIMPIA Y COCKPIT UNIFICADO) ──
    st.markdown("""
    <style>
    .hub-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border-left: 6px solid #EC2024;
        color: #FFFFFF;
        padding: 12px 20px;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
    }
    .hub-header h2 {
        margin: 0;
        font-family: 'Montserrat', sans-serif;
        font-size: 1.4rem;
        font-weight: 900;
        letter-spacing: 1px;
        color: #FFFFFF !important;
    }
    .hub-header span {
        font-size: 0.85rem;
        font-family: 'Questrial', sans-serif;
        color: #94a3b8;
    }
    .hub-header-badge {
        background: rgba(236, 32, 36, 0.18);
        border: 1px solid rgba(236, 32, 36, 0.4);
        color: #f87171;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 700;
        font-family: 'Montserrat', sans-serif;
    }

    /* Cuadro de Número de Pieza / Plano (Caja blanca con marco negro según diagrama) */
    .hub-piece-box {
        background: #FFFFFF;
        color: #0f172a;
        border: 2px solid #0f172a;
        border-radius: 8px;
        padding: 14px 16px;
        text-align: center;
        font-size: 2.1rem;
        font-weight: 900;
        font-family: 'Montserrat', monospace;
        letter-spacing: 2px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.06);
        margin: 6px 0 10px 0;
    }

    /* Subtítulo con metadatos técnicos */
    .hub-meta-pill {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 0.82rem;
        color: #334155;
        margin-bottom: 10px;
        line-height: 1.4;
    }

    /* Encabezados de Columna (Negritas, Centrado, Tamaño Industrial) */
    .hub-col-title {
        text-align: center;
        font-family: 'Montserrat', sans-serif;
        font-weight: 900;
        font-size: 1.25rem;
        letter-spacing: 1px;
        color: #0f172a;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 2px solid #E2E8F0;
        text-transform: uppercase;
    }

    /* Botones de Acción Estilo Diagrama (Azul Industrial) */
    .hub-action-btn-wrapper div.stButton > button,
    .hub-action-btn-wrapper div.stDownloadButton > button {
        background-color: #2563EB !important;
        border: 2px solid #1D4ED8 !important;
        color: #FFFFFF !important;
        font-family: 'Montserrat', sans-serif !important;
        font-size: 1.0rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px !important;
        padding: 14px 16px !important;
        min-height: 56px !important;
        border-radius: 6px !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.22) !important;
        margin-bottom: 12px !important;
        text-transform: uppercase !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .hub-action-btn-wrapper div.stButton > button:hover,
    .hub-action-btn-wrapper div.stDownloadButton > button:hover {
        background-color: #1D4ED8 !important;
        border-color: #1E40AF !important;
        color: #FFFFFF !important;
        box-shadow: 0 6px 18px rgba(29, 78, 216, 0.45) !important;
        transform: translateY(-2px) !important;
    }

    /* Botón especial para abrir Visor 3D en Pantalla Completa */
    .hub-btn-open-3d {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        background: linear-gradient(135deg, #EC2024 0%, #B71C1C 100%);
        color: #FFFFFF !important;
        text-decoration: none !important;
        font-family: 'Montserrat', sans-serif;
        font-size: 1.05rem;
        font-weight: 800;
        padding: 12px 16px;
        border-radius: 8px;
        box-shadow: 0 4px 14px rgba(236, 32, 36, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.25);
        margin-top: 10px;
        transition: all 0.2s ease;
        letter-spacing: 0.5px;
    }
    .hub-btn-open-3d:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(236, 32, 36, 0.55);
        background: linear-gradient(135deg, #FF2E33 0%, #C62828 100%);
        color: #FFFFFF !important;
    }

    /* Ficha de observaciones */
    .hub-obs-panel {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        padding: 14px;
        margin-top: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

    # 1. Cabecera Corporativa de Control Central
    st.markdown("""
    <div class="hub-header">
        <div>
            <h2>CENTRO DE CONTROL PRINCIPAL</h2>
            <span>Planta Metales SIGRAMA — Navegación Centralizada de Calidad, Diseño y Manufactura</span>
        </div>
        <div class="hub-header-badge">
            ⚡ HUB DE OPERACIÓN 4.0
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Cargar catálogo de piezas
    conn = get_connection()
    df_piezas = pd.read_sql_query("""
        SELECT * FROM piezas 
        ORDER BY CASE WHEN consecutivo_ing IS NOT NULL AND consecutivo_ing != '' THEN consecutivo_ing ELSE numero_pieza END ASC
    """, conn)
    conn.close()

    if len(df_piezas) == 0:
        st.warning("⚠️ No se encontraron piezas registradas en el sistema. Registre una nueva pieza en Ingeniería (3.1).")
        return

    total_piezas = len(df_piezas)

    # Manejar índice de pieza seleccionada
    if "hub_piece_idx" not in st.session_state:
        st.session_state["hub_piece_idx"] = 0

    # Si venimos redirigidos con un target_piece_id o hub_selected_sku
    if "hub_selected_sku" in st.session_state:
        target_sku = st.session_state.pop("hub_selected_sku")
        matched = df_piezas[df_piezas["nombre_sku"] == target_sku]
        if not matched.empty:
            st.session_state["hub_piece_idx"] = int(matched.index[0])

    if "hub_selected_piece_id" in st.session_state:
        target_id = st.session_state.pop("hub_selected_piece_id")
        matched = df_piezas[df_piezas["id"] == target_id]
        if not matched.empty:
            st.session_state["hub_piece_idx"] = int(matched.index[0])

    # Asegurar límites del índice
    idx = max(0, min(st.session_state["hub_piece_idx"], total_piezas - 1))
    st.session_state["hub_piece_idx"] = idx

    selected_piece = df_piezas.iloc[idx].to_dict()
    num_pieza = selected_piece.get("numero_pieza") or "S/N"
    sku = selected_piece.get("nombre_sku") or num_pieza
    mat = selected_piece.get("material") or "Acero"
    finish = selected_piece.get("acabado_estandar") or "Natural"
    thk = float(selected_piece.get("espesor_materia_prima") or 0.0)
    thk_mm = thk * 25.4
    version_label = f"V{selected_piece.get('version','1')}-R{selected_piece.get('revision','0')}"

    # ── DISTRIBUCIÓN PRINCIPAL EN 3 COLUMNAS EXACTAS SEGÚN EL DIAGRAMA ──
    col_left, col_center, col_right = st.columns([1.35, 1.0, 1.15], gap="large")

    # ══════════════════════════════════════════════════════════════════
    # COLUMNA 1: PIEZA Y VISOR 3D CAD
    # ══════════════════════════════════════════════════════════════════
    with col_left:
        # Selector rápido y navegación Prev/Next
        p_c1, p_c2, p_c3 = st.columns([1, 2.5, 1])
        with p_c1:
            if st.button("◀ Ant.", key="hub_btn_prev", use_container_width=True, help="Pieza previa", disabled=(idx <= 0)):
                st.session_state["hub_piece_idx"] = idx - 1
                st.rerun()
        with p_c2:
            piezas_options = [
                f"{r['numero_pieza']} ({r.get('consecutivo_ing') or f'ID-{r['id']}'})"
                for _, r in df_piezas.iterrows()
            ]
            selected_option = st.selectbox(
                "Seleccionar Pieza:",
                options=piezas_options,
                index=idx,
                key="hub_selectbox_piece",
                label_visibility="collapsed"
            )
            new_idx = piezas_options.index(selected_option)
            if new_idx != idx:
                st.session_state["hub_piece_idx"] = new_idx
                st.rerun()
        with p_c3:
            if st.button("Sig. ▶", key="hub_btn_next", use_container_width=True, help="Siguiente pieza", disabled=(idx >= total_piezas - 1)):
                st.session_state["hub_piece_idx"] = idx + 1
                st.rerun()

        # Cuadro de Número de Pieza (según diagrama del usuario: 11-B-9016-01)
        st.markdown(f"""
        <div class="hub-piece-box">
            {num_pieza}
        </div>
        <div class="hub-meta-pill">
            <b>SKU:</b> {sku}<br>
            <b>Material:</b> {mat} | <b>Espesor:</b> {thk:.4f}" ({thk_mm:.2f} mm) | <b>Acabado:</b> {finish} | <b>Versión:</b> {version_label}
        </div>
        """, unsafe_allow_html=True)

        # Visor 3D Interactivo incrustado
        cad_view.render_cad_viewer_embedded(selected_piece, height=410)

        # Botón para abrir el Visor 3D en Pantalla Completa
        clean_sku_param = sku.replace(" ", "%20")
        clean_pieza_param = str(num_pieza).replace(" ", "%20")
        url_fullscreen_3d = f"?fullscreen=cad&sku={clean_sku_param}&pieza={clean_pieza_param}"
        
        st.markdown(f"""
        <a href="{url_fullscreen_3d}" target="_blank" class="hub-btn-open-3d">
            <span style="font-size: 1.25rem; vertical-align: middle; margin-right: 8px;">🧊</span>
            <span>ABRIR VISOR 3D (Pantalla Completa) ↗</span>
        </a>
        """, unsafe_allow_html=True)


    # ══════════════════════════════════════════════════════════════════
    # COLUMNA 2: OPCIONES DE REGISTRO
    # ══════════════════════════════════════════════════════════════════
    with col_center:
        st.markdown('<div class="hub-col-title">OPCIONES DE REGISTRO</div>', unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="hub-action-btn-wrapper">', unsafe_allow_html=True)

            # Botón 1: PPVA (Proceso de Aprobación de Producción / Auditoría de Planos)
            if st.button("PPVA", key="hub_btn_ppva", use_container_width=True, help="Proceso de Aprobación de Partes de Producción / Auditoría y Validación de Planos"):
                st.session_state["nav_menu_selection"] = "   3.1 Carga de Registros de Diseño"
                st.session_state["redirect_to_page"] = "   3.1 Carga de Registros de Diseño"
                st.session_state["hub_selected_piece_id"] = selected_piece["id"]
                st.session_state["design_target_tab"] = 0 # Tab 3.2.1 Auditoría
                st.rerun()

            # Botón 2: PRIMERAS PIEZAS
            if st.button("PRIMERAS PIEZAS", key="hub_btn_primeras_piezas", use_container_width=True, help="Inspección y Validación de Primera Pieza"):
                st.session_state["nav_menu_selection"] = "   3.1 Carga de Registros de Diseño"
                st.session_state["redirect_to_page"] = "   3.1 Carga de Registros de Diseño"
                st.session_state["hub_selected_piece_id"] = selected_piece["id"]
                st.session_state["design_target_tab"] = 2 # Tab 3.2.3 Primera Pieza
                st.rerun()

            # Botón 3: MEDICIONES DE ÓRDENES DE FABRICACIÓN
            if st.button("MEDICIONES DE ÓRDENES DE FABRICACIÓN", key="hub_btn_mediciones", use_container_width=True, help="Carga de Inspección Dimensional en Piso (Corte Láser y Doblez)"):
                st.session_state["nav_menu_selection"] = "   4.2 Carga de Inspección (Excel)"
                st.session_state["redirect_to_page"] = "   4.2 Carga de Inspección (Excel)"
                st.session_state["hub_selected_sku"] = selected_piece["nombre_sku"]
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        # Tarjeta informativa de estado actual de registro
        estatus_aud = selected_piece.get("estatus_auditoria") or "Sin Auditar"
        badge_color = "#16a34a" if estatus_aud == "Auditada" else ("#ea580c" if estatus_aud == "En Proceso" else "#dc2626")
        
        st.markdown(f"""
        <div style="background:#F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; margin-top: 14px;">
            <div style="font-size: 0.78rem; color: #64748b; font-weight: 700; text-transform: uppercase;">Estado de Aprobación Oficial:</div>
            <div style="font-size: 1.05rem; font-weight: 800; color: {badge_color}; margin-top: 2px;">
                {'🛡️' if estatus_aud == 'Auditada' else '⚠️'} {estatus_aud.upper()}
            </div>
            <div style="font-size: 0.78rem; color: #64748b; margin-top: 4px;">
                Auditor: <b>{selected_piece.get('auditor_nombre') or 'Pendiente'}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)


    # ══════════════════════════════════════════════════════════════════
    # COLUMNA 3: DESCARGAS
    # ══════════════════════════════════════════════════════════════════
    with col_right:
        st.markdown('<div class="hub-col-title">DESCARGAS</div>', unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="hub-action-btn-wrapper">', unsafe_allow_html=True)

            # Botón 1: DESCARGAR HISTORIALES DE FABRICACIÓN
            pdf_data = dict(selected_piece)
            if not pdf_data.get("usuario_registro"):
                pdf_data["usuario_registro"] = "Ingeniería SIGRAMA"
            pdf_ficha_bytes = generate_first_piece_pdf(pdf_data)

            st.download_button(
                label="DESCARGAR HISTORIALES DE FABRICACIÓN",
                data=pdf_ficha_bytes or b"",
                file_name=f"Historial_Fabricacion_{num_pieza}.pdf",
                mime="application/pdf",
                key="hub_btn_dl_fabricacion",
                use_container_width=True,
                help="Descarga inmediata de la Ficha Técnica y Reporte Oficial de Fabricación en PDF"
            )

            # Botón 2: DESCARGAR HISTORIALES DIMENSIONALES
            # Busca si hay un reporte de inspección de Excel o genera resumen SPC
            excel_path = selected_piece.get("archivo_excel_resumen")
            excel_bytes = get_file_bytes(excel_path) if excel_path else None
            
            st.download_button(
                label="DESCARGAR HISTORIALES DIMENSIONALES",
                data=excel_bytes or pdf_ficha_bytes or b"",
                file_name=f"Historial_Dimensional_SPC_{num_pieza}.xlsx" if excel_bytes else f"Historial_Dimensional_SPC_{num_pieza}.pdf",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if excel_bytes else "application/pdf",
                key="hub_btn_dl_dimensional",
                use_container_width=True,
                help="Descarga del Historial Dimensional y Estadístico SPC de la pieza"
            )

            # Botón 3: DESCARGAR COMPENDIO DE DOCUMENTOS (ZIP con Plano, DXF, STEP y Ficha)
            comp_zip, comp_name, _ = generate_piece_documents_zip(selected_piece, is_full_engineering_pack=False)
            st.download_button(
                label="DESCARGAR COMPENDIO DE DOCUMENTOS",
                data=comp_zip,
                file_name=comp_name,
                mime="application/zip",
                key="hub_btn_dl_compendio",
                use_container_width=True,
                help="Paquete unificado con Plano de Control, Dibujo Original, DXF y Especificaciones"
            )

            # Botón 4: OBSERVACIONES DE ESTAS PIEZAS (Toggle de sección de notas y no conformidades)
            if "show_obs_panel" not in st.session_state:
                st.session_state["show_obs_panel"] = False

            if st.button("OBSERVACIONES DE ESTAS PIEZAS", key="hub_btn_observaciones", use_container_width=True, help="Ver y actualizar el historial de observaciones, notas de auditoría e incidencias de esta pieza"):
                st.session_state["show_obs_panel"] = not st.session_state["show_obs_panel"]
                st.rerun()

            # Botón 5: ARCHIVO INGENIERÍA ZIP COMPLETO (CARPETA)
            eng_zip, eng_name, _ = generate_piece_documents_zip(selected_piece, is_full_engineering_pack=True)
            st.download_button(
                label="ARCHIVO INGENIERÍA ZIP COMPLETO (CARPETA)",
                data=eng_zip,
                file_name=eng_name,
                mime="application/zip",
                key="hub_btn_dl_zip_completo",
                use_container_width=True,
                help="Carpeta oficial completa de Ingeniería con todos los archivos nativos 3D, DXF, Planos y Manifiesto"
            )

            st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # SECCIÓN DESPLEGABLE: OBSERVACIONES Y NOTAS DE ESTA PIEZA
    # ══════════════════════════════════════════════════════════════════
    if st.session_state.get("show_obs_panel", False):
        st.markdown("---")
        st.markdown(f"### 📋 Observaciones y Control de Calidad: `{num_pieza}`")
        
        obs_col1, obs_col2 = st.columns([1.5, 1])
        with obs_col1:
            st.markdown("#### Historial y Notas de Auditoría:")
            current_notes = selected_piece.get("auditoria_notas") or "Sin observaciones registradas."
            st.info(current_notes)

            # Formulario para agregar / editar observaciones
            with st.expander("✏️ Agregar o Actualizar Observaciones"):
                with st.form("form_add_obs"):
                    new_note = st.text_area("Nueva Observación o Incidencia:", placeholder="Describa tolerancias especiales, advertencias de doblez o comentarios del cliente...")
                    guardar = st.form_submit_button("Guardar Observación")
                    if guardar and new_note.strip():
                        conn = get_connection()
                        cur = conn.cursor()
                        updated_notes = f"{current_notes}\n[{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}] {st.session_state.get('nombre_completo', 'Usuario')}: {new_note.strip()}"
                        cur.execute("UPDATE piezas SET auditoria_notas = ? WHERE id = ?", (updated_notes, selected_piece["id"]))
                        conn.commit()
                        conn.close()
                        st.success("✅ Observación registrada con éxito.")
                        st.rerun()

        with obs_col2:
            st.markdown("#### Resumen Documental:")
            has_plano = bool(selected_piece.get("archivo_plano_control"))
            has_dxf = bool(selected_piece.get("archivo_dxf"))
            has_step = bool(selected_piece.get("archivo_step"))
            has_vobo = bool(selected_piece.get("plano_validado_impreso") or selected_piece.get("documento_primera_pieza"))
            
            st.markdown(f"""
            - {'✅' if has_plano else '❌'} **Plano de Control:** {'Disponible' if has_plano else 'Pendiente'}
            - {'✅' if has_dxf else '❌'} **Archivo DXF:** {'Disponible' if has_dxf else 'Pendiente'}
            - {'✅' if has_step else '❌'} **Modelo STEP:** {'Disponible' if has_step else 'Pendiente'}
            - {'✅' if has_vobo else '❌'} **Liberación 1ra Pieza:** {'Liberada' if has_vobo else 'Pendiente'}
            """)
