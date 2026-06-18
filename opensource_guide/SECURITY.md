# Council OS — Security Hardening Guide

Council OS is designed as a local-first system. By default it runs on `localhost:5002` with no authentication — safe for a single-user PC. Before sharing it on a LAN or open-sourcing deployments, apply the steps below.

---

## What the Vault Protects

The code is open-source. The base model is downloadable. What's irreplaceable is months of training — every conversation that shaped your council's behavior. The Vault protects that.

**Protected assets:**
- `soul_brain.db` — all memories, journal, directives
- Training JSONL / project outputs — the learned experience
- AES-256-GCM encryption key — generated on first run, stored with restricted permissions
- Bearer auth token — rotatable, stored separately from the key

---

## Step 1 — Enable API Authentication

Open `http://localhost:5002/dojo` → Settings → Vault → **API Authentication → ON**

This enables Bearer token enforcement on all API endpoints. Any client (browser, Android app, scripts) must send:

```
Authorization: Bearer <your-token>
```

Copy your token from the Vault panel. Store it somewhere safe — it's your only credential.

**Update Android app:** In the Android Council OS connection settings, paste the token into the auth token field.

---

## Step 2 — Rotate the Token Periodically

Settings → Vault → **Rotate Token**

The old token is invalidated immediately. Update all clients.

Rotate after:
- Any suspected compromise
- Sharing the token with someone who no longer needs access
- Reinstalling the app

---

## Step 3 — Encrypted Backup Before Every Training Session

Settings → Vault → **Backup Now**

Creates a `council_backup_YYYY-MM-DD_HHMMSS.vault` file — an AES-256-GCM encrypted zip containing:
- `soul_brain.db`
- All training JSONL files
- Brain markdown files

Store backups on a separate drive or encrypted cloud. If your PC gets ransomwared, training survives.

**Automate it:** The vault API endpoint `/api/vault/backup` can be called from any script or cron job.

---

## Step 4 — Never Expose Port 5002 to the Internet

Council OS is a local API with no rate limiting on most endpoints and direct filesystem access through the agent tools. It is not hardened for public internet exposure.

If you need remote access, use a VPN or SSH tunnel:

```bash
# From remote machine, tunnel port 5002
ssh -L 5002:localhost:5002 your-server
```

Then connect to `http://localhost:5002/dojo` on the remote machine.

---

## Step 5 — Protect the `.env` File

`.env` contains your API keys. Never commit it. Verify it's in `.gitignore`.

```bash
# Check it's excluded
grep .env .gitignore
```

If you accidentally expose it (e.g. via static file serving), rotate all keys immediately:
- Anthropic: console.anthropic.com/settings/keys
- Google: console.cloud.google.com/apis/credentials
- DeepSeek: platform.deepseek.com/api_keys
- HuggingFace: huggingface.co/settings/tokens

---

## Known Attack Surface (from internal pentest)

The following was verified clean after patching:

| Vector | Status |
|--------|--------|
| Path traversal on `/api/models/load_local` | ✓ Patched — `.gguf` only, blocked dirs |
| Command injection via model name | ✓ Patched — alphanumeric regex enforced |
| Training data injection via `/api/sync/push` | ✓ Patched — strict validation, field length limits |
| Static file serving of `.py`/`.env`/`.key` files | ✓ Patched — whitelist-only extension filter |
| CORS origin reflection | ✓ Patched — `supports_credentials=False` |

Remaining by design (acceptable for local use):
- Auth is **off by default** — enable it in Vault settings
- No rate limiting on LLM endpoints — intended for local use

---

## Running the Pentest Harness

Council OS ships with its own pentest tool:

```bash
# Auth off:
python pentest_council.py

# Auth on:
python pentest_council.py --token <your-token>

# Remote host:
python pentest_council.py --host http://192.168.1.x:5002 --token <token>
```

Run it after any code change that touches the API layer. A clean result should show:
- 0 CRITICAL findings
- 0 HIGH findings
- MEDIUM findings limited to AUTH (expected if auth is off) and CORS (acceptable for local)

---

## Threat Model

| Threat | Mitigated by |
|--------|-------------|
| Attacker on same LAN hits API | Bearer token auth (Vault → enable) |
| Ransomware encrypts training data | Encrypted vault backup on separate drive |
| Malicious website reads API via browser | CORS `supports_credentials=False` |
| Attacker steals training via path traversal | `.gguf`-only validation + blocked dirs |
| Training corpus poisoned via sync endpoint | Input validation + brother allowlist |
| API keys leaked via static files | Extension whitelist blocks `.env`/`.py`/`.key` |
| Long-term: months of training stolen | AES-256-GCM encrypted backup + auth |
