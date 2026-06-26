import streamlit as st
from .database import get_connection, hash_password

def check_login(username, password):
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
