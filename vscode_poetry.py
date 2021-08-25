import json
import subprocess
from pathlib import Path

venv_path = subprocess.check_output("poetry env info --path".split())
venv_path = venv_path.decode("UTF-8")

settings = dict()

Path(".vscode").mkdir(parents=True, exist_ok=True)
Path(".vscode/settings.json").touch()


with open(".vscode/settings.json", "r") as f:
    settings = json.load(f)
    settings["python.pythonPath"] = venv_path

with open(".vscode/settings.json", "w") as f:
    json.dump(settings, f, sort_keys=True, indent=4)


print(json.dumps(settings, sort_keys=True, indent=4))
