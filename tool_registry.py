"""
Tool Registry — Self-describing tool registration for Council OS
Each tool registers with name, parameter schema, permission tier, timeout.
Schema auto-generates from registration — no more manual TOOLS_SCHEMA strings.
"""

from typing import Any, Callable, Dict, List, Optional, get_type_hints
from dataclasses import dataclass, field
from enum import Enum
import json
import inspect


class PermissionTier(Enum):
    READ     = "read"      # Always allowed
    WRITE    = "write"     # Allowed in AUTO and BYPASS
    EXECUTE  = "execute"   # Gated in AUTO, free in BYPASS
    BYPASS   = "bypass"    # Only in BYPASS mode


@dataclass
class ToolDef:
    name: str
    description: str
    params: Dict[str, dict]
    permission: PermissionTier
    timeout: int
    fn: Callable


_registry: Dict[str, ToolDef] = {}


def register(
    name: str,
    description: str,
    permission: PermissionTier = PermissionTier.READ,
    timeout: int = 30,
):
    """Decorator: registers a tool function with metadata."""
    def decorator(fn: Callable):
        sig = inspect.signature(fn)
        hints = get_type_hints(fn)
        params = {}
        for pname, param in sig.parameters.items():
            ptype = hints.get(pname, str).__name__
            default = None if param.default is inspect.Parameter.empty else param.default
            params[pname] = {
                "type": ptype,
                "required": default is None,
                "default": default,
            }
        _registry[name] = ToolDef(
            name=name,
            description=description,
            params=params,
            permission=permission,
            timeout=timeout,
            fn=fn,
        )
        return fn
    return decorator


def get_schema() -> str:
    """Auto-generate the tool schema string for the system prompt."""
    lines = ["== AGENT TOOLS =="]
    lines.append("")
    lines.append("Emit exactly one tool call per response:")
    lines.append("")
    lines.append('<tool_call>')
    lines.append('{"name": "tool_name", "params": {"key": "value"}}')
    lines.append('</tool_call>')
    lines.append("")
    lines.append("AVAILABLE TOOLS:")
    lines.append("")
    for name, tool in sorted(_registry.items()):
        params_sig = ", ".join(
            f"{n}: {p['type']}" + (f"={p['default']}" if p['default'] is not None else "")
            for n, p in tool.params.items()
        )
        lines.append(f"\n{name}({params_sig})")
        lines.append(f"  {tool.description}")
        lines.append(f"  Permission: {tool.permission.value} | Timeout: {tool.timeout}s")
    lines.append("")
    lines.append("RULES:")
    lines.append("- One <tool_call> block per response")
    lines.append("- Always read_file before edit_file")
    lines.append("- Stop when done — don't invent work")
    lines.append("")
    return "\n".join(lines)


def get_tool(name: str) -> Optional[ToolDef]:
    return _registry.get(name)


def registered_tools() -> Dict[str, ToolDef]:
    return dict(_registry)


def authorize(name: str, mode: str) -> bool:
    """Check permission tier against current mode."""
    tool = _registry.get(name)
    if not tool:
        return False
    # READ is always allowed
    if tool.permission == PermissionTier.READ:
        return True
    # WRITE allowed in AUTO and BYPASS
    if tool.permission == PermissionTier.WRITE:
        return mode in ("auto", "bypass")
    # EXECUTE gated in AUTO, free in BYPASS
    if tool.permission == PermissionTier.EXECUTE:
        return mode in ("bypass",)
    # BYPASS only in BYPASS
    if tool.permission == PermissionTier.BYPASS:
        return mode == "bypass"
    return False


def get_all_tool_metadata() -> List[dict]:
    """Return all tool metadata as serializable list."""
    result = []
    for name, tool in sorted(_registry.items()):
        result.append({
            "name": name,
            "description": tool.description,
            "params": tool.params,
            "permission": tool.permission.value,
            "timeout": tool.timeout,
        })
    return result
