"""
Constantes de la base de datos + utilidad MANUAL para subirla a GCS.

AVISO: importar este modulo NO sube nada. Subir la BD local pisa las auditorias
hechas en la nube, por eso solo se ejecuta con: python scripts/subir_db_a_gcs.py --force
"""
import sys, os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DB_PATH = os.path.join(PROJECT_ROOT, "data", "sigrama_calidad.db")
GCS_DB_BLOB = "system/sigrama_calidad.db"


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    if "--force" not in sys.argv:
        print("Cancelado: esto sobrescribe la BD de la nube (y sus auditorias). Use --force si es intencional.")
        sys.exit(1)

    from src.services.gcs_storage import get_bucket, DEFAULT_BUCKET_NAME
    print(f"Subiendo {DB_PATH} -> gs://{DEFAULT_BUCKET_NAME}/{GCS_DB_BLOB}")
    bucket = get_bucket()
    if bucket is None:
        print("ERROR: No se pudo conectar a GCS.")
        sys.exit(1)
    bucket.blob(GCS_DB_BLOB).upload_from_filename(DB_PATH, content_type="application/octet-stream")
    print(f"OK! Base de datos persistida en gs://{DEFAULT_BUCKET_NAME}/{GCS_DB_BLOB}")


if __name__ == "__main__":
    main()
