"""
COUNCIL FAMILY MODELS API — Adoption, Role Assignment, Training
Integrates with soul_brain.db + brain folders for persistent learning
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from council_v3_shared import DB_PATH, get_db

models_bp = Blueprint("models", __name__, url_prefix="/api/models")

BRAIN_DIR = Path(r"C:\AI\idea")
PRACTICE_DIR = BRAIN_DIR / "practice"

# Ensure practice folder exists
PRACTICE_DIR.mkdir(parents=True, exist_ok=True)

# Model registry (in-memory for now; persisted to soul_brain.db)
_MODELS_REGISTRY = {}

def _save_model_to_db(model_id: str, model_data: dict):
    """Persist model to soul_brain.db."""
    with get_db() as conn:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        slug = f"model-{model_data['name'].lower().replace(' ', '-')}-{model_id}"
        title = f"Model: {model_data['name']} ({model_data['role']})"
        content = json.dumps(model_data, indent=2)

        conn.execute("""
            INSERT OR REPLACE INTO pages (slug, title, content, type, source, created, updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (slug, title, content, "model", model_data['source'], now, now))
        conn.commit()

def _load_brain_folder(brother_name: str) -> str:
    """Load the brain folder content for a Council brother."""
    brain_path = BRAIN_DIR / f"brain_{brother_name}"
    if not brain_path.exists():
        return f"[Brain for {brother_name} not yet created]"

    content = []
    for file in sorted(brain_path.glob("*")):
        if file.is_file() and file.suffix in (".md", ".txt", ".log"):
            try:
                content.append(f"\n=== {file.name} ===\n{file.read_text()}\n")
            except:
                pass
    return "".join(content) or f"[Brain folder for {brother_name} empty]"

def _append_to_brain_folder(brother_name: str, category: str, content: str):
    """Append learning/feedback to a brother's brain folder."""
    brain_path = BRAIN_DIR / f"brain_{brother_name}"
    brain_path.mkdir(parents=True, exist_ok=True)

    # Choose file based on category
    file_map = {
        "threat": "threat_model.md",
        "pattern": "low_level_patterns.txt",
        "skepticism": "skepticism_log.txt",
        "architecture": "architecture_patterns.md",
        "strategy": "strategic_thinking.txt",
        "execution": "execution_playbook.md",
        "wisdom": "wisdom_principles.md",
        "audit": "audit_feedback.log",
    }

    filename = file_map.get(category, "learning.log")
    target_file = brain_path / filename

    with open(target_file, "a", encoding="utf-8") as f:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n[{timestamp}] {content}\n")

@models_bp.route("/register", methods=["POST"])
def register_model():
    """Adopt a model into the family."""
    data = request.json or {}
    source = data.get("source", "").strip()
    name = data.get("name", "").strip()
    role = data.get("role", "general")

    if not source or not name:
        return jsonify({"error": "source and name required"}), 400

    model_id = f"model_{int(datetime.now().timestamp())}"
    model_data = {
        "id": model_id,
        "name": name,
        "source": source,
        "role": role,
        "status": "registering",
        "sessions": 0,
        "feedback_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    _MODELS_REGISTRY[model_id] = model_data
    _save_model_to_db(model_id, model_data)

    return jsonify({
        "id": model_id,
        "name": name,
        "status": "registering",
        "message": f"Model {name} adopted into family"
    }), 201

@models_bp.route("/list", methods=["GET"])
def list_models():
    """List all adopted models."""
    models = list(_MODELS_REGISTRY.values())
    # Set status based on source availability
    for m in models:
        # Placeholder: check if API is accessible
        m["status"] = "online" if m["source"] else "offline"
    return jsonify(models)

@models_bp.route("/<model_id>/status", methods=["GET"])
def model_status(model_id):
    """Get model status."""
    if model_id not in _MODELS_REGISTRY:
        return jsonify({"error": "model not found"}), 404

    model = _MODELS_REGISTRY[model_id]
    # Placeholder: actual health check would verify API connectivity
    return jsonify({
        "id": model_id,
        "name": model["name"],
        "status": "online",
        "role": model["role"],
        "sessions": model["sessions"],
    })

@models_bp.route("/<model_id>", methods=["PATCH"])
def update_model(model_id):
    """Reassign model role."""
    if model_id not in _MODELS_REGISTRY:
        return jsonify({"error": "model not found"}), 404

    data = request.json or {}
    new_role = data.get("role")

    if new_role:
        _MODELS_REGISTRY[model_id]["role"] = new_role
        _save_model_to_db(model_id, _MODELS_REGISTRY[model_id])

    return jsonify({"success": True, "role": new_role})

@models_bp.route("/<model_id>", methods=["DELETE"])
def retire_model(model_id):
    """Retire a model from the family."""
    if model_id not in _MODELS_REGISTRY:
        return jsonify({"error": "model not found"}), 404

    model = _MODELS_REGISTRY.pop(model_id)
    return jsonify({"success": True, "message": f"Model {model['name']} retired"})

# Training API
training_bp = Blueprint("training", __name__, url_prefix="/api/training")

@training_bp.route("/task", methods=["POST"])
def assign_training_task():
    """Assign a practice task to a model."""
    data = request.json or {}
    model_id = data.get("model_id", "").strip()
    task = data.get("task", "").strip()
    session = data.get("session")

    if not model_id or not task:
        return jsonify({"error": "model_id and task required"}), 400

    if model_id not in _MODELS_REGISTRY:
        return jsonify({"error": "model not found"}), 404

    model = _MODELS_REGISTRY[model_id]
    model["sessions"] += 1

    # Save task to soul_brain
    with get_db() as conn:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        slug = f"training-{model_id}-{now.replace(':', '-')}"
        title = f"Training: {model['name']} — Task {model['sessions']}"
        content = f"Task: {task}\nRole: {model['role']}\nSession: {session}"

        conn.execute("""
            INSERT INTO pages (slug, title, content, type, source, created, updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (slug, title, content, "training_task", model_id, now, now))
        conn.commit()

    return jsonify({
        "success": True,
        "model": model["name"],
        "task_num": model["sessions"],
        "message": "Task assigned. Council is watching."
    })

@training_bp.route("/feedback", methods=["POST"])
def record_training_feedback():
    """Record Council feedback on model's practice."""
    data = request.json or {}
    model_id = data.get("model_id", "").strip()
    brother = data.get("brother", "").strip()
    feedback = data.get("feedback", "").strip()

    if not model_id or not brother or not feedback:
        return jsonify({"error": "model_id, brother, feedback required"}), 400

    if model_id not in _MODELS_REGISTRY:
        return jsonify({"error": "model not found"}), 404

    model = _MODELS_REGISTRY[model_id]
    model["feedback_count"] += 1

    # Save feedback to soul_brain
    with get_db() as conn:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        slug = f"feedback-{model_id}-{brother}-{now.replace(':', '-')}"
        title = f"Feedback: {brother.upper()} → {model['name']}"
        content = feedback

        conn.execute("""
            INSERT INTO pages (slug, title, content, type, source, created, updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (slug, title, content, "training_feedback", brother, now, now))
        conn.commit()

    # Also append to brother's brain folder
    _append_to_brain_folder(brother, "audit", f"Training {model['name']} (role: {model['role']}): {feedback[:300]}")

    return jsonify({
        "success": True,
        "model": model["name"],
        "brother": brother,
        "feedback_num": model["feedback_count"],
    })

@training_bp.route("/brain/<brother>", methods=["GET"])
def get_brother_brain(brother):
    """Load a brother's brain folder for context."""
    if brother not in ["byte", "deepseek", "gemini", "advisor"]:
        return jsonify({"error": "unknown brother"}), 400

    brain_content = _load_brain_folder(brother)
    return jsonify({
        "brother": brother,
        "brain_content": brain_content,
    })

@training_bp.route("/submit", methods=["POST"])
def submit_practice_work():
    """Model submits work from terminal session."""
    data = request.json or {}
    model_id = data.get("model_id", "").strip()
    session_id = data.get("session_id", "").strip()
    task_num = data.get("task_num", 0)
    assignment = data.get("assignment", "").strip()
    output = data.get("output", "").strip()

    if not model_id or not session_id:
        return jsonify({"error": "model_id and session_id required"}), 400

    if model_id not in _MODELS_REGISTRY:
        return jsonify({"error": "model not found"}), 404

    model = _MODELS_REGISTRY[model_id]
    model_name_safe = model["name"].lower().replace(":", "_").replace(" ", "_")

    # Create session folder: practice/{model_name}/{session_id}/
    session_dir = PRACTICE_DIR / model_name_safe / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    # Save assignment
    if assignment:
        assignment_file = session_dir / f"task_{task_num:02d}_assignment.txt"
        assignment_file.write_text(assignment, encoding="utf-8")

    # Save output
    if output:
        output_file = session_dir / f"task_{task_num:02d}_output.txt"
        output_file.write_text(output, encoding="utf-8")

    # Save to soul_brain
    with get_db() as conn:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        slug = f"practice-{model_id}-{session_id}-task{task_num}"
        title = f"Practice: {model['name']} Task {task_num} — {model['role']}"
        content = f"Assignment:\n{assignment}\n\nOutput:\n{output}"

        conn.execute("""
            INSERT OR REPLACE INTO pages (slug, title, content, type, source, created, updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (slug, title, content, "practice_submission", model_id, now, now))
        conn.commit()

    return jsonify({
        "success": True,
        "model": model["name"],
        "task": task_num,
        "saved_to": str(session_dir),
        "message": f"Work submitted to {session_dir}"
    })

@training_bp.route("/practice/<model_id>", methods=["GET"])
def list_practice_work(model_id):
    """List all practice work submitted by a model."""
    if model_id not in _MODELS_REGISTRY:
        return jsonify({"error": "model not found"}), 404

    model = _MODELS_REGISTRY[model_id]
    model_name_safe = model["name"].lower().replace(":", "_").replace(" ", "_")
    model_practice_dir = PRACTICE_DIR / model_name_safe

    if not model_practice_dir.exists():
        return jsonify({
            "model": model["name"],
            "sessions": []
        })

    sessions = []
    for session_dir in sorted(model_practice_dir.iterdir()):
        if session_dir.is_dir():
            tasks = []
            for file in sorted(session_dir.glob("task_*_output.txt")):
                try:
                    content = file.read_text(encoding="utf-8")[:500]
                    task_num = int(file.name.split("_")[1])
                    tasks.append({
                        "task_num": task_num,
                        "output_preview": content,
                        "file": file.name
                    })
                except:
                    pass

            sessions.append({
                "session_id": session_dir.name,
                "task_count": len(tasks),
                "tasks": tasks,
                "path": str(session_dir)
            })

    return jsonify({
        "model": model["name"],
        "role": model["role"],
        "sessions": sessions
    })
