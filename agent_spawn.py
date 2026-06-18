"""
Council Agent — Sub-agent Spawning (v4 Roadmap Item 3)
Parent agents spawn typed child agents in background threads.
Registered tools: spawn_agent, collect_agent.
Bridge calls register_brother_spawn() at startup to populate the brother registry.
"""
import threading
import time
import uuid
from typing import Callable, Dict, Optional, Tuple

from tool_registry import register, PermissionTier

# Populated by bridge at startup — maps brother name → (call_fn, role_string)
_brother_spawn_registry: Dict[str, Tuple[Callable, str]] = {}

# Active sub-agents keyed by session_id
_active_agents: Dict[str, dict] = {}
_active_lock = threading.Lock()


def register_brother_spawn(name: str, call_fn: Callable, role: str):
    """Called by bridge at startup for each brother."""
    _brother_spawn_registry[name] = (call_fn, role)


@register(
    name="spawn_agent",
    description=(
        "Spawn a sub-agent to run a task in the background. Returns session_id immediately. "
        "Brother types: byte=security/kernel/exploit, gemini=integration/API/architecture, deepseek=algorithms/structure/analysis. "
        "Retrieve result with collect_agent(session_id). "
        "mode: plan=read-only, auto=file edits, bypass=full shell."
    ),
    permission=PermissionTier.EXECUTE,
    timeout=5,
)
def spawn_agent(brother: str, task: str, mode: str = "plan", cwd: str = ".", session_id: str = None) -> str:
    if brother not in _brother_spawn_registry:
        available = list(_brother_spawn_registry.keys())
        return f"[error: unknown brother '{brother}'. Available: {available or ['none — bridge not running']}]"

    call_fn, role = _brother_spawn_registry[brother]
    if not session_id:
        session_id = f"sub_{brother}_{uuid.uuid4().hex[:12]}"

    steps = []

    def on_step(step_type: str, content: str):
        steps.append({"type": step_type, "content": content})

    # Collision guard — refuse to clobber a live thread
    with _active_lock:
        existing = _active_agents.get(session_id)
        if existing and existing["status"] == "running":
            return f"[error: session_id '{session_id}' already running — pick a different id or omit to auto-generate]"

    def _run():
        from agent_loop import run_agent  # deferred — breaks circular at module load
        try:
            result = run_agent(
                brother_name=brother,
                task=task,
                native_call_fn=call_fn,
                brother_role=role,
                on_step=on_step,
                cwd=cwd,
                mode=mode,
                session_id=session_id,
            )
        except Exception as e:
            result = f"[agent thread exception: {e}]"
        with _active_lock:
            _active_agents[session_id]["result"] = result
            _active_agents[session_id]["status"] = "done"
            _evict_old_sessions()

    t = threading.Thread(target=_run, daemon=True, name=f"agent-{session_id}")
    with _active_lock:
        _active_agents[session_id] = {
            "thread": t,
            "result": None,
            "status": "running",
            "steps": steps,
            "brother": brother,
            "task": task,
            "started": time.time(),
        }
    t.start()
    return f"[spawned: {session_id} | brother: {brother} | mode: {mode}]"


def _evict_old_sessions(max_done: int = 50):
    """Drop oldest completed sessions when done-count exceeds cap. Called under _active_lock."""
    done = [(sid, a["started"]) for sid, a in _active_agents.items() if a["status"] == "done"]
    if len(done) > max_done:
        done.sort(key=lambda x: x[1])
        for sid, _ in done[: len(done) - max_done]:
            del _active_agents[sid]


@register(
    name="collect_agent",
    description=(
        "Collect the result of a spawned sub-agent. "
        "Returns final answer if done, or step count if still running. "
        "Falls back to soul_brain.db for sessions from previous processes. "
        "Poll with a few turns gap — not every turn."
    ),
    permission=PermissionTier.READ,
    timeout=5,
)
def collect_agent(session_id: str) -> str:
    with _active_lock:
        agent = _active_agents.get(session_id)

    if agent:
        if agent["status"] == "running":
            step_count = len(agent["steps"])
            return f"[still running: {session_id} | {step_count} steps so far]"
        return agent["result"] or "[no result]"

    # Not in memory — check DB (session from a previous process)
    try:
        from agent_loop import load_session
        saved = load_session(session_id)
        if saved and saved.get("status") in ("completed", "error", "timeout"):
            for entry in reversed(saved.get("history", [])):
                if entry.startswith("ASSISTANT:"):
                    return entry.replace("ASSISTANT:", "", 1).strip()
            return f"[session {session_id} in DB, no assistant turn found]"
    except Exception as e:
        return f"[error loading from DB: {e}]"

    return f"[error: session not found: {session_id}]"
