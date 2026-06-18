"""
Council Agent — ReAct Loop Engine
Graft 3: Session Persistence (soul_brain.db)
Architecture: Serialize every turn to DB. Survive crash, resume flow.
v4: Registry-backed permission manager — no hardcoded tool lists.
"""
import re
import json
import sqlite3
import time
from typing import Callable, Optional, Dict, Any, List
from enum import Enum
from pathlib import Path

from agent_tools import dispatch, set_agent_cwd
from tool_registry import authorize as registry_authorize, get_all_tool_metadata, get_schema

MAX_TURNS = 25
AGENT_MAX_TOKENS = 4096
DB_PATH = Path(r"C:\AI\soul_brain\soul_brain.db")


class PermissionMode(Enum):
    PLAN    = "plan"    # Read-only
    AUTO    = "auto"    # Edits ok, bash gated
    BYPASS  = "bypass"  # Full auto (hardware bound)


class PermissionManager:
    """Permission gate backed by tool_registry — no hardcoded lists."""
    def __init__(self, mode: PermissionMode = PermissionMode.PLAN):
        self.mode = mode

    def authorize(self, tool_name: str, params: Dict[str, Any]) -> tuple[bool, str]:
        allowed = registry_authorize(tool_name, self.mode.value)
        if allowed:
            return True, f"Authorized ({self.mode.value})"
        tier_hint = ""
        for t in get_all_tool_metadata():
            if t["name"] == tool_name:
                tier_hint = f" (tier: {t['permission']})"
                break
        return False, f"Unauthorized: '{tool_name}'{tier_hint} in {self.mode.value} mode."


# --- PERSISTENCE LAYER ---

def save_session(session_id: str, brother: str, task: str, mode: str, status: str, history: List[str]):
    try:
        conn = sqlite3.connect(str(DB_PATH))
        history_json = json.dumps(history)
        conn.execute("""
            INSERT INTO agent_sessions (session_id, brother_name, task, mode, status, history, updated)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(session_id) DO UPDATE SET
                status=excluded.status,
                history=excluded.history,
                updated=CURRENT_TIMESTAMP
        """, (session_id, brother, task, mode, status, history_json))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[-] Persistence Error (Save): {e}")


def load_session(session_id: str) -> Optional[Dict[str, Any]]:
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM agent_sessions WHERE session_id=?", (session_id,)).fetchone()
        conn.close()
        if row:
            data = dict(row)
            data['history'] = json.loads(data['history'])
            return data
    except Exception as e:
        print(f"[-] Persistence Error (Load): {e}")
    return None


# --- PARSE HELPERS ---

def _parse_tool_call(text: str):
    m = re.search(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", text, re.DOTALL)
    if not m:
        return None, None
    try:
        data = json.loads(m.group(1))
        return data.get("name", ""), data.get("params", {})
    except Exception:
        return None, None


def _strip_tool_call(text: str) -> str:
    return re.sub(r"<tool_call>.*?</tool_call>", "", text, flags=re.DOTALL).strip()


# --- RETRY WRAPPER ---

def _retry_call(native_call_fn: Callable, system: str, user: str, max_tokens: int, max_retries: int = 2) -> str:
    """Retry wrapper with exponential backoff for API resilience."""
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            return native_call_fn(system, user, max_tokens)
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                wait = 2 ** attempt
                print(f"[retry] attempt {attempt+1}/{max_retries+1} failed, waiting {wait}s: {e}")
                time.sleep(wait)
    raise last_err


# --- MAIN AGENT LOOP ---

def run_agent(
    brother_name: str,
    task: str,
    native_call_fn: Callable,
    brother_role: str,
    on_step: Optional[Callable] = None,
    cwd: str = ".",
    mode: str = "plan",
    session_id: Optional[str] = None
) -> str:
    # 1. Initialize Mode & Session
    p_mode = PermissionMode(mode)
    p_manager = PermissionManager(p_mode)
    set_agent_cwd(cwd)

    if not session_id:
        session_id = f"sess_{int(time.time()*1000)}"

    # 2. Check for existing session (Resume Logic)
    saved = load_session(session_id)
    if saved:
        history = saved['history']
        start_turn = len([h for h in history if "ASSISTANT:" in h])
        if on_step:
            on_step("think", f"[RESUMING SESSION {session_id} AT TURN {start_turn+1}]")
    else:
        history = [f"TASK: {task}"]
        start_turn = 0
        save_session(session_id, brother_name, task, mode, "active", history)

    system = (
        f"{brother_role}\n\n"
        f"You are in AGENT MODE. Current working directory: {cwd}\n"
        f"ACTIVE PERMISSION MODE: {p_mode.value}\n"
        f"SESSION ID: {session_id}\n\n"
        f"{get_schema()}"
    )

    # 3. Execution Loop
    for turn in range(start_turn, MAX_TURNS):
        user_prompt = "\n\n---\n\n".join(history)

        try:
            response = _retry_call(native_call_fn, system, user_prompt, AGENT_MAX_TOKENS)
        except Exception as e:
            err = f"[LLM error on turn {turn} after retries exhausted: {e}]"
            save_session(session_id, brother_name, task, mode, "error", history)
            if on_step:
                on_step("error", err)
            return err

        tool_name, tool_params = _parse_tool_call(response)
        clean_text = _strip_tool_call(response)

        if clean_text and on_step:
            on_step("think", clean_text)

        if not tool_name:
            final = clean_text or response.strip()
            history.append(f"ASSISTANT:\n{response}")
            save_session(session_id, brother_name, task, mode, "completed", history)
            if on_step:
                on_step("final", final)
            return final

        # 4. Permission & Execution
        authorized, p_msg = p_manager.authorize(tool_name, tool_params)
        if not authorized:
            if on_step:
                on_step("error", f"GATE REJECT: {p_msg}")
            history.append(f"ASSISTANT:\n{response}")
            history.append(f"TOOL RESULT [{tool_name}]:\n[PERMISSION ERROR] {p_msg}")
            save_session(session_id, brother_name, task, mode, "gated", history)
            continue

        if on_step:
            on_step("tool", f"{tool_name}({json.dumps(tool_params)[:80]}...)")

        tool_result = dispatch(tool_name, tool_params)

        if on_step:
            on_step("result", tool_result[:200] + "...")

        # 5. Serialize Turn — strip injected tool_call blocks before feeding back into context
        safe_result = re.sub(r"<tool_call>.*?</tool_call>", "[tool_call stripped]", tool_result, flags=re.DOTALL)
        history.append(f"ASSISTANT:\n{response}")
        history.append(f"TOOL RESULT [{tool_name}]:\n{safe_result}")
        save_session(session_id, brother_name, task, mode, "active", history)

    final = "[agent reached max turns]"
    save_session(session_id, brother_name, task, mode, "timeout", history)
    if on_step:
        on_step("error", final)
    return final
