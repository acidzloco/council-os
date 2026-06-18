"""
CouncilOS System Tray App
Right-click tray icon to control Council OS.
Green = all alive. Yellow = degraded. Red = bridge down.
"""

import os
import sys
import json
import time
import threading
import webbrowser
import subprocess
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "service"))

import pystray
from PIL import Image, ImageDraw
import watchdog as wd

LOG_DIR     = os.path.join(BASE_DIR, "logs")
STATUS_FILE = os.path.join(LOG_DIR, "watchdog_status.json")
COUNCIL_URL = "http://127.0.0.1:5002/dojo"
PYTHON_EXE  = sys.executable

os.makedirs(LOG_DIR, exist_ok=True)


# =============================================================================
# ICONS — generated programmatically, no image files needed
# =============================================================================
def _make_icon(color):
    img  = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=color, outline=(30, 30, 30), width=2)
    # small "C" label
    draw.text((20, 18), "C", fill="white")
    return img

ICON_GREEN  = _make_icon("#22c55e")
ICON_YELLOW = _make_icon("#eab308")
ICON_RED    = _make_icon("#ef4444")


# =============================================================================
# STATUS
# =============================================================================
def _get_status():
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _all_alive(status):
    procs = {k: v for k, v in status.items() if not k.startswith("_")}
    if not procs:
        return False
    return all(v.get("alive") for v in procs.values())


def _any_alive(status):
    procs = {k: v for k, v in status.items() if not k.startswith("_")}
    return any(v.get("alive") for v in procs.values())


def _status_text(status):
    lines = []
    for name, v in status.items():
        if name.startswith("_"):
            continue
        icon = "●" if v.get("alive") else "○"
        restarts = v.get("restarts", 0)
        lines.append(f"{icon} {name}  (restarts: {restarts})")
    return "\n".join(lines) if lines else "No process data"


# =============================================================================
# TRAY APP
# =============================================================================
class CouncilTray:
    def __init__(self):
        self.icon    = None
        self.watchdog_threads = []
        self._stop   = threading.Event()

    def _open_browser(self):
        webbrowser.open(COUNCIL_URL)

    def _open_logs(self):
        subprocess.Popen(["explorer", LOG_DIR])

    def _restart_bridge(self):
        wd.stop()
        time.sleep(1)
        wd._stop.clear()
        self.watchdog_threads = wd.start()

    def _stop_all(self):
        wd.stop()
        if self.icon:
            self.icon.stop()

    def _build_menu(self):
        status  = _get_status()
        summary = _status_text(status)
        updated = status.get("_updated", "")
        if updated:
            try:
                dt = datetime.fromisoformat(updated)
                updated = dt.strftime("%H:%M:%S")
            except Exception:
                pass

        return pystray.Menu(
            pystray.MenuItem(f"Council OS", None, enabled=False),
            pystray.MenuItem(f"Updated: {updated}", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(summary, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open Council Dojo", lambda: self._open_browser()),
            pystray.MenuItem("Restart Bridge",    lambda: threading.Thread(target=self._restart_bridge, daemon=True).start()),
            pystray.MenuItem("Open Logs Folder",  lambda: self._open_logs()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Stop Council OS",   lambda: self._stop_all()),
        )

    def _update_loop(self):
        while not self._stop.is_set():
            status = _get_status()
            if _all_alive(status):
                self.icon.icon  = ICON_GREEN
                self.icon.title = "Council OS — All systems operational"
            elif _any_alive(status):
                self.icon.icon  = ICON_YELLOW
                self.icon.title = "Council OS — Degraded"
            else:
                self.icon.icon  = ICON_RED
                self.icon.title = "Council OS — Bridge down"

            self.icon.menu = self._build_menu()
            time.sleep(3)

    def run(self):
        # Start watchdog
        self.watchdog_threads = wd.start()

        # Build tray
        self.icon = pystray.Icon(
            "CouncilOS",
            ICON_YELLOW,
            "Council OS — Starting...",
            menu=self._build_menu(),
        )

        # Update thread
        t = threading.Thread(target=self._update_loop, daemon=True)
        t.start()

        self.icon.run()
        self._stop.set()
        wd.stop()


if __name__ == "__main__":
    app = CouncilTray()
    app.run()
