import streamlit as st
import pandas as pd
import numpy as np
from src.database import get_connection
from src.utils import calculate_spc_stats, generate_gauss_chart
from src.pdf_generator import generate_spc_lote_pdf

def show_floor_capture():
    st.title("3.3. Captura en Piso - Control Estadístico de Proceso (SPC)")
    st.subheader("Captura Dimensional Segmentada por Estación de Trabajo")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Select part SKU
    cursor.execute("SELECT id, nombre_sku, documento_primera_pieza, ruta_almacenamiento FROM piezas")
    pieces = cursor.fetchall()
    
    # Defaults in case DB has no registered parts
    fallback_sku = "12-A-6004-01-(16ga ANSI-61) - K48 - V3-R0"
    
    if not pieces:
        st.warning("⚠️ No hay piezas registradas o validadas en el sistema. Trabajando en Modo Demostración.")
        sku_selected = fallback_sku
        piece_id = 1
        is_validated = True
        dest_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Proyectos", "END_FILLER", "Rev_R0", "FactorK_48", "Espesor_0.060")
    else:
        piece_options = [r["nombre_sku"] for r in pieces]
        sku_selected = st.selectbox("Seleccione el SKU a medir:", piece_options)
        
        piece_row = [r for r in pieces if r["nombre_sku"] == sku_selected][0]
        piece_id = piece_row["id"]
        is_validated = piece_row["documento_primera_pieza"] is not None
        dest_dir = piece_row["ruta_almacenamiento"]
        
        if not is_validated:
            st.error("❌ Este componente no ha sido Validado ni Liberado en la Sección 3.2. La captura en piso está bloqueada para producción.")
            st.stop()
            
    sku = sku_selected
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: space-between; 
                    background-color: #F8F9FA; border: 1px solid #D2D3D5; border-radius: 6px; 
                    padding: 0.5rem 1rem; margin-bottom: 0.8rem; font-family: 'Questrial', sans-serif;">
            <span style="font-family: 'Montserrat', sans-serif; font-weight: bold; font-size: 1.1rem; color: #111111;">
                {sku}
            </span>
            <button onclick="navigator.clipboard.writeText('{sku}').then(() => {{
                const btn = document.getElementById('copy-btn-capture');
                btn.innerHTML = '✅ Copiado!';
                btn.style.backgroundColor = '#16a34a';
                setTimeout(() => {{
                    btn.innerHTML = '📋 Copiar SKU';
                    btn.style.backgroundColor = '#EC2024';
                }}, 2000);
            }})" id="copy-btn-capture" style="
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
    
    # Shift details (General metadata)
    st.markdown("#### 👤 Datos de Control del Lote")
    col_op1, col_op2, col_op3 = st.columns(3)
    with col_op1:
        operator_name = st.text_input("Operador responsable de la medición", value=st.session_state.get("nombre_completo", "Operador de Planta"))
    with col_op2:
        shift = st.selectbox("Turno", ["Turno 1", "Turno 2", "Turno 3"])
    with col_op3:
        v_bending = st.number_input("V de Doblado Utilizada (mm)", value=10.0, step=1.0)
        
    st.markdown("---")
    
    # Tabs for stations
    tab1, tab2 = st.tabs([
        "⚡ Pestaña 3.3.1 - Estación Corte Láser",
        "📐 Pestaña 3.3.2 - Estación Doblez"
    ])
    
    # Dimension specs setup
    laser_specs = {
        "Largo": {"nominal": 19.000, "li": 18.985, "ls": 19.015},
        "Ancho": {"nominal": 3.527, "li": 3.512, "ls": 3.542},
        "Diámetro Φ": {"nominal": 0.312, "li": 0.297, "ls": 0.327}
    }
    
    doblez_specs = {
        "A": {"nominal": 0.630, "li": 0.615, "ls": 0.645},
        "B": {"nominal": 1.250, "li": 1.235, "ls": 1.265},
        "C": {"nominal": 1.880, "li": 1.865, "ls": 1.895},
        "D": {"nominal": 0.380, "li": 0.365, "ls": 0.395},
        "E": {"nominal": 18.630, "li": 18.615, "ls": 18.645},
        "F": {"nominal": 18.130, "li": 18.115, "ls": 18.145},
        "G": {"nominal": 0.880, "li": 0.865, "ls": 0.895},
        "H": {"nominal": 0.630, "li": 0.615, "ls": 0.645},
        "I": {"nominal": 0.380, "li": 0.365, "ls": 0.395},
        "J": {"nominal": 0.031, "li": 0.016, "ls": 0.046}
    }
    
    with tab1:
        st.markdown("#### Captura de Variables - Corte Láser (Subgrupo n=3 piezas)")
        st.markdown(r"""
            Registre las dimensiones críticas de corte extendido. Tolerancia requerida: \(\pm\)0.015 in.
        """)
        
        # Grid input
        m1_col, m2_col, m3_col = st.columns(3)
        
        # Largo measurements
        with m1_col:
            st.markdown("**Muestra 1**")
            laser_l1 = st.number_input("Dim 1 (Largo): M1", value=19.000, format="%.4f")
            laser_a1 = st.number_input("Dim 2 (Ancho): M1", value=3.527, format="%.4f")
            laser_d1 = st.number_input("Dim 3 (Diámetro): M1", value=0.312, format="%.4f")
        with m2_col:
            st.markdown("**Muestra 2**")
            laser_l2 = st.number_input("Dim 1 (Largo): M2", value=19.001, format="%.4f")
            laser_a2 = st.number_input("Dim 2 (Ancho): M2", value=3.526, format="%.4f")
            laser_d2 = st.number_input("Dim 3 (Diámetro): M2", value=0.311, format="%.4f")
        with m3_col:
            st.markdown("**Muestra 3**")
            laser_l3 = st.number_input("Dim 1 (Largo): M3", value=18.999, format="%.4f")
            laser_a3 = st.number_input("Dim 2 (Ancho): M3", value=3.528, format="%.4f")
            laser_d3 = st.number_input("Dim 3 (Diámetro): M3", value=0.312, format="%.4f")
            
        # Real-time statistics and validation
        laser_data_calc = {
            "Largo": [laser_l1, laser_l2, laser_l3],
            "Ancho": [laser_a1, laser_a2, laser_a3],
            "Diámetro Φ": [laser_d1, laser_d2, laser_d3]
        }
        
        results_laser = []
        l_stat_rows = []
        
        for dim, values in laser_data_calc.items():
            spec = laser_specs[dim]
            x_bar = np.mean(values)
            r = np.max(values) - np.min(values)
            
            # Check limits
            pasa = all(spec["li"] <= v <= spec["ls"] for v in values)
            status_str = "🟢 PASA" if pasa else "🔴 FUERA DE TOLERANCIA"
            results_laser.append(pasa)
            
            l_stat_rows.append({
                "Dimensión": dim,
                "Nominal": spec["nominal"],
                "L.I.": spec["li"],
                "L.S.": spec["ls"],
                "Valores": f"{values[0]:.4f}, {values[1]:.4f}, {values[2]:.4f}",
                "Media (X-barra)": f"{x_bar:.4f}",
                "Rango (R)": f"{r:.4f}",
                "Estatus": status_str
            })
            
        st.markdown("##### 📊 Resumen de Resultados de Tolerancia")
        st.table(pd.DataFrame(l_stat_rows))
        
        # Draw Gauss Curve for Laser Dimensions (e.g. Largo)
        st.markdown("##### 🔔 Gráfica de Distribución (Campana de Gauss vs Tolerancias) - Dim 1 (Largo)")
        fig_l = generate_gauss_chart(laser_data_calc["Largo"], 19.000, 18.985, 19.015, "Distribución de Largo en Corte Láser")
        st.plotly_chart(fig_l, use_container_width=True)
        
        # Save Lote Laser
        lote_pasa_laser = all(results_laser)
        if st.button("💾 Guardar Lote Láser y Generar Respaldo PDF", key="btn_save_laser_blue"):
            # Insert to DB
            try:
                cursor.execute(
                    """
                    INSERT INTO lotes_control (pieza_id, operador, turno, estacion, estatus, v_dobladura, gauge_perfil)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (piece_id, operator_name, shift, "Corte Láser", "Aprobado" if lote_pasa_laser else "Rechazado", v_bending, "N/A")
                )
                lote_id = cursor.lastrowid
                
                # Insert measurements
                for i in range(3):
                    cursor.execute(
                        """
                        INSERT INTO mediciones (lote_id, muestra_numero, laser_largo, laser_ancho, laser_diametro)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (lote_id, i+1, laser_data_calc["Largo"][i], laser_data_calc["Ancho"][i], laser_data_calc["Diámetro Φ"][i])
                    )
                conn.commit()
                
                # Generate PDF
                lote_data = {
                    "id": lote_id,
                    "nombre_sku": sku_selected,
                    "estacion": "Corte Láser",
                    "operador": operator_name,
                    "turno": shift,
                    "estatus": "Aprobado" if lote_pasa_laser else "Rechazado",
                    "v_dobladura": v_bending,
                    "gauge_perfil": "N/A",
                    "fecha_captura": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                meas_data = [
                    {"laser_largo": laser_data_calc["Largo"][i], "laser_ancho": laser_data_calc["Ancho"][i], "laser_diametro": laser_data_calc["Diámetro Φ"][i]}
                    for i in range(3)
                ]
                
                # Calculate stats list for PDF
                pdf_stats = []
                for dim, vals in laser_data_calc.items():
                    sp = laser_specs[dim]
                    calc = calculate_spc_stats(vals, sp["nominal"], sp["li"], sp["ls"])
                    pdf_stats.append({
                        "name": dim, "mean": calc["mean"], "std": calc["std"], "cp": calc["cp"], "cpk": calc["cpk"], "status_desc": calc["status_desc"]
                    })
                    
                pdf_bytes = generate_spc_lote_pdf(lote_data, meas_data, pdf_stats)
                
                # Save physically in the component directory
                os.makedirs(dest_dir, exist_ok=True)
                pdf_report_path = os.path.join(dest_dir, f"Reporte_SPC_Laser_Lote_{lote_id}.pdf")
                with open(pdf_report_path, "wb") as f:
                    f.write(pdf_bytes)
                    
                st.success(f"✅ Lote #{lote_id} guardado con éxito. Estatus: " + ("Aprobado ✔" if lote_pasa_laser else "Rechazado ✘"))
                st.info(f"📄 Respaldo PDF automático guardado en el servidor.")
                
                # Immediate PDF download button
                st.download_button(
                    label="📥 Descargar Reporte SPC Láser (PDF)",
                    data=pdf_bytes,
                    file_name=f"Reporte_SPC_Laser_Lote_{lote_id}.pdf",
                    mime="application/pdf",
                    key=f"download_pdf_laser_lote_{lote_id}"
                )
            except Exception as ex:
                st.error(f"Error al guardar mediciones: {str(ex)}")
                
    with tab2:
        st.markdown("#### Captura de Variables - Estación Doblez (Subgrupo n=3 piezas)")
        st.markdown("""
            Registre las 10 cotas dimensionales dobladas (A a J) y marque el criterio del Gauge de Perfil.
        """)
        
        # Setup form layout
        m1_d_col, m2_d_col, m3_d_col = st.columns(3)
        
        doblez_data = {k: [0.0, 0.0, 0.0] for k in doblez_specs.keys()}
        
        with m1_d_col:
            st.markdown("**Muestra 1**")
            doblez_data["A"][0] = st.number_input("Cota A: M1", value=0.630, format="%.3f")
            doblez_data["B"][0] = st.number_input("Cota B: M1", value=1.250, format="%.3f")
            doblez_data["C"][0] = st.number_input("Cota C: M1", value=1.880, format="%.3f")
            doblez_data["D"][0] = st.number_input("Cota D: M1", value=0.380, format="%.3f")
            doblez_data["E"][0] = st.number_input("Cota E: M1", value=18.630, format="%.3f")
            doblez_data["F"][0] = st.number_input("Cota F: M1", value=18.130, format="%.3f")
            doblez_data["G"][0] = st.number_input("Cota G: M1", value=0.880, format="%.3f")
            doblez_data["H"][0] = st.number_input("Cota H: M1", value=0.630, format="%.3f")
            doblez_data["I"][0] = st.number_input("Cota I: M1", value=0.380, format="%.3f")
            doblez_data["J"][0] = st.number_input("Cota J: M1", value=0.031, format="%.3f")
            
        with m2_d_col:
            st.markdown("**Muestra 2**")
            doblez_data["A"][1] = st.number_input("Cota A: M2", value=0.628, format="%.3f")
            doblez_data["B"][1] = st.number_input("Cota B: M2", value=1.248, format="%.3f")
            doblez_data["C"][1] = st.number_input("Cota C: M2", value=1.879, format="%.3f")
            doblez_data["D"][1] = st.number_input("Cota D: M2", value=0.378, format="%.3f")
            doblez_data["E"][1] = st.number_input("Cota E: M2", value=18.629, format="%.3f")
            doblez_data["F"][1] = st.number_input("Cota F: M2", value=18.128, format="%.3f")
            doblez_data["G"][1] = st.number_input("Cota G: M2", value=0.878, format="%.3f")
            doblez_data["H"][1] = st.number_input("Cota H: M2", value=0.628, format="%.3f")
            doblez_data["I"][1] = st.number_input("Cota I: M2", value=0.378, format="%.3f")
            doblez_data["J"][1] = st.number_input("Cota J: M2", value=0.030, format="%.3f")
            
        with m3_d_col:
            st.markdown("**Muestra 3**")
            doblez_data["A"][2] = st.number_input("Cota A: M3", value=0.632, format="%.3f")
            doblez_data["B"][2] = st.number_input("Cota B: M3", value=1.252, format="%.3f")
            doblez_data["C"][2] = st.number_input("Cota C: M3", value=1.882, format="%.3f")
            doblez_data["D"][2] = st.number_input("Cota D: M3", value=0.382, format="%.3f")
            doblez_data["E"][2] = st.number_input("Cota E: M3", value=18.631, format="%.3f")
            doblez_data["F"][2] = st.number_input("Cota F: M3", value=18.132, format="%.3f")
            doblez_data["G"][2] = st.number_input("Cota G: M3", value=0.882, format="%.3f")
            doblez_data["H"][2] = st.number_input("Cota H: M3", value=0.632, format="%.3f")
            doblez_data["I"][2] = st.number_input("Cota I: M3", value=0.382, format="%.3f")
            doblez_data["J"][2] = st.number_input("Cota J: M3", value=0.032, format="%.3f")
            
        st.markdown("##### 🛡️ Criterios de Aceptación del Sistema de Gestión de Calidad (SGC)")
        gauge_status = st.radio("Gauge Perfil de la Pieza (Tabla de Criterios del Plano):", ["Embona", "No Embona"], horizontal=True)
        
        results_doblez = []
        d_stat_rows = []
        
        for cota, values in doblez_data.items():
            spec = doblez_specs[cota]
            x_bar = np.mean(values)
            r = np.max(values) - np.min(values)
            
            pasa = all(spec["li"] <= v <= spec["ls"] for v in values)
            results_doblez.append(pasa)
            status_str = "🟢 PASA" if pasa else "🔴 FUERA"
            
            d_stat_rows.append({
                "Cota": cota,
                "Nominal": spec["nominal"],
                "L.I.": spec["li"],
                "L.S.": spec["ls"],
                "Muestras": f"{values[0]:.3f}, {values[1]:.3f}, {values[2]:.3f}",
                "Media": f"{x_bar:.3f}",
                "Rango": f"{r:.3f}",
                "Estatus": status_str
            })
            
        st.markdown("##### 📊 Resumen de Resultados de Doblez")
        st.table(pd.DataFrame(d_stat_rows))
        
        # Gauss chart for Doblez A
        st.markdown("##### 🔔 Gráfica de Distribución (Campana de Gauss vs Tolerancias) - Cota A")
        fig_a = generate_gauss_chart(doblez_data["A"], 0.630, 0.615, 0.645, "Distribución de Cota A en Estación de Doblez")
        st.plotly_chart(fig_a, use_container_width=True)
        
        # Save Lote Doblez
        lote_pasa_doblez = all(results_doblez) and (gauge_status == "Embona")
        if st.button("💾 Guardar Lote Doblez y Generar Respaldo PDF", key="btn_save_doblez_blue"):
            try:
                cursor.execute(
                    """
                    INSERT INTO lotes_control (pieza_id, operador, turno, estacion, estatus, v_dobladura, gauge_perfil)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (piece_id, operator_name, shift, "Doblez", "Aprobado" if lote_pasa_doblez else "Rechazado", v_bending, gauge_status)
                )
                lote_id = cursor.lastrowid
                
                # Insert measurements
                for i in range(3):
                    cursor.execute(
                        """
                        INSERT INTO mediciones (
                            lote_id, muestra_numero, cota_a, cota_b, cota_c, cota_d, cota_e, cota_f, cota_g, cota_h, cota_i, cota_j
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            lote_id, i+1,
                            doblez_data["A"][i], doblez_data["B"][i], doblez_data["C"][i], doblez_data["D"][i],
                            doblez_data["E"][i], doblez_data["F"][i], doblez_data["G"][i], doblez_data["H"][i],
                            doblez_data["I"][i], doblez_data["J"][i]
                        )
                    )
                conn.commit()
                
                # Generate PDF Report
                lote_data = {
                    "id": lote_id,
                    "nombre_sku": sku_selected,
                    "estacion": "Doblez",
                    "operador": operator_name,
                    "turno": shift,
                    "estatus": "Aprobado" if lote_pasa_doblez else "Rechazado",
                    "v_dobladura": v_bending,
                    "gauge_perfil": gauge_status,
                    "fecha_captura": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Map to standard measurements dict
                meas_data = []
                for i in range(3):
                    row = {"muestra_numero": i+1}
                    for k in doblez_specs.keys():
                        row[f"cota_{k.lower()}"] = doblez_data[k][i]
                    meas_data.append(row)
                    
                # Calculate stats list for PDF
                pdf_stats = []
                for cota, vals in doblez_data.items():
                    sp = doblez_specs[cota]
                    calc = calculate_spc_stats(vals, sp["nominal"], sp["li"], sp["ls"])
                    pdf_stats.append({
                        "name": f"Cota {cota}", "mean": calc["mean"], "std": calc["std"], "cp": calc["cp"], "cpk": calc["cpk"], "status_desc": calc["status_desc"]
                    })
                    
                pdf_bytes = generate_spc_lote_pdf(lote_data, meas_data, pdf_stats)
                
                # Save physically in the component directory
                os.makedirs(dest_dir, exist_ok=True)
                pdf_report_path = os.path.join(dest_dir, f"Reporte_SPC_Doblez_Lote_{lote_id}.pdf")
                with open(pdf_report_path, "wb") as f:
                    f.write(pdf_bytes)
                    
                st.success(f"✅ Lote #{lote_id} guardado con éxito. Estatus: " + ("Aprobado ✔" if lote_pasa_doblez else "Rechazado ✘"))
                st.info(f"📄 Respaldo PDF automático guardado en el servidor.")
                
                # Immediate PDF download button
                st.download_button(
                    label="📥 Descargar Reporte SPC Doblez (PDF)",
                    data=pdf_bytes,
                    file_name=f"Reporte_SPC_Doblez_Lote_{lote_id}.pdf",
                    mime="application/pdf",
                    key=f"download_pdf_doblez_lote_{lote_id}"
                )
            except Exception as ex:
                st.error(f"Error al guardar mediciones de doblez: {str(ex)}")
                
    conn.close()

from datetime import datetime
import os
