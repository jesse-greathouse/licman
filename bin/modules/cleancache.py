import shutil
import os
from pathlib import Path

def main():
    # Get absolute path to src/backend relative to this script's directory
    base_dir = Path(__file__).resolve().parents[1]
    backend_dir = base_dir / "src" / "backend"

    # Walk and remove all __pycache__ directories
    for root, dirs, _ in os.walk(backend_dir):
        for d in dirs:
            if d == "__pycache__":
                target = Path(root) / d
                print(f"...removing: {target}...")
                shutil.rmtree(target, ignore_errors=True)

if __name__ == "__main__":
    main()
