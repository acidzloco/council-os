"""
Council OS — Per-brother backend configuration.
Each brother can independently use local Ollama or any cloud provider.
Config persists to brother_config.json.
"""

import json
import os
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "brother_config.json"

BROTHERS = ["byte", "deepseek", "gemini", "advisor"]

# Available providers + their default models
PROVIDERS = {
    "local": {
        "label": "Local (Ollama)",
        "models": ["dolphin-llama3:latest", "mistral:latest", "qwen2.5:7b",
                   "deepseek-r1:8b", "phi3:mini", "gemma2:9b"],
        "requires_key": False,
        "key_env": None,
    },
    "anthropic": {
        "label": "Claude (Anthropic)",
        "models": ["claude-opus-4-8", "claude-sonnet-4-6", "claude-haiku-4-5-20251001",
                   "claude-opus-4-5", "claude-sonnet-3-5"],
        "requires_key": True,
        "key_env": "ANTHROPIC_API_KEY",
    },
    "gemini": {
        "label": "Gemini (Google)",
        "models": ["gemini-2.5-flash-preview-05-20", "gemini-2.0-flash",
                   "gemini-1.5-pro", "gemini-1.5-flash"],
        "requires_key": True,
        "key_env": "GEMINI_API_KEY",
    },
    "deepseek": {
        "label": "DeepSeek (API)",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "requires_key": True,
        "key_env": "DEEPSEEK_API_KEY",
    },
    "openai": {
        "label": "ChatGPT (OpenAI)",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "requires_key": True,
        "key_env": "OPENAI_API_KEY",
    },
    "openrouter": {
        "label": "OpenRouter",
        "models": ["meta-llama/llama-3.1-70b-instruct", "mistralai/mixtral-8x7b-instruct",
                   "anthropic/claude-3.5-sonnet", "google/gemini-pro",
                   "deepseek/deepseek-chat", "openai/gpt-4o"],
        "requires_key": True,
        "key_env": "OPENROUTER_API_KEY",
    },
}

_DEFAULT_CONFIG = {
    b: {"backend": "local", "model": "dolphin-llama3:latest", "api_key": ""}
    for b in BROTHERS
}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            # Backfill any missing brothers
            for b in BROTHERS:
                if b not in cfg:
                    cfg[b] = _DEFAULT_CONFIG[b].copy()
            return cfg
        except Exception:
            pass
    return {b: v.copy() for b, v in _DEFAULT_CONFIG.items()}


def save_config(cfg: dict):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def get_brother(brother: str) -> dict:
    return load_config().get(brother, _DEFAULT_CONFIG.get(brother, {}).copy())


def set_brother(brother: str, backend: str, model: str, api_key: str = ""):
    if brother not in BROTHERS:
        raise ValueError(f"Unknown brother: {brother}")
    if backend not in PROVIDERS:
        raise ValueError(f"Unknown backend: {backend}")
    cfg = load_config()
    cfg[brother] = {"backend": backend, "model": model, "api_key": api_key}
    save_config(cfg)


def resolve_api_key(brother_cfg: dict, provider_key: str) -> str:
    """Per-brother API key overrides .env; falls back to env var."""
    override = brother_cfg.get("api_key", "").strip()
    if override:
        return override
    env_var = PROVIDERS.get(provider_key, {}).get("key_env")
    return os.environ.get(env_var, "") if env_var else ""


def providers_status() -> dict:
    """Which providers have their API key available (env or config)."""
    status = {}
    for pid, p in PROVIDERS.items():
        if not p["requires_key"]:
            status[pid] = True
        else:
            env_key = p.get("key_env")
            status[pid] = bool(os.environ.get(env_key, ""))
    return status
