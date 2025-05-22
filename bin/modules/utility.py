import sys
import os
import platform
import random
import string
from pathlib import Path

# Determine project root (assumes this file is in bin/modules/ under the project root)
APP_ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = APP_ROOT / "bin"
MODULES_DIR = BIN_DIR / "modules"

if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

def trim(s: str) -> str:
    return s.strip()

def get_operating_system() -> str:
    os_map = {
        "Windows": "Win32",
        "Darwin": "MacOS",
    }
    system = platform.system()
    if system == "Linux":
        return get_linux_distribution()
    if system not in os_map:
        raise RuntimeError(f"Unsupported operating system: {system}")
    return os_map[system]

def get_linux_distribution() -> str:
    distros = [
        ("centos", "CentOS"),
        ("ubuntu", "Ubuntu"),
        ("fedora", "Fedora"),
        ("debian", "Debian"),
        ("opensuse", "OpenSUSE"),
        ("arch", "Arch"),
        ("alpine", "Alpine"),
        ("gentoo", "Gentoo"),
        ("openmandriva", "OpenMandriva")
    ]

    try:
        with open("/etc/os-release", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            for key, name in distros:
                if line.strip().lower().startswith(f"id={key}"):
                    return name
    except FileNotFoundError:
        pass

    fallback_files = ["/etc/lsb-release", "/etc/redhat-release"]
    for file in fallback_files:
        if Path(file).exists():
            with open(file, encoding="utf-8") as f:
                contents = f.read().lower()
                for _, name in distros:
                    if name.lower() in contents:
                        return name

    if Path("/etc/debian_version").exists():
        return "Debian"

    uname = os.popen("uname -a").read().lower()
    for _, name in distros:
        if name.lower() in uname:
            return name

    raise RuntimeError("Unable to determine Linux distribution.")

def read_file(filename: str) -> str:
    with open(filename, encoding="utf-8") as f:
        return f.read()

def write_file(filename: str, content: str):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

def str_replace_in_file(search: str, replacement: str, filename: str):
    content = read_file(filename)
    content = content.replace(search, replacement)
    write_file(filename, content)

def generate_rand_str(length: int = 64) -> str:
    return ''.join(random.choices(string.hexdigits.upper(), k=length))

def is_pid_running(pid_file: str) -> bool:
    try:
        with open(pid_file) as f:
            pid = f.read().strip()
        if not pid.isdigit():
            return False
        pid = int(pid)
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except FileNotFoundError:
        return False
    except ProcessLookupError:
        return False

def command_result(exit_code: int, error, message: str, cmd=None):
    if exit_code == -1:
        print(f"Failed to execute command: {error}")
        if cmd:
            print("Command:", " ".join(cmd))
        exit(1)
    elif exit_code & 127:
        signal_num = exit_code & 127
        coredump = "with" if exit_code & 128 else "without"
        print(f"Command died with signal {signal_num} ({coredump} coredump).")
        if cmd:
            print("Command:", " ".join(cmd))
        exit(1)
    else:
        code = exit_code >> 8
        if code != 0:
            print(f"Command exited with non-zero status {code}.")
            if cmd:
                print("Command:", " ".join(cmd))
            exit(code)
        else:
            print(f"{message} success!")

def splash():
    license_file = Path(__file__).resolve().parents[2] / "LICENSE"
    print("\n+-------------------------- licman Software License --------------------------+\n")
    try:
        print(license_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print("ERROR: LICENSE file not found at:", license_file)
    print("\n+---------------------------------------------------------------------------+\n")
