import sys
import subprocess
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2]
ETC_DIR = APP_ROOT / "etc"
CERT_DIR = ETC_DIR / "ssl" / "certs"
CERT_DIR.mkdir(parents=True, exist_ok=True)

def main():
    bitdepth = 2048
    overwrite = False

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--overwrite":
            overwrite = True
        elif args[i] == "--bitdepth" and i + 1 < len(args):
            i += 1
            try:
                bitdepth = int(args[i])
            except ValueError:
                sys.exit(f"Invalid bitdepth: {args[i]}")
        i += 1

    dhparam_file = CERT_DIR / "dhparam.pem"

    if overwrite and dhparam_file.exists():
        dhparam_file.unlink()

    if not dhparam_file.exists():
        cmd = ["openssl", "dhparam", "-out", str(dhparam_file), str(bitdepth)]
        subprocess.run(cmd, check=True)
        print("✓ DH parameters generated.")
    else:
        print("...dhp file already exists. skipping...")

if __name__ == "__main__":
    main()
