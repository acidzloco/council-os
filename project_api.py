"""
Project submission system — @ext tag triggers all brothers to save to their folders.

Usage in chat:
  build simple notepad @python
  create login form @html
  write sorting algo @cpp
  generate config @json

All brothers save their version → different styles = richer training data.
"""

import re
import uuid
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Blueprint, request, jsonify

project_bp = Blueprint("project", __name__)

# ─── TASK TRACKER ─────────────────────────────────────────────────────────────
# task_id → status dict — lives in memory, survives the session
_tasks: dict = {}
_tasks_lock  = threading.Lock()

PROJECT_ROOT = Path(r"C:\AI\idea\project")

BROTHERS = ["byte", "deepseek", "gemini", "advisor"]

# @tag → file extension mapping
_TAG_EXT = {
    "python": ".py",   "py": ".py",
    "javascript": ".js", "js": ".js",
    "typescript": ".ts", "ts": ".ts",
    "html": ".html",
    "css": ".css",
    "bash": ".sh",     "sh": ".sh",
    "powershell": ".ps1", "ps1": ".ps1",
    "cpp": ".cpp",     "c++": ".cpp",
    "c": ".c",
    "rust": ".rs",
    "go": ".go",
    "java": ".java",
    "sql": ".sql",
    "json": ".json",
    "yaml": ".yaml",   "yml": ".yaml",
    "mql5": ".mq5",    "mq5": ".mq5",
    "txt": ".txt",     "text": ".txt",
    "md": ".md",
    "png": ".png",     "jpg": ".jpg",  "jpeg": ".jpg",
    "csv": ".csv",
    "xml": ".xml",
    "toml": ".toml",
    "ini": ".ini",
}


def _ensure_dirs():
    for name in BROTHERS:
        (PROJECT_ROOT / name).mkdir(parents=True, exist_ok=True)


def _slug(text: str) -> str:
    """Clean topic into a safe filename slug."""
    # strip @tags from slug
    s = re.sub(r"@\w+", "", text)
    s = re.sub(r"[^\w\s-]", "", s.lower())
    s = re.sub(r"[\s_-]+", "_", s).strip("_")
    return s[:50] or "work"


def parse_ext_tag(message: str) -> str | None:
    """
    Find @ext tag in message. Returns file extension (e.g. '.py') or None.
    Examples: '@python' → '.py', '@html' → '.html', '@cpp' → '.cpp'
    """
    matches = re.findall(r"@(\w+)", message.lower())
    for tag in matches:
        # skip brother names and special commands
        if tag in ("byte", "deepseek", "gemini", "advisor", "all", "audit"):
            continue
        if tag in _TAG_EXT:
            return _TAG_EXT[tag]
        # unknown tag but looks like an extension (short, no spaces)
        if len(tag) <= 6:
            return f".{tag}"
    return None


def _extract_code(content: str) -> str:
    """
    Extract code from reply:
    1. Complete fenced block → return largest block content
    2. Truncated block (no closing fence) → strip opening fence line, return rest
    3. No fences → return full reply
    """
    # Complete blocks
    pattern = r"```[a-zA-Z0-9+#]*\n(.*?)```"
    blocks = re.findall(pattern, content, re.DOTALL)
    if blocks:
        return max(blocks, key=len).strip()
    # Truncated block — opening fence present but no closing fence (token limit hit)
    truncated = re.match(r"```[a-zA-Z0-9+#]*\n(.*)", content, re.DOTALL)
    if truncated:
        return truncated.group(1).strip()
    return content.strip()


def auto_save(brother: str, content: str, topic: str = "", ext: str = "") -> list[str]:
    """
    Save a brother's reply to their project folder.

    If ext is given (@python → .py):
      - Extract code block if present, else save raw reply
      - Save as {timestamp}_{slug}{ext}
      - Also save .md summary alongside

    Returns list of saved file paths.
    """
    _ensure_dirs()
    ts     = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug   = _slug(topic) if topic else "work"
    folder = PROJECT_ROOT / brother
    saved  = []

    if ext:
        # Save the actual file (code or content)
        code  = _extract_code(content)
        fname = f"{ts}_{slug}{ext}"
        fpath = folder / fname
        fpath.write_text(code, encoding="utf-8")
        saved.append(str(fpath))
        print(f"[project] {brother} → {fname}", flush=True)

    # Always save .md summary
    md_path = folder / f"{ts}_{slug}.md"
    header  = f"# {brother.upper()} — {topic or 'Work'}\n"
    header += f"**Saved:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    if ext:
        header += f"**File:** `{ts}_{slug}{ext}`\n"
    header += "\n---\n\n"
    md_path.write_text(header + content, encoding="utf-8")
    saved.append(str(md_path))

    return saved


# ─── API ROUTES ───────────────────────────────────────────────────────────────

@project_bp.route("/api/project/list", methods=["GET"])
def project_list():
    """List all submissions — optionally filter by brother."""
    _ensure_dirs()
    brother = request.args.get("brother", "").lower()
    targets = [brother] if brother in BROTHERS else BROTHERS
    results = {}

    for name in targets:
        folder = PROJECT_ROOT / name
        files  = sorted(folder.iterdir(), reverse=True) if folder.exists() else []
        results[name] = [
            {
                "file":    f.name,
                "ext":     f.suffix,
                "size":    f.stat().st_size,
                "created": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            }
            for f in files[:50] if f.is_file()
        ]

    return jsonify({"ok": True, "project": results})


@project_bp.route("/api/project/read", methods=["GET"])
def project_read():
    """Read a specific file."""
    brother = request.args.get("brother", "").lower()
    fname   = request.args.get("file", "")

    if brother not in BROTHERS:
        return jsonify({"error": "unknown brother"}), 400
    if not fname:
        return jsonify({"error": "file required"}), 400

    fpath = PROJECT_ROOT / brother / Path(fname).name
    if not fpath.exists():
        return jsonify({"error": "file not found"}), 404

    return jsonify({
        "ok":      True,
        "brother": brother,
        "file":    fname,
        "content": fpath.read_text(encoding="utf-8", errors="replace"),
    })


@project_bp.route("/api/project/audit", methods=["GET"])
def project_audit():
    """Latest submission from each brother for cross-review."""
    _ensure_dirs()
    summary = {}

    for name in BROTHERS:
        folder = PROJECT_ROOT / name
        # get latest non-.md file first, fallback to .md
        all_files = sorted(folder.glob("*"), reverse=True) if folder.exists() else []
        code_files = [f for f in all_files if f.suffix != ".md" and f.is_file()]
        latest = code_files[0] if code_files else (all_files[0] if all_files else None)

        if latest:
            content = latest.read_text(encoding="utf-8", errors="replace")
            summary[name] = {
                "file":    latest.name,
                "ext":     latest.suffix,
                "preview": content[:500],
                "full":    content,
                "created": datetime.fromtimestamp(latest.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            }
        else:
            summary[name] = None

    return jsonify({"ok": True, "audit": summary})


@project_bp.route("/api/project/stats", methods=["GET"])
def project_stats():
    """Count submissions per brother."""
    _ensure_dirs()
    stats = {}
    total = 0
    for name in BROTHERS:
        folder = PROJECT_ROOT / name
        count  = len([f for f in folder.iterdir() if f.is_file()]) if folder.exists() else 0
        stats[name] = count
        total += count
    return jsonify({"ok": True, "stats": stats, "total": total})


# ─── R1/R2/R3 PROJECT RUNNER ──────────────────────────────────────────────────

def _log(msg: str):
    """Thread-safe print that survives redirected stdout."""
    try:
        import sys as _sys
        out = getattr(_sys, '__stdout__', None) or _sys.stdout
        out.write(msg + "\n")
        out.flush()
    except Exception:
        pass


def _update_task(task_id: str, **kwargs):
    with _tasks_lock:
        _tasks[task_id].update(kwargs)


def _run_project(task_id: str, task: str, ext: str, call_fn):
    """
    R1 → R2 → R3 pipeline running in a background thread.
    call_fn(name, system, user, max_tokens) → str  (injected from bridge)
    """
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = _slug(task)
    _ensure_dirs()

    # ── R1: All brothers write independently (parallel, no peeking) ──────────
    _update_task(task_id, phase="r1")

    R1_SYSTEM = (
        "You are {name}, a Council member. You are doing independent project work.\n"
        "Write a complete, working implementation. No placeholders. No TODO stubs.\n"
        "Output ONLY the code inside a fenced code block. Add a brief comment at the top.\n"
        "Do not explain the code outside the block — just ship it."
    )

    r1_results = {}

    def _do_r1(name):
        _update_task(task_id, **{f"r1_{name}": "running"})
        try:
            system = R1_SYSTEM.format(name=name.upper())
            reply  = call_fn(name, system, task, 6000)
            code   = _extract_code(reply)
            fpath  = PROJECT_ROOT / name / f"{ts}_{slug}_r1{ext}"
            fpath.write_text(code, encoding="utf-8")
            r1_results[name] = {"code": code, "file": str(fpath), "fname": fpath.name}
            _update_task(task_id, **{f"r1_{name}": "done", f"file_r1_{name}": fpath.name})
        except Exception as e:
            r1_results[name] = {"code": f"# error: {e}", "file": "", "fname": ""}
            _update_task(task_id, **{f"r1_{name}": f"error: {e}"})
        _log(f"[R1] {name} → {_tasks[task_id].get(f'r1_{name}','?')}")

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(_do_r1, BROTHERS))

    # ── R2: All brothers cross-review each other's R1 ────────────────────────
    _update_task(task_id, phase="r2")

    # build the context block showing all R1 outputs
    r1_ctx_parts = []
    for name in BROTHERS:
        code = r1_results.get(name, {}).get("code", "[not submitted]")
        r1_ctx_parts.append(f"=== {name.upper()} R1 ===\n```\n{code[:1200]}\n```")
    r1_ctx = "\n\n".join(r1_ctx_parts)

    R2_SYSTEM = (
        "You are {name}, a Council member reviewing your brothers' work.\n"
        "Below are all 4 R1 implementations of the same task.\n"
        "Review them from YOUR specialist perspective:\n"
        "- What's strong in each?\n"
        "- What's missing or wrong?\n"
        "- Which approach is best and why?\n"
        "Be direct. 3-6 sentences per brother. No fluff."
    )

    r2_results = {}

    def _do_r2(name):
        _update_task(task_id, **{f"r2_{name}": "running"})
        try:
            system  = R2_SYSTEM.format(name=name.upper())
            user    = f"TASK: {task}\n\nR1 SUBMISSIONS:\n{r1_ctx}"
            reply   = call_fn(name, system, user, 3000)
            fpath   = PROJECT_ROOT / name / f"{ts}_{slug}_r2_review.md"
            header  = f"# {name.upper()} — R2 Cross-Review\n**Task:** {task}\n\n---\n\n"
            fpath.write_text(header + reply, encoding="utf-8")
            r2_results[name] = reply
            _update_task(task_id, **{f"r2_{name}": "done", f"file_r2_{name}": fpath.name})
        except Exception as e:
            r2_results[name] = f"[review error: {e}]"
            _update_task(task_id, **{f"r2_{name}": f"error: {e}"})
        _log(f"[R2] {name} → {_tasks[task_id].get(f'r2_{name}','?')}")

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(_do_r2, BROTHERS))

    # ── R3: Advisor synthesizes the best approach ─────────────────────────────
    _update_task(task_id, phase="r3")

    r2_ctx_parts = []
    for name in BROTHERS:
        review = r2_results.get(name, "[no review]")
        r2_ctx_parts.append(f"=== {name.upper()} REVIEW ===\n{review[:800]}")
    r2_ctx = "\n\n".join(r2_ctx_parts)

    R3_SYSTEM = (
        "You are the Advisor — the synthesizer of the Council.\n"
        "You have seen all 4 implementations and all 4 reviews.\n"
        "Your job: write the DEFINITIVE version that combines the best of all approaches.\n"
        "Output a complete, working implementation in a fenced code block.\n"
        "After the code block, add a short 'Why this version' section (3-5 sentences)."
    )

    _update_task(task_id, r3_advisor="running")
    try:
        user   = f"TASK: {task}\n\nR1 CODE:\n{r1_ctx}\n\nR2 REVIEWS:\n{r2_ctx}"
        reply  = call_fn("advisor", R3_SYSTEM, user, 6000)
        code   = _extract_code(reply)
        # save synthesis code file
        syn_code  = PROJECT_ROOT / "advisor" / f"{ts}_{slug}_r3_synthesis{ext}"
        syn_code.write_text(code, encoding="utf-8")
        # save full synthesis with reasoning
        syn_full  = PROJECT_ROOT / "advisor" / f"{ts}_{slug}_r3_synthesis.md"
        header    = f"# ADVISOR — R3 Synthesis\n**Task:** {task}\n\n---\n\n"
        syn_full.write_text(header + reply, encoding="utf-8")
        _log(f"[R3] synthesis → {syn_code.name}")
        _update_task(task_id,
                     r3_advisor="done",
                     file_r3_code=syn_code.name,
                     file_r3_md=syn_full.name,
                     r3_preview=reply[:600])
    except Exception as e:
        _update_task(task_id, r3_advisor=f"error: {e}")
        _log(f"[R3] error: {e}")

    _update_task(task_id, phase="done")
    _log(f"[project] task {task_id} complete")


@project_bp.route("/api/project/run", methods=["POST"])
def project_run():
    """
    Start R1→R2→R3 pipeline in background.
    Returns task_id immediately — poll /api/project/status/<task_id> for progress.
    """
    data = request.json or {}
    task = data.get("task", "").strip()
    ext  = data.get("ext", ".py")

    if not task:
        return jsonify({"error": "task required"}), 400

    # get call_fn from bridge (imported at runtime to avoid circular)
    from council_v3_bridge import _native_call

    task_id = str(uuid.uuid4())[:8]
    with _tasks_lock:
        _tasks[task_id] = {
            "task_id": task_id,
            "task":    task,
            "ext":     ext,
            "phase":   "starting",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            **{f"r1_{n}": "pending" for n in BROTHERS},
            **{f"r2_{n}": "pending" for n in BROTHERS},
            "r3_advisor": "pending",
        }

    thread = threading.Thread(
        target=_run_project,
        args=(task_id, task, ext, _native_call),
        daemon=True,
    )
    thread.start()

    return jsonify({"ok": True, "task_id": task_id})


@project_bp.route("/api/project/status/<task_id>", methods=["GET"])
def project_status(task_id):
    """Poll for R1→R2→R3 progress."""
    with _tasks_lock:
        task = _tasks.get(task_id)
    if not task:
        return jsonify({"error": "task not found"}), 404
    return jsonify({"ok": True, "status": task})
