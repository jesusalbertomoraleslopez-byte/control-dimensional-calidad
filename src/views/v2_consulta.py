import streamlit as st
import pandas as pd
import sqlite3
import os
import streamlit.components.v1 as components
from src.database import get_connection

def calculate_conversions(ancho_in, largo_in, espesor_in, material_name=""):
    """Calcula conversiones a mm, área y peso estimado para aceros/metales."""
    try:
        w_in = float(ancho_in or 0.0)
        l_in = float(largo_in or 0.0)
        t_in = float(espesor_in or 0.0)
    except (ValueError, TypeError):
        w_in, l_in, t_in = 0.0, 0.0, 0.0
        
    w_mm = w_in * 25.4
    l_mm = l_in * 25.4
    area_in2 = w_in * l_in
    area_m2 = (w_mm * l_mm) / 1_000_000.0
    
    # Densidad estándar acero al carbono / galvanizado ~ 0.2833 lb/in3 (7850 kg/m3)
    densidad_lb_in3 = 0.2833
    vol_in3 = area_in2 * t_in
    peso_lb = vol_in3 * densidad_lb_in3
    peso_kg = peso_lb * 0.453592
    
    return {
        "w_in": f"{w_in:.3f}", "w_mm": f"{w_mm:.2f}",
        "l_in": f"{l_in:.3f}", "l_mm": f"{l_mm:.2f}",
        "area_in2": f"{area_in2:.2f}", "area_m2": f"{area_m2:.4f}",
        "peso_lb": f"{peso_lb:.2f}", "peso_kg": f"{peso_kg:.2f}",
        "thk_in": f"{t_in:.4f}"
    }

def show_consulta():
    from src.views.v0_hub import render_header_back_to_hub
    render_header_back_to_hub("2_consulta")

    # CSS especial para la pantalla SGP (Diseño Industrial Moderno, Alto Contraste y Calidad Visual)
    st.markdown("""
    <style>
    .sgp-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border-left: 6px solid #EC2024;
        color: #FFFFFF;
        padding: 14px 22px;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
    }
    .sgp-header h2 {
        margin: 0;
        font-family: 'Montserrat', sans-serif;
        font-size: 1.45rem;
        font-weight: 900;
        letter-spacing: 1px;
        color: #FFFFFF !important;
    }
    .sgp-header span {
        font-size: 0.88rem;
        font-family: 'Questrial', sans-serif;
        color: #94a3b8;
    }
    .sgp-header-badge {
        background: rgba(236, 32, 36, 0.18);
        border: 1px solid rgba(236, 32, 36, 0.4);
        color: #f87171;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        font-family: 'Montserrat', sans-serif;
    }
    .sgp-plano-box {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        color: #0f172a;
        border: 2px solid #0f172a;
        border-radius: 10px;
        padding: 14px 20px;
        text-align: center;
        font-size: 2.3rem;
        font-weight: 900;
        font-family: 'Montserrat', monospace;
        letter-spacing: 2px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        margin: 6px 0 14px 0;
    }
    .sgp-card-param {
        background: #FFFFFF;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
        transition: transform 0.1s ease;
    }
    .sgp-card-param:hover {
        border-color: #94a3b8;
    }
    .sgp-badge-tag {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.82rem;
        margin-right: 6px;
        margin-bottom: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .sgp-tag-ok {
        background-color: #dcfce7;
        color: #166534;
        border: 1px solid #86efac;
    }
    .sgp-tag-na {
        background-color: #f1f5f9;
        color: #64748b;
        border: 1px solid #cbd5e1;
    }
    .sgp-dim-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-family: 'Questrial', sans-serif;
        margin-top: 6px;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #cbd5e1;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .sgp-dim-table th {
        background: #0f172a;
        color: #FFFFFF;
        padding: 10px 14px;
        font-size: 0.85rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }
    .sgp-dim-table td {
        padding: 9px 14px;
        border-bottom: 1px solid #e2e8f0;
        font-size: 0.95rem;
        font-weight: 600;
        color: #1e293b;
        background-color: #FFFFFF;
    }
    .sgp-dim-table tr:nth-child(even) td {
        background-color: #f8fafc;
    }
    .sgp-dim-table tr:last-child td {
        border-bottom: none;
    }
    .sgp-btn-open-3d {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        background: linear-gradient(135deg, #EC2024 0%, #B71C1C 100%);
        color: #FFFFFF !important;
        text-decoration: none !important;
        font-family: 'Montserrat', sans-serif;
        font-size: 1.15rem;
        font-weight: 800;
        padding: 14px 20px;
        border-radius: 8px;
        box-shadow: 0 6px 16px rgba(236, 32, 36, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.25);
        margin-top: 14px;
        transition: all 0.2s ease;
        letter-spacing: 0.5px;
    }
    .sgp-btn-open-3d:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 24px rgba(236, 32, 36, 0.55);
        background: linear-gradient(135deg, #FF2E33 0%, #C62828 100%);
        color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # 1. Cabecera Estilo Base SGP
    st.markdown("""
    <div class="sgp-header">
        <div>
            <h2>BASE DE DATOS SGP</h2>
            <span>Planta Metales SIGRAMA — Consulta de Ingeniería y Control Dimensional</span>
        </div>
        <div class="sgp-header-badge">
            ⚙️ SIGRAMA METALES
        </div>
    </div>
    """, unsafe_allow_html=True)

    conn = get_connection()
    df_piezas = pd.read_sql_query("""
        SELECT * FROM piezas 
        ORDER BY CASE WHEN consecutivo_ing IS NOT NULL THEN consecutivo_ing ELSE numero_pieza END ASC
    """, conn)
    conn.close()

    if len(df_piezas) == 0:
        st.warning("⚠️ No se encontraron piezas registradas en la base de datos.")
        return

    # Total de piezas disponibles
    total_piezas = len(df_piezas)

    # Inicializar índice en session_state
    if "sgp_piece_idx" not in st.session_state:
        st.session_state["sgp_piece_idx"] = 0
    
    # Asegurar que el índice esté dentro de los límites
    idx = max(0, min(st.session_state["sgp_piece_idx"], total_piezas - 1))
    st.session_state["sgp_piece_idx"] = idx

    # 2. Barra de Navegación Rápida con Botones
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5, nav_col6 = st.columns([1, 1.2, 3, 1.2, 1, 1.5])

    with nav_col1:
        if st.button("⏮️ Inicio", use_container_width=True, help="Ir a la primera pieza"):
            st.session_state["sgp_piece_idx"] = 0
            st.rerun()

    with nav_col2:
        if st.button("◀ Anterior", use_container_width=True, help="Pieza previa"):
            if st.session_state["sgp_piece_idx"] > 0:
                st.session_state["sgp_piece_idx"] -= 1
                st.rerun()

    with nav_col3:
        # Selector de búsqueda rápida con autocompletado
        piezas_options = [
            f"[{r.get('consecutivo_ing') or f'ID-{r['id']}'}] {r['numero_pieza']} — {r.get('version','V0')}-{r.get('revision','R0')}"
            for _, r in df_piezas.iterrows()
        ]
        selected_option = st.selectbox(
            "Seleccionar Pieza:",
            options=piezas_options,
            index=st.session_state["sgp_piece_idx"],
            label_visibility="collapsed"
        )
        # Si el usuario eligió otra pieza del desplegable, actualizar índice
        new_idx = piezas_options.index(selected_option)
        if new_idx != st.session_state["sgp_piece_idx"]:
            st.session_state["sgp_piece_idx"] = new_idx
            st.rerun()

    with nav_col4:
        if st.button("Siguiente ▶", use_container_width=True, help="Siguiente pieza"):
            if st.session_state["sgp_piece_idx"] < total_piezas - 1:
                st.session_state["sgp_piece_idx"] += 1
                st.rerun()

    with nav_col5:
        if st.button("Fin ⏭️", use_container_width=True, help="Ir a la última pieza"):
            st.session_state["sgp_piece_idx"] = total_piezas - 1
            st.rerun()

    with nav_col6:
        st.markdown(f"<div style='text-align: right; padding-top: 8px; font-weight: 700; color: #555;'>Pieza {idx + 1} de {total_piezas}</div>", unsafe_allow_html=True)

    # Datos de la pieza actual
    p = df_piezas.iloc[idx].to_dict()
    num_pieza = p.get("numero_pieza") or "S/N"
    sku = p.get("nombre_sku") or num_pieza
    consecutivo = p.get("consecutivo_ing") or f"ING{idx+1:04d}"
    mat = p.get("material") or "Acero"
    finish = p.get("acabado_estandar") or "Natural"
    thk = p.get("espesor_materia_prima") or 0.0747
    w = p.get("ancho_materia_prima") or 0.0
    l = p.get("largo_materia_prima") or 0.0
    version_actual = p.get("version") or "V1"
    rev_actual = p.get("revision") or "R0"
    auditoria = p.get("estatus_auditoria") or "Sin Auditar"

    # Conversiones métricas y de peso
    conv = calculate_conversions(w, l, thk, mat)

    # 3. Distribución Principal: Panel Izquierdo (Ficha Técnica) + Panel Derecho (Plano y Apertura)
    col_ficha, col_preview = st.columns([1.1, 1], gap="medium")

    with col_ficha:
        # Cuadro Grande de NO_PLANO
        st.markdown(f"""
        <div style="font-size: 0.85rem; font-weight: 800; color: #555; text-transform: uppercase; margin-bottom: 2px;">
            NO_PLANO / NÚMERO DE PIEZA ({consecutivo})
        </div>
        <div class="sgp-plano-box">
            {num_pieza}
        </div>
        """, unsafe_allow_html=True)

        # Parámetros rápidos en 3 columnas
        f_c1, f_c2, f_c3 = st.columns(3)
        with f_c1:
            st.markdown(f"""
            <div class="sgp-card-param">
                <span style="font-size: 0.75rem; color: #777; font-weight: 700;">MATERIAL:</span><br>
                <b style="font-size: 1.05rem; color: #111;">{mat}</b>
            </div>
            """, unsafe_allow_html=True)
        with f_c2:
            st.markdown(f"""
            <div class="sgp-card-param">
                <span style="font-size: 0.75rem; color: #777; font-weight: 700;">ACABADO (FINISH):</span><br>
                <b style="font-size: 1.05rem; color: #A81C1F;">{finish}</b>
            </div>
            """, unsafe_allow_html=True)
        with f_c3:
            st.markdown(f"""
            <div class="sgp-card-param">
                <span style="font-size: 0.75rem; color: #777; font-weight: 700;">ESPESOR (THK):</span><br>
                <b style="font-size: 1.05rem; color: #111;">{conv['thk_in']} in</b>
            </div>
            """, unsafe_allow_html=True)

        # SKU completo / Descripción
        st.markdown(f"""
        <div style="background-color: #FFFFFF; border: 1px solid #D2D3D5; border-radius: 6px; padding: 8px 12px; margin-bottom: 12px;">
            <span style="font-size: 0.75rem; color: #777; font-weight: 700;">SKU COMPLETO DE INGENIERÍA:</span><br>
            <span style="font-family: monospace; font-size: 0.95rem; font-weight: 700; color: #222;">{sku}</span>
        </div>
        """, unsafe_allow_html=True)

        # Tabla de Conversiones (Pulgadas vs Milímetros - Estilo SGP)
        st.markdown(f"""
        <div style="font-size: 0.85rem; font-weight: 800; color: #444; margin-bottom: 4px;">
            📐 TABLA DE DIMENSIONES Y PESO (DUAL INCH / MM):
        </div>
        <table class="sgp-dim-table">
            <thead>
                <tr>
                    <th>Parámetro</th>
                    <th>Pulgadas (In)</th>
                    <th>Milímetros (mm)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Ancho (Width)</td>
                    <td>{conv['w_in']} in</td>
                    <td>{conv['w_mm']} mm</td>
                </tr>
                <tr>
                    <td>Largo (Long)</td>
                    <td>{conv['l_in']} in</td>
                    <td>{conv['l_mm']} mm</td>
                </tr>
                <tr>
                    <td>Área Calculada</td>
                    <td>{conv['area_in2']} in²</td>
                    <td>{conv['area_m2']} m²</td>
                </tr>
                <tr>
                    <td>Peso Estimado</td>
                    <td>{conv['peso_lb']} Lb</td>
                    <td>{conv['peso_kg']} kg</td>
                </tr>
            </tbody>
        </table>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Documentos disponibles
        has_orig = bool(p.get("archivo_dibujo_original"))
        has_ctrl = bool(p.get("archivo_plano_control"))
        has_step = bool(p.get("archivo_step"))
        has_dxf = bool(p.get("archivo_dxf"))
        has_vobo = bool(p.get("plano_validado_impreso") or p.get("documento_primera_pieza"))

        st.markdown(f"""
        <div style="font-size: 0.85rem; font-weight: 800; color: #444; margin-bottom: 6px;">
            📂 DOCUMENTACIÓN REGISTRADA:
        </div>
        <div>
            <span class="sgp-badge-tag {'sgp-tag-ok' if has_orig else 'sgp-tag-na'}">
                {'✅' if has_orig else '⚪'} Dibujo Original
            </span>
            <span class="sgp-badge-tag {'sgp-tag-ok' if has_ctrl else 'sgp-tag-na'}">
                {'✅' if has_ctrl else '⚪'} Plano de Control
            </span>
            <span class="sgp-badge-tag {'sgp-tag-ok' if has_step else 'sgp-tag-na'}">
                {'✅' if has_step else '⚪'} Modelo 3D STEP
            </span>
            <span class="sgp-badge-tag {'sgp-tag-ok' if has_dxf else 'sgp-tag-na'}">
                {'✅' if has_dxf else '⚪'} Archivo DXF
            </span>
            <span class="sgp-badge-tag {'sgp-tag-ok' if has_vobo else 'sgp-tag-na'}">
                {'✅' if has_vobo else '⚪'} VoBo Liberación
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Versiones de la misma pieza
        hermanas = df_piezas[df_piezas["numero_pieza"] == num_pieza]
        if len(hermanas) > 1:
            st.markdown("<div style='margin-top: 10px; font-size: 0.85rem; font-weight: 800; color: #444;'>VERSIONES REGISTRADAS DE ESTA PIEZA:</div>", unsafe_allow_html=True)
            v_cols = st.columns(min(len(hermanas), 4))
            for v_i, (_, h_row) in enumerate(hermanas.iterrows()):
                col_target = v_cols[v_i % len(v_cols)]
                with col_target:
                    h_label = f"{h_row.get('version','V1')}-{h_row.get('revision','R0')}"
                    es_actual = (h_row["id"] == p["id"])
                    if st.button(
                        f"{'👉 ' if es_actual else ''}{h_label}",
                        key=f"v_btn_{h_row['id']}",
                        use_container_width=True,
                        type="primary" if es_actual else "secondary"
                    ):
                        st.session_state["sgp_piece_idx"] = df_piezas.index[df_piezas["id"] == h_row["id"]].tolist()[0]
                        st.rerun()

    with col_preview:
        st.markdown(f"""
        <div style="font-size: 0.85rem; font-weight: 800; color: #555; text-transform: uppercase; margin-bottom: 2px;">
            VISTA PREVIA DEL PLANO (PDF / CONTROL)
        </div>
        """, unsafe_allow_html=True)

        # Cargar vista previa del plano PDF
        pdf_path = p.get("archivo_plano_control") or p.get("archivo_dibujo_original")
        pdf_bytes = None

        if pdf_path:
            try:
                from src.services.gcs_storage import get_file_bytes
                pdf_bytes = get_file_bytes(pdf_path)
            except Exception:
                pdf_bytes = None

            if not pdf_bytes and os.path.exists(str(pdf_path)):
                try:
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                except Exception:
                    pdf_bytes = None

        if pdf_bytes:
            import base64
            pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
            pdfjs_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="utf-8">
              <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.min.js"></script>
              <style>
                body {{ margin: 0; padding: 0; background-color: #2D2D2D; display: flex; justify-content: center; }}
                #canvas-wrapper {{ width: 100%; max-height: 430px; overflow-y: auto; text-align: center; }}
                canvas {{ max-width: 98%; height: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin: 6px auto; display: block; }}
              </style>
            </head>
            <body>
              <div id="canvas-wrapper"></div>
              <script>
                pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js';
                const pdfData = atob("{pdf_b64}");
                const rawLength = pdfData.length;
                const array = new Uint8Array(new ArrayBuffer(rawLength));
                for(let i = 0; i < rawLength; i++) array[i] = pdfData.charCodeAt(i);

                pdfjsLib.getDocument({{ data: array }}).promise.then(pdf => {{
                  const wrapper = document.getElementById('canvas-wrapper');
                  function renderPage(num) {{
                    pdf.getPage(num).then(page => {{
                      const viewport = page.getViewport({{ scale: 1.1 }});
                      const canvas = document.createElement('canvas');
                      canvas.width = viewport.width; canvas.height = viewport.height;
                      wrapper.appendChild(canvas);
                      page.render({{ canvasContext: canvas.getContext('2d'), viewport }});
                      if (num < pdf.numPages) renderPage(num + 1);
                    }});
                  }}
                  renderPage(1);
                }});
              </script>
            </body>
            </html>
            """
            components.html(pdfjs_html, height=440, scrolling=False)
        else:
            st.info("📄 Vista previa de plano no disponible localmente.")

        # 4. BOTÓN DE APERTURA EN NUEVA VENTANA (PANTALLA COMPLETA 3D)
        # Genera un enlace que abre directamente el modelo 3D de la pieza seleccionada a pantalla completa
        clean_sku_param = sku.replace(" ", "%20")
        clean_pieza_param = str(num_pieza).replace(" ", "%20")
        url_fullscreen_3d = f"?fullscreen=cad&sku={clean_sku_param}&pieza={clean_pieza_param}"
        
        st.markdown(f"""
        <a href="{url_fullscreen_3d}" target="_blank" class="sgp-btn-open-3d">
            <span style="font-size: 1.35rem; vertical-align: middle; margin-right: 8px;">🧊</span>
            <span>ABRIR VISOR 3D (Pantalla Completa) ↗</span>
        </a>
        <div style="text-align: center; font-size: 0.82rem; color: #475569; margin-top: 8px; font-weight: 600;">
            ✨ Abre directamente el modelo 3D de <b>{num_pieza}</b> en pantalla completa para inspección técnica.
        </div>
        """, unsafe_allow_html=True)
