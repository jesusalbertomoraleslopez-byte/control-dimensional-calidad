import streamlit as st

def show_manual():
    st.title("7. Manual de Operación")
    st.subheader("Guía Interactiva Paso a Paso para Operadores y Administradores de Calidad")
    
    st.markdown("""
        Este manual le guiará a través del uso y flujos principales de la aplicación web de Control Dimensional de Calidad de SIGRAMA.
    """)
    
    st.markdown("---")
    
    # Use expanders for interactive steps
    with st.expander("🔑 Paso 1: Inicio de Sesión y Control de Accesos"):
        st.markdown("""
            1. Ingrese a la aplicación y localice la pantalla de **Iniciar Sesión**.
            2. Proporcione sus credenciales. El sistema cuenta con dos perfiles diferenciados:
               * **Operador:** Autorizado para realizar registros de diseño, liberar primeras piezas y capturar mediciones en piso.
               * **Administrador:** Además de las funciones de captura, cuenta con permisos exclusivos en la sección de **8. Área de Mantenimiento** para editar mediciones erróneas o borrar registros.
            3. Una vez autenticado, se habilitará el menú de navegación lateral numerado.
        """)
        
    with st.expander("📁 Paso 2: Registro de Diseño e Ingeniería (Sección 3.2)"):
        st.markdown("""
            1. Diríjase a la pestaña **3.2.1. Registro de Diseño e Ingeniería**.
            2. Complete los campos del formulario: Número de pieza, Material, Acabado, Factor K, Versión y Revisión.
            3. Observe cómo el sistema genera automáticamente el **SKU Concatenado** en tiempo real.
            4. Suba los **6 archivos obligatorios** de diseño (Dibujo original, DXF, Plano de control, SLDDRW, SLDPRT y el resumen de dimensiones en XLSX).
            5. Presione el botón azul **Guardar Registro y Crear Carpetas** para confirmar el SKU y crear la estructura de almacenamiento.
            6. El sistema creará físicamente la jerarquía de carpetas correspondientes en el servidor y descargará un informe en PDF de respaldo de la acción.
            7. **Importación Masiva (Pestaña 3.2.4):** Si cuenta con múltiples piezas preparadas en carpetas compartidas de red con el formato de nombre `INGXXXX - SKU`, ingrese la ruta del directorio y presione **Escanear**. Se presentará una tabla interactiva con casillas de verificación donde podrá inspeccionar qué archivos fueron encontrados y seleccionar explícitamente cuáles importar.
        """)
        
    with st.expander("✔ Paso 3: Liberación de Primera Pieza (Sección 3.2.2)"):
        st.markdown("""
            1. Diríjase a la pestaña **3.2.2. Validación de Primera Pieza**.
            2. Seleccione la pieza recién dada de alta de la lista desplegable.
            3. Suba el archivo escaneado en PDF del **Plano Validado Impreso** firmado.
            4. Confirme que las medidas coincidan marcando la casilla de verificación y presione **Liberar Componente**.
            5. El sistema generará el **Certificado de Primera Pieza Válida** y habilitará el SKU para su captura en piso de producción.
        """)
        
    with st.expander("📦 Paso 4: Módulo Generador de Paquetes para Nesting (Sección 3.2.3)"):
        st.markdown("""
            1. En la sección 3.2, ingrese a la pestaña **3.2.3. Módulo Generador de Paquetes (Nesteo)**.
            2. Descargue la plantilla Excel de muestra si no la tiene.
            3. Prepare su lista de nido especificando la secuencia de ítems, SKU y cantidad de piezas requeridas.
            4. Suba el Excel y presione **Procesar y Generar ZIP de Nesteo**.
            5. Descargue el archivo ZIP. El sistema habrá copiado los DXF de las piezas y los habrá organizado en carpetas por material, renombrados con prefijo de ítem y sufijo de cantidad.
        """)
        
    with st.expander("⚡ Paso 5: Captura en Piso y Gráficos SPC (Sección 3.3)"):
        st.markdown("""
            1. Diríjase a la sección **3.3. Captura en Piso**.
            2. Seleccione el SKU a medir. El sistema validará si está liberado (primera pieza aprobada).
            3. Seleccione el operador, turno y herramental (V de doblez).
            4. **Estación Corte Láser:** Capture las 3 muestras para Largo, Ancho y Diámetro. Revise el estatus PASA/FUERA y la Campana de Gauss interactiva. Presione **Guardar Lote Láser** para registrar y descargar el reporte SPC.
            5. **Estación Doblez:** Capture las 3 muestras para las cotas de la A a la J. Marque el estatus del Gauge de Perfil (Embona/No Embona). Presione **Guardar Lote Doblez** para registrar y descargar el reporte SPC en PDF.
        """)
        
    with st.expander("🔍 Paso 6: Consultas y Mantenimiento (Secciones 2 y 8)"):
        st.markdown("""
            1. **Área de Consulta (Sección 2):** Permite buscar lotes históricos aplicando filtros por SKU, operador, turno, rango de fechas o estatus de aprobación. Permite re-descargar los reportes SPC en PDF generados.
            2. **Área de Mantenimiento (Sección 8):** Exclusivo para administradores. Permite modificar cotas incorrectas capturadas por error del operador, borrar lotes de prueba y realizar limpieza del repositorio local/GitHub.
        """)
        
    st.markdown("---")
    st.markdown("### 📥 Descargar Manual de Operación Completo (PDF)")
    st.markdown("""
        Puede descargar este manual en formato PDF corporativo oficial para capacitación de personal o carpetas del SGC.
    """)
    
    from src.pdf_generator import generate_first_piece_pdf
    dummy_piece = {
        "numero_pieza": "MAN-OPE-01",
        "nombre_sku": "MANUAL DE OPERACION - APP DIMENSIONAL SIGRAMA",
        "material": "N/A",
        "espesor_materia_prima": 0.0,
        "acabado_estandar": "OPE-01",
        "factor_k": 0,
        "version": "V1",
        "revision": "R0",
        "ancho_materia_prima": 0.0,
        "largo_materia_prima": 0.0,
        "ruta_almacenamiento": "/Documentos/Manuales/",
        "usuario_registro": "Aseguramiento de Calidad",
        "archivo_step": None
    }
    pdf_bytes = generate_first_piece_pdf(dummy_piece)
    
    st.download_button(
        label="📥 Descargar Manual de Operación (PDF)",
        data=pdf_bytes,
        file_name="Manual_Operacion_Sistema_Dimensional_SIGRAMA.pdf",
        mime="application/pdf",
        key="btn_download_manual_pdf"
    )
