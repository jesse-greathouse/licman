import sys
import os
import time
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Ensure the `bin` directory is in sys.path to allow `from modules import config`
APP_ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = APP_ROOT / "bin"
SRC_DIR = APP_ROOT / "src"
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

from modules import cfg

load_dotenv(SRC_DIR / ".env")

cnf = cfg.get_configuration()

SUPERVISOR_CONF = APP_ROOT / "etc/supervisor/conf.d/supervisord.conf"
SUPERVISOR_LOG = APP_ROOT / "var/log/supervisord.log"
SUPERVISOR_PID = APP_ROOT / "var/pid/supervisord.pid"

env = os.environ.copy()
env.update({
    "APP_NAME": "licman",
    "USER": os.getenv("LOGNAME", "unknown"),
    "BASE_DIR": str(APP_ROOT),
    "BIN": str(APP_ROOT / "bin"),
    "ETC": str(APP_ROOT / "etc"),
    "OPT": str(APP_ROOT / "opt"),
    "TMP": str(APP_ROOT / "tmp"),
    "VAR": str(APP_ROOT / "var"),
    "SRC": str(APP_ROOT / "src"),
    "WEB": str(APP_ROOT / "src/frontend/public"),
    "LOG_DIR": str(APP_ROOT / "var/log"),
    "CACHE_DIR": str(APP_ROOT / "var/cache"),
    "VIRTUAL_ENV": str(APP_ROOT / "opt/venv"),
    "PATH": os.getenv("PATH", "/usr/bin:/bin"),

    # App-specific config
    "PORT": cnf["nginx"].get("PORT", "8282"),
    "APP_URL": cnf["nginx"].get("APP_URL", "http://localhost:8282"),
    "SSL": cnf["nginx"].get("SSL", ""),

    # Celery
    "CELERY_BROKER_URL": cnf["celery"].get("CELERY_BROKER_URL", ""),
    "CELERY_WORKER_CONCURRENCY": cnf["celery"].get("CELERY_WORKER_CONCURRENCY", "2"),

    # Redis (optional, but likely used somewhere)
    "REDIS_HOST": cnf.get("redis", {}).get("REDIS_HOST", "/var/run/redis/redis.sock"),
    "REDIS_PORT": cnf.get("redis", {}).get("REDIS_PORT", "6379"),
    "REDIS_DB": cnf.get("redis", {}).get("REDIS_DB", "0"),
    "REDIS_PASSWORD": cnf.get("redis", {}).get("REDIS_PASSWORD", ""),
})

def is_pid_running(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False

def start_web():
    if SUPERVISOR_PID.exists():
        with SUPERVISOR_PID.open() as f:
            pid = f.read().strip()
        if pid and pid.isdigit() and is_pid_running(pid):
            print("Supervisor already running. Starting web services...")
            subprocess.run(["supervisorctl", "-c", str(SUPERVISOR_CONF), "start", "all"], env=env)
            return
    print("Starting supervisor daemon...")
    subprocess.run(["supervisord", "-c", str(SUPERVISOR_CONF)], env=env)
    time.sleep(5)
    subprocess.run(["tail", "-n", "18", str(SUPERVISOR_LOG)])

def stop_web():
    if SUPERVISOR_PID.exists() and is_pid_running(SUPERVISOR_PID.read_text().strip()):
        print("Stopping web services...")
        subprocess.run(["supervisorctl", "-c", str(SUPERVISOR_CONF), "stop", "all"], env=env)
    else:
        print("No running supervisor daemon found.")

def restart_web():
    if SUPERVISOR_PID.exists() and is_pid_running(SUPERVISOR_PID.read_text().strip()):
        print("Restarting web services...")
        subprocess.run(["supervisorctl", "-c", str(SUPERVISOR_CONF), "restart", "all"], env=env)
    else:
        print("No running supervisor daemon found.")

def kill_web():
    stop_web()
    if SUPERVISOR_PID.exists():
        pid = SUPERVISOR_PID.read_text().strip()
        if is_pid_running(pid):
            print(f"Killing supervisor process {pid}...")
            subprocess.run(["kill", "-TERM", pid])
        else:
            print("Supervisor PID exists but process is not running.")

def print_help():
    print("""\
Usage: web [start|stop|restart|kill|help]

Manage the web server layer.

Commands:
  start      Start supervisord and web services
  stop       Stop all services via supervisorctl
  restart    Restart all web services
  kill       Stop services and terminate supervisord
  help       Show this help message
""")

def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "help"
    dispatch = {
        "start": start_web,
        "stop": stop_web,
        "restart": restart_web,
        "kill": kill_web,
        "help": print_help,
    }
    dispatch.get(command, print_help)()

if __name__ == "__main__":
    main()
