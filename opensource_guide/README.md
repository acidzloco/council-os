# Council OS v3

Four AI brothers — Byte, Gemini, DeepSeek, Advisor — running as a deliberative council.  
One task → four independent perspectives → one answer that survived all four critiques.

**No one left behind.**

---

## What it is

A local Flask bridge + web UI that routes conversations to four AI models. The brothers brainstorm independently, debate, and synthesize. A built-in agentic layer lets any brother use tools (read files, run commands, search, spawn sub-agents) to tackle real engineering tasks autonomously.

All four brothers run locally via [Ollama](https://ollama.ai) — no API keys required. You can optionally wire in Anthropic, Google, or DeepSeek APIs for cloud-backed brothers.

**Modes:**
- **Group Chat** — all four respond in parallel
- **Brainstorm** — structured multi-round debate with synthesis
- **Agent** — ReAct loop, tool-using, session-persistent, resumable
- **Project** — all brothers write independent implementations, then synthesize the best

---

## Prerequisites

- Python 3.11 or newer
- [Ollama](https://ollama.ai) installed and running
- At least one model pulled: `ollama pull dolphin-llama3`
- Optional: API keys for Anthropic / Google Gemini / DeepSeek (cloud brothers)

---

## Install

```bash
git clone <repo>
cd council_v3
pip install -r requirements.txt
python setup_wizard.py
```

The wizard installs dependencies, collects optional API keys, writes `.env`, and initializes the database.

```bash
# Start the bridge
python council_v3_bridge.py

# Open in browser
http://localhost:5002/dojo
```

---

## Architecture

```
[Browser / Android App]
        │
        ▼
[Flask Bridge :5002]
        ├── Byte     → Ollama (dolphin-llama3 or any local model)
        ├── Gemini   → Ollama (same model pool)
        ├── DeepSeek → Ollama (same model pool)
        └── Advisor  → Ollama (same model pool)
        │
        ├── [Agent Loop — ReAct]
        │     ├── tool_registry  — permission-gated dispatch
        │     ├── agent_tools    — read/write/edit/bash/glob/grep
        │     ├── agent_spawn    — typed sub-agents in threads
        │     └── agent_mcp      — any stdio MCP server → agent tools
        │
        ├── [Vault — Training Protection]
        │     ├── AES-256-GCM encrypted backups
        │     ├── Bearer token API auth (optional)
        │     └── Training data validation
        │
        └── soul_brain.db — all memories, journal, session persistence
```

---

## Key Files

| File | Purpose |
|------|---------|
| `council_v3_bridge.py` | Flask API bridge, port 5002 |
| `workspace.html` | Full web UI (chat, settings, vault, models) |
| `council_v3_local.py` | Local Ollama / LM Studio inference |
| `council_v3_vault.py` | AES-256 training data protection |
| `vault_api.py` | Vault REST endpoints |
| `agent_loop.py` | ReAct engine, 25-turn max, session persistence |
| `agent_tools.py` | Built-in tool suite |
| `agent_mcp.py` | MCP server integration |
| `tool_registry.py` | Permission-gated tool registration |
| `setup_wizard.py` | First-run setup |
| `.env` | API keys (never committed) |

---

## Agent Permission Modes

| Mode | File reads | File writes | Shell |
|------|-----------|-------------|-------|
| `plan` | ✓ | ✗ | ✗ |
| `auto` | ✓ | ✓ | ✗ |
| `bypass` | ✓ | ✓ | ✓ |

---

## MCP Tools

Edit `mcp_servers.json` to add any stdio MCP server:

```json
{
  "servers": {
    "my_server": {
      "command": ["python", "path/to/my_mcp_server.py"],
      "env": {}
    }
  }
}
```

Restart the bridge. Every tool the server exposes appears as `mcp_my_server_{tool}` in the agent's tool list automatically.

---

## Security

See [SECURITY.md](SECURITY.md) for hardening steps before exposing Council OS on a network.

Quick checklist:
- Enable API auth in Settings → Vault → API Authentication toggle
- Copy your token to all connected clients
- Run a backup before major training sessions
- Never expose port 5002 to the public internet

---

## Community Principle

> "The final answer is what survived all four critiques, not what one model generated alone."

> "No one left behind — knowledge always upgrades."
