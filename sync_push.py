"""
Council OS — Mobile Sync Push (Termux)
Run this on your phone before leaving.
Serves soul_brain entries + training files for lab to pull.

Usage:
  python sync_push.py

Then go home, click SYNC_FROM_MOBILE.bat on lab PC.
Server auto-stops after lab pulls or after 1 hour.
"""

import json
import os
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime
import socket
import threading

PORT = 8765

# Find soul_brain.db — search common Termux paths
def find_soul_brain():
    candidates = [
        Path.home() / "soul_brain" / "soul_brain.db",
        Path.home() / "council_v3" / "soul_brain.db",
        Path("/data/data/com.termux/files/home/soul_brain/soul_brain.db"),
        Path("/storage/emulated/0/AI/soul_brain.db"),
        Path.home() / "AI" / "soul_brain" / "soul_brain.db",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

# Find training files
def find_training_files():
    training_dirs = [
        Path.home() / "council_v3" / "brain" / "practice",
        Path.home() / "AI" / "council_v3" / "brain" / "practice",
        Path.home() / "training_data",
    ]
    files = {}
    for d in training_dirs:
        if d.exists():
            for f in d.rglob("*"):
                if f.is_file() and f.suffix in {".jsonl", ".md", ".txt", ".log"}:
                    files[f.name] = f
    return files

# Export soul_brain entries
def export_soul_brain(db_path):
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM pages ORDER BY updated_at DESC LIMIT 100")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[soul_brain] Error: {e}")
        return []

# State
_soul_brain_cache = None
_training_files = {}
_manifest = {}
_pulled = threading.Event()

class SyncHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # quiet

    def do_GET(self):
        if self.path == "/ping":
            self._json({"status": "ok"})

        elif self.path == "/manifest":
            self._json(_manifest)

        elif self.path == "/soul_brain":
            self._json(_soul_brain_cache or [])

        elif self.path == "/files_list":
            self._json(list(_training_files.keys()))

        elif self.path.startswith("/file/"):
            fname = self.path[6:]
            if fname in _training_files:
                data = _training_files[fname].read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                print(f"  [sent] {fname}")
            else:
                self.send_response(404)
                self.end_headers()

        elif self.path == "/done":
            self._json({"status": "sync complete"})
            _pulled.set()

        else:
            self.send_response(404)
            self.end_headers()

    def _json(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except:
        return "127.0.0.1"
    finally:
        s.close()

def main():
    global _soul_brain_cache, _training_files, _manifest

    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║   COUNCIL OS — MOBILE SYNC PUSH      ║")
    print("  ║   Mobile → Lab                       ║")
    print("  ╚══════════════════════════════════════╝")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load soul_brain
    db = find_soul_brain()
    if db:
        print(f"  Soul Brain: {db}")
        _soul_brain_cache = export_soul_brain(db)
        print(f"  Exported {len(_soul_brain_cache)} entries")
    else:
        print("  Soul Brain: not found — skipping")
        _soul_brain_cache = []

    # Load training files
    _training_files = find_training_files()
    print(f"  Training files: {len(_training_files)} files found")

    # Build manifest
    local_ip = get_local_ip()
    _manifest = {
        "device": f"Mobile ({local_ip})",
        "timestamp": datetime.now().isoformat(),
        "entry_count": len(_soul_brain_cache),
        "file_count": len(_training_files),
    }

    # Start server
    server = HTTPServer(("0.0.0.0", PORT), SyncHandler)
    print()
    print(f"  ── Sync server ready ──────────────────")
    print(f"  IP   : {local_ip}")
    print(f"  Port : {PORT}")
    print()
    print(f"  Now go home and click SYNC_FROM_MOBILE.bat")
    print(f"  Server auto-stops after lab pulls.")
    print(f"  Press Ctrl+C to stop manually.")
    print()

    # Run until pulled or 1 hour
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    _pulled.wait(timeout=3600)
    print()
    print("  Sync complete. Shutting down.")
    server.shutdown()

if __name__ == "__main__":
    main()
