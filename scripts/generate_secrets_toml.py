import json
import os

key_path = os.path.join("credentials", "sigrama-cloud-calidad-d8baef08fd5b.json")
if os.path.exists(key_path):
    with open(key_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    os.makedirs(".streamlit", exist_ok=True)
    out_path = os.path.join(".streamlit", "secrets.toml")
    with open(out_path, "w", encoding="utf-8") as f_out:
        f_out.write("[gcp_service_account]\n")
        for k, v in data.items():
            if isinstance(v, str) and "\n" in v:
                f_out.write(f'{k} = """\n{v}"""\n')
            else:
                f_out.write(f'{k} = {json.dumps(v)}\n')
    print("Secrets TOML written to .streamlit/secrets.toml")
