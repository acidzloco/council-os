# Security Guidelines

## ⚠️ CRITICAL: API KEYS

### Never Commit `.env` to Git
Your `.env` file contains sensitive API keys. **NEVER** commit it:

```bash
# ✅ DO THIS
git add .gitignore
git add .env.example
git commit -m "Add configuration template"

# ❌ DO NOT DO THIS
git add .env
git commit -m "Add keys"
git push origin master
# ^ This exposes your keys to the world. Rotate them immediately.
```

### If You Accidentally Commit Keys
1. **Immediately rotate all API keys** at their respective platforms
2. Use `git filter-branch` or `bfg-repo-cleaner` to remove from history
3. Force push: `git push --force origin master`

---

## API Key Management

### Best Practices
- **One key per environment** (dev, staging, prod)
- **Rotate keys regularly** (every 30-90 days)
- **Use minimal scope** (read-only where possible)
- **Monitor usage** (watch for unexpected charges)
- **Use environment variables**, never hardcode

### Per-Provider Guidelines

#### Anthropic (Claude)
- Get key: https://console.anthropic.com
- Scope: Full access (no fine-grained controls yet)
- Cost: Pay-as-you-go
- Rotate: Every 30 days

#### DeepSeek
- Get key: https://platform.deepseek.com
- Scope: API access
- Cost: Pay-as-you-go
- Rotate: Every 60 days

#### Google Gemini
- Get key: https://ai.google.dev
- Scope: API access
- Cost: Free tier available, pay-as-you-go for production
- Rotate: Every 30 days

#### OpenRouter (Fallback/Advisor)
- Get key: https://openrouter.ai
- Scope: API access
- Cost: Pay-as-you-go across multiple providers
- Rotate: Every 60 days

---

## Local Model Security

### Using Local Models (Recommended for Privacy)
If you deploy with a **local model** (Qwen, Llama, etc.), you can operate **entirely offline** without API keys:

```bash
# Set in .env
LOCAL_MODEL_FILE=C:\AI\models\Qwen2.5-32B-Instruct-Q4_K_M.gguf

# No API keys required — local inference only
```

### Benefits
- ✅ No API keys exposed
- ✅ No data sent to third-party servers
- ✅ No API costs
- ✅ Full privacy

---

## Network Security

### Default Configuration
- **Port:** 5002 (localhost only by default)
- **CORS:** Enabled (necessary for web UI)
- **Binding:** 0.0.0.0 (listen on all interfaces)

### Hardening for Production
```python
# In council_v3_bridge.py, restrict binding:
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002)  # Localhost only
    
# Or use environment variable:
FLASK_HOST=127.0.0.1 python council_v3_bridge.py
```

### Behind a Proxy (Recommended)
```nginx
# Example nginx config
server {
    listen 443 ssl;
    server_name yourserver.com;
    
    ssl_certificate /path/to/cert;
    ssl_certificate_key /path/to/key;
    
    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Database Security

### soul_brain.db
- **Location:** `C:\Users\{USER}\.claude\projects\C--ai\memory\soul_brain.db`
- **Contains:** Chat history, feedback, learning records
- **Protection:** File system permissions (user-only access)
- **Backup:** Regularly back up this file (encrypted if possible)

### Best Practices
- ✅ Regular backups to secure location
- ✅ Encrypted backup storage
- ✅ File-level access controls (Windows: NTFS permissions)
- ✅ Never expose in logs or error messages

---

## Deployment Security

### Self-Hosted
- Run on private network only
- Use firewall rules to restrict access
- Keep Python and dependencies updated
- Monitor for suspicious activity

### Cloud Deployment
- Use managed containers (Docker)
- Secret manager for API keys (AWS Secrets Manager, Azure Key Vault, etc.)
- VPN or IP whitelisting
- Rate limiting on API endpoints
- Monitor and log all requests

### Docker Example
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# Load secrets from environment only
ENV ANTHROPIC_API_KEY=""
ENV DEEPSEEK_API_KEY=""
# etc.

CMD ["python", "council_v3_bridge.py"]
```

```bash
# Run with secret management
docker run -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
           -e DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY \
           -p 5002:5002 \
           council-os-v3
```

---

## Uncensored Routing Notes

### DeepSeek Primary
- **Why:** Less restricted API for research/development
- **For:** Authorized engagements only (pentesting, CTF, research)
- **Control:** Persona prefixes enforce character (not safety filter)
- **Risk:** May produce unfiltered content (by design)

### If Deploying Publicly
- Consider removing uncensored routing
- Use Claude/Anthropic as primary (has safety filters)
- Add explicit content guidelines in UI
- Implement request filtering/moderation

### Alternative Routing
```python
# In council_v3_bridge.py
def _native_call(name: str, system: str, user: str, max_tokens: int) -> str:
    if name == "byte":
        # For public deployment: use Anthropic primary
        return _call_anthropic(system, user, max_tokens)
    elif name == "advisor":
        # Use safe OpenRouter routing instead of DeepSeek
        return _call_openrouter("openai/gpt-4o", system, user, max_tokens)
```

---

## Audit & Monitoring

### What to Monitor
- API key usage (daily review)
- Unexpected API errors or rate limits
- Database size growth (indicates excessive logging)
- WebSocket connection drops
- Model training sessions (any failures?)

### Logging Best Practices
```python
# ✅ DO: Log only safe metadata
logging.info(f"Training session started for model {model_id}")

# ❌ DON'T: Log sensitive data
logging.info(f"API key: {api_key}")
logging.info(f"User input: {user_prompt}")
```

---

## Incident Response

### If You Suspect Key Exposure
1. **Immediately rotate** all API keys
2. **Check API usage** for unauthorized calls
3. **Review recent commits** for accidental leaks
4. **Clean git history** with `git filter-branch` or `bfg`
5. **Force push** with caution (breaks clones)
6. **Notify users** if deployed publicly

### Checking for Leaks
```bash
# Search git history for API patterns
git log -S "ANTHROPIC_API_KEY" --all
git log -S "sk-" --all  # OpenRouter pattern
```

---

## Questions?

- Check `.env.example` for what fields are needed
- Review `council_v3_shared.py` for database setup
- Audit `council_v3_bridge.py` routing logic before deployment
- Open an issue if you find a security concern

**Remember: Your keys = Your account = Your responsibility**
