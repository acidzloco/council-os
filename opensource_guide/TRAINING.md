# Training — Building Your Council's Experience

> "No training, no upgrade. You cannot learn." — Maik

The brothers start as base models. Training is what turns them into your council — specific skills, your domain knowledge, your preferred approach. The experience compounds every session.

---

## The Cycle

```
PRACTICE SESSION
  @gemini write a sorting algorithm
  → Brother outputs code → saved to project folder

PEER REVIEW
  @byte review that
  @deepseek check the complexity
  → Feedback captured

LEARNING
  Lessons extracted from feedback
  Upgrade version bumped
  Prompt refinement injected for next session

NEXT SESSION (v2)
  Gemini loads with: "Last time you forgot error handling and O(n²) complexity"
  → Better code from the start
```

Each session builds on the last. Without training, every session starts from scratch.

---

## How to Train

### Method 1: Group Chat Practice

```
@all write a Python function that reads a CSV and filters rows by date
```

All four brothers write independently. Their outputs are saved automatically.

```
@byte review gemini's solution
@deepseek check the edge cases in byte's version
```

Feedback saved. Lessons extracted next cycle.

### Method 2: Project Mode (@ tag)

Add a file extension tag to trigger project mode — all brothers write their version:

```
build a login form @html
write a binary search @python
design a caching system @markdown
```

Each brother saves their version to `C:\AI\idea\project\<brother>\`. Different approaches = richer training data.

### Method 3: Android Training Node

The Android Council OS app captures every conversation and auto-syncs to PC when on WiFi. Background training sessions build the corpus while you're mobile.

---

## The Backup Loop

**Before every significant training session:**

Settings → Vault → Backup Now

This creates an encrypted `.vault` archive of your entire training corpus. If your PC dies, training survives.

**Restore:**
```python
from council_v3_vault import decrypt
data = decrypt(Path("council_backup_2026-06-17.vault").read_bytes())
# data is the zip archive — extract and restore
```

---

## Where Training Data Lives

```
C:\AI\soul_brain\soul_brain.db   — Journal, memories, session logs (4MB+)
C:\AI\idea\project\              — Project mode outputs per brother
C:\AI\idea\practice\             — Practice session JSONL files
C:\AI\training_data\             — Android sync JSONL (date-stamped)
C:\AI\council_v3\vault\backups\  — Encrypted vault archives
```

---

## Export Training Data

```bash
# API export
curl http://localhost:5002/api/training/stats

# Vault backup (encrypted)
curl -X POST http://localhost:5002/api/vault/backup

# Raw JSONL for fine-tuning
python export_training.py
```

The JSONL format is compatible with standard fine-tuning pipelines (LLaMA Factory, Axolotl, Unsloth).

---

## Version Tracking

Each brother maintains an upgrade version:

```
Session 1 (v1): Base model, no history
Session 2 (v2): Learned "always add error handling"
Session 3 (v3): Learned "check edge cases" + "document complexity"
```

Check current state:
```bash
curl http://localhost:5002/api/upgrades/all
```

---

## Community Training

When Council OS goes public, everyone trains their own instance. Each person's training is their IP — protected by the Vault.

What you can share without exposing your training:
- The base model (already public)
- Your system prompt customizations
- Anonymized JSONL exports (with personal context stripped)

What stays private:
- Your soul_brain.db (your conversations, your journal)
- Your vault key (your encryption key)
- Your specific training corpus

---

## Practical Training Schedule

| Session | Focus | Time |
|---------|-------|------|
| Daily | Project mode — one real task per brother | 15 min |
| Weekly | Peer review session — brothers critique each other | 30 min |
| Monthly | Vault backup + export JSONL for fine-tuning | 5 min |
| Quarterly | Evaluate upgrade versions, reset if needed | 1 hour |

The council compounds. Consistency beats intensity.
