import subprocess
from pathlib import Path
from dotenv import load_dotenv

APP_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = APP_ROOT / "src"
ENV_FILE = SRC_DIR / ".env"
VENV_PYTHON = APP_ROOT / "opt" / "venv" / "bin" / "python"

load_dotenv(dotenv_path=ENV_FILE)

def collect_static():
    cmd = [
        str(VENV_PYTHON),
        str(SRC_DIR / "backend/manage.py"),
        "collectstatic",
        "--noinput"
    ]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    collect_static()
