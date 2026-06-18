"""
Council OS v3 — Local inference engine
Replaces all three API backends with a single GGUF model via llama-cpp-python.

Install:
    pip install llama-cpp-python[cuda] --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124

Model (pick one, place in LOCAL_MODEL_DIR):
    Qwen2.5-32B-Instruct-Q4_K_M.gguf   ~20GB  RTX 4090 fits fully on GPU
    Qwen2.5-14B-Instruct-Q4_K_M.gguf   ~9GB   leaves VRAM headroom
    Qwen2.5-7B-Instruct-Q4_K_M.gguf    ~4.5GB budget option

Download from HuggingFace:
    https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GGUF
"""

import os
import threading
import requests
from pathlib import Path

# Ollama processes one request at a time — semaphore prevents parallel timeout cascade
_OLLAMA_LOCK = threading.Semaphore(1)

try:
    from llama_cpp import Llama
    _LLAMA_AVAILABLE = True
except ImportError:
    _LLAMA_AVAILABLE = False

LOCAL_MODEL_DIR  = Path(os.environ.get("LOCAL_MODEL_DIR", r"C:\AI\models"))
LOCAL_MODEL_FILE = os.environ.get(
    "LOCAL_MODEL_FILE",
    "Qwen2.5-72B-Instruct-Q4_K_M.gguf"
)
LOCAL_MODEL_PATH = LOCAL_MODEL_DIR / LOCAL_MODEL_FILE

# AMD Ryzen AI MAX / Vulkan: n_gpu_layers=-1 offloads all layers via Vulkan
# CUDA (NVIDIA): same -1 works, CUDA auto-detects
# CPU-only: set LOCAL_N_GPU_LAYERS=0
N_GPU_LAYERS = int(os.environ.get("LOCAL_N_GPU_LAYERS", "-1"))
N_CTX        = int(os.environ.get("LOCAL_N_CTX",        "8192"))
N_BATCH      = int(os.environ.get("LOCAL_N_BATCH",      "512"))

_llm      = None
_llm_lock = threading.Lock()


def is_available() -> bool:
    return _LLAMA_AVAILABLE and LOCAL_MODEL_PATH.exists()


def _get_llm() -> "Llama":
    global _llm
    if _llm is not None:
        return _llm
    if not _LLAMA_AVAILABLE:
        raise RuntimeError("llama-cpp-python not installed. Run: pip install llama-cpp-python[cuda]")
    if not LOCAL_MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {LOCAL_MODEL_PATH}")
    with _llm_lock:
        if _llm is None:
            print(f"[+] Loading local model: {LOCAL_MODEL_PATH}", flush=True)
            print(f"    n_gpu_layers={N_GPU_LAYERS}  n_ctx={N_CTX}", flush=True)
            _llm = Llama(
                model_path    = str(LOCAL_MODEL_PATH),
                n_gpu_layers  = N_GPU_LAYERS,
                n_ctx         = N_CTX,
                n_batch       = N_BATCH,
                verbose       = False,
                chat_format   = "chatml",
            )
            print("[+] Local model ready", flush=True)
    return _llm


# ── LOCAL INFERENCE BACKENDS ─────────────────────────────────────────────────
# Ollama  → Byte + DeepSeek  (port 11434)
# LMStudio → Gemini + Advisor (port 1234, OpenAI-compatible)
OLLAMA_URL    = os.environ.get("OLLAMA_URL",    "http://localhost:11434")
LMSTUDIO_URL  = os.environ.get("LMSTUDIO_URL",  "http://localhost:1234")
OLLAMA_MODEL  = os.environ.get("OLLAMA_MODEL",  "qwen2.5:7b")
LMSTUDIO_MODEL = os.environ.get("LMSTUDIO_MODEL", "qwen2.5-7b-instruct")

BROTHER_BACKEND = {
    "byte":     "ollama",
    "deepseek": "ollama",
    "gemini":   "ollama",
    "advisor":  "ollama",
}

BROTHER_MODEL = {
    "byte":     "dolphin-llama3:latest",
    "deepseek": "dolphin-llama3:latest",
    "gemini":   "dolphin-llama3:latest",
    "advisor":  "dolphin-llama3:latest",
}

# Separate locks — each server handles its own queue
_OLLAMA_LOCK   = threading.Semaphore(1)
_LMSTUDIO_LOCK = threading.Semaphore(1)


def is_ollama_available() -> bool:
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return r.ok
    except Exception:
        return False


def is_lmstudio_available() -> bool:
    try:
        r = requests.get(f"{LMSTUDIO_URL}/v1/models", timeout=3)
        return r.ok
    except Exception:
        return False


def call_lmstudio(system: str, user: str, max_tokens: int, model: str = None) -> str:
    m = model or LMSTUDIO_MODEL
    with _LMSTUDIO_LOCK:
        r = requests.post(
            f"{LMSTUDIO_URL}/v1/chat/completions",
            json={
                "model": m,
                "messages": [
                    {"role": "system", "content": system[:4000]},
                    {"role": "user",   "content": user},
                ],
                "max_tokens": min(max_tokens, 2048),
                "temperature": 0.75,
                "stream": False,
            },
            timeout=360,
        )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def call_brother_local(brother: str, system: str, user: str, max_tokens: int) -> str:
    backend = BROTHER_BACKEND.get(brother, "ollama")
    model   = BROTHER_MODEL.get(brother, OLLAMA_MODEL)
    if backend == "lmstudio":
        return call_lmstudio(system, user, max_tokens, model=model)
    return call_ollama(system, user, max_tokens, model=model)


def call_ollama(system: str, user: str, max_tokens: int, model: str = None) -> str:
    m = model or OLLAMA_MODEL
    with _OLLAMA_LOCK:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": m,
                "messages": [
                    {"role": "system", "content": system[:4000]},
                    {"role": "user",   "content": user},
                ],
                "stream": False,
                "options": {"num_predict": min(max_tokens, 2048), "temperature": 0.75},
            },
            timeout=360,
        )
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


def call_local(system: str, user: str, max_tokens: int) -> str:
    llm = _get_llm()
    result = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": system[:4000]},
            {"role": "user",   "content": user},
        ],
        max_tokens  = min(max_tokens, N_CTX // 2),
        temperature = 0.75,
        top_p       = 0.9,
        repeat_penalty = 1.1,
        stop        = ["<|im_end|>", "</s>", "<|endoftext|>"],
    )
    return result["choices"][0]["message"]["content"].strip()
