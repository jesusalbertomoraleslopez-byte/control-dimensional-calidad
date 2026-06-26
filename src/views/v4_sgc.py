import streamlit as st
import os

def show_sgc():
    st.title("Sistema de Gestión de Calidad (SGC)")
    st.subheader("Boceto de Procedimiento y Control Documental")
    
    st.markdown("""
        > [!NOTE]
        > Por motivos de seguridad y confidencialidad de la empresa, **los procedimientos oficiales no se despliegan en pantalla** en ninguna sección de la aplicación para evitar copias no autorizadas.
        
        Puedes descargar el archivo oficial **`Procedimiento.md`** a continuación. Este archivo sirve como boceto del procedimiento siempre actualizado con todos los cambios recientes hechos al sistema de control dimensional de SIGRAMA.
    """)
    
    # Slogan of Transformation
    st.markdown("""
        <div style="background-color: #111111; border-left: 6px solid #EC2024; padding: 1.5rem; border-radius: 8px; margin: 2rem 0; text-align: center;">
            <p style="color: #FFFFFF; font-weight: 800; font-size: 1.2rem; letter-spacing: 1px; margin: 0; font-family: 'Montserrat', sans-serif;">
                SOLUCIONES QUE TRANSFORMAN TU EMPRESA
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Markdown content for Procedimiento.md
    procedimiento_content = """# PROCEDIMIENTO GENERAL DE CONTROL DE CALIDAD - SIGRAMA

**Código:** [En revisión por SGC]  
**Versión:** 4.0  
**Fecha de Actualización:** 26/06/2026  
**Estatus:** Activo - Boceto de Procedimiento Integrado al Sistema  

---

## 1. OBJETIVO
Establecer los lineamientos, metodologías y responsabilidades obligatorias para realizar el control de calidad dimensional en los componentes y piezas de chapa metálica fabricados por Industria SIGRAMA, utilizando la aplicación web centralizada de control dimensional y herramientas estadísticas (SPC).

## 2. ALCANCE
Aplica a todos los procesos de:
- **Ingeniería de Diseño:** Para el registro de piezas, carga de DXF, STEP, SolidWorks y tablas de tolerancias.
- **Producción (Corte Láser y Dobladora CNC):** Para la captura en piso de las muestras físicas (n=3).
- **Control de Calidad:** Para la liberación de primeras piezas, análisis estadístico de habilidad de proceso (Cp/Cpk), y consolidación de remisiones.

## 3. PROCEDIMIENTO Y FLUJO DE TRABAJO

### 3.1. Registro del Diseño
El Diseñador debe registrar el componente en el sistema generando el SKU concatenado oficial. Es obligatorio cargar:
1. Dibujo original del cliente (.PDF)
2. Desplegado (.DXF)
3. Plano de control (.PDF)
4. Plano nativo de diseño 3D (.SLDDRW)
5. Dibujo nativo 2D (.SLDPRT)
6. Excel de especificaciones de tolerancias (.XLSX)
7. Modelo 3D (.STEP) para el visualizador interactivo.

### 3.2. Liberación de Primera Pieza
Antes de arrancar la producción de un lote, el Auditor de Calidad debe inspeccionar la primera pieza física contra el plano de control, subir la evidencia escaneada y marcar la pieza como **LIBERADA** en el sistema.

### 3.3. Captura de Mediciones en Piso (Muestreo n=3)
El Operador en planta debe realizar la medición de 3 muestras físicas por cada lote y capturar las dimensiones de largo, ancho y cotas de doblez (A-J) en la aplicación local (`localhost:8501`).

### 3.4. Análisis Estadístico y Cp/Cpk
La aplicación calculará automáticamente los índices de capacidad de proceso (Cp y Cpk). El estándar de aceptación para SIGRAMA es:
- **Cpk >= 1.33:** Proceso capaz. El lote se aprueba para embarque.
- **Cpk < 1.33:** Proceso no capaz. Se debe detener la producción para ajustar la maquinaria (Láser o Dobladora) y recalibrar.

### 3.5. Consolidación de Remisiones
El Administrador generará el reporte consolidado de remisión diaria en PDF que avala la calidad dimensional del embarque frente al cliente final.

---

## 4. REGISTRO DE CAMBIOS Y ACTUALIZACIONES DEL SISTEMA
- **Junio 2026:**
  - Implementación de visualización 3D interactiva WebGL con centrado automático (zoom-to-fit) adaptativo para pantalla completa.
  - Integración del botón de ajuste rápido "Zoom All" para re-encuadrar modelos sin perder la rotación manual.
  - Restructuración jerárquica del menú principal según catálogo de cuentas de la empresa.
  - Inyección de imagen corporativa oficial con tipografías *Questrial* y *Montserrat* y colores institucionales (Rojo #EC2024 y Negro #111111).
  - Implementación del módulo de Importación Masiva mediante carga de archivos comprimidos (.ZIP) en servidores Streamlit Cloud.
  - Restricción de visibilidad y descargas nativas en Word/PDF de control documental para SGC.

---
_Ingeniería que da resultados!!_
"""

    st.download_button(
        label="📥 Descargar Boceto de Procedimiento (Procedimiento.md)",
        data=procedimiento_content,
        file_name="Procedimiento.md",
        mime="text/markdown",
        key="btn_download_procedimiento_md"
    )
    
    st.markdown("<br/><br/>", unsafe_allow_html=True)
    
    # Slogan of Results
    st.markdown("""
        <div style="text-align: right; margin-top: 2rem;">
            <p style="font-family: 'Montserrat', sans-serif; font-style: italic; font-weight: bold; color: #EC2024; font-size: 1.1rem; margin: 0;">
                Ingeniería que da resultados!!
            </p>
            <hr style="border: 0; border-top: 2px solid #EC2024; width: 100px; margin: 0.3rem 0 0 auto;">
        </div>
    """, unsafe_allow_html=True)
