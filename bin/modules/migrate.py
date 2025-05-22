import os
import subprocess
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = APP_ROOT / "src"
VENV_BIN = APP_ROOT / "opt" / "venv" / "bin"
MANAGE_PY = SRC_DIR / "backend" / "manage.py"

if not MANAGE_PY.exists():
    raise FileNotFoundError(f"manage.py not found at: {MANAGE_PY}")

env = os.environ.copy()
env.update({
    "PATH": f"{VENV_BIN}:{env.get('PATH', '')}",
    "PYTHONPATH": str(SRC_DIR / "backend"),
    "DJANGO_SETTINGS_MODULE": "config.settings"
})

cmd = [str(VENV_BIN / "python"), str(MANAGE_PY), "migrate"]
subprocess.run(cmd, env=env, check=True)
