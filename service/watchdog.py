"""
CouncilOS Watchdog
Monitors bridge + brain processes. Auto-restarts dead processes.
Writes status to logs/watchdog_status.json for tray app to read.
Run standalone or imported by tray app.
"""

import os
import sys
import time
import json
import subprocess
import threading
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DIR  = os.path.join(BASE_DIR, "logs")
STATUS_FILE = os.path.join(LOG_DIR, "watchdog_status.json")
PYTHON_EXE  = sys.executable

os.makedirs(LOG_DIR, exist_ok=True)

handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "watchdog.log"),
    maxBytes=2*1024*1024, backupCount=3
)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
log = logging.getLogger("Watchdog")
log.setLevel(logging.INFO)
log.addHandler(handler)
log.addHandler(logging.StreamHandler(sys.stdout))

PROCESSES = {
    "bridge": {
        "script": os.path.join(BASE_DIR, "council_v3_bridge.py"),
        "cwd":    BASE_DIR,
        "restart_delay": 5,
    },
}

_state = {}   # name -> {"proc": Popen, "restarts": int, "status": str, "last_restart": str}
_lock  = threading.Lock()
_stop  = threading.Event()


def _write_status():
    status = {}
    with _lock:
        for name, s in _state.items():
            alive = s["proc"] is not None and s["proc"].poll() is None
            status[name] = {
                "alive":        alive,
                "restarts":     s["restarts"],
                "status":       "running" if alive else "down",
                "last_restart": s.get("last_restart", ""),
            }
    status["_updated"] = datetime.now().isoformat()
    try:
        with open(STATUS_FILE, "w") as f:
            json.dump(status, f, indent=2)
    except Exception:
        pass


def _launch(name, cfg):
    script = cfg["script"]
    if not os.path.exists(script):
        log.error(f"[{name}] Script not found: {script}")
        return None
    log.info(f"[{name}] Launching: {PYTHON_EXE} {script}")
    return subprocess.Popen(
        [PYTHON_EXE, script],
        cwd=cfg.get("cwd", BASE_DIR),
        stdout=open(os.path.join(LOG_DIR, f"{name}_stdout.log"), "a"),
        stderr=open(os.path.join(LOG_DIR, f"{name}_stderr.log"), "a"),
    )


def _watch_one(name, cfg):
    delay = cfg.get("restart_delay", 5)
    with _lock:
        _state[name] = {"proc": None, "restarts": 0, "status": "starting", "last_restart": ""}

    proc = _launch(name, cfg)
    with _lock:
        _state[name]["proc"] = proc

    while not _stop.is_set():
        time.sleep(2)
        with _lock:
            proc = _state[name]["proc"]
            alive = proc is not None and proc.poll() is None

        if not alive and not _stop.is_set():
            log.warning(f"[{name}] Process down. Restarting in {delay}s...")
            time.sleep(delay)
            if _stop.is_set():
                break
            new_proc = _launch(name, cfg)
            with _lock:
                _state[name]["proc"]        = new_proc
                _state[name]["restarts"]   += 1
                _state[name]["last_restart"] = datetime.now().isoformat()
                delay = min(delay * 2, 60)
        else:
            delay = cfg.get("restart_delay", 5)

        _write_status()

    log.info(f"[{name}] Watchdog thread exiting.")


def start(extra_processes=None):
    procs = dict(PROCESSES)
    if extra_processes:
        procs.update(extra_processes)

    threads = []
    for name, cfg in procs.items():
        t = threading.Thread(target=_watch_one, args=(name, cfg), daemon=True)
        t.start()
        threads.append(t)
    return threads


def stop():
    _stop.set()
    with _lock:
        for name, s in _state.items():
            if s["proc"] and s["proc"].poll() is None:
                try:
                    s["proc"].terminate()
                    log.info(f"[{name}] Terminated.")
                except Exception:
                    pass


def get_status():
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


if __name__ == "__main__":
    log.info("Watchdog starting standalone...")
    threads = start()
    try:
        while True:
            time.sleep(5)
            _write_status()
    except KeyboardInterrupt:
        log.info("Watchdog stopping...")
        stop()
