import streamlit as st
import os
from datetime import datetime

def show_industry_40():
    # Header Corporativo
    st.markdown("""
    <div style="background: linear-gradient(135deg, #111111 0%, #1e293b 100%); padding: 1.5rem 2rem; border-radius: 12px; border-left: 6px solid #EC2024; margin-bottom: 1.5rem; color: #FFFFFF;">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
            <div>
                <span style="background-color: #EC2024; color: #FFFFFF; font-size: 11px; font-weight: bold; padding: 4px 10px; border-radius: 20px; text-transform: uppercase; letter-spacing: 1px;">
                    INDUSTRIA SIGRAMA • INDUSTRIA 4.0 & METROLOGÍA AVANZADA
                </span>
                <h1 style="font-family: 'Montserrat', sans-serif; font-size: 26px; font-weight: 700; margin: 8px 0 4px 0; color: #FFFFFF;">
                    🏭 5. Manufactura Inteligente e Industria 4.0
                </h1>
                <p style="font-family: 'Questrial', sans-serif; font-size: 14px; margin: 0; color: #D2D3D5;">
                    Arquitectura de Microservicios, Gemelo Digital Metrológico y Aseguramiento Estadístico en Tiempo Real.
                </p>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 12px; color: #94a3b8;">Despliegue Activo:</span><br/>
                <span style="font-size: 14px; font-weight: bold; color: #10B981;">🟢 Nube & Localhost Híbrido</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Métricas Clave de Industria 4.0 (KPI Cards)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown("""
        <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1rem; border-top: 4px solid #EC2024; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.04);">
            <div style="font-size: 26px; font-weight: 700; color: #111111; font-family: 'Montserrat', sans-serif;">100%</div>
            <div style="font-size: 12px; color: #64748B; font-family: 'Questrial', sans-serif;">Trazabilidad Digital (CAD a FAI)</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi2:
        st.markdown("""
        <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1rem; border-top: 4px solid #10B981; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.04);">
            <div style="font-size: 26px; font-weight: 700; color: #111111; font-family: 'Montserrat', sans-serif;">1,024 MB</div>
            <div style="font-size: 12px; color: #64748B; font-family: 'Questrial', sans-serif;">Ingesta Masiva (.ZIP / .RAR)</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi3:
        st.markdown("""
        <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1rem; border-top: 4px solid #3B82F6; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.04);">
            <div style="font-size: 26px; font-weight: 700; color: #111111; font-family: 'Montserrat', sans-serif;">125+ SKUs</div>
            <div style="font-size: 12px; color: #64748B; font-family: 'Questrial', sans-serif;">Auto-Sincronización en Arranque</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi4:
        st.markdown("""
        <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1rem; border-top: 4px solid #8B5CF6; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.04);">
            <div style="font-size: 26px; font-weight: 700; color: #111111; font-family: 'Montserrat', sans-serif;">SSO Token</div>
            <div style="font-size: 12px; color: #64748B; font-family: 'Questrial', sans-serif;">Interconexión Hub Concentrador</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Navegación por Pestañas Especializadas
    tab_stack, tab_pilares, tab_ecosistema, tab_ficha = st.tabs([
        "💻 Stack Tecnológico Completo",
        "🤖 Pilares de Industria 4.0",
        "🔄 Ecosistema & Concentradora (SSO)",
        "📥 Ficha Técnica & Descargas"
    ])

    # =========================================================================
    # TAB 1: STACK TECNOLÓGICO COMPLETO
    # =========================================================================
    with tab_stack:
        st.markdown("""
        ### 🛠️ Arquitectura y Tecnologías del Sistema
        Esta aplicación integra un ecosistema de librerías de vanguardia en Python, WebGL y computación científica, 
        diseñado para operar tanto en terminales industriales táctiles en piso de planta como en la nube corporativa de alta disponibilidad.
        """)

        col_l1, col_l2 = st.columns(2)

        with col_l1:
            st.markdown("""
            <div style="background-color: #F8F9FA; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1.2rem; margin-bottom: 1rem;">
                <h4 style="color: #EC2024; margin-top: 0; font-family: 'Montserrat', sans-serif;">
                    1. Presentación & Experiencia de Usuario (UI / UX Metrológica)
                </h4>
                <ul style="font-size: 13.5px; color: #334155; line-height: 1.6; padding-left: 1.2rem; margin: 0;">
                    <li><b>Streamlit 1.35+:</b> Arquitectura Single-Page Application (SPA) reactiva y en tiempo real, optimizada para tablets y estaciones de inspección.</li>
                    <li><b>WebGL & Three.js Canvas 3D:</b> Renderizador interactivo de geometrías CAD (.STEP) en navegador web sin requerir licencias CAD comerciales en el puesto de trabajo.</li>
                    <li><b>Plotly Interactive Engine:</b> Gráficos analíticos vectoriales para cartas de control estadístico (SPC), histogramas de frecuencias y Campanas de Gauss con cálculo de subgrupos <i>n=3</i>.</li>
                    <li><b>Identidad Corporativa SIGRAMA:</b> Estilizado CSS inyectado bajo normas corporativas (Pantone 485 C <code>#EC2024</code>, Pantone Black 7 C <code>#111111</code>, gris <code>#D2D3D5</code>, fuentes Questrial y Montserrat).</li>
                    <li><b>Diálogos Nativos Windows (Tkinter/Win32):</b> Explorador nativo de carpetas para escaneo directo de la unidad de red corporativa <code>Z:\\02 - INGENIERIA\\BASE DE DATOS PRODUCTOS</code>.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="background-color: #F8F9FA; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1.2rem; margin-bottom: 1rem;">
                <h4 style="color: #111111; margin-top: 0; font-family: 'Montserrat', sans-serif;">
                    2. Backend & Algoritmia Metrológica (Python Core)
                </h4>
                <ul style="font-size: 13.5px; color: #334155; line-height: 1.6; padding-left: 1.2rem; margin: 0;">
                    <li><b>Python 3.10+ / 3.14:</b> Núcleo computacional de alta concurrencia y orquestación lógica del sistema.</li>
                    <li><b>SciPy & NumPy:</b> Modelado matemático de distribución normal, cálculo de desviación estándar poblacional (&sigma;), índices de capacidad de proceso (Cp, Cpk) y límites UCL / LCL.</li>
                    <li><b>Trimesh 3.23+:</b> Motor de geometría computacional para análisis de sólidos 3D, teselado de mallas, cálculo de volúmenes, momentos de inercia y cajas envolventes (Bounding Box).</li>
                    <li><b>Pandas 2.0+:</b> Procesamiento vectorial de matrices de tolerancias de corte láser y doblado, concatenación dinámica de SKUs y normalización de textos.</li>
                    <li><b>Rarfile 4.5 & Zipfile:</b> Descompresión asíncrona de paquetes masivos con soporte dual para archivos <b>.ZIP</b> y <b>.RAR</b>.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col_l2:
            st.markdown("""
            <div style="background-color: #F8F9FA; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1.2rem; margin-bottom: 1rem;">
                <h4 style="color: #0284C7; margin-top: 0; font-family: 'Montserrat', sans-serif;">
                    3. Generación Documental & Big Data Export
                </h4>
                <ul style="font-size: 13.5px; color: #334155; line-height: 1.6; padding-left: 1.2rem; margin: 0;">
                    <li><b>OpenPyXL 3.1+:</b> Generador avanzado de libros de auditoría Excel con paleta semafórica (🟢 <code>#D4EDDA</code> para registros completos, 🔴 <code>#F8D7DA</code> para faltantes). Incluye hoja ejecutiva de pendientes para el Departamento de Ingeniería.</li>
                    <li><b>ReportLab 4.0+ & FPDF2:</b> Compilador vectorial de reportes oficiales de Primera Pieza (FAI - First Article Inspection) con numeración dinámica, tabla de cotas críticas y firmas autorizadas.</li>
                    <li><b>Python-docx:</b> Generación programática de expedientes técnicos y manuales operativos estandarizados bajo la norma ISO 9001 / SGC.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="background-color: #F8F9FA; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1.2rem; margin-bottom: 1rem;">
                <h4 style="color: #10B981; margin-top: 0; font-family: 'Montserrat', sans-serif;">
                    4. Persistencia, Datos Relacionales & Sincronización
                </h4>
                <ul style="font-size: 13.5px; color: #334155; line-height: 1.6; padding-left: 1.2rem; margin: 0;">
                    <li><b>SQLite 3 & SQLAlchemy 2.0+:</b> Base de datos relacional integrada con 9 tablas relacionales (piezas, materias primas, lotes, mediciones, inspecciones, usuarios, glosario SGC).</li>
                    <li><b>Motor Auto-Sync Startup:</b> Al arrancar el contenedor en la nube, el sistema escanea automáticamente los 125 directorios de <code>src/Proyectos/</code> y sincroniza la base de datos sin pérdida de información.</li>
                    <li><b>Integración con Servidor de Red:</b> Mapeo jerárquico por calibre, material y espesor en la unidad corporativa <code>Z:\\</code>.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background-color: #1E293B; border-radius: 8px; padding: 1.2rem; color: #FFFFFF; margin-top: 0.5rem;">
            <h4 style="color: #38BDF8; margin-top: 0; font-family: 'Montserrat', sans-serif;">
                5. Cloud, DevOps & Ciberseguridad (Despliegue Continuo)
            </h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px; font-size: 13px;">
                <div>
                    <b>☁️ Streamlit Community Cloud:</b> Despliegue en contenedor Linux Debian con CI/CD automático conectado a la rama <code>main</code> de GitHub.
                </div>
                <div>
                    <b>⚙️ Configuración 1 GB:</b> Archivo <code>.streamlit/config.toml</code> con <code>maxUploadSize = 1024</code> y <code>maxMessageSize = 1024</code> para admitir planos y modelos 3D de alta densidad.
                </div>
                <div>
                    <b>🔑 Single Sign-On (SSO):</b> Token criptográfico <code>SIGRAMA_AUTH_TOKEN</code> que permite navegar entre el Hub Concentrador y los módulos sin reingresar usuario ni contraseña.
                </div>
                <div>
                    <b>📦 Dependencias de Sistema:</b> Archivo <code>packages.txt</code> con motor <code>unar</code> para descompresión nativa de archivos .RAR en servidores Debian sin interfaz gráfica.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # =========================================================================
    # TAB 2: PILARES DE INDUSTRIA 4.0
    # =========================================================================
    with tab_pilares:
        st.markdown("""
        ### 🤖 Los 4 Pilares de la Transformación Digital en SIGRAMA
        """)

        p1, p2 = st.columns(2)

        with p1:
            st.markdown("""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1.3rem; margin-bottom: 1.2rem; border-left: 5px solid #EC2024;">
                <h4 style="margin-top:0; color: #EC2024; font-family: 'Montserrat', sans-serif;">
                    1. Edge Data Capture (Digitalización en Piso)
                </h4>
                <p style="font-size: 13.5px; color: #475569; line-height: 1.5;">
                    Sustitución completa de las hojas de control impresas y bitácoras manuales en las áreas de <b>Corte Láser</b> y <b>Doblado CNC</b>. 
                    El operario captura las cotas de la muestra (n=3) directamente en la estación de trabajo y recibe retroalimentación inmediata sobre la conformidad de la pieza antes de autorizar la corrida del lote.
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1.3rem; margin-bottom: 1.2rem; border-left: 5px solid #10B981;">
                <h4 style="margin-top:0; color: #10B981; font-family: 'Montserrat', sans-serif;">
                    2. Gemelo Digital Metrológico (Digital Twin)
                </h4>
                <p style="font-size: 13.5px; color: #475569; line-height: 1.5;">
                    Cada componente fabricado mantiene una vinculación bidireccional entre su <b>modelo geométrico CAD nativo (.SLDPRT / .STEP)</b>, el desplegado de chapa (.DXF para nido en ProNest) y los valores metrológicos reales registrados en piso. Esto permite comparar el diseño nominal vs. la realidad dimensional de manufactura.
                </p>
            </div>
            """, unsafe_allow_html=True)

        with p2:
            st.markdown("""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1.3rem; margin-bottom: 1.2rem; border-left: 5px solid #3B82F6;">
                <h4 style="margin-top:0; color: #3B82F6; font-family: 'Montserrat', sans-serif;">
                    3. Metrología Estadística Predictiva (SPC)
                </h4>
                <p style="font-size: 13.5px; color: #475569; line-height: 1.5;">
                    Cálculo automatizado de la capacidad de proceso en tiempo real (Cp y Cpk) y construcción dinámica de la Campana de Gauss. Permite detectar anticipadamente desviaciones en la calibración del cabezal láser, desgaste en los dados de plegadora y variaciones de lote a lote en el espesor de la chapa metálica.
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1.3rem; margin-bottom: 1.2rem; border-left: 5px solid #8B5CF6;">
                <h4 style="margin-top:0; color: #8B5CF6; font-family: 'Montserrat', sans-serif;">
                    4. Trazabilidad de Ciclo Completo & Auditoría Ágil
                </h4>
                <p style="font-size: 13.5px; color: #475569; line-height: 1.5;">
                    Generación con un solo clic de auditorías completas en Excel y reportes formales de Primera Pieza (FAI) en PDF. Reduce el tiempo de preparación de auditorías de calidad de horas a segundos, garantizando cumplimiento riguroso bajo los procedimientos del Sistema de Gestión de Calidad (SGC).
                </p>
            </div>
            """, unsafe_allow_html=True)

    # =========================================================================
    # TAB 3: ECOSISTEMA & CONCENTRADORA (SSO)
    # =========================================================================
    with tab_ecosistema:
        st.markdown("""
        ### 🔄 Ecosistema Unificado de Manufactura SIGRAMA
        Esta aplicación no opera como una isla aislada; forma parte integral de la **Suite Digital SIGRAMA**, 
        orquestada por la **Concentradora de Aplicaciones (Hub)** con control de acceso basado en roles (RBAC) y Single Sign-On (SSO).
        """)

        st.markdown("""
        <table style="width:100%; border-collapse: collapse; font-family: 'Questrial', sans-serif; font-size: 13px; margin: 15px 0;">
            <thead>
                <tr style="background-color: #111111; color: #FFFFFF; text-align: left;">
                    <th style="padding: 10px 14px; border-radius: 6px 0 0 0;">Aplicación</th>
                    <th style="padding: 10px 14px;">Módulo Operativo</th>
                    <th style="padding: 10px 14px;">Puerto Local</th>
                    <th style="padding: 10px 14px; border-radius: 0 6px 0 0;">Acceso Cloud Oficial</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid #E2E8F0; background: #FFFFFF;">
                    <td style="padding: 10px 14px;"><b>📐 Prototipos de Ingeniería</b></td>
                    <td style="padding: 10px 14px;">Control dimensional, visor 3D, auditoría de planos y FAI</td>
                    <td style="padding: 10px 14px;"><code>:8504</code></td>
                    <td style="padding: 10px 14px;"><a href="https://prototiposingenieria.streamlit.app/" target="_blank" style="color:#EC2024; font-weight:bold;">prototiposingenieria.streamlit.app</a></td>
                </tr>
                <tr style="border-bottom: 1px solid #E2E8F0; background: #F8F9FA;">
                    <td style="padding: 10px 14px;"><b>📦 Remisiones de Materiales</b></td>
                    <td style="padding: 10px 14px;">Control de remisiones, entarimado, órdenes de fabricación y WIP</td>
                    <td style="padding: 10px 14px;"><code>:8502</code></td>
                    <td style="padding: 10px 14px;"><a href="https://remisiones-de-materiales.streamlit.app/" target="_blank" style="color:#EC2024; font-weight:bold;">remisiones-de-materiales.streamlit.app</a></td>
                </tr>
                <tr style="border-bottom: 1px solid #E2E8F0; background: #FFFFFF;">
                    <td style="padding: 10px 14px;"><b>✂️ Control de Corte y Doblez</b></td>
                    <td style="padding: 10px 14px;">Programación de corte láser, doblado CNC y monitoreo de piso</td>
                    <td style="padding: 10px 14px;"><code>:8503</code></td>
                    <td style="padding: 10px 14px;"><a href="https://control-corte-doblez.streamlit.app/" target="_blank" style="color:#EC2024; font-weight:bold;">control-corte-doblez.streamlit.app</a></td>
                </tr>
                <tr style="border-bottom: 1px solid #E2E8F0; background: #F8F9FA;">
                    <td style="padding: 10px 14px;"><b>🛒 PO Tracker & Requerimientos</b></td>
                    <td style="padding: 10px 14px;">Seguimiento de órdenes de compra, dossiers técnicos y compras</td>
                    <td style="padding: 10px 14px;"><code>:8501</code></td>
                    <td style="padding: 10px 14px;"><a href="https://sigramapotracker.streamlit.app/" target="_blank" style="color:#EC2024; font-weight:bold;">sigramapotracker.streamlit.app</a></td>
                </tr>
                <tr style="border-bottom: 1px solid #E2E8F0; background: #FFFFFF;">
                    <td style="padding: 10px 14px;"><b>🛡️ Calidad en Recepción (Incoming)</b></td>
                    <td style="padding: 10px 14px;">Validación de materia prima recibida y criterios de aceptación</td>
                    <td style="padding: 10px 14px;"><code>:8505</code></td>
                    <td style="padding: 10px 14px;"><a href="https://incoming-calidad.streamlit.app/" target="_blank" style="color:#EC2024; font-weight:bold;">incoming-calidad.streamlit.app</a></td>
                </tr>
                <tr style="border-bottom: 1px solid #E2E8F0; background: #F8F9FA;">
                    <td style="padding: 10px 14px;"><b>👥 Prenómina y Asistencia</b></td>
                    <td style="padding: 10px 14px;">Control de reloj checador, turnos, retardos, horas extra e incidencias</td>
                    <td style="padding: 10px 14px;"><code>:8508</code></td>
                    <td style="padding: 10px 14px;"><a href="https://sig-prenomina-app.streamlit.app/" target="_blank" style="color:#EC2024; font-weight:bold;">sig-prenomina-app.streamlit.app</a></td>
                </tr>
                <tr style="background: #FFFFFF;">
                    <td style="padding: 10px 14px;"><b>⚙️ Matriz MCE SIGRAMA</b></td>
                    <td style="padding: 10px 14px;">Estructura de procesos de manufactura y criterios de ensamble</td>
                    <td style="padding: 10px 14px;"><code>:8509</code></td>
                    <td style="padding: 10px 14px;"><a href="https://matriz-mce.streamlit.app/" target="_blank" style="color:#EC2024; font-weight:bold;">matriz-mce.streamlit.app</a></td>
                </tr>
            </tbody>
        </table>
        """, unsafe_allow_html=True)

        st.info("🔐 **Arquitectura Single Sign-On (SSO):** Al iniciar sesión como Administrador en la Concentradora (puerto `8080` o en la nube), el sistema transmite de manera cifrada los parámetros `sso_user`, `sso_role` y `sso_token`, autenticando de inmediato tu acceso sin requerir volver a escribir usuario ni clave en ninguna app.")

    # =========================================================================
    # TAB 4: FICHA TÉCNICA & DESCARGAS
    # =========================================================================
    with tab_ficha:
        st.markdown("### 📥 Descargar Ficha Técnica Oficial de Industria 4.0")
        st.markdown("""
            Puedes emitir y descargar el documento técnico formal del sistema con sellos corporativos, 
            diseñado bajo estándares de ingeniería y calidad para respaldar auditorías de clientes y acreditaciones del SGC.
        """)

        from src.pdf_generator import generate_first_piece_pdf
        dummy_piece = {
            "numero_pieza": "SIG-IND4.0",
            "nombre_sku": "FICHA TECNICA - MANUFACTURA INTELIGENTE SIGRAMA",
            "material": "ACERO / ALUMINIO / SHEET METAL",
            "espesor_materia_prima": 0.0,
            "acabado_estandar": "IND-4.0",
            "factor_k": 33,
            "version": "V2.0",
            "revision": "R0",
            "ancho_materia_prima": 0.0,
            "largo_materia_prima": 0.0,
            "ruta_almacenamiento": "/SIGRAMA/Ingenieria/Industria_4_0/",
            "usuario_registro": "Dirección de Calidad e Ingeniería",
            "archivo_step": None
        }
        
        try:
            pdf_bytes = generate_first_piece_pdf(dummy_piece)
            st.download_button(
                label="📥 Descargar Ficha Oficial de Industria 4.0 (PDF)",
                data=pdf_bytes,
                file_name=f"Ficha_Tecnica_Industria_4_0_SIGRAMA_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                key="btn_download_ind_40_pdf",
                use_container_width=True
            )
        except Exception as e_pdf:
            st.error(f"Error al compilar Ficha Técnica PDF: {str(e_pdf)}")
