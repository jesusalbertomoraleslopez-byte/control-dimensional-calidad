import streamlit as st
import streamlit.components.v1 as components
import os
import base64
from src.database import get_connection

def detect_step_units(file_bytes) -> str:
    """
    OpenCascade (occt-import-js) siempre triangula y exporta las coordenadas en milímetros
    independientemente de la unidad definida en el archivo STEP.
    Por lo tanto, siempre retornamos 'mm' para aplicar la conversión a pulgadas en el visualizador.
    """
    return "mm"

def show_cad_viewer():
    st.title("3.1. Visualizador 3D CAD")
    st.subheader("Visualización WebGL Interactiva de Archivos de Diseño")

    # Direct DOM queries from the same-origin WebGL iframe are used for button click navigation.

    # ── Scoped CSS: refined piece selector and column filter dropdowns ──
    st.markdown("""
    <style>
    /* ══ ALL SELECTBOXES: corporate black container ══════════════════════════ */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:first-child {
        background: linear-gradient(135deg, #111111 0%, #2A2A2A 100%) !important;
        border: 2px solid #EC2024 !important;
        border-radius: 8px !important;
        min-height: 52px !important; /* Reducido de 72px */
    }
    /* Nuclear selector: force every child element to white text */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] svg {
        fill: #ffffff !important;
    }
    
    /* Centrar verticalmente y eliminar paddings que recortan el texto */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] [role="button"],
    div[data-testid="stSelectbox"] div[data-baseweb="select"] input {
        padding-top: 0px !important;
        padding-bottom: 0px !important;
        display: flex !important;
        align-items: center !important;
    }

    /* ══ PIECE SELECTOR (not in column): large bold text ═══════════ */
    div[data-testid="stVerticalBlock"] > div > div[data-testid="stSelectbox"] div[data-baseweb="select"] span,
    div[data-testid="stVerticalBlock"] > div > div[data-testid="stSelectbox"] div[data-baseweb="select"] [role="button"] {
        font-size: 1.8rem !important; /* Reducido un 30% de 2.6rem */
        font-weight: 800 !important;
        line-height: 1.2 !important;
        text-shadow: 0 1px 3px rgba(0,0,0,0.4) !important;
    }

    /* ══ COLUMN FILTER DROPDOWNS: standard size override ════════════════════ */
    div[data-testid="stColumn"] div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:first-child {
        background: linear-gradient(135deg, #111111 0%, #2A2A2A 100%) !important;
        border: 1px solid #EC2024 !important;
        min-height: 38px !important;
        border-radius: 6px !important;
    }
    div[data-testid="stColumn"] div[data-testid="stSelectbox"] div[data-baseweb="select"] span,
    div[data-testid="stColumn"] div[data-testid="stSelectbox"] div[data-baseweb="select"] [role="button"] {
        font-size: 0.92rem !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
        text-shadow: none !important;
    }
    </style>
    """, unsafe_allow_html=True)


    st.markdown("""
        Esta sección permite cargar o seleccionar archivos de diseño (ej. `.STL` o `.STEP`) para su inspección visual tridimensional y medición de cotas generales.
    """)

    # 1. Database connection and querying
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM piezas ORDER BY nombre_sku")
    registered_pieces = [dict(r) for r in cursor.fetchall()]
    conn.close()


    # ── Filter Panel ────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="background:linear-gradient(135deg,#111111 0%,#2A2A2A 100%);
                border-left:5px solid #EC2024;
                border-radius:10px;padding:1rem 1.5rem 0.5rem 1.5rem;margin-bottom:1rem;
                box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
      <span style="color:#fff;font-weight:800;font-size:1.1rem;letter-spacing:.5px;font-family:'Montserrat';">
        🔍 Filtros de Búsqueda de Piezas
      </span>
    </div>
    """, unsafe_allow_html=True)

    # Derive unique values for each filter
    all_numbers   = sorted(set(p["numero_pieza"]     for p in registered_pieces))
    all_materials = sorted(set(p["material"]         for p in registered_pieces))
    all_finishes  = sorted(set(p["acabado_estandar"] for p in registered_pieces))
    all_versions  = sorted(set(p["version"]          for p in registered_pieces))
    all_revisions = sorted(set(p["revision"]         for p in registered_pieces))

    fcol1, fcol2, fcol3 = st.columns([2, 1, 1])
    with fcol1:
        filt_text = st.text_input(
            "🔎 Buscar por Número de Pieza o SKU",
            placeholder="Ej: 12-A-6004  ó  K48  ó  END_FILLER",
            key="cad_filt_text"
        )
    with fcol2:
        filt_material = st.selectbox(
            "Material / Calibre",
            ["Todos"] + all_materials,
            key="cad_filt_material"
        )
    with fcol3:
        filt_finish = st.selectbox(
            "Acabado / Estándar",
            ["Todos"] + all_finishes,
            key="cad_filt_finish"
        )

    fcol4, fcol5, fcol6 = st.columns([1, 1, 2])
    with fcol4:
        filt_version = st.selectbox(
            "Versión",
            ["Todos"] + all_versions,
            key="cad_filt_version"
        )
    with fcol5:
        filt_revision = st.selectbox(
            "Revisión",
            ["Todos"] + all_revisions,
            key="cad_filt_revision"
        )
    with fcol6:
        filt_numero = st.selectbox(
            "Número de Pieza (exacto)",
            ["Todos"] + all_numbers,
            key="cad_filt_numero"
        )

    # Apply all filters
    filtered_pieces = registered_pieces
    if filt_text.strip():
        q = filt_text.strip().lower()
        filtered_pieces = [p for p in filtered_pieces
                           if q in p["nombre_sku"].lower()
                           or q in p["numero_pieza"].lower()]
    if filt_material != "Todos":
        filtered_pieces = [p for p in filtered_pieces if p["material"] == filt_material]
    if filt_finish != "Todos":
        filtered_pieces = [p for p in filtered_pieces if p["acabado_estandar"] == filt_finish]
    if filt_version != "Todos":
        filtered_pieces = [p for p in filtered_pieces if p["version"] == filt_version]
    if filt_revision != "Todos":
        filtered_pieces = [p for p in filtered_pieces if p["revision"] == filt_revision]
    if filt_numero != "Todos":
        filtered_pieces = [p for p in filtered_pieces if p["numero_pieza"] == filt_numero]

    # Match counter badge
    n = len(filtered_pieces)
    badge_color = "#16a34a" if n > 0 else "#dc2626"
    st.markdown(
        f'<div style="margin-bottom:.5rem;">'
        f'<span style="background:{badge_color};color:#fff;font-weight:bold;'
        f'font-size:.85rem;padding:3px 12px;border-radius:20px;">'
        f'{"✅" if n>0 else "❌"} {n} pieza{"s" if n!=1 else ""} encontrada{"s" if n!=1 else ""}'
        f'</span></div>',
        unsafe_allow_html=True
    )

    # Dropdown with filtered results
    piece_options = ["-- Cargar Archivo Manual --"] + [p["nombre_sku"] for p in filtered_pieces]
    
    # Ensure current selection in session state is valid for new options list
    if "cad_piece_select" in st.session_state:
        if st.session_state["cad_piece_select"] not in piece_options:
            st.session_state["cad_piece_select"] = piece_options[0]

    selected_option = st.selectbox(
        "Seleccione la pieza a visualizar:",
        piece_options,
        key="cad_piece_select"
    )

    uploaded_step = None
    selected_piece = None

    if selected_option == "-- Cargar Archivo Manual --":
        uploaded_step = st.file_uploader(
            "Cargar archivo CAD 3D de la pieza (.STEP, .STL)",
            type=["step", "stp", "stl"]
        )
    else:
        selected_piece = next(
            (p for p in filtered_pieces if p["nombre_sku"] == selected_option), None
        )
        # Show piece info card
        if selected_piece:
            sku = selected_piece["nombre_sku"]
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; justify-content: space-between; 
                            background-color: #F8F9FA; border: 1px solid #D2D3D5; border-radius: 6px; 
                            padding: 0.5rem 1rem; margin-bottom: 0.8rem; font-family: 'Questrial', sans-serif;">
                    <span style="font-family: 'Montserrat', sans-serif; font-weight: bold; font-size: 1.1rem; color: #111111;">
                        {sku}
                    </span>
                    <button onclick="navigator.clipboard.writeText('{sku}').then(() => {{
                        const btn = document.getElementById('copy-btn-cad');
                        btn.innerHTML = '✅ Copiado!';
                        btn.style.backgroundColor = '#16a34a';
                        setTimeout(() => {{
                            btn.innerHTML = '📋 Copiar SKU';
                            btn.style.backgroundColor = '#EC2024';
                        }}, 2000);
                    }})" id="copy-btn-cad" style="
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
            st.markdown(
                f"""<div style="background:#f0f9ff;border:1px solid #bae6fd;
                    border-radius:8px;padding:.8rem 1.2rem;margin:.5rem 0;
                    display:flex;flex-wrap:wrap;gap:1.5rem;font-size:.9rem;">
                  <span>📌 <b>No. Pieza:</b> {selected_piece['numero_pieza']}</span>
                  <span>🧱 <b>Material:</b> {selected_piece['material']}</span>
                  <span>📏 <b>Espesor:</b> {selected_piece['espesor_materia_prima']:.4f} in</span>
                  <span>📐 <b>Largo:</b> {selected_piece['largo_materia_prima']:.3f} in</span>
                  <span>↔️ <b>Ancho:</b> {selected_piece['ancho_materia_prima']:.3f} in</span>
                  <span>🎨 <b>Acabado:</b> {selected_piece['acabado_estandar']}</span>
                  <span>🔖 <b>Factor K:</b> {selected_piece['factor_k']}</span>
                  <span>📋 <b>Versión:</b> {selected_piece['version']}-{selected_piece['revision']}</span>
                </div>""",
                unsafe_allow_html=True
            )

    st.markdown("---")
    st.markdown("#### 📐 Vista Interactiva 3D (WebGL)")

    
    # Setup dimension values based on selected option
    largo_val = 19.000
    ancho_val = 3.527
    espesor_val = 0.060
    material_val = "16ga"
    pieza_id_str = "END FILLER (12-A-6004-01)"
    sku_for_overlay = "Manual"
    
    # Navigation logic calculations (placed early so html_code can interpolate them)
    only_pieces = [p["nombre_sku"] for p in filtered_pieces]
    prev_disabled = True
    next_disabled = True
    prev_target = None
    next_target = None
    middle_text = ""
    
    if len(only_pieces) > 0:
        if selected_piece:
            current_idx = only_pieces.index(selected_piece["nombre_sku"])
            prev_disabled = current_idx <= 0
            next_disabled = current_idx >= len(only_pieces) - 1
            middle_text = f"Pieza {current_idx + 1} de {len(only_pieces)}"
            prev_target = only_pieces[current_idx - 1] if not prev_disabled else None
            next_target = only_pieces[current_idx + 1] if not next_disabled else None
        else:
            prev_disabled = True
            next_disabled = False
            middle_text = f"Filtro: {len(only_pieces)} pieza{'s' if len(only_pieces) != 1 else ''}"
            prev_target = None
            next_target = only_pieces[0]

    prev_disabled_attr = "disabled" if prev_disabled else ""
    next_disabled_attr = "disabled" if next_disabled else ""
    
    step_units = "in"
    stl_data_b64 = ""
    step_data_b64 = ""
    file_type = "mock"
    
    if selected_piece:
        largo_val = selected_piece["largo_materia_prima"]
        ancho_val = selected_piece["ancho_materia_prima"]
        espesor_val = selected_piece["espesor_materia_prima"]
        material_val = selected_piece["material"]
        pieza_id_str = f"{selected_piece['numero_pieza']} ({selected_piece['nombre_sku'].split('(')[0].strip()})"
        sku_for_overlay = selected_piece["nombre_sku"].replace('"', '\\"').replace("'", "\\'")
        
        # Check if physical step/stl file was uploaded and exists
        step_path = selected_piece["archivo_step"]
        if step_path and os.path.exists(step_path):
            file_ext = os.path.splitext(step_path)[1].lower()
            if file_ext == ".stl":
                with open(step_path, "rb") as f:
                    file_bytes = f.read()
                stl_data_b64 = base64.b64encode(file_bytes).decode('utf-8')
                file_type = "stl"
                st.success(f"✅ Cargado modelo STL registrado: `{os.path.basename(step_path)}`")
            elif file_ext in [".step", ".stp"]:
                with open(step_path, "rb") as f:
                    file_bytes = f.read()
                step_data_b64 = base64.b64encode(file_bytes).decode('utf-8')
                file_type = "step"
                step_units = detect_step_units(file_bytes)
                st.success(f"✅ Cargado modelo STEP registrado: `{os.path.basename(step_path)}` ({step_units})")
        else:
            file_type = "mock"
            st.info("💡 Renderizando malla dinámica en base a parámetros registrados (No se encontró archivo STEP/STL físico)")
            
    elif uploaded_step:
        file_ext = os.path.splitext(uploaded_step.name)[1].lower()
        sku_for_overlay = uploaded_step.name.replace('"', '\\"').replace("'", "\\'")
        if file_ext == ".stl":
            file_bytes = uploaded_step.read()
            stl_data_b64 = base64.b64encode(file_bytes).decode('utf-8')
            file_type = "stl"
            pieza_id_str = uploaded_step.name
            st.success(f"✅ Archivo '{uploaded_step.name}' cargado con éxito. Procesando geometría...")
        elif file_ext in [".step", ".stp"]:
            file_bytes = uploaded_step.read()
            step_data_b64 = base64.b64encode(file_bytes).decode('utf-8')
            file_type = "step"
            pieza_id_str = uploaded_step.name
            step_units = detect_step_units(file_bytes)
            st.success(f"✅ Archivo STEP '{uploaded_step.name}' cargado con éxito ({step_units}). Procesando geometría...")
            
    # Three.js embed HTML with dynamic coordinates and overlay
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ margin: 0; overflow: hidden; background-color: #e2e8f0; font-family: sans-serif; }}
            #canvas-container {{ width: 100%; height: 500px; position: relative; }}
            .dim-label {{
                background: rgba(0, 86, 179, 0.88);
                color: #fff;
                font-size: 22px;
                font-weight: bold;
                font-family: 'Courier New', monospace;
                padding: 4px 10px;
                border-radius: 3px;
                border: 1px solid #0369a1;
                white-space: nowrap;
                pointer-events: none;
                user-select: none;
            }}
            #info-overlay {{
                position: absolute;
                top: 10px;
                left: 10px;
                color: #f8fafc;
                background: rgba(15, 23, 42, 0.8);
                padding: 10px;
                border-radius: 6px;
                font-size: 12px;
                border: 1px solid #334155;
                pointer-events: none;
                z-index: 100;
            }}
            .dimension-label {{
                font-weight: bold;
                color: #38bdf8;
            }}
            #toggle-dim-btn {{
                position: absolute;
                top: 10px;
                right: 10px;
                z-index: 200;
                background: rgba(0, 86, 179, 0.90);
                color: #fff;
                border: 1px solid #0369a1;
                border-radius: 5px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: bold;
                font-family: sans-serif;
                cursor: pointer;
                transition: background 0.2s;
                user-select: none;
            }}
            #toggle-dim-btn:hover {{
                background: rgba(0, 56, 120, 0.95);
            }}
            #toggle-grid-btn {{
                position: absolute;
                top: 44px;
                right: 10px;
                z-index: 200;
            }}
            #fullscreen-btn {{
                position: absolute;
                top: 78px;
                right: 10px;
                z-index: 200;
                background: rgba(0, 86, 179, 0.90);
                color: #fff;
                border: 1px solid #0369a1;
                border-radius: 5px;
                padding: 5px 12px;
                font-weight: bold;
                font-family: sans-serif;
                cursor: pointer;
                transition: background 0.2s;
                user-select: none;
            }}
            #fullscreen-btn:hover {{
                background: rgba(0, 56, 120, 0.95);
            }}
            #sku-overlay-btn {{
                position: absolute;
                bottom: 15px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 200;
                background: #EC2024 !important; /* Corporate Red */
                color: #fff !important;
                border: 2px solid #b30000 !important;
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 20px;
                font-weight: bold;
                font-family: sans-serif;
                cursor: pointer;
                transition: background 0.2s, transform 0.2s;
                user-select: none;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }}
            #sku-overlay-btn:hover {{
                background: #b30000 !important;
                transform: translateX(-50%) scale(1.03);
            }}
            #sku-overlay-btn:active {{
                transform: translateX(-50%) scale(0.97);
            }}
            #prev-overlay-btn {{
                position: absolute;
                bottom: 15px;
                left: 15px;
                z-index: 200;
                background: #EC2024 !important; /* Corporate Red */
                color: #fff !important;
                border: 1px solid #b30000 !important;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
                font-family: sans-serif;
                cursor: pointer;
                transition: background 0.2s;
                user-select: none;
                box-shadow: 0 4px 10px rgba(0,0,0,0.25);
            }}
            #prev-overlay-btn:hover {{
                background: #b30000 !important;
            }}
            #prev-overlay-btn:disabled {{
                background: rgba(80, 80, 80, 0.5) !important;
                border-color: rgba(80, 80, 80, 0.5) !important;
                color: #aaa !important;
                cursor: not-allowed;
                box-shadow: none;
            }}
            #next-overlay-btn {{
                position: absolute;
                bottom: 15px;
                right: 15px;
                z-index: 200;
                background: #EC2024 !important; /* Corporate Red */
                color: #fff !important;
                border: 1px solid #b30000 !important;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
                font-family: sans-serif;
                cursor: pointer;
                transition: background 0.2s;
                user-select: none;
                box-shadow: 0 4px 10px rgba(0,0,0,0.25);
            }}
            #next-overlay-btn:hover {{
                background: #b30000 !important;
            }}
            #next-overlay-btn:disabled {{
                background: rgba(80, 80, 80, 0.5) !important;
                border-color: rgba(80, 80, 80, 0.5) !important;
                color: #aaa !important;
                cursor: not-allowed;
                box-shadow: none;
            }}
            :fullscreen #canvas-container,
            :-webkit-full-screen #canvas-container,
            body.parent-fullscreen,
            body.parent-fullscreen #canvas-container {{
                width: 100vw !important;
                height: 100vh !important;
                margin: 0 !important;
                padding: 0 !important;
                overflow: hidden !important;
            }}
            #style-selector {{
                position: absolute;
                top: 112px;
                right: 10px;
                z-index: 200;
                background: rgba(0, 86, 179, 0.90);
                color: #fff;
                border: 1px solid #0369a1;
                border-radius: 5px;
                padding: 4px;
                font-size: 12px;
                font-weight: bold;
                font-family: sans-serif;
                cursor: pointer;
                outline: none;
            }}
            #style-selector option {{
                background: #0f172a;
                color: #fff;
            }}
            #measure-btn {{
                position: absolute;
                top: 146px;
                right: 10px;
                z-index: 200;
                background: rgba(5, 150, 105, 0.92);
                color: #fff;
                border: 1px solid #059669;
                border-radius: 5px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: bold;
                font-family: sans-serif;
                cursor: pointer;
                transition: background 0.2s;
                user-select: none;
            }}
            .view-btn {{
                background: rgba(0, 86, 179, 0.90);
                color: #fff;
                border: 1px solid #0369a1;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: bold;
                font-family: sans-serif;
                cursor: pointer;
                transition: background 0.2s;
                user-select: none;
            }}
            #view-iso-btn {{
                background: #16a34a !important;
                color: #fff !important;
                border: 1px solid #15803d !important;
            }}
            #view-iso-btn:hover {{
                background: #15803d !important;
            }}
            #view-front-btn {{
                background: #ffffff !important;
                color: #1e293b !important;
                border: 1px solid #cbd5e1 !important;
            }}
            #view-front-btn:hover {{
                background: #f1f5f9 !important;
            }}
            #view-top-btn {{
                background: #ef4444 !important;
                color: #fff !important;
                border: 1px solid #dc2626 !important;
            }}
            #view-top-btn:hover {{
                background: #dc2626 !important;
            }}
            #view-side-btn {{
                background: #16a34a !important;
                color: #fff !important;
                border: 1px solid #15803d !important;
            }}
            #view-side-btn:hover {{
                background: #15803d !important;
            }}
            #zoom-all-btn {{
                background: #0284c7 !important;
                color: #fff !important;
                border: 1px solid #0369a1 !important;
                margin-top: 2px;
            }}
            #zoom-all-btn:hover {{
                background: #0369a1 !important;
            }}
            .view-btn:hover {{
                background: rgba(0, 56, 120, 0.95);
            }}
            #view-btn-container {{
                position: absolute;
                top: 165px;
                left: 10px;
                z-index: 200;
                display: grid;
                grid-template-columns: repeat(4, auto);
                gap: 5px;
            }}
        </style>
        <!-- Load Three.js and OrbitControls -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/STLLoader.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/renderers/CSS2DRenderer.js"></script>
    </head>
    <body>
        <div id="info-overlay">
            <div><strong>Pieza:</strong> {pieza_id_str}</div>
            <div><span class="dimension-label">Largo Nominal:</span> {largo_val:.3f} in</div>
            <div><span class="dimension-label">Ancho Nominal:</span> {ancho_val:.3f} in</div>
            <div><span class="dimension-label">Espesor Chapa:</span> {espesor_val:.4f} in ({material_val})</div>
            <div><span class="dimension-label">Ángulo de Doblez:</span> 90° (Cotas A-J)</div>
            <div style="margin-top: 5px; font-size:10px; color:#94a3b8;" id="control-hint">* Click Izq + Arrastrar para rotar, Click Der para desplazar, Rueda para Zoom</div>
        </div>
        <div id="view-btn-container">
            <button class="view-btn" id="view-iso-btn" title="Vista Isométrica" style="grid-column: 1; grid-row: 1;">👁️ Iso</button>
            <button class="view-btn" id="view-front-btn" title="Vista Frontal (Eje Z)" style="grid-column: 2; grid-row: 1;">Frontal</button>
            <button class="view-btn" id="view-top-btn" title="Vista Superior (Eje Y)" style="grid-column: 3; grid-row: 1;">Superior</button>
            <button class="view-btn" id="view-side-btn" title="Vista Lateral (Eje X)" style="grid-column: 4; grid-row: 1;">Lateral</button>
            <button class="view-btn" id="zoom-all-btn" title="Extender Imagen (Zoom All)" style="grid-column: 1; grid-row: 2;">🔍 Zoom All</button>
        </div>
        <button id="prev-overlay-btn" {prev_disabled_attr} title="Pieza Anterior">⬅️ Pieza Anterior</button>
        <button id="toggle-dim-btn" title="Mostrar/ocultar cotas dimensionales">📐 Ocultar Cotas</button>
        <button id="toggle-grid-btn" title="Mostrar/ocultar malla de referencia" style="background: rgba(80, 80, 80, 0.85);">⋯ Mostrar Malla</button>
        <button id="fullscreen-btn" title="Maximizar a pantalla completa">🖥️ Pantalla Completa</button>
        <button id="sku-overlay-btn" title="Copiar SKU al portapapeles">📋 SKU: {sku_for_overlay}</button>
        <button id="next-overlay-btn" {next_disabled_attr} title="Siguiente Pieza">Siguiente Pieza ➡️</button>
        <select id="style-selector" title="Estilo Visual">
            <option value="shaded_edges">Sombreado con Bordes</option>
            <option value="wireframe">Estructura Alámbrica</option>
            <option value="monochrome" selected>Monocromático Técnico</option>
        </select>
        <div id="canvas-container"></div>
        
        <script>
            // Set up scene, camera, renderer
            const container = document.getElementById('canvas-container');
            
            // Check if Three.js is loaded successfully
            if (typeof THREE === 'undefined') {{
                const errDiv = document.createElement('div');
                errDiv.style.color = '#ef4444';
                errDiv.style.padding = '25px';
                errDiv.style.fontWeight = 'bold';
                errDiv.style.background = '#0f172a';
                errDiv.style.borderRadius = '8px';
                errDiv.style.margin = '20px';
                errDiv.innerHTML = '❌ Error: No se pudo cargar la librería Three.js de 3D. Verifique su conexión de red o configuraciones de proxy/CORS en el navegador.';
                container.appendChild(errDiv);
            }}
            
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0xe2e8f0);
            
            // Grid helper
            let gridHelper = new THREE.GridHelper(30, 30, 0x0056b3, 0x94a3b8);
            gridHelper.position.y = -2;
            gridHelper.visible = false; // Start hidden
            scene.add(gridHelper);
            
            // Determine width dynamically, falling back to window.innerWidth or 800 if clientWidth is 0 (occurs on loading inside Streamlit iframe)
            const width = container.clientWidth || window.innerWidth || 800;
            
            const camera = new THREE.PerspectiveCamera(45, width / 500, 0.1, 1000);
            camera.position.set(20, 15, 25);
            
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(width, 500);
            renderer.shadowMap.enabled = true;
            renderer.outputEncoding = THREE.sRGBEncoding;
            renderer.physicallyCorrectLights = true;
            container.appendChild(renderer.domElement);
            
            // CSS2D renderer for dimension labels
            let labelRenderer = null;
            if (typeof THREE.CSS2DRenderer !== 'undefined') {{
                labelRenderer = new THREE.CSS2DRenderer();
                labelRenderer.setSize(width, 500);
                labelRenderer.domElement.style.position = 'absolute';
                labelRenderer.domElement.style.top = '0';
                labelRenderer.domElement.style.left = '0';
                labelRenderer.domElement.style.pointerEvents = 'none';
                container.appendChild(labelRenderer.domElement);
            }}
            
            // Orbit Controls
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            
            const fileType = "{file_type}";
            if (fileType === "mock") {{
                controls.autoRotate = true;
                controls.autoRotateSpeed = 1.2;
            }}
            
            // Lighting
            const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 1.5);
            hemiLight.position.set(0, 20, 0);
            scene.add(hemiLight);
            
            const dirLight1 = new THREE.DirectionalLight(0xffffff, 2.0);
            dirLight1.position.set(20, 40, 20);
            scene.add(dirLight1);
            
            const dirLight2 = new THREE.DirectionalLight(0x0056b3, 0.8);
            dirLight2.position.set(-20, 20, -20);
            scene.add(dirLight2);
            
            // Material - Light Blue Metallic look
            const material = new THREE.MeshStandardMaterial({{
                color: 0x38bdf8,
                metalness: 0.6,
                roughness: 0.2,
                side: THREE.DoubleSide
            }});
            
            let currentMesh;
            let dimGroup = null; // module-level so toggle button can reach it
            
            let currentViewName = 'iso';

            function fitCamera(viewName) {{
                if (!currentMesh) return;
                
                currentViewName = viewName || currentViewName;
                
                // Force update matrix world of the entire scene so Box3 has fresh world matrices
                scene.updateMatrixWorld(true);
                
                const box = new THREE.Box3().setFromObject(currentMesh);
                const center = new THREE.Vector3();
                box.getCenter(center);
                const size = new THREE.Vector3();
                box.getSize(size);
                
                // Safety check: fallback if box is empty or size is invalid (NaN)
                if (isNaN(size.x) || isNaN(size.y) || isNaN(size.z) || (size.x === 0 && size.y === 0 && size.z === 0)) {{
                    size.set(15, 15, 15);
                    center.set(0, 0, 0);
                }}
                
                const maxDim = Math.max(size.x, size.y, size.z) || 10;
                
                controls.target.copy(center);
                
                const fovRad = (camera.fov * Math.PI) / 180;
                const aspect = camera.aspect || (window.innerWidth / window.innerHeight) || 1.6;
                
                // Extremely robust radius calculation: half of box diagonal length
                const radius = (size.length() * 0.5) || (maxDim * 0.5) || 5;
                
                let dist = radius / Math.sin(fovRad / 2);
                if (aspect < 1) {{
                    dist = dist / aspect;
                }}
                
                dist = dist * 1.15;
                
                camera.near = Math.min(0.1, dist / 10);
                camera.far = Math.max(1000, dist * 10);
                camera.updateProjectionMatrix();
                
                camera.up.set(0, 1, 0);
                
                if (viewName === 'top') {{
                    camera.position.set(center.x, center.y + dist, center.z + 0.0001);
                    camera.up.set(0, 0, -1);
                }} else if (viewName === 'front') {{
                    camera.position.set(center.x, center.y, center.z + dist);
                }} else if (viewName === 'side') {{
                    camera.position.set(center.x + dist, center.y, center.z);
                }} else {{
                    const dir = new THREE.Vector3(1, 0.8, 1).normalize();
                    camera.position.copy(center).addScaledVector(dir, dist);
                }}
                
                controls.update();
            }}

            function fitCameraKeepOrientation() {{
                if (!currentMesh) return;
                
                // Force update matrix world of the entire scene
                scene.updateMatrixWorld(true);
                
                const box = new THREE.Box3().setFromObject(currentMesh);
                const center = new THREE.Vector3();
                box.getCenter(center);
                const size = new THREE.Vector3();
                box.getSize(size);
                
                // Safety check: fallback if box is empty or size is invalid (NaN)
                if (isNaN(size.x) || isNaN(size.y) || isNaN(size.z) || (size.x === 0 && size.y === 0 && size.z === 0)) {{
                    size.set(15, 15, 15);
                    center.set(0, 0, 0);
                }}
                
                const maxDim = Math.max(size.x, size.y, size.z) || 10;
                const fovRad = (camera.fov * Math.PI) / 180;
                const aspect = camera.aspect || (window.innerWidth / window.innerHeight) || 1.6;
                
                const radius = (size.length() * 0.5) || (maxDim * 0.5) || 5;
                
                let dist = radius / Math.sin(fovRad / 2);
                if (aspect < 1) {{
                    dist = dist / aspect;
                }}
                dist = dist * 1.15;
                
                const dir = new THREE.Vector3().subVectors(camera.position, controls.target);
                if (dir.lengthSq() === 0 || isNaN(dir.x) || isNaN(dir.y) || isNaN(dir.z)) {{
                    dir.set(1, 0.8, 1);
                }}
                dir.normalize();
                
                camera.position.copy(center).addScaledVector(dir, dist);
                
                camera.near = Math.min(0.1, dist / 10);
                camera.far = Math.max(1000, dist * 10);
                camera.updateProjectionMatrix();
                
                controls.target.copy(center);
                controls.update();
            }}
            
            // State for styles
            window.allMeshes = [];
            window.allEdgeLines = [];
            window.originalMaterials = new Map();
            const monochromeMaterial = new THREE.MeshStandardMaterial({{
                color: 0xdddddd, roughness: 0.5, metalness: 0.2, side: THREE.DoubleSide
            }});
            
            const stlDataB64 = "{stl_data_b64}";
            const stepDataB64 = "{step_data_b64}";
            const stepUnits = "{step_units}";
            const largo = parseFloat("{largo_val}");
            const ancho = parseFloat("{ancho_val}");
            const espesor = parseFloat("{espesor_val}");
            
            if (fileType === "stl" && stlDataB64 !== "") {{
                // Parse and load uploaded STL file
                try {{
                    const binaryString = atob(stlDataB64);
                    const bytes = new Uint8Array(binaryString.length);
                    for (let i = 0; i < binaryString.length; i++) {{
                        bytes[i] = binaryString.charCodeAt(i);
                    }}
                    
                    const loader = new THREE.STLLoader();
                    const geometry = loader.parse(bytes.buffer);
                    
                    geometry.center();
                    currentMesh = new THREE.Mesh(geometry, material);
                    
                    // Rotate STL to fit view better
                    currentMesh.rotation.x = -Math.PI / 2;
                    scene.add(currentMesh);
                    
                    window.allMeshes.push(currentMesh);
                    window.originalMaterials.set(currentMesh.uuid, material);
                    
                    // Create edges for STL
                    const edges = new THREE.EdgesGeometry(geometry, 20);
                    const lineMat = new THREE.LineBasicMaterial({{ color: 0x000000, linewidth: 2 }});
                    const lineSeg = new THREE.LineSegments(edges, lineMat);
                    lineSeg.rotation.x = -Math.PI / 2;
                    scene.add(lineSeg);
                    window.allEdgeLines.push(lineSeg);
                    
                    // Adjust camera to fit mesh size
                    fitCamera('iso');
                    
                    document.getElementById('info-overlay').innerHTML += "<div><span class='dimension-label'>Modo:</span> Malla Real STL</div>";
                    
                    // Draw COMSOL-style dimension annotations
                    drawDimensionAnnotations(currentMesh);
                    
                    // Aplicar estilo inicial
                    aplicarEstilo('monochrome');
                }} catch (e) {{
                    console.error("Error loading STL: ", e);
                    drawMockPiece();
                }}
            }} else if (fileType === "step" && stepDataB64 !== "") {{
                // Load and parse STEP file using occt-import-js
                document.getElementById('info-overlay').innerHTML += "<div id='loading-status' style='color:#facc15;font-weight:bold;margin-top:5px;'>Cargando motor de triangulación CAD (WASM)...</div>";
                
                // Fetch the WASM binary ourselves to avoid Emscripten same-origin fetch restrictions
                fetch("https://unpkg.com/occt-import-js@0.0.12/dist/occt-import-js.wasm")
                    .then(response => {{
                        if (!response.ok) {{
                            throw new Error("HTTP error, status = " + response.status);
                        }}
                        return response.arrayBuffer();
                    }})
                    .then(wasmBuffer => {{
                        const Module = {{
                            wasmBinary: wasmBuffer
                        }};
                        
                        const lStatus = document.getElementById('loading-status');
                        if (lStatus) lStatus.innerText = "Cargando módulo ES...";
                        
                        return import("https://esm.sh/occt-import-js@0.0.12").then((m) => {{
                            if (lStatus) lStatus.innerText = "Triangulando archivo STEP real...";
                            const factory = m.default;
                            return factory(Module);
                        }});
                    }})
                    .then((occt) => {{
                        try {{
                            const binaryString = atob(stepDataB64);
                            const bytes = new Uint8Array(binaryString.length);
                            for (let i = 0; i < binaryString.length; i++) {{
                                bytes[i] = binaryString.charCodeAt(i);
                            }}
                            
                            const result = occt.ReadStepFile(bytes);
                            
                            const lStatus = document.getElementById('loading-status');
                            if (lStatus) lStatus.remove();
                            
                            if (result.success && result.meshes && result.meshes.length > 0) {{
                                const stepGroup = new THREE.Group();
                                
                                result.meshes.forEach((mesh) => {{
                                    const geometry = new THREE.BufferGeometry();
                                    
                                    const vertices = new Float32Array(mesh.attributes.position.array);
                                    geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
                                    
                                    if (mesh.attributes.normal && mesh.attributes.normal.array) {{
                                        const normals = new Float32Array(mesh.attributes.normal.array);
                                        geometry.setAttribute('normal', new THREE.BufferAttribute(normals, 3));
                                    }} else {{
                                        geometry.computeVertexNormals();
                                    }}
                                    
                                    if (mesh.index && mesh.index.array) {{
                                        const indices = new Uint32Array(mesh.index.array);
                                        geometry.setIndex(new THREE.BufferAttribute(indices, 1));
                                    }}
                                    
                                    let meshColor = 0x38bdf8; // Default to Light Blue
                                    if (mesh.color && mesh.color.length === 3) {{
                                        const r = Math.round(mesh.color[0] * 255);
                                        const g = Math.round(mesh.color[1] * 255);
                                        const b = Math.round(mesh.color[2] * 255);
                                        // If it is not a default grey, use the CAD color, otherwise use light blue
                                        const isGrey = Math.abs(r - g) < 10 && Math.abs(g - b) < 10;
                                        if (!isGrey) {{
                                            meshColor = (r << 16) + (g << 8) + b;
                                        }}
                                    }}
                                    
                                    const stepMaterial = new THREE.MeshStandardMaterial({{
                                        color: meshColor,
                                        metalness: 0.6,
                                        roughness: 0.2,
                                        side: THREE.DoubleSide
                                    }});
                                    
                                    const threeMesh = new THREE.Mesh(geometry, stepMaterial);
                                    stepGroup.add(threeMesh);
                                    
                                    // Guardar info para los estilos
                                    window.allMeshes.push(threeMesh);
                                    window.originalMaterials.set(threeMesh.uuid, stepMaterial);
                                    
                                    // Crear bordes
                                    const edges = new THREE.EdgesGeometry(geometry, 1);
                                    const lineMat = new THREE.LineBasicMaterial({{ color: 0x000000, linewidth: 2 }});
                                    const lineSeg = new THREE.LineSegments(edges, lineMat);
                                    stepGroup.add(lineSeg);
                                    window.allEdgeLines.push(lineSeg);
                                }});
                                
                                // If origin units is mm, scale down to inches
                                if (stepUnits === "mm") {{
                                    stepGroup.scale.set(1/25.4, 1/25.4, 1/25.4);
                                }}
                                
                                // Force matrix world update so that bounding box calculations use the correct scale
                                stepGroup.updateMatrixWorld(true);
                                
                                // Center group geometry
                                const box = new THREE.Box3().setFromObject(stepGroup);
                                const center = new THREE.Vector3();
                                box.getCenter(center);
                                stepGroup.position.sub(center);
                                
                                // Force matrix world update again after repositioning
                                stepGroup.updateMatrixWorld(true);
                                
                                scene.add(stepGroup);
                                currentMesh = stepGroup;
                                
                                // Dynamic zoom fit
                                fitCamera('iso');
                                
                                const unitText = "in (Convertido desde mm)";
                                document.getElementById('info-overlay').innerHTML += "<div><span class='dimension-label'>Modo:</span> Visualización Real CAD (.STEP)</div>";
                                document.getElementById('info-overlay').innerHTML += "<div><span class='dimension-label'>Unidades:</span> " + unitText + "</div>";
                                
                                // Draw COMSOL-style dimension annotations
                                drawDimensionAnnotations(stepGroup);
                                
                                // Aplicar estilo inicial
                                aplicarEstilo('monochrome');
                            }} else {{
                                const errMsg = (result && result.error) || "No se encontraron mallas 3D en el archivo STEP.";
                                console.error("STEP parsing succeeded but no meshes returned: ", errMsg);
                                const lStatus = document.getElementById('loading-status');
                                if (lStatus) {{
                                    lStatus.style.color = '#facc15';
                                    lStatus.innerText = "Advertencia STEP: " + errMsg;
                                }} else {{
                                    document.getElementById('info-overlay').innerHTML += "<div style='color:#facc15;font-weight:bold;margin-top:5px;'>Advertencia: " + errMsg + "</div>";
                                }}
                                drawMockPiece();
                            }}
                        }} catch (err) {{
                            console.error("Error processing STEP: ", err);
                            const lStatus = document.getElementById('loading-status');
                            if (lStatus) {{
                                lStatus.style.color = '#ef4444';
                                lStatus.innerText = "Error procesando STEP: " + err.message;
                            }} else {{
                                document.getElementById('info-overlay').innerHTML += "<div style='color:#ef4444;font-weight:bold;margin-top:5px;'>Error procesando STEP: " + err.message + "</div>";
                            }}
                            drawMockPiece();
                        }}
                    }})
                    .catch((err) => {{
                        console.error("Failed to load/parse WASM: ", err);
                        const lStatus = document.getElementById('loading-status');
                        if (lStatus) {{
                            lStatus.style.color = '#ef4444';
                            lStatus.innerText = "Error de carga/triangulación: " + err.message;
                        }} else {{
                            document.getElementById('info-overlay').innerHTML += "<div style='color:#ef4444;font-weight:bold;margin-top:5px;'>Error de carga: " + err.message + "</div>";
                        }}
                        drawMockPiece();
                    }});
            }} else {{
                // Render Mock Sheet Metal Piece with dynamic parameters
                drawMockPiece();
            }}
            
            function drawMockPiece() {{
                const pieceGroup = new THREE.Group();
                
                // Base sheet: largo x espesor x ancho
                const baseGeom = new THREE.BoxGeometry(largo, espesor, ancho);
                const baseMesh = new THREE.Mesh(baseGeom, material);
                pieceGroup.add(baseMesh);
                window.allMeshes.push(baseMesh);
                window.originalMaterials.set(baseMesh.uuid, material);
                
                // Edges for baseMesh
                const baseEdges = new THREE.EdgesGeometry(baseGeom);
                const baseLine = new THREE.LineSegments(baseEdges, new THREE.LineBasicMaterial({{ color: 0x000000, linewidth: 2 }}));
                pieceGroup.add(baseLine);
                window.allEdgeLines.push(baseLine);
                
                // Folded flanges (e.g. 90 degree flanges at the borders)
                const flangeGeom1 = new THREE.BoxGeometry(largo, 1.2, espesor);
                const flange1 = new THREE.Mesh(flangeGeom1, material);
                flange1.position.set(0, 0.6, ancho / 2); // positioned at the edge
                pieceGroup.add(flange1);
                window.allMeshes.push(flange1);
                window.originalMaterials.set(flange1.uuid, material);
                
                // Edges for flange1
                const flange1Edges = new THREE.EdgesGeometry(flangeGeom1);
                const flange1Line = new THREE.LineSegments(flange1Edges, new THREE.LineBasicMaterial({{ color: 0x000000, linewidth: 2 }}));
                flange1Line.position.copy(flange1.position);
                pieceGroup.add(flange1Line);
                window.allEdgeLines.push(flange1Line);
                
                const flangeGeom2 = new THREE.BoxGeometry(largo, 0.8, espesor);
                const flange2 = new THREE.Mesh(flangeGeom2, material);
                flange2.position.set(0, 0.4, -ancho / 2);
                pieceGroup.add(flange2);
                window.allMeshes.push(flange2);
                window.originalMaterials.set(flange2.uuid, material);
                
                // Edges for flange2
                const flange2Edges = new THREE.EdgesGeometry(flangeGeom2);
                const flange2Line = new THREE.LineSegments(flange2Edges, new THREE.LineBasicMaterial({{ color: 0x000000, linewidth: 2 }}));
                flange2Line.position.copy(flange2.position);
                pieceGroup.add(flange2Line);
                window.allEdgeLines.push(flange2Line);
                
                // Holes simulation: create cylinder punch holes
                const holeGeom = new THREE.CylinderGeometry(0.156, 0.156, espesor + 0.02, 32);
                const holeMat = new THREE.MeshBasicMaterial({{ color: 0x0f172a }});
                
                const hole1 = new THREE.Mesh(holeGeom, holeMat);
                hole1.position.set(-largo * 0.4, espesor / 2, 0);
                pieceGroup.add(hole1);
                
                const hole2 = new THREE.Mesh(holeGeom, holeMat);
                hole2.position.set(0, espesor / 2, 0);
                pieceGroup.add(hole2);
                
                const hole3 = new THREE.Mesh(holeGeom, holeMat);
                hole3.position.set(largo * 0.4, espesor / 2, 0);
                pieceGroup.add(hole3);
                
                scene.add(pieceGroup);
                currentMesh = pieceGroup;
                
                document.getElementById('info-overlay').innerHTML += "<div><span class='dimension-label'>Modo:</span> Malla Paramétrica Dinámica</div>";
                
                // Draw COMSOL-style dimension annotations
                drawDimensionAnnotations(pieceGroup);
                
                // Aplicar estilo inicial
                aplicarEstilo('monochrome');
                if (document.getElementById('style-selector')) document.getElementById('style-selector').value = 'monochrome';
                fitCamera('iso');
            }}
            
            // Animation Loop
            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
                if (labelRenderer) labelRenderer.render(scene, camera);
            }}
            
            animate();
            
            // Handle window resize
            window.addEventListener('resize', () => {{
                handleFsChange(); // Sync fullscreen state classes first
                const w = container.clientWidth || window.innerWidth || 800;
                const h = container.clientHeight || window.innerHeight || 500;
                camera.aspect = w / h;
                camera.updateProjectionMatrix();
                renderer.setSize(w, h);
                if (labelRenderer) labelRenderer.setSize(w, h);
                fitCameraKeepOrientation();
            }});
            
            // Toggle dimension annotations button
            const toggleBtn = document.getElementById('toggle-dim-btn');
            if (toggleBtn) {{
                toggleBtn.addEventListener('click', () => {{
                    if (!dimGroup) return;
                    dimGroup.visible = !dimGroup.visible;
                    // CSS2DRenderer does not inherit Three.js visibility — toggle DOM element directly
                    if (labelRenderer) {{
                        labelRenderer.domElement.style.display = dimGroup.visible ? '' : 'none';
                    }}
                    toggleBtn.textContent = dimGroup.visible ? '📐 Ocultar Cotas' : '📐 Mostrar Cotas';
                    toggleBtn.style.background = dimGroup.visible
                        ? 'rgba(0, 86, 179, 0.90)'
                        : 'rgba(80, 80, 80, 0.85)';
                }});
            }}
            
            // Style logic
            function aplicarEstilo(modo) {{
                window.allMeshes.forEach(mesh => {{
                    if (modo === 'shaded_edges') {{
                        mesh.material = window.originalMaterials.get(mesh.uuid);
                        mesh.visible = true;
                    }} else if (modo === 'monochrome') {{
                        mesh.material = monochromeMaterial;
                        mesh.visible = true;
                    }} else if (modo === 'wireframe') {{
                        mesh.visible = false;
                    }}
                }});
                window.allEdgeLines.forEach(line => {{
                    line.visible = true; // Siempre mostrar los bordes
                }});
            }}
            
            const styleSelector = document.getElementById('style-selector');
            if (styleSelector) {{
                styleSelector.addEventListener('change', (e) => {{
                    aplicarEstilo(e.target.value);
                }});
            }}

            // Toggle grid button
            const toggleGridBtn = document.getElementById('toggle-grid-btn');
            if (toggleGridBtn) {{
                toggleGridBtn.addEventListener('click', () => {{
                    gridHelper.visible = !gridHelper.visible;
                    toggleGridBtn.textContent = gridHelper.visible ? '⋯ Ocultar Malla' : '⋯ Mostrar Malla';
                    toggleGridBtn.style.background = gridHelper.visible
                        ? 'rgba(0, 86, 179, 0.90)'
                        : 'rgba(80, 80, 80, 0.85)';
                }});
            }}

            // Toggle fullscreen
            const fullscreenBtn = document.getElementById('fullscreen-btn');
            if (fullscreenBtn) {{
                fullscreenBtn.addEventListener('click', () => {{
                    const isFs = !!(
                        document.fullscreenElement ||
                        document.webkitFullscreenElement ||
                        (window.parent && window.parent.document && (window.parent.document.fullscreenElement || window.parent.document.webkitFullscreenElement))
                    );
                    if (!isFs) {{
                        let target = document.documentElement;
                        if (window.parent && window.parent.document && window.frameElement) {{
                            target = window.frameElement.closest('div.element-container') || window.frameElement.parentElement || target;
                        }}
                        const req = target.requestFullscreen || target.webkitRequestFullscreen || target.msRequestFullscreen;
                        if (req) {{
                            req.call(target).catch(err => {{
                                console.error("Fullscreen error: ", err);
                            }});
                        }}
                    }} else {{
                        const doc = (window.parent && window.parent.document) ? window.parent.document : document;
                        const exit = doc.exitFullscreen || doc.webkitExitFullscreen || doc.msExitFullscreen;
                        if (exit) {{
                            exit.call(doc).catch(err => {{
                                console.error("Exit fullscreen error: ", err);
                            }});
                        }}
                    }}
                }});
            }}

            const handleFsChange = () => {{
                try {{
                    if (!document || !document.body) return;
                    const isFs = !!(
                        document.fullscreenElement ||
                        document.webkitFullscreenElement ||
                        (window.parent && window.parent.document && (window.parent.document.fullscreenElement || window.parent.document.webkitFullscreenElement))
                    );
                    const fsBtn = document.getElementById('fullscreen-btn');
                    if (isFs) {{
                        document.body.classList.add('parent-fullscreen');
                        if (fsBtn) fsBtn.textContent = '🗗 Salir Pantalla';
                    }} else {{
                        document.body.classList.remove('parent-fullscreen');
                        if (fsBtn) fsBtn.textContent = '🖥️ Pantalla Completa';
                    }}
                }} catch(e) {{
                    // Context might be partially destroyed during Streamlit reload
                }}
            }};

            // Run once on load to initialize state
            handleFsChange();

            // Listen to fullscreen changes inside our own document
            document.addEventListener('fullscreenchange', () => {{
                handleFsChange();
                window.dispatchEvent(new Event('resize'));
            }});
            document.addEventListener('webkitfullscreenchange', () => {{
                handleFsChange();
                window.dispatchEvent(new Event('resize'));
            }});

            // Register parent document listeners with cleanup to avoid Dead Object errors
            try {{
                if (window.parent && window.parent.document) {{
                    window.parent.document.addEventListener('fullscreenchange', handleFsChange);
                    window.parent.document.addEventListener('webkitfullscreenchange', handleFsChange);
                }}
            }} catch(e) {{
                console.error("Parent fullscreen listener failed: ", e);
            }}

            window.addEventListener('unload', () => {{
                try {{
                    if (window.parent && window.parent.document) {{
                        window.parent.document.removeEventListener('fullscreenchange', handleFsChange);
                        window.parent.document.removeEventListener('webkitfullscreenchange', handleFsChange);
                    }}
                }} catch(e) {{}}
            }});

            // Copy SKU overlay button listener
            const skuBtn = document.getElementById('sku-overlay-btn');
            if (skuBtn) {{
                skuBtn.addEventListener('click', () => {{
                    navigator.clipboard.writeText("{sku_for_overlay}").then(() => {{
                        const origText = skuBtn.textContent;
                        skuBtn.textContent = '✅ Copiado!';
                        skuBtn.style.setProperty('background', 'rgba(22, 163, 74, 0.9)', 'important');
                        setTimeout(() => {{
                            skuBtn.textContent = origText;
                            skuBtn.style.setProperty('background', '#EC2024', 'important');
                        }}, 1500);
                    }});
                }});
            }}

            // Navigation buttons listeners (directly querying parent window document to trigger Streamlit callbacks)
            const prevOverlayBtn = document.getElementById('prev-overlay-btn');
            if (prevOverlayBtn) {{
                prevOverlayBtn.addEventListener('click', () => {{
                    try {{
                        const doc = window.parent.document;
                        const buttons = Array.from(doc.querySelectorAll('button'));
                        const targetBtn = buttons.find(b => b.textContent.toLowerCase().includes('pieza anterior'));
                        if (targetBtn) targetBtn.click();
                    }} catch (err) {{
                        console.error("Navigation error:", err);
                    }}
                }});
            }}

            const nextOverlayBtn = document.getElementById('next-overlay-btn');
            if (nextOverlayBtn) {{
                nextOverlayBtn.addEventListener('click', () => {{
                    try {{
                        const doc = window.parent.document;
                        const buttons = Array.from(doc.querySelectorAll('button'));
                        const targetBtn = buttons.find(b => b.textContent.toLowerCase().includes('siguiente pieza'));
                        if (targetBtn) targetBtn.click();
                    }} catch (err) {{
                        console.error("Navigation error:", err);
                    }}
                }});
            }}

            // View Preset Button Listeners
            function setPresetView(viewName) {{
                fitCamera(viewName);
            }}
            
            const btnIso = document.getElementById('view-iso-btn');
            if (btnIso) btnIso.addEventListener('click', () => setPresetView('iso'));
            
            const btnFront = document.getElementById('view-front-btn');
            if (btnFront) btnFront.addEventListener('click', () => setPresetView('front'));
            
            const btnTop = document.getElementById('view-top-btn');
            if (btnTop) btnTop.addEventListener('click', () => setPresetView('top'));
            
            const btnSide = document.getElementById('view-side-btn');
            if (btnSide) btnSide.addEventListener('click', () => setPresetView('side'));
            
            const btnZoomAll = document.getElementById('zoom-all-btn');
            if (btnZoomAll) btnZoomAll.addEventListener('click', () => fitCameraKeepOrientation());
            
            // ─── COMSOL-style Dimension Annotations ───────────────────────────────────
            // Draws 3 bounding-box dimension lines (X/Y/Z) with arrow cones and 2D labels.
            function drawDimensionAnnotations(object) {{
                const box = new THREE.Box3().setFromObject(object);
                const min = box.min;
                const max = box.max;
                const size = new THREE.Vector3();
                box.getSize(size);
                
                if (size.x === 0 && size.y === 0 && size.z === 0) return;
                
                // Remove any previous annotation group
                if (dimGroup) {{ scene.remove(dimGroup); dimGroup = null; }}
                dimGroup = new THREE.Group();
                scene.add(dimGroup);
                
                const lineMat = new THREE.LineBasicMaterial({{ color: 0x0056b3, linewidth: 2 }});
                const arrowMat = new THREE.MeshBasicMaterial({{ color: 0x0056b3 }});
                const gap = Math.max(size.x, size.y, size.z) * 0.08;
                
                function makeArrow(from, to) {{
                    const dir = new THREE.Vector3().subVectors(to, from).normalize();
                    const len = from.distanceTo(to);
                    const coneH = Math.min(len * 0.12, gap * 0.9);
                    const coneR = coneH * 0.3;
                    const coneGeom = new THREE.ConeGeometry(coneR, coneH, 8);
                    const cone = new THREE.Mesh(coneGeom, arrowMat);
                    cone.position.copy(to);
                    cone.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
                    dimGroup.add(cone);
                    
                    const cone2 = new THREE.Mesh(coneGeom, arrowMat);
                    cone2.position.copy(from);
                    cone2.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().negate());
                    dimGroup.add(cone2);
                    
                    const pts = [from.clone(), to.clone()];
                    const geom = new THREE.BufferGeometry().setFromPoints(pts);
                    const line = new THREE.Line(geom, lineMat);
                    dimGroup.add(line);
                }}
                
                function makeExtLine(a, b) {{
                    const pts = [a.clone(), b.clone()];
                    const mat = new THREE.LineDashedMaterial({{ color: 0x0056b3, dashSize: 0.5, gapSize: 0.3 }});
                    const geom = new THREE.BufferGeometry().setFromPoints(pts);
                    const line = new THREE.Line(geom, mat);
                    line.computeLineDistances();
                    dimGroup.add(line);
                }}
                
                function makeLabel(pos, text) {{
                    if (!labelRenderer) return;
                    const div = document.createElement('div');
                    div.className = 'dim-label';
                    div.textContent = text;
                    const lbl = new THREE.CSS2DObject(div);
                    lbl.position.copy(pos);
                    dimGroup.add(lbl);
                }}
                
                function fmt(v) {{
                    return v.toFixed(4) + ' in';
                }}
                
                // ── X dimension (bottom front, below model) ──────────────────────────
                const yLow = min.y - gap * 1.5;
                const zFront = max.z + gap;
                const xA = new THREE.Vector3(min.x, yLow, zFront);
                const xB = new THREE.Vector3(max.x, yLow, zFront);
                makeExtLine(new THREE.Vector3(min.x, min.y, max.z), xA);
                makeExtLine(new THREE.Vector3(max.x, min.y, max.z), xB);
                makeArrow(xA, xB);
                makeLabel(new THREE.Vector3((min.x + max.x) / 2, yLow - gap * 0.6, zFront), fmt(size.x));
                
                // ── Y dimension (right side, height) ─────────────────────────────────
                const xRight = max.x + gap * 1.5;
                const zRight = max.z + gap;
                const yA = new THREE.Vector3(xRight, min.y, zRight);
                const yB = new THREE.Vector3(xRight, max.y, zRight);
                makeExtLine(new THREE.Vector3(max.x, min.y, max.z), yA);
                makeExtLine(new THREE.Vector3(max.x, max.y, max.z), yB);
                makeArrow(yA, yB);
                makeLabel(new THREE.Vector3(xRight + gap * 0.6, (min.y + max.y) / 2, zRight), fmt(size.y));
                
                // ── Z dimension (depth, right side bottom) ───────────────────────────
                const xRight2 = max.x + gap * 1.5;
                const yLow2 = min.y - gap * 1.5;
                const zA = new THREE.Vector3(xRight2, yLow2, min.z);
                const zB = new THREE.Vector3(xRight2, yLow2, max.z);
                makeExtLine(new THREE.Vector3(max.x, min.y, min.z), zA);
                makeExtLine(new THREE.Vector3(max.x, min.y, max.z), zB);
                makeArrow(zA, zB);
                makeLabel(new THREE.Vector3(xRight2 + gap * 0.6, yLow2 - gap * 0.6, (min.z + max.z) / 2), fmt(size.z));
            }}
        </script>
    </body>
    </html>
    """
    if not selected_piece and not uploaded_step:
        st.markdown(
            """<div style="border:2px dashed #94a3b8;border-radius:12px;
                padding:4rem 2rem;text-align:center;color:#64748b;
                background:#f8fafc;margin-top:1rem;display:flex;
                align-items:center;justify-content:center;flex-direction:column;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
              <div style="font-size:4rem;margin-bottom:1.5rem;">🔍</div>
              <div style="font-weight:bold;font-size:1.3rem;color:#1e293b;">Esperando Selección de Pieza</div>
              <div style="font-size:.95rem;margin-top:.5rem;max-width:450px;line-height:1.5;">
                Seleccione una pieza del catálogo usando los filtros superiores o cargue un archivo CAD manual (.STEP, .STL) para iniciar la inspección tridimensional.
              </div>
            </div>""",
            unsafe_allow_html=True
        )
        return

    col3d, colpdf = st.columns([3, 2])

    with col3d:
        components.html(html_code, height=520, scrolling=False)
        
        # Style normal buttons for corporate theme consistency
        st.markdown("""
        <style>
        div[data-testid="stButton"] button {
            background-color: #EC2024 !important;
            color: white !important;
            border: 1px solid #EC2024 !important;
            font-weight: bold !important;
            border-radius: 6px !important;
            padding: 0.5rem 1rem !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stButton"] button:hover {
            background-color: #111111 !important;
            border-color: #111111 !important;
            color: white !important;
            transform: translateY(-1px);
        }
        div[data-testid="stButton"] button:active {
            transform: translateY(0);
        }
        div[data-testid="stButton"] button:disabled {
            background-color: #D2D3D5 !important;
            border-color: #D2D3D5 !important;
            color: #888888 !important;
            cursor: not-allowed !important;
            transform: none !important;
        }
        /* Hide the specific sibling button container */
        div.element-container:has(.hide-sibling-btn) + div.element-container {
            position: absolute !important;
            width: 0 !important;
            height: 0 !important;
            overflow: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        
        /* Fullscreen container styling in parent page */
        div.element-container:fullscreen,
        div.element-container:-webkit-full-screen {
            width: 100vw !important;
            height: 100vh !important;
            background: #111111 !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        div.element-container:fullscreen iframe,
        div.element-container:-webkit-full-screen iframe,
        div.element-container:fullscreen div,
        div.element-container:-webkit-full-screen div {
            width: 100vw !important;
            height: 100vh !important;
            max-width: 100vw !important;
            max-height: 100vh !important;
            border: none !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Navigation buttons below the interactive view
        if len(only_pieces) > 0:
            def update_piece(sku):
                st.session_state["cad_piece_select"] = sku

            nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
            
            with nav_col1:
                st.markdown('<div class="hide-sibling-btn"></div>', unsafe_allow_html=True)
                st.button(
                    "⬅️ Pieza Anterior", 
                    use_container_width=True, 
                    disabled=prev_disabled, 
                    key="btn_prev_piece",
                    on_click=update_piece,
                    args=(prev_target,)
                )
            with nav_col2:
                st.markdown(
                    f"""<div style="text-align:center; font-family:'Questrial', sans-serif; 
                                     font-weight:bold; font-size:1.1rem; padding: 0.4rem; color:#111111;">
                            {middle_text}
                        </div>""",
                    unsafe_allow_html=True
                )
            with nav_col3:
                st.markdown('<div class="hide-sibling-btn"></div>', unsafe_allow_html=True)
                st.button(
                    "Siguiente Pieza ➡️", 
                    use_container_width=True, 
                    disabled=next_disabled, 
                    key="btn_next_piece",
                    on_click=update_piece,
                    args=(next_target,)
                )

    with colpdf:
        st.markdown("#### 📄 Plano de Control (Vista Preliminar)")

        pdf_orig_path = selected_piece["archivo_plano_control"] if selected_piece else None
        # Fallback: try dibujo_original if plano_control is missing
        if selected_piece and (not pdf_orig_path or not os.path.exists(str(pdf_orig_path))):
            pdf_orig_path = selected_piece.get("archivo_dibujo_original")

        if pdf_orig_path and os.path.exists(str(pdf_orig_path)):
            with open(pdf_orig_path, "rb") as f:
                pdf_b64 = base64.b64encode(f.read()).decode("utf-8")

            pdfjs_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="utf-8">
              <style>
                * {{ box-sizing: border-box; margin: 0; padding: 0; }}
                body {{
                  background: #e2e8f0;
                  font-family: sans-serif;
                  overflow-y: auto;
                  height: 510px;
                }}
                #pdf-wrapper {{
                  border: 2px solid #0056b3;
                  border-radius: 8px;
                  overflow-y: auto;
                  height: 510px;
                  background: #525659;
                  display: flex;
                  flex-direction: column;
                  align-items: center;
                  padding: 12px 8px;
                  gap: 10px;
                }}
                canvas {{
                  display: block;
                  box-shadow: 0 2px 8px rgba(0,0,0,0.5);
                  border-radius: 2px;
                  max-width: 100%;
                }}
                #pdf-loading {{
                  color: #94a3b8;
                  font-size: 14px;
                  padding: 2rem;
                  text-align: center;
                }}
              </style>
              <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
            </head>
            <body>
              <div id="pdf-wrapper">
                <div id="pdf-loading">⏳ Cargando plano...</div>
              </div>
              <script>
                pdfjsLib.GlobalWorkerOptions.workerSrc =
                  'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

                const b64 = "{pdf_b64}";
                const raw = atob(b64);
                const uint8 = new Uint8Array(raw.length);
                for (let i = 0; i < raw.length; i++) uint8[i] = raw.charCodeAt(i);

                const wrapper = document.getElementById('pdf-wrapper');

                pdfjsLib.getDocument({{ data: uint8 }}).promise.then(pdf => {{
                  document.getElementById('pdf-loading').remove();
                  const total = pdf.numPages;
                  const renderPage = (num) => {{
                    pdf.getPage(num).then(page => {{
                      // Scale to wrapper width
                      const vp0 = page.getViewport({{ scale: 1 }});
                      const scale = (wrapper.clientWidth - 16) / vp0.width;
                      const viewport = page.getViewport({{ scale }});
                      const canvas = document.createElement('canvas');
                      canvas.width  = viewport.width;
                      canvas.height = viewport.height;
                      wrapper.appendChild(canvas);
                      page.render({{ canvasContext: canvas.getContext('2d'), viewport }});
                      if (num < total) renderPage(num + 1);
                    }});
                  }};
                  renderPage(1);
                }}).catch(err => {{
                  document.getElementById('pdf-loading').textContent = '⚠️ Error al renderizar el plano: ' + err.message;
                }});
              </script>
            </body>
            </html>
            """
            components.html(pdfjs_html, height=520, scrolling=False)

            # Download button below preview
            with open(pdf_orig_path, "rb") as f:
                st.download_button(
                    label="📥 Descargar Plano de Control (PDF)",
                    data=f.read(),
                    file_name=os.path.basename(pdf_orig_path),
                    mime="application/pdf",
                    key="btn_dl_plano_orig_blue"
                )

        else:
            st.markdown(
                """<div style="border:2px dashed #94a3b8;border-radius:8px;
                    padding:3rem 1.5rem;text-align:center;color:#64748b;
                    background:#f8fafc;height:480px;display:flex;
                    align-items:center;justify-content:center;flex-direction:column;">
                  <div style="font-size:3rem;margin-bottom:1rem;">📄</div>
                  <div style="font-weight:bold;font-size:1rem;">Sin Plano de Control Registrado</div>
                  <div style="font-size:.85rem;margin-top:.5rem;">
                    Suba el Plano de Control al registrar la pieza<br>
                    en la sección <b>3.5. Carga de Registros de Diseño</b>
                  </div>
                </div>""",
                unsafe_allow_html=True
            )

    if selected_piece:
        st.markdown("---")
        st.markdown("### 📥 Descargar Certificado de Geometría CAD (PDF)")
        st.markdown("Puede exportar una ficha técnica en PDF con la información general de diseño, cotas del plano y vistas de calibración.")

        from src.pdf_generator import generate_first_piece_pdf

        pdf_piece_data = selected_piece
        if "usuario_registro" not in pdf_piece_data or not pdf_piece_data["usuario_registro"]:
            pdf_piece_data["usuario_registro"] = st.session_state["nombre_completo"]

        pdf_bytes = generate_first_piece_pdf(pdf_piece_data)

        st.download_button(
            label=f"📥 Descargar Certificado CAD de {pdf_piece_data.get('numero_pieza', 'la Pieza')} (PDF)",
            data=pdf_bytes,
            file_name=f"Certificado_Ficha_Tecnica_CAD_{pdf_piece_data.get('numero_pieza', 'Muestra')}.pdf",
            mime="application/pdf",
            key="btn_download_cad_pdf_blue"
        )