import sys
import subprocess
from pathlib import Path

def main():
    bitdepth = 2048
    overwrite = False

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--overwrite":
            overwrite = True
        elif args[i] == "--bitdepth":
            i += 1
            try:
                bitdepth = int(args[i])
            except ValueError:
                sys.exit(f"Invalid bitdepth: {args[i]}")
        i += 1

    # Resolve etc directory relative to script location
    base_dir = Path(__file__).resolve().parents[2]
    cert_dir = base_dir / "etc" / "ssl" / "certs"
    cert_dir.mkdir(parents=True, exist_ok=True)

    dhparam_file = cert_dir / "dhparam.pem"

    if overwrite and dhparam_file.exists():
        dhparam_file.unlink()

    if not dhparam_file.exists():
        cmd = ["openssl", "dhparam", "-out", str(dhparam_file), str(bitdepth)]
        result = subprocess.run(cmd)
        if result.returncode != 0:
            sys.exit(f"openssl dhparam failed: {' '.join(cmd)}")
        print()
    else:
        print("...dhp file already exists. skipping...")
        sys.exit(0)

if __name__ == "__main__":
    main()
