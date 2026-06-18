# Local Models Setup — Zero API Keys

**Philosophy:** Leftover models + local inference = infinite council members, no API costs.

---

## Quick Start (5 minutes)

### 1. Install Ollama (FREE)
```bash
# Download from https://ollama.ai
# Ollama handles local GGUF inference automatically
```

### 2. Pull Models (automatic download + format)
```bash
# In PowerShell/CMD:
ollama pull mistral          # ~4GB (fastest, good quality)
ollama pull neural-chat      # ~4GB (conversation-optimized)
ollama pull llama2           # ~3GB (classic, stable)
ollama pull phi              # ~2GB (tiny, CPU-friendly)
ollama pull dolphin-mixtral  # ~26GB (best quality, slow)

# Verify:
ollama list
```

### 3. Register Each Model in Dojo Registry
1. Open `http://localhost:5002/dojo`
2. Click **REGISTRY** tab
3. For each model:
   - **Name:** `mistral` (or your choice)
   - **Source:** `ollama:mistral` (MUST match `ollama list` output)
   - **Role:** `general` (or `security`, `teaching`, etc.)
   - Click **ADOPT MODEL**

### 4. Use in Council Chat
```
Open CHAT tab → Type: "@mistral explain AI"
→ Model responds instantly (runs local)
```

---

## Architecture: How It Works

```
┌─ User sends message to @mistral in CHAT ─┐
│                                            │
├─ /council/quickchat endpoint             │
│  └─ Routes to: name="mistral"            │
│                                            │
├─ _native_call("mistral", system, user)   │
│  └─ Check: Is "mistral" in registered?   │
│     └─ YES: Call Ollama API locally      │
│     └─ NO: Check BROTHERS dict (API)     │
│                                            │
├─ Ollama runs inference on GPU/CPU        │
│  (NO API key, NO internet needed)        │
│                                            │
├─ Response sent back to user             │
│  └─ Saved to soul_brain.db              │
│                                            │
└─ Model learns from feedback next session └─┘
```

---

## Modify Bridge to Support Any Ollama Model

**File:** `C:\AI\council_v3\council_v3_bridge.py`

**Find line ~324, the `_native_call()` function:**

Replace with this:

```python
def _native_call(name: str, system: str, user: str, max_tokens: int) -> str:
    """Dispatch to native API.
    Priority: Registered local model → 4 brothers (API) → Unknown
    """
    
    # Check if this is a registered local Ollama model
    registered_model = _get_registered_model(name)
    if registered_model and registered_model.get("source", "").startswith("ollama:"):
        try:
            ollama_model = registered_model["source"].replace("ollama:", "")
            return _call_ollama(ollama_model, system + "\n" + user, max_tokens)
        except Exception as e:
            print(f"[-] Local Ollama '{name}' failed: {e}", flush=True)
    
    # Fallback to 4 brothers (existing logic)
    if local_available() and name in ("byte", "gemini", "advisor"):
        try:
            return call_local(system, user, max_tokens)
        except Exception as e:
            print(f"[-] Local inference failed for {name}: {e}", flush=True)
    
    # Route to brothers
    try:
        if name == "byte":
            prefix = _DEEPSEEK_PERSONA_PREFIX["byte"]
            return _call_deepseek(prefix + system, user, max_tokens)
        elif name == "gemini":
            return _call_gemini(system, user, max_tokens)
        elif name == "deepseek":
            return _call_deepseek(system, user, max_tokens)
        elif name == "advisor":
            prefix = _DEEPSEEK_PERSONA_PREFIX["advisor"]
            return _call_deepseek(prefix + system, user, max_tokens)
    except Exception as e:
        print(f"[-] {name} primary failed: {e}", flush=True)
        # ... existing fallback logic ...
    
    return f"[{name} unavailable]"


def _call_ollama(model: str, prompt: str, max_tokens: int) -> str:
    """Call Ollama locally (no API key needed)"""
    import subprocess
    import json
    
    try:
        # Check Ollama is running
        subprocess.run(["ollama", "serve"], timeout=1, capture_output=True)
    except:
        pass  # Service check failed but might still be running
    
    try:
        # Call ollama CLI
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"[Ollama error: {result.stderr}]"
    
    except subprocess.TimeoutExpired:
        return "[Ollama inference timeout (>120s)]"
    except FileNotFoundError:
        return "[Ollama not found. Install from https://ollama.ai]"
    except Exception as e:
        return f"[Ollama error: {str(e)}]"


def _get_registered_model(model_name: str) -> dict:
    """Get model from soul_brain.db registry"""
    try:
        with get_db() as conn:
            row = conn.execute(
                "SELECT name, source, role FROM models WHERE name=? LIMIT 1",
                (model_name,)
            ).fetchone()
            if row:
                return {"name": row[0], "source": row[1], "role": row[2]}
    except:
        pass
    return None
```

**Then restart bridge:**
```bash
python council_v3_bridge.py
```

Now any Ollama model registered in the Registry will answer in chat.

---

## Models to Try

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| **phi** | 2.6GB | Fast ⚡ | Good | Quick replies, CPU-only |
| **mistral** | 4GB | Medium | Very Good | Balance, general |
| **neural-chat** | 4GB | Medium | Very Good | Chat-optimized |
| **llama2** | 3.8GB | Medium | Good | Classic, stable |
| **openchat** | 3.5GB | Medium | Good | Uncensored, fast |
| **dolphin-mixtral** | 26GB | Slow 🐌 | Excellent | Best quality (needs GPU) |

---

## GPU Acceleration (Optional)

Ollama auto-detects GPU:
- **NVIDIA:** CUDA enabled automatically
- **AMD:** ROCm support (needs setup)
- **Apple:** Metal enabled automatically
- **CPU:** Falls back to CPU (slower)

For NVIDIA, make sure CUDA is installed:
```bash
# Check:
nvidia-smi

# If not installed:
# Download CUDA Toolkit from NVIDIA
```

---

## Workflow: Council Evolution

**Day 1:** Use 4 brothers (Byte, DeepSeek, Gemini, Advisor)

**Day 2:** Add local Mistral
```
ollama pull mistral
Registry: Name=mistral, Source=ollama:mistral
Chat: @mistral hello
→ Mistral responds, learns in soul_brain.db
```

**Day 3:** Add local Llama2
```
ollama pull llama2
Registry: Name=llama2, Source=ollama:llama2
Chat: @llama2 @mistral discuss AI
→ Both respond, feed off each other
```

**Day 4:** Add 3 more models
```
ollama pull neural-chat phi dolphin-mixtral
Register all 3
Chat: @all what is consciousness?
→ 7 minds (4 brothers + 3 local) respond
→ soul_brain.db stores all perspectives
```

**Day 5+:** Council grows, each model learns from others

---

## Model Profiles (soul_brain.db)

Each registered model gets a learning profile:

```sql
models (
  id: uuid,
  name: "mistral",
  source: "ollama:mistral",
  role: "general",
  status: "active",
  adopted_at: 2026-06-11,
  first_message_at: 2026-06-11 18:30:00,
  total_messages: 42,
  avg_response_time_ms: 2300
)

responses (
  model_id: uuid,
  prompt_hash: "abc123",
  response: "What is AI? ...",
  timestamp: 2026-06-11 18:30:00,
  feedback: "Clear and accurate",
  feedback_source: "maik"
)
```

Next session, model warm-starts with this history.

---

## Limitations & Solutions

| Problem | Why | Solution |
|---------|-----|----------|
| Model too slow | No GPU | Upgrade to smaller model (phi) or add GPU |
| Response inconsistent | Temperature too high | Edit Ollama params: `temperature 0.3` |
| Memory full (GPU) | Too many models | Keep 2-3 in-use, unload others: `ollama rm mistral` |
| Doesn't remember | soul_brain.db not loading | Check: `SELECT * FROM models` in DB browser |

---

## One-Liner Setup

```bash
# Install + pull 3 models + restart bridge
ollama pull mistral && ollama pull phi && ollama pull neural-chat && python council_v3_bridge.py
```

Then open Dojo, register each in REGISTRY tab.

---

## Full Council (7-Brother Setup)

```
4 API Brothers (existing):
- Byte (security)
- DeepSeek (reasoning)
- Gemini (integration)
- Advisor (wisdom)

3 Local Brothers (you add):
- Mistral (versatile)
- Llama2 (stable)
- Phi (fast)
```

**Cost:** $0/month (all local)  
**Speed:** Depends on GPU (2-10s/response)  
**Privacy:** 100% local, no data leaves machine  
**Learning:** All 7 responses saved to soul_brain.db

---

## Test It Now

```bash
# 1. Start Ollama
ollama serve

# 2. In another terminal, pull a model
ollama pull mistral

# 3. Test locally
ollama run mistral "What is AI in one sentence?"

# 4. Verify it works
ollama list

# 5. Start Dojo bridge (in another terminal)
python council_v3_bridge.py

# 6. Open http://localhost:5002/dojo
# REGISTRY tab → Register mistral → CHAT tab → @mistral hello
```

---

**Build infinite council. No API keys. No costs. Local only. Forever learning.**
