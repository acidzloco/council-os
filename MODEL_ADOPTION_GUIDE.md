# Model Adoption Guide — How to Add Models to Council

---

## Overview

The **Model Registry** lets you adopt (register) models. But there are 3 different ways to use them:

1. **Display in Registry** — just show model info (no API needed)
2. **Local Ollama Model** — runs locally, can participate in chat
3. **API-Based Model** — uses API key (HuggingFace, OpenRouter, etc.)

---

## Quick Answer: What You Asked

**Q: When I register a model, can it directly message in the council?**

**A:** Not yet automatically. The current 4 brothers (Byte, DeepSeek, Gemini, Advisor) are fixed in the routing. To make a newly-registered model participate:

**Option 1: Use Ollama (EASIEST)**
- Install Ollama locally
- Pull model: `ollama pull mistral`
- Register in Dojo: Name=`mistral`, Source=`ollama:mistral`, Role=`general`
- Model can now answer in chat (no API key needed)

**Option 2: Use API Key (needs key)**
- Get API key from provider (HuggingFace, OpenRouter, etc.)
- Add to `.env`: `OPENROUTER_API_KEY=sk-xxxx`
- Register in Dojo: Source=`openrouter:mistralai/Mistral-7B`
- Model answers in chat via API

**Option 3: Just Record It (NO API)**
- Register in Registry
- Show in model list
- Use manually in TRAINING terminal
- Doesn't auto-answer in chat

---

## Step-by-Step: Register a Model

### Method 1: Ollama (Local — FREE)

#### 1. Download & Install Ollama
- Go to https://ollama.ai
- Download for your OS
- Install and start Ollama service

#### 2. Pull a Model
```bash
# In PowerShell/Terminal:
ollama pull mistral              # ~4GB, fast, smart
ollama pull llama2              # ~4GB, classic
ollama pull neural-chat         # ~4GB, conversation-focused
ollama pull dolphin-mixtral     # ~26GB, powerful but slow
```

Check what's installed:
```bash
ollama list
```

#### 3. Register in Dojo
1. Open Dojo: `http://localhost:5002/dojo`
2. Click **REGISTRY** tab
3. Fill in form:
   - **Model name**: `mistral` (or any name)
   - **Source**: `ollama:mistral` (must match `ollama list`)
   - **Role**: `general` (or `security`, `teaching`, `accounting`)
4. Click **ADOPT MODEL**
5. Model appears in registry

#### 4. Model Now Participates
- Open **CHAT** tab
- Send message: `@mistral what is AI?`
- Model responds via local Ollama (no API key needed)
- Response saved to soul_brain.db

---

### Method 2: API-Based (HuggingFace, OpenRouter, etc.)

#### 1. Get API Key
- **OpenRouter** (easiest): https://openrouter.ai
  - Sign up, get free credits
  - Copy API key
  
- **HuggingFace**: https://huggingface.co/settings/tokens
  - Create token with API access
  
- **Local LLM API** (llama.cpp): Run locally, no key needed

#### 2. Add Key to `.env`
```
# Edit C:\AI\council_v3\.env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx
```

Save and restart bridge:
```bash
# Kill current: CTRL+C in terminal
python council_v3_bridge.py
```

#### 3. Register in Dojo
1. Click **REGISTRY** tab
2. Fill form:
   - **Model name**: `gpt-mini` (your choice)
   - **Source**: `openrouter:openai/gpt-3.5-turbo` 
   - **Role**: `general`
3. Click **ADOPT MODEL**

#### 4. Model Can Now Answer
- Send chat message with `@gpt-mini`
- Responds via API call
- Uses your API credits

---

### Method 3: Local GGUF File (Without Ollama)

If you have a `.gguf` file on disk:

```
C:\Models\mistral-7b-q4.gguf
```

#### Register in Dojo
1. Click **REGISTRY** tab
2. Fill form:
   - **Model name**: `mistral-local`
   - **Source**: `C:\Models\mistral-7b-q4.gguf`
   - **Role**: `general`
3. Click **ADOPT MODEL**

#### Run in Training Terminal
- Click **TRAINING** tab
- Use `llama.cpp` to load and inference:
  ```bash
  ./llama-cli -m C:\Models\mistral-7b-q4.gguf -p "What is AI?"
  ```

---

## How Council Routing Works

### Current: 4 Fixed Brothers

```
CHAT message sent
    ↓
Sent to: /council/quickchat
    ↓
Routes to 4 brothers:
  ├─ Byte → DeepSeek API (with Byte persona)
  ├─ DeepSeek → DeepSeek API (native)
  ├─ Gemini → Google Gemini API (native)
  └─ Advisor → DeepSeek API (with Advisor persona)
    ↓
All 4 respond in parallel
    ↓
Responses saved to soul_brain.db
```

### How to Add New Models to Chat

**SHORT ANSWER:** Edit `council_v3_bridge.py`, add new brother to `BROTHERS` dict:

```python
BROTHERS = {
    'byte': 'claude-opus-4-5',
    'deepseek': 'deepseek-chat',
    'gemini': 'gemini-2.0-flash',
    'advisor': 'gpt-4o',
    'mistral': 'ollama:mistral',  # ← ADD YOUR MODEL HERE
}
```

Then restart bridge:
```bash
python council_v3_bridge.py
```

Now chat with `@mistral` and it will answer.

---

## API Key Setup

### Where to Put Keys

**File:** `C:\AI\council_v3\.env`

**What to add:**
```bash
# For Ollama (no key needed — local only)
# Just have Ollama running

# For OpenRouter (many models via one API)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx

# For HuggingFace
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxx

# For Direct LLM APIs
LLAMA_CPP_URL=http://127.0.0.1:8000

# For Local Llama Server
LOCAL_MODEL_FILE=C:\Models\mistral-7b-q4.gguf
```

### Get Free API Keys

| Provider | Free? | How to Get | Cost |
|----------|-------|-----------|------|
| **Ollama** | ✓ FREE | Download from ollama.ai | $0 (local) |
| **OpenRouter** | ✓ FREE Credits | Sign up at openrouter.ai | $0-20/month |
| **HuggingFace** | ✓ FREE Tier | Sign up, create token | $0-50/month |
| **Anthropic** | ✓ FREE Trial | https://console.anthropic.com | $0.50/1M tokens |
| **Google Gemini** | ✓ FREE Tier | https://ai.google.dev | $0-25/month |
| **DeepSeek** | ✓ FREE Trial | https://platform.deepseek.com | $0.14/1M tokens |

---

## Example Workflows

### Workflow 1: Add Mistral (Ollama) to Council

```bash
# Step 1: Pull model
ollama pull mistral

# Step 2: Verify it works
ollama run mistral "What is AI?"

# Step 3: Register in Dojo
# (UI: REGISTRY tab → Name=mistral, Source=ollama:mistral, Role=general)

# Step 4: Chat with it
# (UI: CHAT tab → Type: "@mistral what is AI?" → SEND)
```

### Workflow 2: Add OpenAI Model via OpenRouter

```bash
# Step 1: Get API key
# (Visit openrouter.ai, sign up, copy API key)

# Step 2: Add to .env
# (Edit C:\AI\council_v3\.env, add: OPENROUTER_API_KEY=sk-or-v1-xxx)

# Step 3: Restart bridge
# (Kill with CTRL+C, run: python council_v3_bridge.py)

# Step 4: Register in Dojo
# (REGISTRY tab → Name=gpt35, Source=openrouter:openai/gpt-3.5-turbo)

# Step 5: Chat with it
# (CHAT tab → "@gpt35 hello!" → SEND)
```

### Workflow 3: Use Local GGUF in Training

```bash
# Step 1: Download model (or register existing GGUF)
# (Use HuggingFace or download from Civitai)

# Step 2: Register in Dojo
# (REGISTRY tab → Source=C:\Models\model.gguf)

# Step 3: Use in Training terminal
# (TRAINING tab → run llama.cpp or other inference tool)

# Step 4: Capture output and submit
# (Feedback saved to soul_brain.db for next session)
```

---

## Troubleshooting

### Problem: Model registered but won't answer in chat

**Check:**
1. Is Ollama running? (If using Ollama)
2. Is API key in `.env`? (If using API)
3. Did you restart bridge after adding key?
4. Did you add brother to `BROTHERS` dict in `council_v3_bridge.py`?

### Problem: API key keeps failing

**Check:**
1. Is the key correct? (Copy-paste from provider)
2. Does key have proper scope? (API access enabled?)
3. Does key have credits? (Check account)
4. Is it in the right format? (Check `.env.example`)

### Problem: Ollama model is slow

**Fix:**
1. Use smaller model: `ollama pull phi` (~2GB, fastest)
2. Upgrade GPU: nvidia-cuda, apple-mps
3. Reduce context: Add `NUM_CONTEXT=1024` to `.env`

### Problem: Can't draw — drawing board still too small

**Check browser:**
1. Try fullscreen (F11)
2. Try zooming out (CTRL+- )
3. Try different browser tab

---

## What Happens After Registration

### Database Entry
Model is saved to `soul_brain.db`:
```sql
models (
  id: uuid,
  name: "mistral",
  source: "ollama:mistral",
  role: "general",
  status: "active",
  adopted_at: timestamp,
  first_message_at: null
)
```

### Soul Brain Learning
Every chat response this model makes is stored:
```sql
responses (
  model_id: uuid,
  message: "What is AI? ...",
  timestamp: 2026-06-11 18:25:00,
  feedback: "Good, clear explanation"
)
```

### Continuity Moat
Next session, the model's past responses are loaded, giving it warm-start context.

---

## Summary

| Task | How | Cost | API Key? |
|------|-----|------|----------|
| **Just show in registry** | Enter name + source | FREE | ❌ No |
| **Chat with Ollama model** | Install Ollama, register | FREE | ❌ No |
| **Chat with API model** | Get key, register, add to .env | $0-50/mo | ✅ Yes |
| **Use in Training terminal** | Register + run CLI tool | FREE | ❌ No |
| **Full council participation** | Edit `BROTHERS` dict | Varies | Varies |

**Start with Ollama** — it's free, local, no API key needed. Then explore API models when ready.

---

**Ready to adopt your first model? Go to REGISTRY tab and start!**
