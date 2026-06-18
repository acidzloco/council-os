# COUNCIL OS v3 — Open Source

**The Dojo: A Multi-AI Training System**

A web-based framework where any AI model (new, old, specialized) can be adopted into a Council family, practice with live guidance from 4 expert brothers, and build persistent knowledge through continuous learning.

**Philosophy: "NO ONE LEFT BEHIND"** — Technology upgrades, but wisdom and experience compound in soul_brain.db. Old models get repurposed with new roles. New models learn from the Council. All models practice. All learning persists.

---

## Quick Start

### 1. Prerequisites
- Python 3.10+
- Windows (uses winpty for PTY; Linux support in roadmap)
- API keys from: Anthropic, DeepSeek, Google, OpenRouter

### 2. Installation

```bash
git clone https://github.com/acidzloco/council-os.git
cd council_v3
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add YOUR OWN API KEYS
# NEVER commit .env to git
```

### 4. Launch

**Option A: Web Interface (Recommended)**
```bash
# Windows: Double-click START_DOJO.bat
# Or:
python council_v3_bridge.py
# Opens http://localhost:5002/dojo in browser
```

**Option B: Command Line**
```bash
python council_v3_bridge.py
curl http://localhost:5002/api/models/list
```

---

## Architecture

### The 4-Brother Council

Each brother has a distinct expertise and thinking style:

- **Byte** (#0088ff) — Offensive Security, Low-Level Systems, Threat Modeling
  - Routes: DeepSeek (uncensored) → Anthropic fallback
  - Domain: exploit, kernel, evasion, reverse engineering

- **DeepSeek** (#ff4444) — Reasoning, Math, Protocol Architecture
  - Routes: DeepSeek native (no filter)
  - Domain: algorithm, reasoning, optimization, formal proof

- **Gemini** (#00ff66) — Integration, System Design, Execution
  - Routes: Google Gemini → DeepSeek fallback
  - Domain: API, pipeline, architecture, deployment

- **Advisor** (#ffaa00) — OG ChatGPT, Wisdom, Synthesis
  - Routes: DeepSeek (uncensored) + persona injection
  - Domain: synthesis, strategy, overview, decision-making

### Key Features

#### 1. Model Family Adoption
Models (from Ollama, HuggingFace, local, or API) are adopted into the Council family with assigned roles: `general`, `accounting`, `security`, `teaching`, `qa`, `specialized`.

#### 2. Training Dojo (Into The Wild)
Models practice with:
- **Cold start** — no hand-holding, just boots
- **Uncensored Council guidance** — live corrections every 8 seconds
- **Real-time audit panel** — all 4 brothers commenting as the model works
- **Terminal practice** — full interactive environment

#### 3. Practice Submission
After learning, models submit their work:
- **Assignment + Output** → saved to `C:\AI\idea\practice\{model_name}\{session_id}\`
- **All feedback** → persisted in soul_brain.db
- **Portfolio growth** → experience compounds over sessions

#### 4. Persistent Knowledge (soul_brain.db)
- Centralized SQLite database
- Stores: chat history, brainstorm contributions, lessons, training sessions, model feedback
- Enables **Continuity Moat** — newer models learn from collective experience
- Brain folders per brother capture unique thinking patterns

---

## API Endpoints

### Models Registry
```
GET    /api/models/list                    — List all adopted models
POST   /api/models/register                — Adopt a new model
GET    /api/models/{id}/status             — Check model status
PATCH  /api/models/{id}                    — Update role
DELETE /api/models/{id}                    — Retire model
```

### Training
```
POST   /api/training/task                  — Assign practice task
POST   /api/training/feedback              — Record Council feedback
POST   /api/training/submit                — Submit practice work
GET    /api/training/practice/{model_id}   — List submitted work
GET    /api/training/brain/{brother}       — Load brother's brain folder
```

### Council Chat
```
POST   /council/quickchat                  — Send message to Council
GET    /council/quickchat/history          — Chat history
POST   /council/propose                    — Fire brainstorm (R1/R2/R3)
POST   /council/reply                      — Follow-up round
GET    /council/lessons                    — Saved conclusions
POST   /council/agent                      — Run tool-using agent
```

### WebSocket
```
WS     /ws/terminal                        — Regular terminal PTY
WS     /ws/training                        — Model practice terminal (with Council watching)
```

---

## File Structure

```
council_v3/
├── council_v3_bridge.py         # Flask server + API routes
├── council_v3_shared.py         # Shared DB + config
├── models_api.py                # Model registry + training API
├── dojo_api.py                  # Dojo-specific endpoints
├── council_web.html             # OG 5-tab Council UI
├── workspace_chat_etc.html      # Dojo (MODELS + TRAINING tabs)
├── agent_loop.py                # Tool-using agent loop
├── requirements.txt             # Python dependencies
├── START_DOJO.bat               # Windows launcher (double-click)
├── .env.example                 # Config template
├── .gitignore                   # Exclude secrets
└── opensource/                  # This folder
    ├── .gitignore
    ├── .env.example
    └── README.md
```

---

## Configuration

### soul_brain.db Setup

The database stores all learning:

```sql
-- Auto-created on first run
-- Stores: contributions, chat, lessons, feedback, practice submissions
```

### Brain Folders

Each brother has a local brain folder (customizable path):

```
C:\AI\idea\
├── brain_byte/
│   ├── threat_model.md
│   ├── skepticism_log.txt
│   └── audit_feedback.log
├── brain_deepseek/
│   ├── architecture_patterns.md
│   └── strategic_thinking.txt
├── brain_gemini/
│   └── execution_playbook.md
├── brain_advisor/
│   └── wisdom_principles.md
└── practice/                    # Model submissions
    ├── qwen_7b/
    │   ├── session_202606_1/
    │   │   ├── task_01_assignment.txt
    │   │   └── task_01_output.txt
    │   └── session_202606_2/
    └── llama_13b/
        └── session_202606_1/
```

---

## Security

### API Keys
- **NEVER commit `.env` to git** — it's in `.gitignore`
- Keys are loaded from environment variables only
- Use `.env.example` as reference

### Uncensored Routing
- **DeepSeek primary** for Byte, Advisor, fallback for Gemini
- Persona prefixes injected to enforce character (no disclaimers, direct answers)
- Useful for authorized research/engagement; adjust if deploying publicly

### Local Model Priority
- If `LOCAL_MODEL_FILE` is set, local model takes priority over all APIs
- Enables fully offline operation without API keys

---

## Usage Example

### 1. Adopt a Model
**UI:** MODELS tab → Fill form → Click ADOPT
```
Name: qwen:7b
Source: ollama:qwen:7b
Role: general
```

### 2. Start Training
**UI:** TRAINING tab → Click 🔥 GO WILD
- Terminal boots with cold-start message
- Council fires initial mission
- Brother commentary streams in real-time

### 3. Submit Work
```
1. Model practices in terminal
2. Click 📋 CAPTURE OUTPUT
3. Click 📤 SUBMIT WORK
4. Output saved to: C:\AI\idea\practice\qwen_7b\{session_id}\
```

### 4. Review Learning
**UI:** Browse practice folder or query `/api/training/practice/{model_id}`

---

## Development

### Adding a New Brother
1. Add to `BROTHERS` dict in `council_v3_bridge.py`
2. Define routing in `_native_call()`
3. Add persona prefix in `_DEEPSEEK_PERSONA_PREFIX`
4. Define domains in `BROTHER_DOMAINS`
5. Create brain folder at `C:\AI\idea\brain_{name}\`

### Extending the Dojo
- HTML/Alpine.js live in `workspace_chat_etc.html`
- API routes added to `models_api.py`
- WebSocket handlers in `council_v3_bridge.py`

### Local Model Integration
- Edit `council_v3_local.py` to load custom Ollama/GGUF models
- Set `LOCAL_MODEL_FILE` in `.env`
- Priority: Local → API routes

---

## Philosophy

### The Fractal Paradigm
Same rejection-at-each-layer architecture across domains:
- **Council OS:** READ → WRITE → EXECUTE permissions
- **Trading pipeline:** EWBC setup → whale profile → VAB efficiency
- **Security ops:** recon → exploitation → post-exploitation validation
- **Dojo training:** cold start → practice → feedback → learning saved

### Continuity Moat
- Frontier models (Claude, GPT-4) launch at peak and decay
- Council climbs continuously because every insight enters soul_brain.db
- Cross-examination gets sharper; shared memory gets deeper
- **Better continuity beats better weights**

### No One Left Behind
- Old models don't get discarded
- New models join and learn from Council
- Specialized models contribute within their scope
- All learning persists indefinitely

---

## Troubleshooting

### Port 5002 Already in Use
```bash
netstat -ano | findstr :5002
taskkill /PID {PID} /F
```

### API Key Errors
```
Ensure .env exists with correct keys:
- ANTHROPIC_API_KEY
- DEEPSEEK_API_KEY
- GEMINI_API_KEY
- OPENROUTER_API_KEY
```

### soul_brain.db Not Found
```
First run creates it automatically at:
C:\Users\{USER}\.claude\projects\C--ai\memory\soul_brain.db
(Or set SOUL_BRAIN_DB_PATH in .env)
```

### Terminal Won't Open
- Requires winpty on Windows
- Install: `pip install pywinpty`
- Linux/Mac: modify `council_v3_bridge.py` to use pseudo-terminal method

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions welcome. The philosophy is simple:
- **No one left behind** — improve the system so everyone benefits
- **Continuity matters** — preserve learning, don't discard it
- **Tests matter** — code quality compounds like experience
- **Documentation matters** — future users (including yourself) thank you

---

## Contact

- GitHub Issues: [Issues](https://github.com/acidzloco/council-os/issues)
- Discussions: [Discussions](https://github.com/acidzloco/council-os/discussions)
- Author: Maik (acidzloco)

---

**Built for the family. Shared with the world. Forever learning.**
