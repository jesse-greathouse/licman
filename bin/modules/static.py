import subprocess
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = BASE_DIR / "src"
ENV_FILE = SRC_DIR / ".env"

from dotenv import load_dotenv
load_dotenv(dotenv_path=ENV_FILE)

cmd = [
    os.environ["VIRTUAL_ENV"] + "/bin/python",
    str(SRC_DIR / "backend/manage.py"),
    "collectstatic",
    "--noinput"
]

subprocess.run(cmd, check=True)
