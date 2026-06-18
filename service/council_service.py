"""
CouncilOS Windows Service
Runs council_v3_bridge.py as a proper Windows service.
Install:  python council_service.py install
Start:    python council_service.py start
Stop:     python council_service.py stop
Remove:   python council_service.py remove
"""

import sys
import os
import subprocess
import logging
import time
from logging.handlers import RotatingFileHandler

import win32service
import win32serviceutil
import win32event
import win32api
import servicemanager

BASE_DIR   = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BRIDGE     = os.path.join(BASE_DIR, "council_v3_bridge.py")
LOG_DIR    = os.path.join(BASE_DIR, "logs")
LOG_FILE   = os.path.join(LOG_DIR, "council_service.log")
PYTHON_EXE = sys.executable

os.makedirs(LOG_DIR, exist_ok=True)

handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
log = logging.getLogger("CouncilService")
log.setLevel(logging.INFO)
log.addHandler(handler)


class CouncilOSService(win32serviceutil.ServiceFramework):
    _svc_name_         = "CouncilOS"
    _svc_display_name_ = "Council OS — AI Mesh Bridge"
    _svc_description_  = "Council OS multi-model AI bridge. Keeps the brothers alive."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.process    = None
        self.running    = True

    def SvcStop(self):
        log.info("Service stop requested.")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.running = False
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        log.info("CouncilOS service starting.")
        self._run_bridge()

    def _run_bridge(self):
        restart_delay = 5
        while self.running:
            try:
                log.info(f"Launching bridge: {PYTHON_EXE} {BRIDGE}")
                self.process = subprocess.Popen(
                    [PYTHON_EXE, BRIDGE],
                    cwd=BASE_DIR,
                    stdout=open(os.path.join(LOG_DIR, "bridge_stdout.log"), "a"),
                    stderr=open(os.path.join(LOG_DIR, "bridge_stderr.log"), "a"),
                )
                self.process.wait()
                if not self.running:
                    break
                log.warning(f"Bridge exited (code {self.process.returncode}). Restarting in {restart_delay}s...")
                time.sleep(restart_delay)
                restart_delay = min(restart_delay * 2, 60)
            except Exception as e:
                log.error(f"Bridge crash: {e}")
                time.sleep(restart_delay)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(CouncilOSService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(CouncilOSService)
