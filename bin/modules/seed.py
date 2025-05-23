import subprocess
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = APP_ROOT / "bin"
SRC_DIR = APP_ROOT / "src"
VENV_PYTHON = APP_ROOT / "opt" / "venv" / "bin" / "python"

def seed():
    print("Running seed routines...\n")

    seeds = [
        ("Initialize groups", [str(VENV_PYTHON), str(SRC_DIR / "backend/manage.py"), "init_groups"]),
    ]

    for label, command in seeds:
        print(f"→ {label}")
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed: {label}\n  Error: {e}")
            break
        else:
            print(f"✓ Done: {label}\n")

    print("Seeding complete.")

if __name__ == "__main__":
    seed()
