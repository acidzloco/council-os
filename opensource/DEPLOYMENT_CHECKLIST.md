# Deployment Checklist — Before GitHub Push

## ✅ Pre-Deployment Security Check

Run this checklist **before** pushing to GitHub to ensure no API keys or secrets are exposed.

---

## 1. Environment Files

- [ ] `.env` file exists but is **NOT** in git
- [ ] `.env.example` exists with **NO** real keys (just placeholders)
- [ ] `.gitignore` includes:
  ```
  .env
  .env.local
  *.env
  *_key.txt
  *_secret.txt
  credentials.json
  ```

**Test:**
```bash
git status
# Should NOT show .env
```

---

## 2. Source Code Audit

Grep for accidentally hardcoded secrets:

```bash
# Check for API key patterns
git grep -i "sk-" -- "*.py" "*.js" "*.html"     # OpenRouter/OpenAI
git grep -i "AIzaSy" -- "*.py" "*.js" "*.html" # Google keys
git grep -i "ANTHROPIC_API_KEY=" -- "*.py"     # Hardcoded keys
git grep -i "DEEPSEEK_API_KEY=" -- "*.py"
git grep -i "password" -- "*.py" "*.js"
git grep -i "secret" -- "*.py" "*.js"
```

**If found:**
- [ ] Remove all hardcoded secrets
- [ ] Commit the fix
- [ ] Use `git filter-branch` or `bfg-repo-cleaner` to remove from history
- [ ] Force push ONLY if not yet shared

---

## 3. File-Level Checks

### council_v3_bridge.py
- [ ] No API keys hardcoded
- [ ] All keys loaded from `os.environ.get()`
- [ ] Database path uses environment variable or default

### models_api.py
- [ ] No secrets in code
- [ ] Uses `os.environ.get()` for sensitive config

### workspace_chat_etc.html
- [ ] No API keys in JavaScript
- [ ] No hardcoded server URLs (use localhost defaults)

### council_v3_shared.py
- [ ] Database path is configurable
- [ ] No secrets in defaults

---

## 4. Configuration Templates

- [ ] `.env.example` exists with **all** required fields
- [ ] `.env.example` has descriptive comments
- [ ] `.env.example` has NO real values
- [ ] Example values clearly marked as placeholders:
  ```
  ANTHROPIC_API_KEY=your-anthropic-key-here
  DEEPSEEK_API_KEY=sk-xxxx-your-key-here
  ```

---

## 5. Documentation

- [ ] README.md exists with quick-start guide
- [ ] SECURITY.md exists with key management guidelines
- [ ] Getting Started section mentions `.env.example` → `.env`
- [ ] Warns about never committing `.env`

**Key sections:**

```markdown
### Configuration
1. Copy `.env.example` to `.env`
2. Add your API keys to `.env`
3. NEVER commit `.env` to git
```

---

## 6. Git History Check

Before first push, verify no secrets in history:

```bash
# Search entire history for API patterns
git log -S "ANTHROPIC_API_KEY=" --all
git log -S "sk-" --all
git log -S "AIzaSy" --all

# Search for common secret variable assignments
git log -p --all -S "SECRET\|PASSWORD\|KEY" | grep -i "api\|key\|secret" | head -20
```

If anything found:
```bash
# Remove from history BEFORE first push
git filter-branch --tree-filter 'rm -f .env' HEAD
```

---

## 7. .gitignore Verification

```bash
# Verify .env would be ignored
git check-ignore -v .env
# Output should show it's ignored

# Double-check no secrets are tracked
git ls-files | grep -E "\.env|_key\.txt|_secret\.txt|credentials"
# Should return nothing
```

---

## 8. Final Pre-Push Verification

```bash
# 1. Check what will be pushed
git diff --cached --name-only

# 2. Verify no env files in staging
git status | grep -E "\.env|credentials"
# Should show nothing

# 3. Count files
git ls-files | wc -l
# Should be reasonable (not accidentally including node_modules, __pycache__, etc)

# 4. Test install from fresh checkout
cd /tmp
git clone {your-repo}
cd council-os-v3
pip install -r requirements.txt
cp .env.example .env
# Edit .env with test keys
python council_v3_bridge.py
# Should start without leaking any secrets in logs
```

---

## 9. GitHub-Specific Checks

- [ ] Repository is **public** only if you're OK with source being public
- [ ] No secrets in README or documentation
- [ ] LICENSE file included (if applicable)
- [ ] CONTRIBUTING.md included (optional but recommended)

---

## 10. Post-Push Verification

After pushing to GitHub:

```bash
# Visit your repo: https://github.com/youruser/council-os-v3
# Search repo for patterns:
# Click "Search" → search for "sk-" or "ANTHROPIC_API"
# Should find nothing
```

---

## ✅ Deployment Ready Checklist

Before announcing/deploying:

- [ ] No .env file in repo
- [ ] No hardcoded keys in any code
- [ ] .env.example has placeholder values only
- [ ] .gitignore protects all secret files
- [ ] Git history clean (no accidental commits of keys)
- [ ] README warns about .env setup
- [ ] SECURITY.md explains key management
- [ ] All tests pass locally with .env configured
- [ ] Docs mention "rotate keys after cloning"

---

## Quick Commands

```bash
# One-shot verification
echo "=== Checking for API patterns ===" && \
git log -p --all -S "ANTHROPIC_API_KEY" | head -5 && \
git log -p --all -S "sk-" | head -5 && \
echo "=== Checking tracked files ===" && \
git ls-files | grep -E "\.env|credentials|secret" && \
echo "=== All clear! ===" || echo "FOUND SECRETS — DO NOT PUSH"
```

---

## If You Made a Mistake

### Accidentally Committed .env
```bash
# Remove from git but keep locally
git rm --cached .env
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Remove .env from git, add to .gitignore"
git push

# THEN rotate all API keys (they're in history now)
```

### Accidentally Pushed Keys to GitHub
1. **IMMEDIATELY rotate all keys**
2. Remove from history:
   ```bash
   git filter-branch --tree-filter 'rm -f .env' HEAD
   git push --force
   ```
3. Force push ONLY if few users have cloned
4. Notify users to rotate keys on their machines

---

**REMEMBER: Better to be paranoid about secrets than exposed.**

If in doubt, rotate your API keys. It's free and takes 2 minutes.
