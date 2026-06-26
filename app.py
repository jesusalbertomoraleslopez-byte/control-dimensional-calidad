import streamlit as st
import os
from src.database import initialize_database
from src.auth import check_login, logout

# Page Config
favicon_path = os.path.join(os.path.dirname(__file__), "favicon.png")
st.set_page_config(
    page_title="SIGRAMA - Control Dimensional de Calidad",
    page_icon=favicon_path if os.path.exists(favicon_path) else "📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Note: Streamlit's global hotkey listener is intercepted below in the main st.markdown block via inline HTML

# Initialize Database
initialize_database()

# Inject Custom CSS for Premium Look & Feel and Corporate Branding
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,300;0,400;0,700;1,300;1,400;1,700&family=Questrial&display=swap');

    /* Apply Montserrat to headers and Questrial to body, avoiding overriding icon fonts */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], [data-testid="stHeader"] {
        font-family: 'Questrial', sans-serif !important;
    }
    
    /* Apply font to inputs and buttons specifically, excluding generic span and p to prevent icon font breakage */
    input, select, textarea, button, label {
        font-family: 'Questrial', sans-serif !important;
    }
    
    /* Protect icon fonts from cascading overrides */
    [class^="material-"], [class*=" material-"], .material-icons, .material-symbols-outlined, .material-symbols-rounded {
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
    }
    
    h1, h2, h3, h4, h5, h6, .gotham-font {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700 !important;
        color: #111111 !important;
    }
    
    /* Style all buttons to be red (Pantone 485 C) with white text */
    div.stButton > button,
    div.stDownloadButton > button,
    div.stFormSubmitButton > button,
    button[data-testid="baseButton-secondary"]:not([role="tab"]):not([data-baseweb="tab"]),
    button[data-testid="baseButton-primary"]:not([role="tab"]):not([data-baseweb="tab"]),
    button[kind="secondary"]:not([role="tab"]):not([data-baseweb="tab"]),
    button[kind="primary"]:not([role="tab"]):not([data-baseweb="tab"]) {
        background-color: #EC2024 !important;
        color: #FFFFFF !important;
        border: 1px solid #EC2024 !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem !important;
        font-weight: bold !important;
        font-family: 'Questrial', sans-serif !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    div.stButton > button:hover,
    div.stDownloadButton > button:hover,
    div.stFormSubmitButton > button:hover,
    button[data-testid="baseButton-secondary"]:not([role="tab"]):not([data-baseweb="tab"]):hover,
    button[data-testid="baseButton-primary"]:not([role="tab"]):not([data-baseweb="tab"]):hover,
    button[kind="secondary"]:not([role="tab"]):not([data-baseweb="tab"]):hover,
    button[kind="primary"]:not([role="tab"]):not([data-baseweb="tab"]):hover {
        background-color: #111111 !important;
        border-color: #111111 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(236, 32, 36, 0.15) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Style all dropdown selectbox inputs to use brand colors */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        border-radius: 6px !important;
        border: 1px solid #D2D3D5 !important;
        transition: border-color 0.2s ease !important;
    }
    
    div[data-testid="stSelectbox"] div[data-baseweb="select"]:hover,
    div[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within {
        border-color: #EC2024 !important;
    }
    
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #111111 !important;
    }
    
    div[data-testid="stSelectbox"] div[data-baseweb="select"] span {
        color: #111111 !important;
        font-weight: 500 !important;
        font-family: 'Questrial', sans-serif !important;
    }
    
    div[data-testid="stSelectbox"] div[data-baseweb="select"] svg {
        fill: #111111 !important;
    }
    
    /* Option items in the dropdown list */
    div[role="listbox"] li,
    ul[role="listbox"] li,
    div[data-baseweb="popover"] li,
    div[data-baseweb="menu"] li {
        background-color: #FFFFFF !important;
        color: #111111 !important;
        font-family: 'Questrial', sans-serif !important;
        transition: background-color 0.15s ease, color 0.15s ease !important;
    }
    
    div[role="listbox"] li:hover,
    ul[role="listbox"] li:hover,
    div[data-baseweb="popover"] li:hover,
    div[data-baseweb="menu"] li:hover {
        background-color: #EC2024 !important;
        color: #FFFFFF !important;
    }
    
    /* Sidebar premium styling (Light Gray theme for Logo Legibility) */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stText,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] h5,
    [data-testid="stSidebar"] h6 {
        color: #111111 !important;
    }
    
    /* Force white text on sidebar buttons to override general sidebar text rules */
    [data-testid="stSidebar"] button,
    [data-testid="stSidebar"] button * {
        color: #FFFFFF !important;
    }
    
    /* Active navigation item highlighting: Red Pill style with White Text and White dot */
    [data-testid="stSidebar"] div[role="radiogroup"] label span {
        color: #111111 !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input[type="radio"]:checked) {
        background-color: #EC2024 !important;
        border-radius: 6px !important;
        padding: 6px 12px !important;
        transition: background-color 0.2s ease !important;
    }
    
    /* Reset background colors of all inner elements in the active label to prevent white box overlay and show white text */
    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input[type="radio"]:checked) div,
    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input[type="radio"]:checked) span,
    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input[type="radio"]:checked) p {
        background-color: transparent !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
    }
    
    /* Make the selected radio dot white (overriding transparency on the dot element) */
    [data-testid="stSidebar"] div[role="radiogroup"] input[type="radio"]:checked + div,
    [data-testid="stSidebar"] div[role="radiogroup"] input[type="radio"]:checked + div * {
        background-color: #FFFFFF !important;
        border-color: #FFFFFF !important;
        color: #EC2024 !important;
    }
    
    /* Layout styling */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    
    /* Corporate styling details */
    .report-card {
        background-color: #FFFFFF;
        border: 1px solid #D2D3D5;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    /* Reset file uploader button styling to avoid overlap issues and fit corporate secondary styling */
    [data-testid="stFileUploader"] button[data-testid="baseButton-secondary"]:not([role="tab"]):not([data-baseweb="tab"]),
    .stFileUploader button[data-testid="baseButton-secondary"]:not([role="tab"]):not([data-baseweb="tab"]),
    [data-testid="stFileUploader"] button,
    .stFileUploader button {
        background-color: #FFFFFF !important;
        color: #111111 !important;
        border: 1px solid #D2D3D5 !important;
        border-radius: 6px !important;
        padding: 0.375rem 0.75rem !important;
        font-weight: 500 !important;
        box-shadow: none !important;
        transform: none !important;
    }
    
    /* Ensure the text inside the file uploader button is dark and not overridden by sidebar rules */
    [data-testid="stFileUploader"] button *,
    .stFileUploader button * {
        background-color: transparent !important;
        color: #111111 !important;
    }
    
    [data-testid="stFileUploader"] button[data-testid="baseButton-secondary"]:not([role="tab"]):not([data-baseweb="tab"]):hover,
    .stFileUploader button[data-testid="baseButton-secondary"]:not([role="tab"]):not([data-baseweb="tab"]):hover,
    [data-testid="stFileUploader"] button:hover,
    .stFileUploader button:hover {
        background-color: #F8F9FA !important;
        border-color: #EC2024 !important;
        color: #EC2024 !important;
        box-shadow: none !important;
        transform: none !important;
    }
    
    [data-testid="stFileUploader"] button:hover *,
    .stFileUploader button:hover * {
        color: #EC2024 !important;
    }
</style>
<img src="x" onerror="
    if (!window.__hotkeysPrevented) {
        window.__hotkeysPrevented = true;
        const preventStreamlitHotkeys = function(e) {
            const key = e.key ? e.key.toLowerCase() : '';
            if (key === 'c' || key === 'r' || e.keyCode === 67 || e.keyCode === 82) {
                if (e.ctrlKey || e.metaKey) {
                    e.stopImmediatePropagation();
                }
            }
        };
        window.addEventListener('keydown', preventStreamlitHotkeys, true);
        window.addEventListener('keypress', preventStreamlitHotkeys, true);
        window.addEventListener('keyup', preventStreamlitHotkeys, true);
        document.addEventListener('keydown', preventStreamlitHotkeys, true);
        document.addEventListener('keypress', preventStreamlitHotkeys, true);
        document.addEventListener('keyup', preventStreamlitHotkeys, true);
    }
" style="display:none;">""", unsafe_allow_html=True)

# Session State Initialization
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "role" not in st.session_state:
    st.session_state["role"] = None
if "nombre_completo" not in st.session_state:
    st.session_state["nombre_completo"] = None

# 2000x400 Institutional Banner
BANNER_PATH = os.path.join(os.path.dirname(__file__), "banner_app.png")



def show_banner():
    if os.path.exists(BANNER_PATH):
        st.image(BANNER_PATH)
    else:
        # Fallback stylized banner in case file is missing (using Pantone Black 7 C & Pantone 485 C)
        st.markdown("""
        <div style="background: linear-gradient(135deg, #111111 0%, #2A2A2A 100%); 
                    color: white; padding: 2.2rem 2rem; border-radius: 8px; text-align: center; margin-bottom: 1.5rem;
                    border-bottom: 5px solid #EC2024; position: relative; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
            <div style="position: absolute; top: -50px; right: -50px; width: 150px; height: 150px; 
                        background-color: rgba(236, 32, 36, 0.1); transform: rotate(45deg); pointer-events: none;"></div>
            <h1 style="margin:0; font-family: 'Montserrat', sans-serif; font-size: 2.6rem; font-weight: 900; letter-spacing: 2px; color: #FFFFFF !important;">SIGRAMA</h1>
            <p style="margin: 0.4rem 0 0.2rem 0; font-family: 'Questrial', sans-serif; font-size: 1.1rem; color: #D2D3D5; letter-spacing: 1px;">Control Dimensional de Calidad e Industria 4.0</p>
            <p style="margin: 0.4rem 0 0 0; font-family: 'Questrial', sans-serif; font-style: italic; font-size: 0.9rem; color: #EC2024; font-weight: bold;">Ingeniería que da resultados!!</p>
        </div>
        """, unsafe_allow_html=True)

# Auth Flow
if not st.session_state["logged_in"]:
    show_banner()
    
    st.markdown("<h2 style='text-align: center;'>Iniciar Sesión</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Ingresar", key="blue_btn_login")
            
            if submitted:
                if check_login(username, password):
                    st.success("¡Inicio de sesión exitoso!")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
                    
        st.info("Credenciales de prueba:\n\n- Operador: `operador` / `operador123`\n- Administrador: `admin` / `admin123`")
else:
    # App Shell with Header Banner
    show_banner()
    
    # Sidebar Logo and Header
    LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo_sigrama.png")
    if os.path.exists(LOGO_PATH):
        st.sidebar.image(LOGO_PATH, use_container_width=True)
    else:
        st.sidebar.markdown("<h2 style='color:#EC2024; margin:0; font-family:\"Montserrat\";'>SIGRAMA</h2>", unsafe_allow_html=True)
        
    st.sidebar.markdown(f"### Bienvenido, **{st.session_state['nombre_completo']}**")
    st.sidebar.markdown(f"Rol: `{st.session_state['role']}`")
    
    # Navigation Menu
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📌 MENÚ DE NAVEGACIÓN")
    
    menu_options = [
        "1. Dashboard Principal",
        "2. Área de Consulta",
        "3. Ingeniería",
        "   3.1 Carga de Registros de Diseño",
        "   3.2 Visualizador 3D CAD",
        "   3.3 Impresión de Reportes de Ingeniería",
        "4. Calidad",
        "   4.1 Dashboard de Calidad",
        "   4.2 Carga de Inspección (Excel)",
        "   4.3 Consolidación de Remisión",
        "   4.4 Impresión de Reportes de Calidad",
        "5. Manufactura Inteligente e Industria 4.0",
        "6. Manual de Operación"
    ]
    
    if st.session_state["role"] == "Administrador":
        menu_options.extend([
            "7. Área de Mantenimiento y Almacenamiento",
            "   7.1 Gestión de Registros",
            "   7.2 Explorador de Almacenamiento Local",
            "   7.3 Integración GitHub & Despliegue Streamlit",
            "   7.4 Glosario de Documentación (Oculto solo Administrador)",
            "   7.5 Sistema de Gestión de Calidad (SGC) (Oculto solo Administrador)"
        ])
    
    choice = st.sidebar.radio("Ir a la sección:", menu_options, label_visibility="collapsed")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Cerrar Sesión", key="logout_btn"):
        logout()

    # Sidebar Footer (Slogan & Contact details)
    st.sidebar.markdown("""
    <div style="text-align: center; padding-top: 1.5rem; border-top: 1px solid #E2E8F0; margin-top: 1rem;">
        <p style="font-family: 'Questrial', sans-serif; font-size: 0.8rem; color: #666666; margin: 0;">
            Industria Sigrama S.A. de C.V.
        </p>
        <p style="font-family: 'Montserrat', sans-serif; font-style: italic; font-weight: bold; color: #EC2024; font-size: 0.9rem; margin: 0.4rem 0 0.8rem 0;">
            Ingeniería que da resultados!!
        </p>
        <hr style="border: 0; border-top: 2px solid #EC2024; width: 30px; margin: 0.5rem auto;">
        <p style="font-size: 0.75rem; color: #666666; margin: 0.2rem 0; font-family: 'Questrial', sans-serif;">📧 <a href="mailto:sigrama@sigrama.com.mx" style="color: #EC2024; text-decoration: none;">sigrama@sigrama.com.mx</a></p>
        <p style="font-size: 0.75rem; color: #666666; margin: 0.2rem 0; font-family: 'Questrial', sans-serif;">🌐 <a href="https://www.sigrama.com.mx" target="_blank" style="color: #EC2024; text-decoration: none;">www.sigrama.com.mx</a></p>
        <p style="font-size: 0.75rem; color: #666666; margin: 0.2rem 0; font-family: 'Questrial', sans-serif;">📞 871 722 3132</p>
    </div>
    """, unsafe_allow_html=True)
        
    # Route Content
    import importlib
    if choice == "1. Dashboard Principal":
        import src.views.v1_dashboard
        importlib.reload(src.views.v1_dashboard)
        src.views.v1_dashboard.show_dashboard()
    elif choice == "2. Área de Consulta":
        import src.views.v2_consulta
        importlib.reload(src.views.v2_consulta)
        src.views.v2_consulta.show_consulta()
    elif choice == "3. Ingeniería":
        st.title("3. Ingeniería de Diseño")
        st.subheader("Planos, Modelos 3D y Control Dimensional")
        st.markdown("""
        Sección para dar de alta componentes, visualizar geometrías CAD interactiva y descargar planos oficiales:
        
        * 📂 **3.1 Carga de Registros de Diseño**: Alta de nuevos SKUs y carga de planos de control y de fabricación.
        * 📐 **3.2 Visualizador 3D CAD**: Inspección tridimensional interactiva y visualización de cotas.
        * 📄 **3.3 Impresión de Reportes de Ingeniería**: Consulta y descarga de fichas técnicas y reportes de liberación.
        
        *Seleccione una subsección en la barra lateral para comenzar.*
        """)
    elif choice == "   3.1 Carga de Registros de Diseño":
        import src.views.v3_control.v3_2_design
        importlib.reload(src.views.v3_control.v3_2_design)
        src.views.v3_control.v3_2_design.show_design_loader()
    elif choice == "   3.2 Visualizador 3D CAD":
        import src.views.v3_control.v3_1_cad_viewer
        importlib.reload(src.views.v3_control.v3_1_cad_viewer)
        src.views.v3_control.v3_1_cad_viewer.show_cad_viewer()
    elif choice == "   3.3 Impresión de Reportes de Ingeniería":
        import src.views.v3_control.v3_3_engineering_reports
        importlib.reload(src.views.v3_control.v3_3_engineering_reports)
        src.views.v3_control.v3_3_engineering_reports.show_engineering_reports()
    elif choice == "4. Calidad":
        st.title("4. Control de Calidad y SPC")
        st.subheader("Auditoría, Carga de Inspecciones y Análisis de Habilidad")
        st.markdown("""
        Monitoreo de inspecciones, análisis estadístico y control de embarques diarios:
        
        * 📊 **4.1 Dashboard de Calidad**: Panel de control interactivo de indicadores, defectos e histórico de inspecciones.
        * 📝 **4.2 Carga de Inspección (Excel)**: Carga de reportes en piso mediante plantillas dinámicas de Excel.
        * 🚚 **4.3 Consolidación de Remisión**: Consolidado diario de mediciones y cálculo de capacidad de proceso Cp/Cpk.
        * 📑 **4.4 Impresión de Reportes de Calidad**: Consulta e impresión individual y consolidada de reportes PDF.
        
        *Seleccione una subsección en la barra lateral para comenzar.*
        """)
    elif choice == "   4.1 Dashboard de Calidad":
        import src.views.v3_control.v3_1_spc_dashboard
        importlib.reload(src.views.v3_control.v3_1_spc_dashboard)
        src.views.v3_control.v3_1_spc_dashboard.show_spc_dashboard()
    elif choice == "   4.2 Carga de Inspección (Excel)":
        import src.views.v3_control.v3_2_capture_excel
        importlib.reload(src.views.v3_control.v3_2_capture_excel)
        src.views.v3_control.v3_2_capture_excel.show_spc_excel()
    elif choice == "   4.3 Consolidación de Remisión":
        import src.views.v3_control.v3_3_remision
        importlib.reload(src.views.v3_control.v3_3_remision)
        src.views.v3_control.v3_3_remision.show_remision()
    elif choice == "   4.4 Impresión de Reportes de Calidad":
        import src.views.v3_control.v4_4_quality_reports
        importlib.reload(src.views.v3_control.v4_4_quality_reports)
        src.views.v3_control.v4_4_quality_reports.show_quality_reports()
    elif choice == "5. Manufactura Inteligente e Industria 4.0":
        import src.views.v6_industry_40
        importlib.reload(src.views.v6_industry_40)
        src.views.v6_industry_40.show_industry_40()
    elif choice == "6. Manual de Operación":
        import src.views.v7_manual
        importlib.reload(src.views.v7_manual)
        src.views.v7_manual.show_manual()
    elif choice == "7. Área de Mantenimiento y Almacenamiento":
        import src.views.v8_maintenance
        importlib.reload(src.views.v8_maintenance)
        src.views.v8_maintenance.show_maintenance(sub_section=None)
    elif choice == "   7.1 Gestión de Registros":
        import src.views.v8_maintenance
        importlib.reload(src.views.v8_maintenance)
        src.views.v8_maintenance.show_maintenance(sub_section="7.1")
    elif choice == "   7.2 Explorador de Almacenamiento Local":
        import src.views.v8_maintenance
        importlib.reload(src.views.v8_maintenance)
        src.views.v8_maintenance.show_maintenance(sub_section="7.2")
    elif choice == "   7.3 Integración GitHub & Despliegue Streamlit":
        import src.views.v8_maintenance
        importlib.reload(src.views.v8_maintenance)
        src.views.v8_maintenance.show_maintenance(sub_section="7.3")
    elif choice == "   7.4 Glosario de Documentación (Oculto solo Administrador)":
        import src.views.v5_glossary
        importlib.reload(src.views.v5_glossary)
        src.views.v5_glossary.show_glossary()
    elif choice == "   7.5 Sistema de Gestión de Calidad (SGC) (Oculto solo Administrador)":
        import src.views.v4_sgc
        importlib.reload(src.views.v4_sgc)
        src.views.v4_sgc.show_sgc()

# Force hot reload token: 2026-06-19T15:40:00
