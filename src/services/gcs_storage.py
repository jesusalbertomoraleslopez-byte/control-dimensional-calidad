"""
Módulo de Gestión Segura de Google Cloud Storage (GCS) para SIGRAMA
Control Dimensional y Calidad Industrial 4.0

Administra la conexión autenticada con el bucket privado 'sigrama-planos-calidad-2026',
proporcionando lectura, escritura, generación de URLs firmadas temporales y resolución
transparente de archivos tanto en la nube (Streamlit Cloud) como en entorno local.
"""

import os
import io
import mimetypes
from datetime import timedelta
from typing import Optional, Union, Tuple

# Nombre oficial del bucket configurado en Google Cloud
DEFAULT_BUCKET_NAME = "sigrama-planos-calidad-2026"

_client_instance = None
_bucket_instance = None

def _find_credentials_file() -> Optional[str]:
    """Busca un archivo de credenciales JSON local en el directorio credentials/"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cred_dir = os.path.join(base_dir, "credentials")
    if os.path.exists(cred_dir):
        for f in os.listdir(cred_dir):
            if f.endswith(".json"):
                full_path = os.path.join(cred_dir, f)
                if os.path.isfile(full_path):
                    return full_path
    return None

def get_storage_client():
    """
    Obtiene o inicializa el cliente de Google Cloud Storage.
    Detecta automáticamente:
    1. Streamlit Secrets (st.secrets["gcp_service_account"]) para Streamlit Cloud.
    2. Archivo .json en credentials/ para ejecución local.
    3. Variable de entorno GOOGLE_APPLICATION_CREDENTIALS.
    """
    global _client_instance
    if _client_instance is not None:
        return _client_instance

    try:
        from google.cloud import storage
    except ImportError:
        return None

    client = None

    # 1. Intentar desde st.secrets (Streamlit Cloud)
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "gcp_service_account" in st.secrets:
                sa_dict = dict(st.secrets["gcp_service_account"])
                client = storage.Client.from_service_account_info(sa_dict)
            elif "GCP_SERVICE_ACCOUNT" in st.secrets:
                sa_dict = dict(st.secrets["GCP_SERVICE_ACCOUNT"])
                client = storage.Client.from_service_account_info(sa_dict)
    except Exception:
        pass

    # 2. Intentar desde archivo local en credentials/
    if client is None:
        local_key = _find_credentials_file()
        if local_key and os.path.exists(local_key):
            try:
                client = storage.Client.from_service_account_json(local_key)
            except Exception as e:
                print(f"[GCS WARNING] Error cargando credenciales desde {local_key}: {e}")

    # 3. Intentar credenciales por defecto del entorno
    if client is None:
        try:
            client = storage.Client()
        except Exception:
            client = None

    _client_instance = client
    return _client_instance

def get_bucket(bucket_name: str = DEFAULT_BUCKET_NAME):
    """Retorna la instancia del Bucket conectado"""
    global _bucket_instance
    if _bucket_instance is not None and _bucket_instance.name == bucket_name:
        return _bucket_instance

    client = get_storage_client()
    if client is None:
        return None

    try:
        _bucket_instance = client.bucket(bucket_name)
        return _bucket_instance
    except Exception as e:
        print(f"[GCS ERROR] Error al conectar con el bucket {bucket_name}: {e}")
        return None

def is_gcs_available() -> bool:
    """Verifica si Google Cloud Storage está disponible y autenticado"""
    try:
        bucket = get_bucket()
        return bucket is not None
    except Exception:
        return False

def normalize_blob_name(path_or_uri: str) -> str:
    """
    Convierte una ruta absoluta de Windows/Linux o una URI gs:// a un nombre relativo de Blob en GCS.
    Ejemplo: 'C:\\...\\src\\Proyectos\\11-B\\plano.pdf' -> 'Proyectos/11-B/plano.pdf'
    """
    if not path_or_uri:
        return ""

    clean = str(path_or_uri).strip()
    if clean.startswith("gs://"):
        parts = clean[5:].split("/", 1)
        if len(parts) > 1:
            clean = parts[1]
        else:
            clean = parts[0]

    clean = clean.replace("\\", "/")
    if "Proyectos/" in clean:
        idx = clean.find("Proyectos/")
        clean = clean[idx:]
    elif clean.startswith("src/Proyectos/"):
        clean = clean[4:]

    return clean.lstrip("/")

def upload_file_to_gcs(
    source: Union[str, bytes, io.BytesIO],
    destination_blob_name: str,
    content_type: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Sube un archivo físico o en memoria a Google Cloud Storage.
    Retorna (True, 'gs://bucket/blob_name') si fue exitoso, o (False, error_msg).
    """
    bucket = get_bucket()
    if bucket is None:
        return False, "Google Cloud Storage no está configurado o autenticado."

    blob_name = normalize_blob_name(destination_blob_name)
    blob = bucket.blob(blob_name)

    if not content_type:
        guessed, _ = mimetypes.guess_type(blob_name)
        content_type = guessed or "application/octet-stream"

    try:
        if isinstance(source, (str, os.PathLike)):
            if not os.path.exists(source):
                return False, f"El archivo local '{source}' no existe."
            blob.upload_from_filename(str(source), content_type=content_type)
        elif isinstance(source, bytes):
            blob.upload_from_string(source, content_type=content_type)
        elif hasattr(source, "read"):
            source.seek(0)
            blob.upload_from_file(source, content_type=content_type)
        else:
            return False, "Tipo de fuente no compatible para carga a GCS."

        gs_uri = f"gs://{bucket.name}/{blob_name}"
        return True, gs_uri
    except Exception as e:
        return False, f"Error al subir a GCS: {str(e)}"

def get_file_bytes(path_or_uri: Optional[str]) -> Optional[bytes]:
    """
    Obtiene los bytes de un archivo de manera transparente:
    1. Si existe localmente en disco, lo lee del disco.
    2. Si es una URI gs:// o no existe en disco local, intenta descargarlo de GCS.
    """
    if not path_or_uri:
        return None

    # 1. Intentar lectura local
    if os.path.isabs(path_or_uri) and os.path.exists(path_or_uri):
        try:
            with open(path_or_uri, "rb") as f:
                return f.read()
        except Exception:
            pass

    # 2. Intentar lectura desde GCS
    bucket = get_bucket()
    if bucket is None:
        return None

    blob_name = normalize_blob_name(path_or_uri)
    try:
        blob = bucket.blob(blob_name)
        if blob.exists():
            return blob.download_as_bytes()
    except Exception as e:
        print(f"[GCS WARNING] No se pudo descargar {blob_name} de GCS: {e}")

    return None

def generate_secure_signed_url(
    path_or_uri: str,
    expiration_minutes: int = 15
) -> Optional[str]:
    """
    Genera una URL firmada V4 con expiración temporal para acceso seguro y restringido.
    Solo funciona si la cuenta de servicio cuenta con su llave privada.
    """
    bucket = get_bucket()
    if bucket is None:
        return None

    blob_name = normalize_blob_name(path_or_uri)
    try:
        blob = bucket.blob(blob_name)
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET"
        )
        return url
    except Exception as e:
        print(f"[GCS WARNING] No se pudo generar URL firmada para {blob_name}: {e}")
        return None

def delete_gcs_file(path_or_uri: str) -> bool:
    """Elimina un objeto de GCS"""
    bucket = get_bucket()
    if bucket is None:
        return False

    blob_name = normalize_blob_name(path_or_uri)
    try:
        blob = bucket.blob(blob_name)
        if blob.exists():
            blob.delete()
        return True
    except Exception as e:
        print(f"[GCS ERROR] Error al eliminar {blob_name}: {e}")
        return False

def delete_gcs_folder(prefix: str) -> int:
    """Elimina todos los objetos con un prefijo (simulando eliminar una carpeta)"""
    bucket = get_bucket()
    if bucket is None:
        return 0

    norm_prefix = normalize_blob_name(prefix).rstrip("/") + "/"
    client = get_storage_client()
    if client is None:
        return 0

    count = 0
    try:
        blobs = client.list_blobs(bucket, prefix=norm_prefix)
        for b in blobs:
            b.delete()
            count += 1
        return count
    except Exception as e:
        print(f"[GCS ERROR] Error eliminando carpeta {norm_prefix}: {e}")
        return count
