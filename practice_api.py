"""
Practice API — Shared practice log for all brothers to see
When @gemini, @byte, etc practice, their output goes to shared log
All brothers can view in real-time
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import os
from pathlib import Path

practice_bp = Blueprint('practice', __name__, url_prefix='/api/practice')

PRACTICE_LOG = Path(r"C:\AI\idea\practice_session.log")
PRACTICE_LOG.parent.mkdir(parents=True, exist_ok=True)

# In-memory session buffer (persisted to file)
practice_session = {
    "started": datetime.now().isoformat(),
    "entries": []
}


@practice_bp.route('/log', methods=['GET'])
def get_practice_log():
    """Get current practice session log"""
    try:
        if PRACTICE_LOG.exists():
            content = PRACTICE_LOG.read_text(encoding='utf-8')
            return jsonify({
                "started": practice_session["started"],
                "log": content,
                "lines": content.strip().split('\n') if content.strip() else []
            })
        else:
            return jsonify({
                "started": practice_session["started"],
                "log": "",
                "lines": []
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@practice_bp.route('/write', methods=['POST'])
def write_practice_log():
    """Write to practice log (called by models)

    Request:
    {
        "brother": "gemini",
        "action": "code" | "output" | "error" | "thought",
        "content": "...",
        "timestamp": "2026-06-11T18:30:00"
    }
    """
    try:
        data = request.json or {}
        brother = data.get("brother", "unknown")
        action = data.get("action", "output")
        content = data.get("content", "")
        timestamp = data.get("timestamp", datetime.now().isoformat())

        # Format log entry
        symbol = {
            "code": "💻",
            "output": "📤",
            "error": "❌",
            "thought": "💭",
            "feedback": "💬"
        }.get(action, "📝")

        entry = f"[{timestamp}] {symbol} {brother.upper()}: {action}\n{content}\n"

        # Append to file
        with open(PRACTICE_LOG, 'a', encoding='utf-8') as f:
            f.write(entry + "\n")

        # Track in memory
        practice_session["entries"].append({
            "brother": brother,
            "action": action,
            "content": content,
            "timestamp": timestamp
        })

        return jsonify({
            "status": "logged",
            "brother": brother,
            "total_entries": len(practice_session["entries"])
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@practice_bp.route('/clear', methods=['POST'])
def clear_practice_log():
    """Clear practice session log (start fresh)"""
    try:
        PRACTICE_LOG.unlink(missing_ok=True)
        practice_session["entries"] = []
        practice_session["started"] = datetime.now().isoformat()
        return jsonify({"status": "cleared"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@practice_bp.route('/save', methods=['POST'])
def save_practice_session():
    """Save current practice session to named file

    Request:
    {
        "name": "gemini-training-2026-06-11",
        "notes": "Tested coding abilities..."
    }
    """
    try:
        data = request.json or {}
        name = data.get("name", f"session-{datetime.now().timestamp()}")
        notes = data.get("notes", "")

        if PRACTICE_LOG.exists():
            content = PRACTICE_LOG.read_text(encoding='utf-8')
        else:
            content = ""

        # Save to practice folder
        save_dir = Path(r"C:\AI\idea\practice\shared")
        save_dir.mkdir(parents=True, exist_ok=True)

        save_file = save_dir / f"{name}.log"
        with open(save_file, 'w', encoding='utf-8') as f:
            f.write(f"# Practice Session: {name}\n")
            f.write(f"# Started: {practice_session['started']}\n")
            f.write(f"# Notes: {notes}\n")
            f.write(f"# Entries: {len(practice_session['entries'])}\n\n")
            f.write(content)

        return jsonify({
            "status": "saved",
            "file": str(save_file),
            "size_bytes": len(content)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
