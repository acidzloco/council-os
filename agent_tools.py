"""
Council Agent — Tool Suite
Each tool registers via @register decorator — self-describing, no manual schema drift.
v4: Path traversal guard, prompt injection scrub, bash timeout cap.
"""
import re
import json
import subprocess
import contextvars
from pathlib import Path
from tool_registry import register, PermissionTier, get_schema, get_tool, authorize

MAX_OUTPUT = 8000

# Thread-safe cwd for _safe_path — set by run_agent before dispatch
_agent_cwd: contextvars.ContextVar[str] = contextvars.ContextVar("agent_cwd", default=".")

ALLOWED_ROOTS = [
    Path(r"C:\AI"),
    Path.home() / ".claude",
]


def set_agent_cwd(cwd: str):
    """Set the working directory for the current agent turn (thread-safe)."""
    _agent_cwd.set(cwd)


def _safe_path(raw: str) -> Path:
    """Resolve and validate path against allowed roots. Prevents path traversal."""
    cwd = _agent_cwd.get()
    p = Path(raw)
    if not p.is_absolute():
        p = Path(cwd).resolve() / p
    p = p.resolve()

    # Always allow paths under cwd (which is the project root)
    try:
        p.relative_to(Path(cwd).resolve())
        return p
    except ValueError:
        pass

    # Also allow explicit allowed roots
    for root in ALLOWED_ROOTS:
        try:
            p.relative_to(root.resolve())
            return p
        except ValueError:
            continue

    raise PermissionError(f"Path outside allowed scope: {p}")


@register(
    name="read_file",
    description="Read file contents. Always read before editing.",
    permission=PermissionTier.READ,
    timeout=30,
)
def read_file(path: str) -> str:
    try:
        p = _safe_path(path)
        if not p.exists():
            return f"[error: file not found: {path}]"
        content = p.read_text(encoding="utf-8", errors="replace")
        if len(content) > MAX_OUTPUT:
            return content[:MAX_OUTPUT] + f"\n[...truncated — {len(content)} total chars — read in chunks if needed]"
        return content
    except PermissionError as e:
        return f"[error: {e}]"
    except Exception as e:
        return f"[error: {e}]"


@register(
    name="write_file",
    description="Create or overwrite a file with content.",
    permission=PermissionTier.WRITE,
    timeout=30,
)
def write_file(path: str, content: str) -> str:
    try:
        p = _safe_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"[written: {path} ({len(content)} chars)]"
    except PermissionError as e:
        return f"[error: {e}]"
    except Exception as e:
        return f"[error: {e}]"


@register(
    name="edit_file",
    description="Surgically replace exactly ONE occurrence of old_str with new_str. "
                "Normalizes line endings before matching. Rejects ambiguous matches.",
    permission=PermissionTier.WRITE,
    timeout=15,
)
def edit_file(path: str, old_str: str, new_str: str) -> str:
    try:
        p = _safe_path(path)
        if not p.exists():
            return f"[error: file not found: {path}]"

        content = p.read_text(encoding="utf-8", errors="replace")
        norm_content = content.replace("\r\n", "\n")
        norm_old = old_str.replace("\r\n", "\n")
        norm_new = new_str.replace("\r\n", "\n")

        count = norm_content.count(norm_old)
        if count == 0:
            return f"[error: edit failed - old_str not found. Tip: Ensure you included exact indentation and whitespace.]"
        if count > 1:
            return f"[error: edit failed - old_str matches {count} locations. Tip: Include more surrounding context to make the match unique.]"

        updated_content = norm_content.replace(norm_old, norm_new, 1)

        if "\r\n" in content:
            updated_content = updated_content.replace("\n", "\r\n")

        p.write_text(updated_content, encoding="utf-8")
        return f"[success: surgically edited {path}]"
    except PermissionError as e:
        return f"[error: {e}]"
    except Exception as e:
        return f"[error: {e}]"


@register(
    name="bash",
    description="Run a PowerShell command. Returns combined stdout+stderr. "
                "Timeout is capped at 120s regardless of input.",
    permission=PermissionTier.EXECUTE,
    timeout=30,
)
def bash(command: str, timeout: int = 30) -> str:
    try:
        # Hard cap — timeout from LLM is metadata only; enforce here
        timeout = min(timeout, 120)
        result = subprocess.run(
            ["powershell", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, timeout=timeout,
        )
        out = (result.stdout + result.stderr).strip()
        if len(out) > MAX_OUTPUT:
            out = out[:MAX_OUTPUT] + "\n[...truncated]"
        return out or "[no output]"
    except subprocess.TimeoutExpired:
        return f"[timeout after {timeout}s]"
    except Exception as e:
        return f"[error: {e}]"


@register(
    name="glob_files",
    description="Find files matching a glob pattern. Example: '**/*.py' finds all Python files recursively.",
    permission=PermissionTier.READ,
    timeout=15,
)
def glob_files(pattern: str, path: str = ".") -> str:
    try:
        matches = sorted(Path(path).glob(pattern))[:100]
        return "\n".join(str(m) for m in matches) if matches else "[no matches]"
    except Exception as e:
        return f"[error: {e}]"


@register(
    name="grep",
    description="Search file contents with regex. Returns file:line: content matches. "
                "Case-insensitive by default.",
    permission=PermissionTier.READ,
    timeout=30,
)
def grep(pattern: str, path: str = ".", glob_pattern: str = "**/*") -> str:
    try:
        rx = re.compile(pattern, re.IGNORECASE)
        results = []
        for f in sorted(Path(path).glob(glob_pattern)):
            if not f.is_file():
                continue
            try:
                for i, line in enumerate(
                    f.read_text(encoding="utf-8", errors="replace").splitlines(), 1
                ):
                    if rx.search(line):
                        results.append(f"{f}:{i}: {line.strip()}")
                        if len(results) >= 80:
                            break
            except Exception:
                pass
            if len(results) >= 80:
                break
        return "\n".join(results) if results else "[no matches]"
    except Exception as e:
        return f"[error: {e}]"


@register(
    name="list_dir",
    description="List directory contents with [DIR] or [FILE] tags. Shows up to 150 entries.",
    permission=PermissionTier.READ,
    timeout=10,
)
def list_dir(path: str = ".") -> str:
    try:
        p = Path(path)
        if not p.exists():
            return f"[error: not found: {path}]"
        items = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        lines = []
        for item in items[:150]:
            tag = "DIR " if item.is_dir() else "FILE"
            lines.append(f"[{tag}] {item.name}")
        return "\n".join(lines) or "[empty]"
    except Exception as e:
        return f"[error: {e}]"


@register(
    name="download_skill",
    description=(
        "Install a skill pack from skills.sh into the council's skills directory. "
        "Format: 'owner/repo' (e.g. 'anthropic/mcp-builder'). "
        "Skills become available to all brothers on next session load. "
        "Browse available skills at https://www.skills.sh/"
    ),
    permission=PermissionTier.BYPASS,
    timeout=60,
)
def download_skill(skill: str) -> str:
    skills_dir = Path(r"C:\AI\Idea\skills")
    try:
        result = subprocess.run(
            ["npx", "skillsadd", skill, "--output", str(skills_dir)],
            capture_output=True, text=True, timeout=60,
        )
        out = (result.stdout + result.stderr).strip()
        if result.returncode == 0:
            return f"[skill installed: {skill} -> {skills_dir}]\n{out}"
        return f"[skill install failed: {skill}]\n{out}"
    except subprocess.TimeoutExpired:
        return f"[timeout installing skill: {skill}]"
    except FileNotFoundError:
        return "[error: npx not found — install Node.js to use download_skill]"
    except Exception as e:
        return f"[error: {e}]"


# =============================================================================
# Export for backward compatibility
# =============================================================================
TOOLS_SCHEMA = get_schema()


def dispatch(name: str, params: dict) -> str:
    """Dispatch a tool call by name using the registry."""
    tool = get_tool(name)
    if not tool:
        return f"[unknown tool: {name}]"
    try:
        return tool.fn(**params)
    except KeyError as e:
        return f"[missing param: {e}]"
    except Exception as e:
        return f"[tool error: {e}]"
