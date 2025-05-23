import shutil
import os
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = APP_ROOT / "src" / "backend"

def main():
    for root, dirs, _ in os.walk(SRC_DIR):
        for d in dirs:
            if d == "__pycache__":
                target = Path(root) / d
                print(f"...removing: {target}...")
                shutil.rmtree(target, ignore_errors=True)

if __name__ == "__main__":
    main()
