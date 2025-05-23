import subprocess
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = APP_ROOT / "src"
MANAGE_PY = SRC_DIR / "backend" / "manage.py"

if not MANAGE_PY.exists():
    raise FileNotFoundError(f"manage.py not found at: {MANAGE_PY}")

# Assume wrapper has already set interpreter, PYTHONPATH, and environment
subprocess.run(["python", str(MANAGE_PY), "migrate"], check=True)
