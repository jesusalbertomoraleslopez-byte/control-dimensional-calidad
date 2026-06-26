import streamlit as st

def show_industry_40():
    st.title("6. Manufactura Inteligente e Industria 4.0")
    st.subheader("La Digitalización y el Aseguramiento Metrológico en SIGRAMA")
    
    st.markdown("""
        La integración del **Control Estadístico de Procesos (SPC)** y la automatización del control dimensional en esta aplicación web
        responden a los estándares globales de **Industria 4.0** y **Manufactura Inteligente**. A continuación se detallan los pilares
        que justifican, sustentan y estructuran tecnológicamente este proyecto.
    """)
    
    st.markdown("---")
    
    # Grid for Justification & Benefits
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="report-card" style="border-left: 5px solid #EC2024;">
            <h3 style="color:#EC2024; margin-top:0;">🤖 Justificación de Manufactura Inteligente</h3>
            <p>Tradicionalmente, el control metrológico en piso de producción se ha gestionado mediante formatos impresos y hojas de cálculo desconectadas, 
            generando retrasos en la detección de desviaciones y riesgo de pérdida de trazabilidad.</p>
            <p>Este sistema implementa una digitalización activa del dato en el puesto de trabajo (Edge Data Capture). Al centralizar las mediciones del subgrupo (n=3), 
            el sistema realiza un cálculo y renderizado estadístico instantáneo de la capacidad de proceso (Cp y Cpk). Esto permite a los operadores e inspectores de calidad 
            visualizar en tiempo real el comportamiento del herramental y tomar decisiones correctivas preventivas antes de que se generen piezas defectuosas.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="report-card" style="border-left: 5px solid #10b981;">
            <h3 style="color:#10b981; margin-top:0;">🎯 Beneficios Estratégicos</h3>
            <ul>
                <li><b>Reducción de Desperdicios (Scrap):</b> Detección oportuna de desgaste de dados de doblez o desajuste del cabezal láser mediante la Campana de Gauss.</li>
                <li><b>Trazabilidad Digital Completa:</b> Vinculación instantánea del archivo de diseño original (.SLDPRT / .DXF) con las mediciones físicas capturadas en piso y la evidencia en PDF del nido (nesting).</li>
                <li><b>Auditorías Rápidas e Inmediatas:</b> Filtros de búsqueda dinámicos por SKU, operador o lote que reducen el tiempo de preparación de auditorías del SGC de horas a segundos.</li>
                <li><b>Agilidad en Ingeniería:</b> Generación automática del SKU concatenado y de las carpetas jerárquicas en el servidor, minimizando errores humanos en la organización de planos.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    # Technology Stack
    st.subheader("💻 Resumen del Stack Tecnológico Empleado")
    st.markdown("""
        La aplicación está construida sobre una arquitectura robusta, ligera y escalable, utilizando estándares de software moderno de código abierto:
    """)
    
    tech_col1, tech_col2, tech_col3 = st.columns(3)
    
    with tech_col1:
        st.markdown("""
        <div style="background-color: #f1f5f9; padding: 1.2rem; border-radius: 8px; min-height: 160px; border: 1px solid #e2e8f0;">
            <h4 style="margin-top:0; color:#334155;">🐍 Backend & Lógica</h4>
            <p style="font-size:13px; margin:0;">
                <b>Python 3:</b> Motor lógico del sistema.<br/>
                <b>SQLAlchemy / SQLite:</b> Motor de persistencia estructurado para registros de metadatos y mediciones de piso.<br/>
                <b>Pandas & NumPy:</b> Procesamiento ágil de datos matriciales y estructuración del Excel de nido.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with tech_col2:
        st.markdown("""
        <div style="background-color: #f1f5f9; padding: 1.2rem; border-radius: 8px; min-height: 160px; border: 1px solid #e2e8f0;">
            <h4 style="margin-top:0; color:#334155;">🎨 Frontend & UX</h4>
            <p style="font-size:13px; margin:0;">
                <b>Streamlit:</b> Framework ágil para interfaces de ciencia de datos y control de procesos en tiempo real.<br/>
                <b>Three.js (WebGL):</b> Renderizado CAD 3D dinámico en el navegador del operador sin requerir software instalado.<br/>
                <b>Plotly:</b> Gráficos interactivos de capacidad de proceso y campanas de Gauss.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with tech_col3:
        st.markdown("""
        <div style="background-color: #f1f5f9; padding: 1.2rem; border-radius: 8px; min-height: 160px; border: 1px solid #e2e8f0;">
            <h4 style="margin-top:0; color:#334155;">📄 Reportes & Git Ops</h4>
            <p style="font-size:13px; margin:0;">
                <b>ReportLab:</b> Generador dinámico de reportes en PDF corporativos con firmas y metadatos de control.<br/>
                <b>Zipfile & Openpyxl:</b> Compresión automática de DXF en nidos por material para ProNest.<br/>
                <b>GitHub Integration:</b> Trazabilidad de código y despliegue continuo en la nube de Streamlit.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Universal PDF download for the documentation
    st.markdown("### 📥 Descargar Ficha Técnica de Industria 4.0")
    
    from src.pdf_generator import generate_first_piece_pdf
    dummy_piece = {
        "numero_pieza": "SIG-IND4.0",
        "nombre_sku": "FICHA TECNICA - MANUFACTURA INTELIGENTE SIGRAMA",
        "material": "N/A",
        "espesor_materia_prima": 0.0,
        "acabado_estandar": "IND-4.0",
        "factor_k": 0,
        "version": "V1",
        "revision": "R0",
        "ancho_materia_prima": 0.0,
        "largo_materia_prima": 0.0,
        "ruta_almacenamiento": "/Documentos/Fichas/",
        "usuario_registro": "Dirección de Calidad",
        "archivo_step": None
    }
    pdf_bytes = generate_first_piece_pdf(dummy_piece)
    
    st.download_button(
        label="📥 Descargar Ficha de Manufactura Inteligente (PDF)",
        data=pdf_bytes,
        file_name="Ficha_Manufactura_Inteligente_SIGRAMA.pdf",
        mime="application/pdf",
        key="btn_download_ind_40_pdf"
    )
