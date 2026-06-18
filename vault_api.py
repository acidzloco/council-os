"""
Council OS Vault API — Security endpoints blueprint
"""

import secrets
import subprocess
import sys
from pathlib import Path
from flask import Blueprint, request, jsonify
from council_v3_vault import (
    get_or_create_token,
    rotate_token,
    is_auth_enabled,
    set_auth_enabled,
    create_backup,
    list_backups,
    vault_status,
    crypto_available,
)

vault_bp = Blueprint("vault", __name__, url_prefix="/api/vault")

# These paths never require auth — the UI itself must load
_SKIP_AUTH_EXACT = {"/", "/dojo", "/api/vault/auth-check"}
_SKIP_AUTH_PREFIX = ("/static/", "/favicon", "/.well-known")


def check_auth():
    """
    Returns None if the request is authorised, or a (response, 401) tuple if not.
    Call this from a before_request hook registered on the app.
    """
    if not is_auth_enabled():
        return None

    path = request.path
    if path in _SKIP_AUTH_EXACT:
        return None
    for prefix in _SKIP_AUTH_PREFIX:
        if path.startswith(prefix):
            return None

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "Unauthorized", "hint": "Bearer token required"}), 401

    token = auth[7:].strip()
    expected = get_or_create_token()
    # Constant-time compare prevents timing attacks
    if not secrets.compare_digest(
        token.encode("utf-8"), expected.encode("utf-8")
    ):
        return jsonify({"error": "Unauthorized", "hint": "Invalid token"}), 401

    return None


# ── ENDPOINTS ─────────────────────────────────────────────────────────────────

@vault_bp.route("/auth-check")
def auth_check():
    """No-auth health check — lets the UI know if auth is required."""
    return jsonify({"auth_required": is_auth_enabled()})


@vault_bp.route("/status")
def status():
    return jsonify(vault_status())


@vault_bp.route("/token")
def get_token():
    """Return full token — only call from local UI."""
    token = get_or_create_token()
    return jsonify({
        "token": token,
        "preview": token[:8] + "..." + token[-4:],
    })


@vault_bp.route("/token/rotate", methods=["POST"])
def do_rotate():
    """Generate a new token. Old token is immediately invalid."""
    token = rotate_token()
    return jsonify({
        "token": token,
        "preview": token[:8] + "..." + token[-4:],
        "message": "Token rotated. Update all connected clients.",
    })


@vault_bp.route("/auth", methods=["POST"])
def set_auth():
    data = request.json or {}
    enabled = bool(data.get("enabled", False))
    set_auth_enabled(enabled)
    return jsonify({
        "auth_enabled": enabled,
        "message": f"Auth {'ENABLED — copy your token to all clients' if enabled else 'DISABLED'}",
    })


@vault_bp.route("/backup", methods=["POST"])
def backup():
    if not crypto_available():
        return jsonify({
            "error": "cryptography not installed",
            "fix": "pip install cryptography",
        }), 500
    try:
        data = request.json or {}
        dest = data.get("dest")
        dest_path = None
        if dest:
            resolved = Path(dest).resolve()
            allowed = Path.home().resolve()
            if not str(resolved).startswith(str(allowed)):
                return jsonify({"error": "Invalid backup path — must be within home directory"}), 400
            dest_path = resolved
        vault_file = create_backup(dest_path)
        stat = vault_file.stat()
        return jsonify({
            "success": True,
            "path": str(vault_file),
            "size_mb": round(stat.st_size / 1024 / 1024, 2),
            "message": "Backup complete. Encrypted with AES-256-GCM.",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@vault_bp.route("/backups")
def backups():
    return jsonify(list_backups())


@vault_bp.route("/install-crypto", methods=["POST"])
def install_crypto():
    """Install cryptography library at runtime."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "cryptography"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            return jsonify({"success": True, "message": "cryptography installed. Restart Council OS."})
        return jsonify({"success": False, "error": result.stderr[-500:]}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
