import sys
import os
import time
import subprocess
from pathlib import Path
from config import get_configuration

# Ensure the `bin` directory is in sys.path to allow `from modules import config`
APP_ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = APP_ROOT / "bin"
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

from modules import config

SUPERVISOR_CONF = APP_ROOT / "etc/supervisor/queue-manager.conf"
SUPERVISOR_LOG = APP_ROOT / "var/log/queue-manager.log"
SUPERVISOR_PID = APP_ROOT / "var/pid/queue-manager.pid"

cfg = config.get_configuration()

env = os.environ.copy()
env.update({
    "APP_NAME": "licman",
    "USER": os.getenv("LOGNAME", "unknown"),
    "DIR": str(APP_ROOT),
    "BIN": str(APP_ROOT / "bin"),
    "ETC": str(APP_ROOT / "etc"),
    "OPT": str(APP_ROOT / "opt"),
    "TMP": str(APP_ROOT / "tmp"),
    "VAR": str(APP_ROOT / "var"),
    "SRC": str(APP_ROOT / "src"),
    "CACHE_DIR": str(APP_ROOT / "var/cache"),
    "LOG_DIR": str(APP_ROOT / "var/log"),
    "PATH": os.getenv("PATH", "/usr/bin:/bin"),
    "CELERY_BROKER_URL": cfg["celery"].get("CELERY_BROKER_URL", ""),
    "CELERY_WORKER_CONCURRENCY": cfg["celery"].get("CELERY_WORKER_CONCURRENCY", "2"),
    "BASE_DIR": str(APP_ROOT),
})

def start_queue():
    if SUPERVISOR_PID.exists():
        with SUPERVISOR_PID.open() as f:
            pid = f.read().strip()
        if pid and pid.isdigit() and is_pid_running(pid):
            print("Supervisor already running. Starting queue services...")
            subprocess.run(["supervisorctl", "-c", str(SUPERVISOR_CONF), "start", "all"], env=env)
            return
    print("Starting queue manager daemon...")
    subprocess.run(["supervisord", "-c", str(SUPERVISOR_CONF)], env=env)
    time.sleep(3)
    subprocess.run(["tail", "-n", "18", str(SUPERVISOR_LOG)])

def stop_queue():
    if SUPERVISOR_PID.exists() and is_pid_running(SUPERVISOR_PID.read_text().strip()):
        print("Stopping queue services...")
        subprocess.run(["supervisorctl", "-c", str(SUPERVISOR_CONF), "stop", "all"], env=env)
    else:
        print("No running supervisor daemon found.")

def restart_queue():
    if SUPERVISOR_PID.exists() and is_pid_running(SUPERVISOR_PID.read_text().strip()):
        print("Restarting queue services...")
        subprocess.run(["supervisorctl", "-c", str(SUPERVISOR_CONF), "restart", "all"], env=env)
    else:
        print("No running supervisor daemon found.")

def kill_queue():
    stop_queue()
    if SUPERVISOR_PID.exists():
        pid = SUPERVISOR_PID.read_text().strip()
        if is_pid_running(pid):
            print(f"Killing supervisor process {pid}...")
            subprocess.run(["kill", "-TERM", pid])
        else:
            print("Supervisor PID exists but process is not running.")

def is_pid_running(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False

def print_help():
    print("""
Usage: queue [start|stop|restart|kill|help]

Manage the Celery queue service layer.

Commands:
  start      Start supervisord and queue worker
  stop       Stop all workers via supervisorctl
  restart    Restart all workers
  kill       Stop workers and terminate supervisord
  help       Show this help message
""")

def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "help"
    dispatch = {
        "start": start_queue,
        "stop": stop_queue,
        "restart": restart_queue,
        "kill": kill_queue,
        "help": print_help,
    }
    dispatch.get(command, print_help)()

if __name__ == "__main__":
    main()
