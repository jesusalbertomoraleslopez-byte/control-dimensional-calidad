import sys, json
sys.stdout.reconfigure(encoding='utf-8')

# Simular normalize_blob_name con la logica actual
def normalize_blob_name_actual(path_or_uri):
    if not path_or_uri:
        return ""
    clean = str(path_or_uri).strip()
    if clean.startswith("gs://"):
        parts = clean[5:].split("/", 1)
        if len(parts) > 1:
            clean = parts[1]  # Todo despues del bucket name
        else:
            clean = parts[0]

    clean = clean.replace("\\", "/")
    if "Proyectos/" in clean:
        idx = clean.find("Proyectos/")
        clean = clean[idx:]
    elif clean.startswith("src/Proyectos/"):
        clean = clean[4:]

    return clean.lstrip("/")

# Probar con los paths reales del bucket
test_paths = [
    "gs://sigrama-planos-calidad-2026/Sin_Auditar/ING0001 - 11-B-9016-01-(12gacr ANSI-61) - K30 - V0-R0/11-B-9016-01-(12gacr ANSI-61) - K30 - V0-R0.STEP",
    "gs://sigrama-planos-calidad-2026/Sin_Auditar/ING0002 - PP15509-(14gacr ANSI-61) - K48 - V2-R0/PP15509-(14gacr ANSI-61) - K48 - V2-R0.STEP",
]

print("=== DIAGNOSTICO normalize_blob_name ===")
for path in test_paths:
    result = normalize_blob_name_actual(path)
    print(f"INPUT:  {path}")
    print(f"OUTPUT: {result}")
    print(f"CORRECTO? {'SI' if result.startswith('Sin_Auditar/') else 'NO - FALLA!'}")
    print()
