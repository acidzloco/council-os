"""
Council OS Vault — Training data protection layer.

Theme: No one left behind.
The code is open-source. The base model is downloadable.
What's irreplaceable is the training — months of community work.
This protects it.
"""

import io
import json
import os
import secrets
import zipfile
from datetime import datetime
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    _CRYPTO_OK = True
except ImportError:
    _CRYPTO_OK = False

# ── PATHS ─────────────────────────────────────────────────────────────────────
_IS_ANDROID = os.path.exists("/data/data/com.termux")
if _IS_ANDROID:
    _ROOT = Path(os.path.expanduser("~/council_v3"))
else:
    _ROOT = Path(r"C:\AI")

VAULT_DIR   = Path(os.environ.get("COUNCIL_VAULT_DIR", str(_ROOT / "council_v3" / "vault")))
KEY_FILE    = VAULT_DIR / "council.key"
TOKEN_FILE  = VAULT_DIR / "council.token"
CONFIG_FILE = VAULT_DIR / "vault_config.json"
BACKUP_DIR  = VAULT_DIR / "backups"

SOUL_DB     = _ROOT / "soul_brain" / "soul_brain.db"
BRAIN_DIR   = _ROOT / "idea"
TRAINING_DIRS = [
    BRAIN_DIR / "practice",
    BRAIN_DIR / "project",           # where project_api.py saves brother outputs
    Path(r"C:\AI\council_v3\vault_project"),  # future vault-specific exports
]


# ── INIT ──────────────────────────────────────────────────────────────────────

def _ensure_vault():
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        try:
            import subprocess
            user = os.environ.get("USERNAME", "User")
            subprocess.run(
                ["icacls", str(VAULT_DIR), "/inheritance:r",
                 "/grant:r", f"{user}:(OI)(CI)F"],
                capture_output=True, timeout=5,
            )
        except Exception:
            pass


# ── KEY + TOKEN ───────────────────────────────────────────────────────────────

def get_or_create_key() -> bytes:
    _ensure_vault()
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    key = os.urandom(32)
    KEY_FILE.write_bytes(key)
    return key


def get_or_create_token() -> str:
    _ensure_vault()
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    token = secrets.token_urlsafe(32)
    TOKEN_FILE.write_text(token, encoding="utf-8")
    return token


def rotate_token() -> str:
    """Generate a new auth token, invalidating the old one."""
    _ensure_vault()
    token = secrets.token_urlsafe(32)
    TOKEN_FILE.write_text(token, encoding="utf-8")
    return token


# ── CONFIG ────────────────────────────────────────────────────────────────────

def _load_cfg() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_cfg(cfg: dict):
    _ensure_vault()
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def is_auth_enabled() -> bool:
    return _load_cfg().get("auth_enabled", False)


def set_auth_enabled(enabled: bool):
    cfg = _load_cfg()
    cfg["auth_enabled"] = enabled
    _save_cfg(cfg)


# ── CRYPTO ────────────────────────────────────────────────────────────────────

def crypto_available() -> bool:
    return _CRYPTO_OK


def encrypt(plaintext: bytes) -> bytes:
    """AES-256-GCM encrypt. Output: 12-byte nonce + ciphertext+tag."""
    if not _CRYPTO_OK:
        raise RuntimeError("pip install cryptography")
    nonce = os.urandom(12)
    ct = AESGCM(get_or_create_key()).encrypt(nonce, plaintext, None)
    return nonce + ct


def decrypt(data: bytes) -> bytes:
    """AES-256-GCM decrypt. Expects 12-byte nonce prefix."""
    if not _CRYPTO_OK:
        raise RuntimeError("pip install cryptography")
    nonce, ct = data[:12], data[12:]
    return AESGCM(get_or_create_key()).decrypt(nonce, ct, None)


# ── BACKUP ────────────────────────────────────────────────────────────────────

def create_backup(dest_dir: Path = None) -> Path:
    """
    Bundle all training data + soul_brain.db into an AES-256-GCM encrypted
    .vault archive. Returns the path to the created file.
    """
    if not _CRYPTO_OK:
        raise RuntimeError(
            "cryptography library not installed. Run: pip install cryptography"
        )

    dest = dest_dir or BACKUP_DIR
    dest.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_path = dest / f"council_backup_{ts}.vault"

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # soul_brain.db — the journal, all memories
        if SOUL_DB.exists():
            zf.write(SOUL_DB, "soul_brain.db")

        # Training artifacts (JSONL, code, markdown, text)
        _TRAIN_EXT = {".jsonl", ".md", ".txt", ".py", ".js", ".html", ".cpp", ".c", ".json", ".log"}
        for tdir in TRAINING_DIRS:
            if tdir.exists():
                for f in tdir.rglob("*"):
                    if f.is_file() and f.suffix.lower() in _TRAIN_EXT:
                        try:
                            zf.write(f, f"training/{tdir.name}/{f.relative_to(tdir)}")
                        except Exception:
                            pass

        # Brain markdown files (brother knowledge)
        if BRAIN_DIR.exists():
            for f in BRAIN_DIR.rglob("*.md"):
                try:
                    zf.write(f, f"brain/{f.relative_to(BRAIN_DIR)}")
                except Exception:
                    pass

    out_path.write_bytes(encrypt(buf.getvalue()))
    return out_path


def list_backups() -> list[dict]:
    if not BACKUP_DIR.exists():
        return []
    result = []
    for f in sorted(BACKUP_DIR.glob("*.vault"), reverse=True):
        stat = f.stat()
        result.append({
            "name": f.name,
            "path": str(f),
            "size_mb": round(stat.st_size / 1024 / 1024, 2),
            "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        })
    return result


# ── STATUS ────────────────────────────────────────────────────────────────────

_TRAIN_EXT = {".jsonl", ".md", ".txt", ".py", ".js", ".html", ".cpp", ".c", ".json", ".log"}

def vault_status() -> dict:
    training_count = 0
    training_size_mb = 0.0
    for tdir in TRAINING_DIRS:
        if tdir.exists():
            for f in tdir.rglob("*"):
                if f.is_file() and f.suffix.lower() in _TRAIN_EXT:
                    training_count += 1
                    try:
                        training_size_mb += f.stat().st_size / 1024 / 1024
                    except Exception:
                        pass

    backups = list_backups()
    token = get_or_create_token()

    return {
        "crypto_available": _CRYPTO_OK,
        "auth_enabled": is_auth_enabled(),
        "key_exists": KEY_FILE.exists(),
        "training_files": training_count,
        "training_size_mb": round(training_size_mb, 2),
        "soul_db_exists": SOUL_DB.exists(),
        "soul_db_mb": round(SOUL_DB.stat().st_size / 1024 / 1024, 2) if SOUL_DB.exists() else 0,
        "backup_count": len(backups),
        "last_backup": backups[0]["name"] if backups else None,
        "token_preview": token[:8] + "..." + token[-4:] if len(token) > 12 else "***",
    }
