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

from modules import cfg
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

    cnf = cfg.get_configuration()

    if interactive:
        print("\n=== Interactive Configuration ===\n")
        cnf = interactive_prompt(cnf)
    else:
        print("\n=== Non-Interactive Configuration ===\nUsing defaults or pre-existing values.")

    merged = merge_defaults(cnf)
    merged = assign_dynamic_config(merged)
    cfg.save_configuration(merged)

    print("Writing .env file...")
    cfg.write_env_file(ENV_FILE, merged["django"])

    print("🛠️ Writing config files...")
    for _, (src, dst) in CONFIG_FILES.items():
        if src.exists():
            cfg.write_template_file(src, dst, **flatten_config(merged))

    print("✅ Configuration complete.")

    if interactive:
        post_configuration_options()

def merge_defaults(cnf: dict) -> dict:
    for domain in DEFAULTS:
        cnf.setdefault(domain, {})
        for key, value in DEFAULTS[domain].items():
            cnf[domain].setdefault(key, value)
    return cnf

def flatten_config(cnf: dict) -> dict:
    flat = {}
    for section in cnf.values():
        flat.update(section)
    return flat

def interactive_prompt(cnf: dict) -> dict:
    cnf.setdefault("django", {})

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
        existing = cnf["django"].get(key)
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

        cnf["django"][key] = value

    cnf["django"]["STATIC_ROOT"] = str(VAR_DIR / "static")
    cnf["django"]["MEDIA_ROOT"] = str(VAR_DIR / "media")
    cnf["django"]["LOG_DIR"] = str(LOG_DIR)

    return cnf

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

    choice = input("Create superuser now? (y or n) [default n] ").strip().lower()
    if choice in ("y", "yes"):
        run_script(BIN_DIR / "adminuser")
    else:
        choice = input("Update superuser instead? (y or n) [default n] ").strip().lower()
        if choice in ("y", "yes"):
            run_script(BIN_DIR / "adminuser", "--update")

    print("\n" + "=" * 66)
    print(" Seed Data")
    print("=" * 66)
    print("""
You can optionally seed the database with default records, such as system groups
and permissions. This is safe to re-run multiple times.

You can also run this manually later using: bin/seed
""")
    response = input("Run seed script now? (y or n) [default y] ").strip().lower()
    if response in ("", "y", "yes"):
        run_script(BIN_DIR / "seed")

def assign_dynamic_config(cnf: dict) -> dict:
    import os

    cnf["nginx"] = cnf.get("nginx", {})
    cnf["django"] = cnf.get("django", {})
    cnf["supervisord"] = cnf.get("supervisord", {})
    cnf["queue_manager"] = cnf.get("queue_manager", {})
    cnf["openssl"] = cnf.get("openssl", {})
    cnf["ssl_params"] = cnf.get("ssl_params", {})
    cnf["force_ssl"] = cnf.get("force_ssl", {})
    cnf["redis"] = cnf.get("redis", {})

    session_secret = cnf["nginx"].get("SESSION_SECRET") or utility.generate_rand_str(64)
    cnf["nginx"]["SESSION_SECRET"] = session_secret

    current_user = os.getenv("LOGNAME") or getpass.getuser()

    is_ssl = cnf["nginx"].get("IS_SSL", "false") == "true"
    if is_ssl:
        cnf["nginx"]["SSL"] = "ssl http2"
        cnf["nginx"]["PORT"] = "443"
        cnf["nginx"]["SSL_CERT_LINE"] = f"ssl_certificate {cnf['nginx'].get('SSL_CERT', ETC_DIR / 'ssl/certs/licman.cert')}"
        cnf["nginx"]["SSL_KEY_LINE"] = f"ssl_certificate_key {cnf['nginx'].get('SSL_KEY', ETC_DIR / 'ssl/private/licman.key')}"
        cnf["nginx"]["INCLUDE_FORCE_SSL_LINE"] = f"include {ETC_DIR}/nginx/force-ssl.conf"
    else:
        cnf["nginx"]["SSL"] = ""
        cnf["nginx"]["SSL_CERT_LINE"] = ""
        cnf["nginx"]["SSL_KEY_LINE"] = ""
        cnf["nginx"]["INCLUDE_FORCE_SSL_LINE"] = ""

    redis_host = cnf["redis"].get("REDIS_HOST", "/var/run/redis/redis.sock")
    redis_port = cnf["redis"].get("REDIS_PORT", "6379")
    redis_db = cnf["redis"].get("REDIS_DB", "0")

    if redis_host.startswith("/"):
        broker_url = f"redis+socket://{redis_host}?virtual_host={redis_db}"
    else:
        broker_url = f"redis://{redis_host}:{redis_port}/{redis_db}"

    cnf["celery"]["CELERY_BROKER_URL"] = broker_url

    allowed_hosts = cnf["django"].get("ALLOWED_HOSTS", "localhost,127.0.0.1")
    parsed_hosts = [d.strip() for d in allowed_hosts.replace(",", " ").split()]

    port = cnf["nginx"].get("PORT", "8282")
    is_default_port = port in ("80", "443")

    cnf["nginx"]["DOMAINS"] = " ".join(parsed_hosts)
    csrf_origins = [f"http://{h}:{port}" if not is_default_port else f"http://{h}" for h in parsed_hosts] + \
        [f"https://{h}:{port}" if not is_default_port else f"https://{h}" for h in parsed_hosts]
    cnf["django"]["CSRF_TRUSTED_ORIGINS"] = ",".join(csrf_origins)

    cnf["nginx"].update({
        "APP_URL": cnf["django"].get("APP_URL", f"http://{parsed_hosts[0]}:{port}"),
        "DIR": str(APP_ROOT),
        "BIN": str(BIN_DIR),
        "ETC": str(ETC_DIR),
        "OPT": str(OPT_DIR),
        "TMP": str(TMP_DIR),
        "VAR": str(VAR_DIR),
        "WEB": str(VAR_DIR / "www/html"),
        "SRC": str(SRC_DIR),
        "USER": current_user,
        "LOG": str(LOG_DIR / "error.log"),
        "PORT": port,
    })

    cnf["ssl_params"]["ETC"] = str(ETC_DIR)
    cnf["openssl"]["ETC"] = str(ETC_DIR)
    cnf["force_ssl"]["DOMAINS"] = cnf["nginx"]["DOMAINS"]

    supervisor_secret = cnf["supervisord"].get("SUPERVISORCTL_SECRET") or utility.generate_rand_str(32)
    queue_secret = cnf["queue_manager"].get("QUEUECTL_SECRET") or utility.generate_rand_str(32)

    cnf["supervisord"].update({
        "SUPERVISORCTL_USER": current_user,
        "SUPERVISORCTL_SECRET": supervisor_secret,
        "SUPERVISORCTL_PORT": cnf["supervisord"].get("SUPERVISORCTL_PORT", 5959),
    })

    cnf["queue_manager"].update({
        "QUEUECTL_USER": current_user,
        "QUEUECTL_SECRET": queue_secret,
        "QUEUECTL_PORT": cnf["queue_manager"].get("QUEUECTL_PORT", 5960),
    })

    cnf["django"].update({
        "APP_NAME": "licman",
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "BASE_DIR": str(APP_ROOT),
        "SRC": str(SRC_DIR),
        "VIRTUAL_ENV": str(OPT_DIR / "venv"),
        "REDIS_HOST": redis_host,
        "REDIS_PORT": redis_port,
        "REDIS_DB": redis_db,
        "REDIS_PASSWORD": cnf["redis"].get("REDIS_PASSWORD", ""),
        "CELERY_BROKER_URL": broker_url,
    })

    return cnf

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--non-interactive", action="store_true", help="Run without prompting for input")
    args = parser.parse_args()

    configure(interactive=not args.non_interactive)
