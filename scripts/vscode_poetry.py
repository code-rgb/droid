import json
import subprocess
from pathlib import Path

venv_path = subprocess.check_output("poetry env info --path".split())
venv_path = venv_path.decode("UTF-8")

Path(".vscode").mkdir(parents=True, exist_ok=True)
vs_settings = Path(".vscode/settings.json")

settings = {}
if vs_settings.is_file():
    with vs_settings.open("r") as f:
        try:
            settings = json.load(f)
        except json.decoder.JSONDecodeError:
            pass

settings["python.pythonPath"] = venv_path

with vs_settings.open("w") as f:
    json.dump(settings, f, sort_keys=True, indent=4)

print(settings)
