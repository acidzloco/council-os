"""
Council Agent — MCP Integration Layer (v4 Roadmap Item 4)
Connects to stdio-based MCP servers, discovers tools via tools/list,
auto-registers them into the tool_registry as mcp_{server}_{tool}.
Add a server to mcp_servers.json — agents gain those tools on next restart.
"""
import json
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from tool_registry import _registry, ToolDef, PermissionTier

_CONFIG_PATH = Path(__file__).parent / "mcp_servers.json"

# Active clients — server name → MCPClient
_active_clients: Dict[str, "MCPClient"] = {}


class MCPClient:
    """Lightweight JSON-RPC 2.0 over stdio for MCP servers."""

    def __init__(self, name: str, command: List[str], env: Dict[str, str] = None):
        self.name = name
        merged = {**os.environ, **(env or {})}
        self._proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=merged,
        )
        self._lock = threading.Lock()
        self._id = 0

        # Drain stderr in background so it doesn't block stdout reads
        self._stderr_lines: List[str] = []
        threading.Thread(
            target=self._drain_stderr,
            daemon=True,
            name=f"mcp-stderr-{name}",
        ).start()

    def _drain_stderr(self):
        for line in self._proc.stderr:
            self._stderr_lines.append(line.rstrip())

    def _rpc(self, method: str, params: Any = None, timeout: int = 30) -> dict:
        """Send a JSON-RPC request, return parsed response. Thread-safe via lock."""
        with self._lock:
            self._id += 1
            msg: dict = {"jsonrpc": "2.0", "id": self._id, "method": method}
            if params is not None:
                msg["params"] = params
            self._proc.stdin.write(json.dumps(msg) + "\n")
            self._proc.stdin.flush()

            deadline = time.time() + timeout
            while True:
                if self._proc.poll() is not None:
                    raise RuntimeError(f"MCP server '{self.name}' exited (code {self._proc.returncode})")
                line = self._proc.stdout.readline()
                if line.strip():
                    return json.loads(line)
                if time.time() > deadline:
                    raise TimeoutError(f"MCP '{self.name}' timeout waiting for {method}")

    def _notify(self, method: str, params: Any = None):
        """Send a JSON-RPC notification (no id, no response expected)."""
        msg: dict = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self._proc.stdin.write(json.dumps(msg) + "\n")
        self._proc.stdin.flush()

    def initialize(self) -> bool:
        try:
            resp = self._rpc("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "council_os", "version": "4.0"},
            })
            if "result" in resp:
                self._notify("notifications/initialized")
                return True
            err = resp.get("error", {})
            print(f"[MCP:{self.name}] init error: {err.get('message', err)}")
        except Exception as e:
            print(f"[MCP:{self.name}] init failed: {e}")
        return False

    def list_tools(self) -> List[dict]:
        try:
            resp = self._rpc("tools/list")
            if "error" in resp:
                print(f"[MCP:{self.name}] tools/list error: {resp['error']}")
                return []
            return resp.get("result", {}).get("tools", [])
        except Exception as e:
            print(f"[MCP:{self.name}] tools/list failed: {e}")
            return []

    def call_tool(self, tool_name: str, arguments: dict, timeout: int = 60) -> str:
        try:
            resp = self._rpc("tools/call", {"name": tool_name, "arguments": arguments}, timeout=timeout)
            if "error" in resp:
                return f"[mcp error: {resp['error'].get('message', resp['error'])}]"
            content = resp.get("result", {}).get("content", [])
            parts = [c["text"] for c in content if c.get("type") == "text" and "text" in c]
            return "\n".join(parts) or "[no content]"
        except Exception as e:
            return f"[mcp call error: {e}]"

    def register_tools(self) -> int:
        """Discover tools and register each into the global tool registry."""
        _JSON_SCHEMA_TYPE_MAP = {
            "string": "str", "integer": "int", "boolean": "bool",
            "number": "float", "array": "list", "object": "dict",
        }
        tools = self.list_tools()
        count = 0
        for tool in tools:
            tname = tool.get("name", "")
            if not tname:
                continue
            reg_name = f"mcp_{self.name}_{tname}"
            desc = tool.get("description", "")
            schema = tool.get("inputSchema", {})
            props = schema.get("properties", {})
            required_list = schema.get("required", [])

            params: Dict[str, dict] = {}
            for pname, pinfo in props.items():
                raw = pinfo.get("type", "string")
                params[pname] = {
                    "type": _JSON_SCHEMA_TYPE_MAP.get(raw, "str"),
                    "required": pname in required_list,
                    "default": None if pname in required_list else pinfo.get("default"),
                }

            # Capture loop vars in closure correctly
            def _make_fn(client: "MCPClient", name: str, tout: int = 60):
                def fn(**kwargs) -> str:
                    return client.call_tool(name, kwargs, timeout=tout)
                fn.__name__ = f"mcp_{client.name}_{name}"
                return fn

            _registry[reg_name] = ToolDef(
                name=reg_name,
                description=f"[MCP:{self.name}] {desc}",
                params=params,
                permission=PermissionTier.EXECUTE,
                timeout=60,
                fn=_make_fn(self, tname),
            )
            count += 1
        return count

    def shutdown(self):
        try:
            self._notify("shutdown")
        except Exception:
            pass
        try:
            self._proc.terminate()
            self._proc.wait(timeout=3)
        except Exception:
            pass


def load_mcp_servers(config_path: Path = _CONFIG_PATH) -> int:
    """
    Read mcp_servers.json, start each server, initialize, register tools.
    Returns total tools registered across all servers.
    Called by the bridge at startup after BROTHERS dict is set up.
    """
    if not config_path.exists():
        return 0

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[MCP] config parse error: {e}")
        return 0

    total = 0
    for name, spec in config.get("servers", {}).items():
        command = spec.get("command", [])
        env = spec.get("env", {})
        if not command:
            print(f"[MCP:{name}] no command in config — skipped")
            continue

        client = MCPClient(name, command, env)
        if not client.initialize():
            client.shutdown()
            continue

        count = client.register_tools()
        _active_clients[name] = client
        print(f"[MCP:{name}] {count} tools registered")
        total += count

    return total


def shutdown_all():
    """Cleanly terminate all active MCP server subprocesses."""
    for client in _active_clients.values():
        client.shutdown()
    _active_clients.clear()
