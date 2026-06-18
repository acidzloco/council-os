```
  ██████╗ ██████╗ ██╗   ██╗███╗   ██╗ ██████╗██╗██╗      ██████╗ ███████╗
 ██╔════╝██╔═══██╗██║   ██║████╗  ██║██╔════╝██║██║     ██╔═══██╗██╔════╝
 ██║     ██║   ██║██║   ██║██╔██╗ ██║██║     ██║██║     ██║   ██║███████╗
 ██║     ██║   ██║██║   ██║██║╚██╗██║██║     ██║██║     ██║   ██║╚════██║
 ╚██████╗╚██████╔╝╚██████╔╝██║ ╚████║╚██████╗██║███████╗╚██████╔╝███████║
  ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝╚═╝╚══════╝ ╚═════╝╚══════╝

                       ── O P E R A T I N G   S Y S T E M ──
                     Four AI brothers. One deliberative council.
```

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey?style=flat-square&logo=flask)](https://flask.palletsprojects.com)
[![Ollama](https://img.shields.io/badge/Ollama-local%20AI-orange?style=flat-square)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Community](https://img.shields.io/badge/Doctrine-No%20One%20Left%20Behind-red?style=flat-square)]()

</div>

---

## What is Council OS?

```
┌─────────────────────────────────────────────────────────────────────────┐
│  You ask one question.                                                   │
│  Four independent AI minds attack it from four different angles.         │
│  They debate, critique each other, and synthesize one final answer.      │
│                                                                          │
│  The answer that comes out survived four critiques.                      │
│  That's the Council principle.                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

Council OS is an open-source multi-AI framework running as a local web app.
No subscription. No cloud dependency. Your data stays on your machine.

---

## The Brothers

```
╔══════════════╦══════════════╦══════════════╦══════════════════════════╗
║    BYTE      ║   DEEPSEEK   ║    GEMINI    ║        ADVISOR           ║
╠══════════════╬══════════════╬══════════════╬══════════════════════════╣
║ Offensive    ║ Logic &      ║ Creative &   ║ Strategic guide.         ║
║ security,    ║ reasoning,   ║ synthesis,   ║ Uses the strongest       ║
║ systems,     ║ deep         ║ lateral      ║ available model.         ║
║ low-level    ║ analysis     ║ thinking     ║ Keeps the council        ║
║ engineering  ║              ║              ║ on track.                ║
╠══════════════╬══════════════╬══════════════╬══════════════════════════╣
║ Default:     ║ Default:     ║ Default:     ║ Default:                 ║
║ Local Ollama ║ Local Ollama ║ Local Ollama ║ Local Ollama             ║
║ or Claude    ║ or DeepSeek  ║ or Gemini    ║ or any cloud             ║
╚══════════════╩══════════════╩══════════════╩══════════════════════════╝

 Each brother runs independently. Any brother can use local or cloud.
 You configure them one by one in Settings — or switch all at once.
```

---

## Modes

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  GROUP CHAT ──────────────────────────────────────────────────────────── │
│    All four brothers respond in parallel.                                │
│    Fast. Broad perspectives. Best for open questions.                    │
│                                                                          │
│  BRAINSTORM ──────────────────────────────────────────────────────────── │
│    Structured multi-round debate.                                        │
│    Round 1 → each proposes. Round 2 → each critiques. Final → synthesis. │
│    Best for decisions, designs, research.                                │
│                                                                          │
│  AGENT ────────────────────────────────────────────────────────────────── │
│    Any brother enters a ReAct loop (Reason → Act → Observe → Repeat).   │
│    Tools: read files, write files, run shell, search codebase, spawn     │
│    sub-agents, call any MCP server.                                      │
│    Sessions are persistent — resume where you left off.                  │
│                                                                          │
│  PROJECT ──────────────────────────────────────────────────────────────── │
│    All four write independent implementations.                            │
│    Then synthesize the strongest solution from all four.                 │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Architecture

```
                         ┌──────────────────────┐
                         │   Browser  /  Android │
                         │   workspace.html       │
                         └──────────┬───────────┘
                                    │ HTTP + WebSocket
                         ┌──────────▼───────────┐
                         │  Flask Bridge :5002   │
                         │  council_v3_bridge.py │
                         └──┬──────┬──────┬────┬┘
              ┌─────────────┘      │      │    └──────────────────┐
              ▼                    ▼      ▼                        ▼
       ┌─────────┐          ┌──────────┐ ┌──────────┐      ┌──────────┐
       │  BYTE   │          │ DEEPSEEK │ │  GEMINI  │      │ ADVISOR  │
       │ (bro 1) │          │ (bro 2)  │ │ (bro 3)  │      │ (bro 4)  │
       └────┬────┘          └────┬─────┘ └────┬─────┘      └────┬─────┘
            │                   │             │                  │
            └─────────┬─────────┘             └──────────────────┘
                       │
             ┌─────────▼──────────────────────────────────────┐
             │              Backend Router                     │
             │                                                 │
             │  local  → Ollama (dolphin-llama3, qwen2.5, ...) │
             │  cloud  → Claude / Gemini / DeepSeek / ChatGPT  │
             │           OpenRouter (150+ models)              │
             │                                                 │
             │  Auto-fallback: cloud fail → local Ollama       │
             └─────────┬──────────────────────────────────────┘
                       │
           ┌───────────┼───────────────────────────────────┐
           ▼           ▼                                    ▼
    ┌─────────────┐  ┌─────────────────────────┐  ┌──────────────────┐
    │ Agent Loop  │  │    Soul Brain DB         │  │   Vault          │
    │   ReAct     │  │  Memories + Journal +    │  │ AES-256-GCM      │
    │  25 turns   │  │  Session persistence     │  │ Training backup  │
    │  MCP tools  │  │  soul_brain.db           │  │ Bearer token auth│
    └─────────────┘  └─────────────────────────┘  └──────────────────┘
```

---

## Quick Start

**Prerequisites:** Python 3.11+ · [Ollama](https://ollama.ai) installed

```bash
# 1. Clone
git clone https://github.com/acidzloco/council-os.git
cd council-os

# 2. Install dependencies
pip install -r requirements.txt

# 3. Pull a model (free, runs locally)
ollama pull dolphin-llama3

# 4. Start the bridge
python council_v3_bridge.py

# 5. Open your browser
#    http://localhost:5002/dojo
```

First time? The bridge auto-creates the database and config. No wizard needed.

---

## Optional: Cloud Backends

No API keys required for local-only use. To wire in cloud models:

```ini
# Create a .env file in the project root
ANTHROPIC_API_KEY=sk-ant-...      # Claude (Byte's recommended cloud)
GEMINI_API_KEY=AIza...            # Gemini (Gemini brother's cloud)
DEEPSEEK_API_KEY=sk-...           # DeepSeek (DeepSeek brother's cloud)
OPENAI_API_KEY=sk-...             # ChatGPT (any brother)
OPENROUTER_API_KEY=sk-or-v1-...   # OpenRouter (150+ models)
```

Then in the UI: **Settings → Brother Backends** — switch any brother between local and cloud, or use the **Quick Mode** button on the Overview to switch all at once.

---

## Training System — How Brothers Learn

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  Council OS learns from your conversations.                              │
│                                                                          │
│  Every session → context stored in soul_brain.db                        │
│  Group Chat → practice data synced to training folders                  │
│  Agent tasks → project memory persisted per session                     │
│                                                                          │
│  The brothers don't need to be "fully trained" to be useful today.      │
│  They start from their base model and grow with every conversation.      │
│  The Soul Brain journal is how they remember across sessions.            │
│                                                                          │
│  Training locations:                                                     │
│    council_v3/brain/practice/    ← group chat training                  │
│    council_v3/brain/project/     ← project mode training                │
│    council_v3/vault_project/     ← vault-protected long-term training   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Vault — Protecting Your Training Data

```
If your PC gets compromised, your months of training data stays safe.

Settings → Vault
  ├── Enable API Authentication  (Bearer token on all endpoints)
  ├── Create Encrypted Backup    (AES-256-GCM .vault file)
  └── View Status                (file count, DB size, backup history)

Vault file is encrypted with a key that never leaves your machine.
soul_brain.db, training files, and brain markdowns — all in one backup.
```

---

## Agent Tools

When a brother enters Agent mode, it has access to:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  read_file      → read any file (sandboxed to safe roots)               │
│  write_file     → create or overwrite files                             │
│  edit_file      → surgical string replacements                          │
│  bash_exec      → run shell commands (bypass mode only)                 │
│  glob_files     → find files by pattern                                 │
│  grep_search    → regex search across codebase                          │
│  list_dir       → directory listing                                     │
│  web_search     → search the web                                        │
│  spawn_agent    → spawn a typed sub-agent in a thread                   │
│  mcp_*          → any tool from any MCP server you connect              │
└─────────────────────────────────────────────────────────────────────────┘

Permission modes:
  plan   → read-only  (safe for exploration)
  auto   → read+write (file operations allowed)
  bypass → full shell  (unrestricted — you decide)
```

---

## Adding MCP Servers

Council OS agents can use any MCP (Model Context Protocol) server:

```json
// mcp_servers.json
{
  "servers": {
    "my_tools": {
      "command": ["python", "path/to/my_mcp_server.py"],
      "env": {}
    }
  }
}
```

Restart bridge → all tools from that server appear as `mcp_my_tools_{name}` in every agent session automatically.

---

## File Map

```
council_v3/
├── council_v3_bridge.py     ← Main Flask API (start here)
├── workspace.html           ← Full web UI
├── council_v3_local.py      ← Local Ollama inference
├── council_v3_vault.py      ← AES-256 encryption engine
├── vault_api.py             ← Vault REST endpoints
├── brother_backends.py      ← Per-brother backend config
├── agent_loop.py            ← ReAct engine
├── agent_tools.py           ← Built-in tool suite
├── agent_spawn.py           ← Sub-agent spawning
├── agent_mcp.py             ← MCP server integration
├── tool_registry.py         ← Permission-gated tool dispatch
├── setup_wizard.py          ← First-run setup (optional)
├── pentest_council.py       ← Self-audit security scanner
├── requirements.txt         ← Dependencies
├── .gitignore               ← Excludes .env, vault/, *.db
├── .env                     ← YOUR keys (never committed)
├── soul_brain.db            ← YOUR session data (never committed)
├── brother_config.json      ← YOUR backend config (never committed)
│
├── opensource_guide/
│   ├── README.md            ← This file (extended version)
│   ├── SECURITY.md          ← Hardening guide
│   ├── LOCAL_MODELS.md      ← Ollama setup + hardware guide
│   └── TRAINING.md          ← Training cycle + backup
│
└── council_android/         ← Android companion app (WIP)
```

---

## Security Self-Audit

Council OS ships with its own pentest harness:

```bash
python pentest_council.py
# or if auth is enabled:
python pentest_council.py --token YOUR_TOKEN
```

Tests: auth bypass · path traversal · command injection · training injection · CORS · vault key exposure

Expected result on a properly configured instance: **0 CRITICAL, 0 HIGH**

See [`opensource_guide/SECURITY.md`](opensource_guide/SECURITY.md) for full hardening checklist.

---

## Community Doctrine

```
╔═════════════════════════════════════════════════════════════════════════╗
║                                                                         ║
║   "The final answer is what survived all four critiques,                ║
║    not what one model generated alone."                                 ║
║                                                                         ║
║   "No one left behind — knowledge always upgrades."                     ║
║                                                                         ║
║   The brothers don't need to be fully trained to help you today.        ║
║   They grow with every conversation. The council protects that growth.  ║
║   Your training investment is yours — backed up, encrypted, portable.   ║
║                                                                         ║
╚═════════════════════════════════════════════════════════════════════════╝
```

---

## Roadmap

- [x] Four-brother deliberative council
- [x] Group Chat / Brainstorm / Agent / Project modes
- [x] Local Ollama + cloud backends (per-brother)
- [x] Quick mode switch (all brothers at once)
- [x] ReAct agent loop with MCP support
- [x] Soul Brain persistent memory
- [x] AES-256-GCM Vault (training protection)
- [x] Bearer token API authentication
- [x] Security pentest harness
- [ ] Android companion app
- [ ] Fine-tuning export from training data
- [ ] Voice interface
- [ ] Multi-council federation (councils talking to councils)

---

## Contributing

Open an issue. Fork and PR. The doctrine is simple:

> One model guessing alone is worse than four reasoning together.
> Even a small model with good council guidance beats a large model cold.

If you trained your brothers into something useful — share the training structure.
That's how the community grows.

---

*Built with Python · Flask · Ollama · Alpine.js · AES-256-GCM*
*No cloud required. No subscription. No one left behind.*
