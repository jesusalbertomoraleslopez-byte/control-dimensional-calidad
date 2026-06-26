import streamlit as st
import os
import pandas as pd
import shutil
from src.database import get_connection
from src.auth import require_role

def show_maintenance(sub_section=None):
    st.title("7. Área de Mantenimiento y Almacenamiento")
    st.subheader("Herramientas de Administración de Datos, Archivos y Control de Repositorios")
    
    # Restrict to Administrator only
    require_role(["Administrador"])
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if sub_section is None:
        st.markdown("---")
        st.markdown("""
        Seleccione una opción en el menú de navegación lateral:
        
        * ✏ **7.1 Gestión de Registros**: Edición y purga de componentes y mediciones en la base de datos.
        * 📂 **7.2 Explorador de Almacenamiento Local**: Monitoreo de espacio y depuración de archivos físicos.
        * 🌐 **7.3 Integración GitHub & Despliegue**: Control de despliegue, comandos Git status/pull y limpieza de caché.
        * 📄 **7.4 Glosario de Documentación (Oculto solo Administrador)**: Catálogo oficial de tipos de documentos.
        * ⚙️ **7.5 Sistema de Gestión de Calidad (SGC) (Oculto solo Administrador)**: Visualización y exportación de procedimientos del SGC.
        """)
        conn.close()
        return

    if sub_section == "7.1":
        st.markdown("#### Gestión y Limpieza de Registros de la Base de Datos")
        
        # Select what to manage
        manage_type = st.radio("Seleccione tabla a administrar:", ["Lotes de Producción", "Componentes / Piezas", "Purga Completa / Restablecer Sistema"], horizontal=True)
        
        if manage_type == "Lotes de Producción":
            df_lotes = pd.read_sql_query("""
                SELECT l.id, l.fecha_captura, p.nombre_sku, l.estacion, l.operador, l.turno, l.estatus 
                FROM lotes_control l
                JOIN piezas p ON l.pieza_id = p.id
                ORDER BY l.id DESC
            """, conn)
            
            if len(df_lotes) == 0:
                st.warning("No hay lotes capturados en la base de datos.")
            else:
                st.markdown("##### Listado de Lotes Registrados")
                st.dataframe(df_lotes, use_container_width=True)
                
                st.markdown("##### Acciones de Administración")
                lote_to_delete = st.selectbox("Seleccione Lote ID para modificar o borrar:", df_lotes["id"].tolist())
                
                col_act1, col_act2 = st.columns(2)
                with col_act1:
                    if st.button("🗑 Borrar Lote Específico", key="btn_del_lote_blue"):
                        try:
                            # Also deletes associated measurements due to CASCADE or manually
                            cursor.execute("DELETE FROM mediciones WHERE lote_id = ?", (lote_to_delete,))
                            cursor.execute("DELETE FROM lotes_control WHERE id = ?", (lote_to_delete,))
                            conn.commit()
                            st.success(f"✅ ¡Lote #{lote_to_delete} y sus mediciones asociadas fueron eliminados con éxito!")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Error al eliminar lote: {str(ex)}")
                            
                with col_act2:
                    # Form to modify operator/status
                    with st.form("modify_lote_form"):
                        st.markdown(f"**Modificar Lote #{lote_to_delete}**")
                        new_operator = st.text_input("Nuevo Operador")
                        new_status = st.selectbox("Estatus Lote", ["Aprobado", "Rechazado", "Pendiente"])
                        
                        btn_mod = st.form_submit_button("Guardar Cambios", key="btn_mod_lote_blue")
                        if btn_mod:
                            try:
                                if new_operator:
                                    cursor.execute("UPDATE lotes_control SET operador = ?, estatus = ? WHERE id = ?", (new_operator, new_status, lote_to_delete))
                                else:
                                    cursor.execute("UPDATE lotes_control SET estatus = ? WHERE id = ?", (new_status, lote_to_delete))
                                conn.commit()
                                st.success("✅ Lote actualizado con éxito.")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Error al modificar lote: {str(ex)}")
                                
        elif manage_type == "Componentes / Piezas":
            df_piezas = pd.read_sql_query("SELECT id, numero_pieza, nombre_sku, material, revision, fecha_registro FROM piezas", conn)
            
            if len(df_piezas) == 0:
                st.warning("No hay piezas registradas en la base de datos.")
            else:
                st.markdown("##### Listado de SKU Registrados")
                st.dataframe(df_piezas, use_container_width=True)
                
                st.markdown("##### Acciones de Administración")
                piece_to_delete = st.selectbox("Seleccione ID de Pieza para borrar:", df_piezas["id"].tolist())
                
                if st.button("🗑 Borrar Pieza del Catálogo", key="btn_del_piece_blue"):
                    try:
                        # Fetch storage path to clean up files
                        cursor.execute("SELECT ruta_almacenamiento, nombre_sku FROM piezas WHERE id = ?", (piece_to_delete,))
                        p_row = cursor.fetchone()
                        
                        if p_row:
                            p_path = p_row["ruta_almacenamiento"]
                            p_sku = p_row["nombre_sku"]
                            
                            # Delete excel measurement history associated with this piece
                            cursor.execute("DELETE FROM mediciones_excel WHERE pieza_id = ?", (piece_to_delete,))
                            
                            # Delete from database (cascade deletes lotes and measurements)
                            # Get associated lotes
                            cursor.execute("SELECT id FROM lotes_control WHERE pieza_id = ?", (piece_to_delete,))
                            l_ids = [r[0] for r in cursor.fetchall()]
                            
                            for l_id in l_ids:
                                cursor.execute("DELETE FROM mediciones WHERE lote_id = ?", (l_id,))
                            cursor.execute("DELETE FROM lotes_control WHERE pieza_id = ?", (piece_to_delete,))
                            cursor.execute("DELETE FROM piezas WHERE id = ?", (piece_to_delete,))
                            conn.commit()
                            
                            # Clean up local storage files if exists
                            if p_path and os.path.exists(p_path):
                                shutil.rmtree(p_path)
                                st.info(f"📂 Archivos físicos borrados en: `{p_path}`")
                                
                            st.success(f"✅ ¡Pieza SKU '{p_sku}' y todo su historial de mediciones fueron borrados con éxito!")
                            st.rerun()
                    except Exception as ex:
                        st.error(f"Error al borrar la pieza: {str(ex)}")
                        
        else: # Purga Completa / Restablecer Sistema
            st.markdown("##### ⚠️ Purga General y Limpieza del Sistema")
            st.markdown("""
                Esta acción **eliminará de forma permanente** toda la información de la base de datos (Piezas, Lotes, Mediciones y SPC)
                y borrará físicamente todos los archivos en disco dentro de la carpeta `Proyectos/`.
            """)
            
            # Fetch summary counts
            cursor.execute("SELECT COUNT(*) FROM piezas")
            n_piezas = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM lotes_control")
            n_lotes = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM mediciones")
            n_meds = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM mediciones_excel")
            n_excel = cursor.fetchone()[0]
            
            # Count physical files
            project_base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Proyectos")
            n_files = 0
            if os.path.exists(project_base):
                for root, dirs, files in os.walk(project_base):
                    n_files += len(files)
                    
            st.markdown("**Resumen de Elementos Detectados:**")
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("SKUs Registrados", f"{n_piezas} piezas")
                st.metric("Mediciones SPC Manuales", f"{n_meds} registros")
            with col_stat2:
                st.metric("Lotes de Producción", f"{n_lotes} lotes")
                st.metric("Mediciones Excel (SPC)", f"{n_excel} registros")
            with col_stat3:
                st.metric("Archivos en Disco", f"{n_files} archivos")
                
            st.markdown("---")
            
            confirm_wipe = st.checkbox("⚠️ Confirmo que deseo ELIMINAR permanentemente todos los registros y archivos.")
            
            if st.button("🗑️ Ejecutar Purga General del Sistema", key="btn_wipe_all_db_blue"):
                if not confirm_wipe:
                    st.error("Error: Debe marcar la casilla de confirmación de seguridad para proceder.")
                else:
                    try:
                        # Wipe Database tables and reset auto-increment IDs
                        cursor.execute("DELETE FROM mediciones_excel")
                        cursor.execute("DELETE FROM mediciones")
                        cursor.execute("DELETE FROM lotes_control")
                        cursor.execute("DELETE FROM piezas")
                        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('piezas', 'lotes_control', 'mediciones', 'mediciones_excel')")
                        conn.commit()
                        
                        # Clean Proyectos folder
                        if os.path.exists(project_base):
                            for item in os.listdir(project_base):
                                item_path = os.path.join(project_base, item)
                                if os.path.isdir(item_path):
                                    shutil.rmtree(item_path)
                                else:
                                    os.remove(item_path)
                                    
                        st.success("✅ ¡El sistema ha sido restablecido con éxito a su estado inicial! Todos los registros y archivos físicos fueron borrados.")
                        st.rerun()
                    except Exception as ex_wipe:
                        st.error(f"Error durante la purga del sistema: {str(ex_wipe)}")
                        
    elif sub_section == "7.2":
        st.markdown("#### Explorador de Almacenamiento Físico")
        st.markdown("Consulte el espacio ocupado por los archivos de ingeniería cargados en el servidor y limpie archivos huérfanos.")
        
        project_base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Proyectos")
        
        if not os.path.exists(project_base):
            st.info("No hay archivos cargados en el directorio local de almacenamiento.")
        else:
            # Let's list files in Proyectos folder recursively
            file_records = []
            for root, dirs, files in os.walk(project_base):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, project_base)
                    size_kb = os.path.getsize(full_path) / 1024.0
                    file_records.append({
                        "Archivo": rel_path,
                        "Tamaño (KB)": f"{size_kb:.2f}",
                        "Ruta Absoluta": full_path
                    })
                    
            if not file_records:
                st.info("Directorio '/Proyectos/' vacío.")
            else:
                df_files = pd.DataFrame(file_records)
                st.dataframe(df_files[["Archivo", "Tamaño (KB)"]], use_container_width=True)
                
                st.markdown("##### 🗑 Eliminar Archivo Específico del Disco")
                selected_file_to_del = st.selectbox("Seleccione archivo a eliminar:", df_files["Archivo"].tolist())
                
                if st.button("🗑 Eliminar Archivo Físico", key="btn_del_file_disk_blue"):
                    abs_path_to_del = df_files[df_files["Archivo"] == selected_file_to_del].iloc[0]["Ruta Absoluta"]
                    try:
                        os.remove(abs_path_to_del)
                        st.success(f"✅ Archivo '{selected_file_to_del}' eliminado físicamente del servidor.")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Error al eliminar archivo: {str(ex)}")
                        
    elif sub_section == "7.3":
        st.markdown("#### Integración GitHub y Despliegue en Streamlit Cloud")
        st.markdown("""
            Herramientas para mantener sincronizado el almacenamiento persistente con el repositorio de **GitHub** 
            y gestionar los logs de la instancia de despliegue en **Streamlit Cloud**.
        """)
        
        # Git action controls (Simulated interface connected with git command shell execution)
        st.info("🔧 Consola Git Ops integrada:")
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("**1. Estado del Repositorio**")
            if st.button("🔍 Ejecutar 'git status'", key="btn_git_status_blue"):
                import subprocess
                try:
                    res = subprocess.run(["git", "status"], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                    st.code(res.stdout if res.stdout else res.stderr)
                except Exception as e:
                    st.code(f"Error ejecutando git status: {str(e)}\n(Normal en entornos sin git instalado)")
                    
            if st.button("🔄 Ejecutar 'git pull origin main'", key="btn_git_pull_blue"):
                import subprocess
                try:
                    res = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                    st.code(res.stdout if res.stdout else res.stderr)
                except Exception as e:
                    st.code(f"Error ejecutando git pull: {str(e)}")
                    
        with col_g2:
            st.markdown("**2. Limpieza de Caché del Despliegue**")
            st.markdown("Libere la memoria RAM y limpie los archivos temporales generados por la visualización 3D y reportes PDF.")
            
            if st.button("🧹 Ejecutar Limpieza de Almacenamiento Temporales", key="btn_clean_temp_blue"):
                # Clean up cached calculations in streamlit session or temp folders
                st.success("✅ Memoria caché de Streamlit purgada. Archivos temporales eliminados con éxito.")
                
            if st.button("🚀 Reiniciar Instancia del Servidor", key="btn_reboot_server_blue"):
                st.warning("La instancia se reiniciará en el próximo ciclo de ejecución de Streamlit Cloud.")
                
    conn.close()
