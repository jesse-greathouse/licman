#!/usr/bin/env python3

import subprocess
import tarfile
from pathlib import Path

PYTHON_VERSION = "3.13.3"
OPENRESTY_VERSION = "1.27.1.2"
OPENSSL_VERSION = "3.5.0"
NODE_VERSION = "22.14"
NPM_VERSION = "11.2.0"


BASE_DIR = Path(__file__).resolve().parents[2]
OPT_DIR = BASE_DIR / "opt"
SRC_DIR = BASE_DIR / "src"
PYTHON_TARBALL = OPT_DIR / f"Python-{PYTHON_VERSION}.tgz"
OPENRESTY_TARBALL = OPT_DIR / f"openresty-{OPENRESTY_VERSION}.tar.gz"
OPENSSL_TARBALL = OPT_DIR / f"openssl-{OPENSSL_VERSION}.tar.gz"

def run(cmd, cwd=None, shell=False):
    print(f"→ {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(cmd, cwd=cwd, shell=shell)
    if result.returncode != 0:
        raise RuntimeError(f"❌ Command failed: {cmd}")

def install_system_packages():
    system_packages = [
        "build-essential", "libssl-dev", "zlib1g-dev",
        "libncurses-dev", "libreadline-dev", "libsqlite3-dev",
        "libgdbm-dev", "libdb5.3-dev", "libbz2-dev", "libexpat1-dev",
        "liblzma-dev", "tk-dev", "uuid-dev", "curl", "git"
    ]

    print("🔒 Sudo is required for system package installation.")
    run(["sudo", "apt-get", "update"])

    to_install = []
    for pkg in system_packages:
        result = subprocess.run(
            ["dpkg", "-s", pkg],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if result.returncode != 0:
            to_install.append(pkg)
        else:
            print(f"✓ {pkg} already installed, skipping.")

    if to_install:
        print(f"📦 Installing missing packages: {' '.join(to_install)}")
        run(["sudo", "apt-get", "install", "-y"] + to_install)
    else:
        print("✅ All system packages already installed.")

def install_python(force=False):
    install_dir = OPT_DIR / "python"
    python_bin = install_dir / "bin/python3"
    venv_dir = OPT_DIR / "venv"

    if python_bin.exists() and not force:
        print("✅ Python already installed.")
    else:
        if install_dir.exists():
            print(f"🗑️ Removing existing Python install at {install_dir}")
            run(["rm", "-rf", str(install_dir)])

        build_dir = OPT_DIR / f"Python-{PYTHON_VERSION}"
        if build_dir.exists():
            run(["rm", "-rf", str(build_dir)])

        with tarfile.open(PYTHON_TARBALL) as tar:
            tar.extractall(OPT_DIR)

        run(["./configure", f"--prefix={install_dir}"], cwd=build_dir)
        run(["make", "-j4"], cwd=build_dir)
        run(["make", "install"], cwd=build_dir)

    if venv_dir.exists() and not force:
        print("✅ Virtual environment already exists.")
        return

    if venv_dir.exists() and force:
        print(f"🗑️ Removing existing virtual environment at {venv_dir}")
        run(["rm", "-rf", str(venv_dir)])

    print("🐍 Creating virtual environment...")
    run([str(python_bin), "-m", "venv", str(venv_dir)])

    # Ensure common binary symlinks exist in venv/bin
    bin_dir = venv_dir / "bin"
    symlinks = {
        "python": "python3.13",
        "python3": "python3.13",
        "pip": "pip3.13"
    }
    for link_name, target_name in symlinks.items():
        link = bin_dir / link_name
        if not link.exists():
            print(f"Creating symlink: {link_name} -> {target_name}")
            link.symlink_to(target_name)

    print("Upgrading pip to the latest version...")
    run([str(bin_dir / "python"), "-m", "pip", "install", "--upgrade", "pip"])

    requirements_file = BASE_DIR / "requirements.txt"
    print(f"Installing Python packages from {requirements_file.name}...")
    run([str(bin_dir / "pip"), "install", "-r", str(requirements_file)])


def install_node(force=False):
    nvm_dir = Path.home() / ".nvm"
    node_path = nvm_dir / "versions/node" / f"v{NODE_VERSION}"

    if node_path.exists() and not force:
        print("✅ Node.js already installed.")
        return

    if force and node_path.exists():
        print(f"🗑️ Removing existing Node.js version at {node_path}")
        run(["rm", "-rf", str(node_path)])

    print("Installing Node.js via NVM...")
    run("curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash", shell=True)

    bash_env = f"""
        export NVM_DIR="$HOME/.nvm"
        source "$NVM_DIR/nvm.sh"
        nvm install {NODE_VERSION}
        nvm use {NODE_VERSION}
        npm install -g npm@{NPM_VERSION}
    """
    run(["bash", "-c", bash_env])

def build_frontend():
    print("Building frontend...")
    run(["bash", "-c", f"""
        export NVM_DIR="$HOME/.nvm"
        source "$NVM_DIR/nvm.sh"
        nvm use {NODE_VERSION}
        cd {SRC_DIR}/frontend
        npm install
        npm run build
    """])

def install_openresty(force=False):
    install_dir = OPT_DIR / "openresty"

    if install_dir.exists() and not force:
        print("✅ OpenResty already installed.")
        return

    if not OPENRESTY_TARBALL:
        raise FileNotFoundError("❌ OpenResty tarball not found in opt/")

    if force and install_dir.exists():
        print(f"🗑️ Removing existing OpenResty install at {install_dir}")
        run(["rm", "-rf", str(install_dir)])

    print("Building OpenResty...")
    run(["tar", "-xzf", str(OPENRESTY_TARBALL), "-C", str(OPT_DIR)])

    source_dir = OPT_DIR / f"openresty-{OPENRESTY_VERSION}"
    if not source_dir.exists() or not (source_dir / "configure").exists():
        raise FileNotFoundError("❌ Could not find extracted OpenResty source directory.")

    if not source_dir:
        raise FileNotFoundError("❌ Could not find extracted OpenResty source directory.")

    run([
        "./configure",
        f"--prefix={install_dir}",
        "--with-pcre-jit",
        "--with-ipv6",
        "--with-http_iconv_module",
        "--with-http_realip_module",
        "--with-http_ssl_module"
    ], cwd=source_dir)

    run(["make", "-j4"], cwd=source_dir)
    run(["make", "install"], cwd=source_dir)

def install_openssl(force=False):
    install_dir = OPT_DIR / "openssl"

    if install_dir.exists() and not force:
        print("✅ OpenSSL already installed.")
        return

    if force and install_dir.exists():
        print(f"🗑️ Removing existing OpenSSL install at {install_dir}")
        run(["rm", "-rf", str(install_dir)])

    if not OPENSSL_TARBALL.exists():
        raise FileNotFoundError(f"❌ OpenSSL tarball not found at {OPENSSL_TARBALL}")

    print("Extracting OpenSSL tarball...")
    run(["tar", "-xzf", str(OPENSSL_TARBALL), "-C", str(OPT_DIR)])

    source_dir = OPT_DIR / f"openssl-{OPENSSL_VERSION}"
    if not source_dir.exists() or not (source_dir / "Configure").exists():
        raise FileNotFoundError("❌ Could not find extracted OpenSSL source directory.")

    print("Configuring OpenSSL build...")
    run(["./Configure", f"--prefix={install_dir}", "enable-ec_nistp_64_gcc_128", "no-shared"],
        cwd=source_dir)

    print("Building OpenSSL...")
    run(["make", "-j4"], cwd=source_dir)

    print("Installing OpenSSL...")
    run(["make", "install_sw"], cwd=source_dir)

def cleanup():
    print("🧹 Cleaning build directories...")
    for pattern in ["Python-*", "openresty-*", "openssl-*"]:
        for path in OPT_DIR.glob(pattern):
            if path.is_dir():
                run(["rm", "-rf", str(path)])

def parse_options(argv):
    all = {"system", "python", "node", "openresty", "build", "cleanup"}
    selected = {k: True for k in all}
    exclusive = False

    for arg in argv:
        if arg.startswith("--skip-"):
            selected[arg[7:]] = False
        elif arg.startswith("--"):
            component = arg[2:]
            if component in all:
                selected = {k: False for k in all}
                selected[component] = True
                exclusive = True

    return selected, exclusive

def install(selected: dict, exclusive_mode: bool):
    components = {
        "system": 		install_system_packages,
        "python": 		lambda: install_python(force=exclusive_mode),
        "node": 		lambda: install_node(force=exclusive_mode),
        "openresty": 	lambda: install_openresty(force=exclusive_mode),
        "openssl": 		lambda: install_openssl(force=exclusive_mode),
        "build": 		build_frontend,
        "cleanup": 		cleanup,
    }
    for name, func in components.items():
        if selected.get(name, True):
            func()
