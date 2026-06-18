
import sys
import os
import json
import subprocess
import threading
from datetime import datetime
from queue import Queue

# Define the base directory and add it to sys.path
BASE_DIR = r"C:\AI\council_v3"
sys.path.append(BASE_DIR)

from flask import Blueprint, jsonify, request, Response
from council_v3_shared import BROTHERS, get_db, DB_PATH

dojo_bp = Blueprint('dojo', __name__)

# Terminal process management
terminal_process = None
terminal_output_queue = Queue()

def read_terminal_output(process, queue):
    while True:
        line = process.stdout.readline()
        if not line:
            break
        queue.put(line)

@dojo_bp.route("/api/version")
def get_version():
    return jsonify({"version": "Council OS v5 - Dojo", "badge": "v5.0-Dojo"})

@dojo_bp.route("/api/overview")
def get_overview():
    try:
        with get_db() as conn:
            total_pages = conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
            total_lessons = conn.execute("SELECT COUNT(*) FROM pages WHERE type='lesson'").fetchone()[0]
            total_sessions = conn.execute("SELECT COUNT(*) FROM agent_sessions").fetchone()[0]
    except Exception as e:
        print(f"[-] DB Error in /api/overview: {e}")
        total_pages = total_lessons = total_sessions = 0
        
    return jsonify({
        "generated_at": datetime.now().isoformat(),
        "today": datetime.now().strftime("%Y-%m-%d"),
        "totals": {
            "subjects": 0,
            "note_files": total_pages,
            "quizzes": total_lessons,
            "agent_tasks": total_sessions
        },
        "hero": {
            "greeting": "Welcome to the Dojo, Commander",
            "date": datetime.now().strftime("%A, %B %d, %Y"),
            "day_streak": 7 
        }
    })

@dojo_bp.route("/api/chat/agents")
def get_chat_agents():
    agents = []
    colors = {"byte": "#f43f5e", "deepseek": "#60a5fa", "gemini": "#14b8a6", "advisor": "#a855f7"}
    icons = {"byte": "☠", "deepseek": "🧠", "gemini": "♊", "advisor": "📜"}
    roles = {
        "byte": "Offensive Security",
        "deepseek": "Research & Math",
        "gemini": "Integration & Tools",
        "advisor": "Synthesis"
    }
    
    for key in BROTHERS:
        agents.append({
            "key": key,
            "name": key.capitalize(),
            "role": roles.get(key, "Council Member"),
            "icon": icons.get(key, "🤖"),
            "color": colors.get(key, "#f97316"),
            "desc": BROTHERS[key].get("role", "")[:100],
            "platform": "Dojo Terminal",
            "status": "online",
            "running": False
        })
    return jsonify({"agents": agents})

@dojo_bp.route("/api/agents/analytics")
def get_agents_analytics():
    agents = []
    colors = {"byte": "#f43f5e", "deepseek": "#60a5fa", "gemini": "#14b8a6", "advisor": "#a855f7"}
    icons = {"byte": "☠", "deepseek": "🧠", "gemini": "♊", "advisor": "📜"}
    
    try:
        with get_db() as conn:
            for key in BROTHERS:
                count = conn.execute("SELECT COUNT(*) FROM agent_sessions WHERE brother_name=?", (key,)).fetchone()[0]
                agents.append({
                    "key": key,
                    "name": key.capitalize(),
                    "role": "Council Member",
                    "icon": icons.get(key, "🤖"),
                    "color": colors.get(key, "#f97316"),
                    "status": "live",
                    "totals": {"tasks": count, "completed": count, "failed": 0},
                    "success_percentage": 100.0,
                    "tasks_today": 0,
                    "last_active_time": datetime.now().isoformat(),
                    "last_model_used": "Native API"
                })
    except Exception as e:
        print(f"[-] DB Error in /api/agents/analytics: {e}")
        
    return jsonify({"generated_at": datetime.now().isoformat(), "agents": agents})

# --- Terminal Dojo Routes ---

@dojo_bp.route("/api/terminal/command", methods=["POST"])
def run_command():
    global terminal_process
    data = request.json or {}
    cmd = data.get("command", "").strip()
    
    if not cmd:
        return jsonify({"error": "command required"}), 400
        
    try:
        # Start a persistent shell if not already running
        if terminal_process is None or terminal_process.poll() is not None:
            terminal_process = subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-NoLogo"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd="C:\\AI"
            )
            threading.Thread(target=read_terminal_output, args=(terminal_process, terminal_output_queue), daemon=True).start()
            
        terminal_process.stdin.write(cmd + "\n")
        terminal_process.stdin.flush()
        return jsonify({"status": "sent"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dojo_bp.route("/api/terminal/stream")
def stream_logs():
    def generate():
        while True:
            if not terminal_output_queue.empty():
                line = terminal_output_queue.get()
                yield f"data: {json.dumps({'line': line})}\n\n"
            else:
                import time
                time.sleep(0.1)
    return Response(generate(), mimetype="text/event-stream")

