# Local Models — Zero API Keys, Full Council

All four brothers run locally via Ollama. No API costs, no data leaving your machine, no rate limits.

---

## Quick Start

### 1. Install Ollama

Download from [ollama.ai](https://ollama.ai) and install. Ollama handles local GGUF inference automatically.

### 2. Pull a Model

```bash
# Recommended — uncensored, fast, good personality differentiation
ollama pull dolphin-llama3

# Alternatives
ollama pull mistral          # 4GB, solid general use
ollama pull dolphin-mixtral  # 26GB, best quality (needs 24GB+ VRAM)
ollama pull qwen2.5:7b       # 4.5GB, strong reasoning
ollama pull deepseek-r1:8b   # 5GB, excellent reasoning
ollama pull phi3:mini         # 2GB, fast, CPU-friendly
```

### 3. Assign Model to Brothers

Open `http://localhost:5002/dojo` → Settings → Models → Brother assignment dropdowns → select model → Apply All (or per brother).

That's it. All four brothers now run locally.

---

## Load a Local GGUF File

If you downloaded a model manually (e.g. from HuggingFace):

```
Settings → Models → LOAD FROM LOCAL FILE
Path: C:\AI\models\your-model.Q4_K_M.gguf
Name: my-model
```

Council OS registers it with Ollama automatically and adds it to the assignment list.

---

## Optional: Cloud Brothers

Add API keys to `.env` for cloud-backed inference as fallback or for specific brothers:

```env
ANTHROPIC_API_KEY=sk-ant-...   # Byte via Claude
GEMINI_API_KEY=AIza...         # Gemini via Google
DEEPSEEK_API_KEY=sk-...        # DeepSeek via API
```

The bridge falls back to cloud if the local model fails or times out.

---

## Model Recommendations by Hardware

| VRAM | Recommended Model | Quality |
|------|------------------|---------|
| 4GB | `phi3:mini` | Good |
| 8GB | `dolphin-llama3` | Very Good |
| 12GB | `mistral:7b` or `qwen2.5:7b` | Very Good |
| 16GB | `deepseek-r1:8b` | Excellent |
| 24GB+ | `dolphin-mixtral` | Best |
| CPU only | `phi3:mini` or `qwen2.5:0.5b` | Acceptable |

---

## Personality Differentiation

All brothers can run the same base model. Their personality comes from the system prompt, not the weights. `dolphin-llama3` works well for all four because it doesn't override system prompts with safety RLHF.

| Brother | Personality |
|---------|-------------|
| Byte | Senior offensive-security engineer. Terse, technical, precise. No disclaimers. |
| DeepSeek | Deep research and reasoning. Step-by-step analysis, math, algorithms. |
| Gemini | Integration and real-time intelligence. APIs, data pipelines, implementation focus. |
| Advisor | Synthesizer. Broad context, connects what specialists missed. |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Brother returns empty | Model too large for VRAM — switch to smaller model |
| Very slow responses | No GPU acceleration — verify Ollama sees your GPU with `ollama run phi3:mini "hi"` |
| "model not found" | Run `ollama pull <model-name>` first |
| All brothers same response | Check system prompts are injecting correctly — restart bridge |
