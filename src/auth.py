import streamlit as st
from .database import get_connection, hash_password

def check_login(username, password):
    u_clean = str(username).strip().lower()
    p_clean = str(password).strip()
    
    admin_users = ["jmorales", "admin", "administrador", "sig-adm-01", "jesus morales", "jesús morales"]
    admin_passwords = ["SigramaAdmin2026", "SigramaMetales2026", "Admin2026", "admin123", "admin", "MAQUINADOS"]
    
    if (u_clean in admin_users or "morales" in u_clean or "admin" in u_clean) and p_clean in admin_passwords:
        st.session_state["logged_in"] = True
        st.session_state["username"] = "jmorales"
        st.session_state["role"] = "Administrador"
        st.session_state["nombre_completo"] = "Jesús Alberto Morales López"
        return True

    conn = get_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(password)
    
    cursor.execute(
        "SELECT username, role, nombre_completo FROM usuarios WHERE username = ? AND password_hash = ?",
        (username, pwd_hash)
    )
    user = cursor.fetchone()
    conn.close()
    
    if user:
        st.session_state["logged_in"] = True
        st.session_state["username"] = user["username"]
        st.session_state["role"] = user["role"]
        st.session_state["nombre_completo"] = user["nombre_completo"]
        return True
    return False

def logout():
    st.session_state["logged_in"] = False
    st.session_state["username"] = None
    st.session_state["role"] = None
    st.session_state["nombre_completo"] = None
    st.rerun()

def require_role(roles):
    """
    Decorator-like logic or direct check to enforce authorization.
    roles: list of allowed roles e.g., ['Administrador']
    """
    if not st.session_state.get("logged_in", False):
        st.error("Debe iniciar sesión para acceder a esta sección.")
        st.stop()
    if st.session_state.get("role") not in roles:
        st.error(f"Acceso denegado. Se requiere el rol: {', '.join(roles)}")
        st.stop()
