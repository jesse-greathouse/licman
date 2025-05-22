import sys
import subprocess
import getpass
import secrets
from pathlib import Path

# Determine project root (assumes this file is in bin/modules/ under the project root)
APP_ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = APP_ROOT / "bin"
MODULES_DIR = BIN_DIR / "modules"

if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

from modules import config
from modules import utility

# Base paths
SRC_DIR = APP_ROOT / "src"
VAR_DIR = APP_ROOT / "var"
OPT_DIR = APP_ROOT / "opt"
ETC_DIR = APP_ROOT / "etc"
TMP_DIR = APP_ROOT / "tmp"
LOG_DIR = VAR_DIR / "log"
DOWNLOAD_DIR = VAR_DIR / "download"
CACHE_DIR = VAR_DIR / "cache"
ENV_FILE = SRC_DIR / ".env"
CONFIG_FILE = APP_ROOT / ".licman-cfg.yml"

# Config templates and their output files
CONFIG_FILES = {
    "celery":           [ ETC_DIR / "supervisor/celery.conf.dist",              ETC_DIR / "supervisor/celery.conf" ],
    "nginx":            [ ETC_DIR / "nginx/nginx.dist.conf",                    ETC_DIR / "nginx/nginx.conf" ],
    "supervisord":      [ ETC_DIR / "supervisor/conf.d/supervisord.conf.dist",  ETC_DIR / "supervisor/conf.d/supervisord.conf" ],
    "force_ssl":        [ ETC_DIR / "nginx/force-ssl.dist.conf",                ETC_DIR / "nginx/force-ssl.conf" ],
    "ssl_params":       [ ETC_DIR / "nginx/ssl-params.dist.conf",               ETC_DIR / "nginx/ssl-params.conf" ],
    "queue_manager":    [ ETC_DIR / "supervisor/queue-manager.conf.dist",       ETC_DIR / "supervisor/queue-manager.conf" ],
}

DEFAULTS = {
    "django": {
        "DJANGO_SECRET_KEY": utility.generate_rand_str(50),
        "DEBUG": "true",
        "ALLOWED_HOSTS": "localhost,127.0.0.1",
        "DATABASE_NAME": "licman",
        "DATABASE_USER": "licman",
        "DATABASE_PASSWORD": "licman",
        "DATABASE_HOST": "localhost",
        "DATABASE_PORT": "5432",
        "TIME_ZONE": "UTC",
        "STATIC_ROOT": str(VAR_DIR / "static"),
        "MEDIA_ROOT": str(VAR_DIR / "media"),
        "LOG_DIR": str(LOG_DIR),
    },
    "celery": {
        "CELERY_RESULT_BACKEND": "",  # Optional — some apps skip this
        "CELERY_WORKER_CONCURRENCY": "2",
        "CELERY_TASK_TIME_LIMIT": "300",
        "CELERY_TASK_SOFT_TIME_LIMIT": "240",
    },
    "supervisor": {
        "SUPERVISORCTL_USER": getpass.getuser(),
        "SUPERVISORCTL_SECRET": secrets.token_hex(16),
        "SUPERVISORCTL_PORT": "6160",
    },
    "queue_manager": {
        "QUEUECTL_USER": getpass.getuser(),
        "QUEUECTL_SECRET": secrets.token_hex(16),
        "QUEUECTL_PORT": "6161",
    },
}

def configure(interactive: bool = True):
    utility.splash()

    cfg = config.get_configuration()

    if interactive:
        print("\n=== Interactive Configuration ===\n")
        cfg = interactive_prompt(cfg)
    else:
        print("\n=== Non-Interactive Configuration ===\nUsing defaults or pre-existing values.")

    merged = merge_defaults(cfg)
    merged = assign_dynamic_config(merged)
    config.save_configuration(merged)

    print("Writing .env file...")
    config.write_env_file(ENV_FILE, merged["django"])

    print("🛠️ Writing config files...")
    for _, (src, dst) in CONFIG_FILES.items():
        if src.exists():
            config.write_template_file(src, dst, **flatten_config(merged))

    print("✅ Configuration complete.")

    if interactive:
        post_configuration_options()

def merge_defaults(cfg: dict) -> dict:
    for domain in DEFAULTS:
        cfg.setdefault(domain, {})
        for key, value in DEFAULTS[domain].items():
            cfg[domain].setdefault(key, value)
    return cfg

def flatten_config(cfg: dict) -> dict:
    flat = {}
    for section in cfg.values():
        flat.update(section)
    return flat

def interactive_prompt(cfg: dict) -> dict:
    cfg.setdefault("django", {})

    prompts = [
        ("DJANGO_SECRET_KEY", "Secret Key", utility.generate_rand_str(50)),
        ("DEBUG", "Enable Debug Mode (true/false)", "true"),
        ("ALLOWED_HOSTS", "Allowed Hosts (comma-separated)", "localhost,127.0.0.1"),
        ("DATABASE_NAME", "Database Name", "licman"),
        ("DATABASE_USER", "Database User", "licman"),
        ("DATABASE_PASSWORD", "Database Password", "licman"),
        ("DATABASE_HOST", "Database Host", "localhost"),
        ("DATABASE_PORT", "Database Port", "5432"),
        ("TIME_ZONE", "Time Zone", "UTC"),

        # Required admin fields — no default allowed
        ("ADMIN_USERNAME", "Superuser Username (Required)", None),
        ("ADMIN_EMAIL", "Superuser Email (Required)", None),
        ("ADMIN_PASSWORD", "Superuser Password (Required)", None),
    ]

    for key, label, default in prompts:
        existing = cfg["django"].get(key)
        is_password = key == "ADMIN_PASSWORD"

        # Show ***** for ADMIN_PASSWORD default, actual value used behind the scenes
        display_default = "*****" if is_password and (existing or default) else existing or default

        prompt_text = f"{label}"
        if display_default is not None:
            prompt_text += f" [{display_default}]"
        prompt_text += ": "

        value = input(prompt_text).strip()

        if not value:
            if existing:
                value = existing
            elif default:
                value = default
            else:
                print(f"❌ {label} is required.")
                sys.exit(1)

        cfg["django"][key] = value

    cfg["django"]["STATIC_ROOT"] = str(VAR_DIR / "static")
    cfg["django"]["MEDIA_ROOT"] = str(VAR_DIR / "media")
    cfg["django"]["LOG_DIR"] = str(LOG_DIR)

    return cfg

def run_script(script_path: Path, *args):
    """
    Runs a given script using the same interpreter without replacing the process.
    """
    if not script_path.exists():
        print(f"⚠️  Script not found at: {script_path}")
        return

    cmd = [str(script_path), *args]
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"❌ Script failed with exit code {result.returncode}")
        sys.exit(result.returncode)

def post_configuration_options():
    """
    Presents optional post-configuration actions such as running database migrations.
    """
    print("\n" + "=" * 66)
    print(" Database Migrations")
    print("=" * 66)
    print("""
    Now that your database is configured, you may update the schema to the latest design.
    This will apply all pending migrations.

    You can also run this manually later using: bin/migrate
    """)
    response = input("Run Database Migrations? (y or n) [default y] ").strip().lower()
    if response in ("", "y", "yes"):
        run_script(BIN_DIR / "migrate")

    print("\n" + "=" * 65)
    print(" Superuser Setup")
    print("=" * 65)
    print("""
You can create or update the Django superuser (admin account) now.

The credentials provided during configuration will be used.

You can also run this manually later using: bin/adminuser
""")

    choice = input("Create superuser now? (y or n) [default y] ").strip().lower()
    if choice in ("", "y", "yes"):
        run_script(BIN_DIR / "adminuser")
        return

    choice = input("Update superuser instead? (y or n) [default n] ").strip().lower()
    if choice in ("y", "yes"):
        run_script(BIN_DIR / "adminuser", "--update")

def assign_dynamic_config(cfg: dict) -> dict:
    import os

    cfg["nginx"] = cfg.get("nginx", {})
    cfg["django"] = cfg.get("django", {})
    cfg["supervisord"] = cfg.get("supervisord", {})
    cfg["queue_manager"] = cfg.get("queue_manager", {})
    cfg["openssl"] = cfg.get("openssl", {})
    cfg["ssl_params"] = cfg.get("ssl_params", {})
    cfg["force_ssl"] = cfg.get("force_ssl", {})
    cfg["redis"] = cfg.get("redis", {})

    session_secret = cfg["nginx"].get("SESSION_SECRET") or utility.generate_rand_str(64)
    cfg["nginx"]["SESSION_SECRET"] = session_secret

    current_user = os.getenv("LOGNAME") or getpass.getuser()

    is_ssl = cfg["nginx"].get("IS_SSL", "false") == "true"
    if is_ssl:
        cfg["nginx"]["SSL"] = "ssl http2"
        cfg["nginx"]["PORT"] = "443"
        cfg["nginx"]["SSL_CERT_LINE"] = f"ssl_certificate {cfg['nginx'].get('SSL_CERT', ETC_DIR / 'ssl/certs/licman.cert')}"
        cfg["nginx"]["SSL_KEY_LINE"] = f"ssl_certificate_key {cfg['nginx'].get('SSL_KEY', ETC_DIR / 'ssl/private/licman.key')}"
        cfg["nginx"]["INCLUDE_FORCE_SSL_LINE"] = f"include {ETC_DIR}/nginx/force-ssl.conf"
    else:
        cfg["nginx"]["SSL"] = ""
        cfg["nginx"]["SSL_CERT_LINE"] = ""
        cfg["nginx"]["SSL_KEY_LINE"] = ""
        cfg["nginx"]["INCLUDE_FORCE_SSL_LINE"] = ""

    redis_host = cfg["redis"].get("REDIS_HOST", "/var/run/redis/redis.sock")
    redis_port = cfg["redis"].get("REDIS_PORT", "6379")
    redis_db = cfg["redis"].get("REDIS_DB", "0")

    if redis_host.startswith("/"):
        broker_url = f"redis+socket://{redis_host}?virtual_host={redis_db}"
    else:
        broker_url = f"redis://{redis_host}:{redis_port}/{redis_db}"

    cfg["celery"]["CELERY_BROKER_URL"] = broker_url

    allowed_hosts = cfg["django"].get("ALLOWED_HOSTS", "localhost,127.0.0.1")
    parsed_hosts = [d.strip() for d in allowed_hosts.replace(",", " ").split()]

    port = cfg["nginx"].get("PORT", "8282")
    is_default_port = port in ("80", "443")

    cfg["nginx"]["DOMAINS"] = " ".join(parsed_hosts)
    csrf_origins = [f"http://{h}:{port}" if not is_default_port else f"http://{h}" for h in parsed_hosts] + \
        [f"https://{h}:{port}" if not is_default_port else f"https://{h}" for h in parsed_hosts]
    cfg["django"]["CSRF_TRUSTED_ORIGINS"] = ",".join(csrf_origins)

    cfg["nginx"].update({
        "APP_URL": cfg["django"].get("APP_URL", f"http://{parsed_hosts[0]}:{port}"),
        "DIR": str(APP_ROOT),
        "BIN": str(BIN_DIR),
        "ETC": str(ETC_DIR),
        "OPT": str(OPT_DIR),
        "TMP": str(TMP_DIR),
        "VAR": str(VAR_DIR),
        "WEB": str(SRC_DIR / "frontend/public"),
        "SRC": str(SRC_DIR),
        "USER": current_user,
        "LOG": str(LOG_DIR / "error.log"),
        "PORT": port,
    })

    cfg["ssl_params"]["ETC"] = str(ETC_DIR)
    cfg["openssl"]["ETC"] = str(ETC_DIR)
    cfg["force_ssl"]["DOMAINS"] = cfg["nginx"]["DOMAINS"]

    supervisor_secret = cfg["supervisord"].get("SUPERVISORCTL_SECRET") or utility.generate_rand_str(32)
    queue_secret = cfg["queue_manager"].get("QUEUECTL_SECRET") or utility.generate_rand_str(32)

    cfg["supervisord"].update({
        "SUPERVISORCTL_USER": current_user,
        "SUPERVISORCTL_SECRET": supervisor_secret,
        "SUPERVISORCTL_PORT": cfg["supervisord"].get("SUPERVISORCTL_PORT", 5959),
    })

    cfg["queue_manager"].update({
        "QUEUECTL_USER": current_user,
        "QUEUECTL_SECRET": queue_secret,
        "QUEUECTL_PORT": cfg["queue_manager"].get("QUEUECTL_PORT", 5960),
    })

    cfg["django"].update({
        "APP_NAME": "licman",
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "BASE_DIR": str(APP_ROOT),
        "SRC": str(SRC_DIR),
        "VIRTUAL_ENV": str(OPT_DIR / "venv"),
        "REDIS_HOST": redis_host,
        "REDIS_PORT": redis_port,
        "REDIS_DB": redis_db,
        "REDIS_PASSWORD": cfg["redis"].get("REDIS_PASSWORD", ""),
        "CELERY_BROKER_URL": broker_url,
    })

    return cfg

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--non-interactive", action="store_true", help="Run without prompting for input")
    args = parser.parse_args()

    configure(interactive=not args.non_interactive)
