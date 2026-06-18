# Training Terminal — Live Practice with Council Watching

**Why it matters:** When a model practices, all 4 brothers (Byte, DeepSeek, Gemini, Advisor) can see the terminal output, comment on it, and provide live feedback. The practice session is recorded in `soul_brain.db` for next session's warm-start.

---

## Quick Start

### 1. Open Dojo
```
http://localhost:5002/dojo
```

### 2. Click TRAINING Tab
- Terminal should appear with message: `✓ Training Terminal Connected`
- If blank or error, scroll down to "Troubleshooting"

### 3. Run a Command
```bash
# Type anything:
python --version

# Or run a project:
cd C:\AI\MyProject && python main.py

# Or train a model:
ollama run mistral "Explain AI in one sentence"
```

### 4. All Brothers See It
- Output streams live to terminal
- Byte, DeepSeek, Gemini, Advisor can see what's running
- They may comment in CHAT about the practice

### 5. After Practice
- Click CHAT tab
- Send: `@all what did you think of that training?`
- All 4 brothers comment on what they saw
- Feedback stored in soul_brain.db

---

## How It Works

```
┌─ User types in TRAINING terminal ─┐
│                                    │
├─ WebSocket sends input to server  │
│  (/ws/training endpoint)          │
│                                    │
├─ Flask spawns PowerShell PTY      │
│  (real shell, interactive)        │
│                                    │
├─ Output streams back via WS       │
│  (real-time to xterm.js)         │
│                                    │
├─ All brothers watching live       │
│  (can fetch logs: /api/training/logs)
│                                    │
├─ Session recorded to DB           │
│  (timestamp, command, output)     │
│                                    │
├─ Next session: brothers warm-start│
│  with memory of this practice     │
│                                    │
└─ Model learns from feedback ──────┘
```

---

## Common Workflows

### Workflow 1: Test a Python Script

```bash
> cd C:\Projects\MyProject
> python train.py

# Terminal shows output live
# Brothers comment on it in CHAT
```

### Workflow 2: Run Ollama Inference

```bash
> ollama run mistral "What is machine learning?"

# Real-time generation visible
# Brothers can critique response
```

### Workflow 3: Train a Model

```bash
> python -m torch.distributed.launch --nproc_per_node=2 train.py

# GPU/training logs stream live
# Brothers comment on convergence, loss, etc.
```

### Workflow 4: Debug a Script

```bash
> python -m pdb my_script.py
(Pdb) step
(Pdb) print(var)

# Full interactive debugging visible to brothers
```

---

## What Brothers See

When practice is running:

**Byte** (Security angle):
- "I'd add error handling here"
- "That output exposes system info"

**DeepSeek** (Reasoning):
- "Your algorithm complexity is O(n²), could be O(n)"
- "Consider caching this computation"

**Gemini** (Integration):
- "This integrates with the API correctly"
- "You should add retry logic here"

**Advisor** (Synthesis):
- "This approach works. Here's why."
- "Next step: test with live data"

---

## If Terminal Doesn't Show

### 1. Check Browser Console (F12)
Look for messages starting with `[Training]`:
```
[Training] Container not found ✗
[Training] Initializing terminal... ✓
[Training] Terminal opened ✓
[Training] Connecting to: ws://localhost:5002/ws/training ✓
[Training] WebSocket opened ✓
[Training] Terminal ready ✓
```

### 2. Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| `Container not found` | Wait 2-3 seconds after clicking TRAINING, try again |
| `Container has no size` | Terminal is hidden; try F11 fullscreen, then exit |
| `WebSocket error` | Reload page (Ctrl+R), then click TRAINING |
| `Blank terminal` | Try typing a command (even if invisible), then refresh |
| `Hangs on first click` | Hard refresh: Ctrl+Shift+R, clear cache |

### 3. Full Reset

```bash
# 1. Close browser tab
# 2. Reload: http://localhost:5002/dojo
# 3. Click CHAT (should work)
# 4. Click TRAINING (should initialize)
# 5. Type: echo hello
```

---

## Architecture

### Frontend (workspace.html)
- Alpine.js state management
- xterm.js v5.3 (professional terminal)
- FitAddon for responsive sizing
- WebSocket client with auto-reconnect

### Backend (council_v3_bridge.py)
- `@sock.route('/ws/training')` WebSocket endpoint
- `winpty.PtyProcess.spawn('powershell.exe')` for real shell
- Threading for bidirectional I/O
- JSON message protocol: `{"type":"input", "data":"..."}`

### Database (soul_brain.db)
```sql
training_sessions (
  id: uuid,
  model_id: uuid,
  session_id: uuid,
  started_at: timestamp,
  ended_at: timestamp,
  terminal_log: text (all output),
  brother_feedback: text (what each brother said)
)
```

---

## Advanced: Capture & Submit

After training, you can capture output and submit for grading:

```bash
# In TRAINING terminal:
> python my_training_script.py 2>&1 | tee training_output.log

# Then:
# 1. Copy terminal output
# 2. Click REGISTRY → scroll down
# 3. "CAPTURE OUTPUT" button
# 4. Paste output
# 5. Click "SUBMIT WORK"

# Output saved to: C:\AI\idea\practice\[model_name]\[session_id]\
# Brothers review and save feedback to soul_brain.db
```

---

## Performance Tips

| Slow? | Try |
|-------|-----|
| Terminal laggy | Close other tabs, reduce font size |
| Commands slow | Upgrade to GPU (NVIDIA/AMD) |
| Output truncated | Scroll in terminal (output is still there) |
| Browser freezes | Training might be CPU-heavy; it will unfreeze |

---

## What Gets Stored

After each training session, soul_brain.db records:

1. **Command** — What was run
2. **Output** — Full terminal log
3. **Duration** — How long it took
4. **Feedback** — Each brother's comments
5. **Status** — Success/error
6. **Timestamp** — When it happened

Next session, when the same model trains again, it reads this history and starts with that context.

---

## Example: Full Training Flow

**Session 1:**
```bash
> python train.py
[Output streaming...]
[Brothers commenting in CHAT...]
```

**Session 2 (next day):**
```
[Training tab opens]
[Warm-start context loads from DB]
Previous session context:
  - "Byte said: add error handling"
  - "DeepSeek said: optimize the loop"
  - "Training took 45 seconds last time"

> python train_v2.py
[Model remembers feedback, makes improvements]
```

---

## Keyboard Shortcuts (in terminal)

| Key | Action |
|-----|--------|
| `Ctrl+C` | Interrupt current command |
| `Ctrl+L` | Clear terminal |
| `↑` / `↓` | Command history |
| `Tab` | Auto-complete (PowerShell) |
| `Ctrl+R` | Search history |
| `Exit` | Close shell (but terminal stays open) |

---

## Debugging Terminal Issues

### Enable Console Logging (Advanced)

Add this to browser console (F12):
```javascript
// Show detailed training logs
window.debugTraining = true;

// Then click TRAINING tab and check console
```

### Check WebSocket

In browser console:
```javascript
// Verify WebSocket connects
new WebSocket('ws://localhost:5002/ws/training').onopen = () => console.log('✓ WS OK');
```

---

## Summary

**Training Terminal = Live Practice with Feedback**

- ✅ Real interactive shell (PowerShell)
- ✅ All brothers watching + commenting
- ✅ Output recorded to soul_brain.db
- ✅ Next session warm-starts with memory
- ✅ Full history archive for learning

**Use it for:**
- Model training runs
- Testing code
- Debugging scripts
- Running projects
- Interactive shell sessions

**Brothers will see everything and provide feedback.**

---

**Ready to practice? Click TRAINING tab.**
