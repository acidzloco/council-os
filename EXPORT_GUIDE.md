# Export Guide — Save & Share Your Council Work

**Export everything your brothers learned and practiced.**

---

## What Can Be Exported

```
✓ Chat history (all conversations)
✓ Practice logs (training sessions)
✓ Brother upgrades (lessons learned)
✓ Brainstorm topics (ideas discussed)
✓ Complete database (soul_brain.db)
✓ Model registry (adopted models)
✓ Drawing board (PNG images)
```

---

## Export Methods

### **1. Export Chat History**

**Manual Export (Copy-Paste):**
```
1. Open http://localhost:5002/dojo
2. Click HISTORY tab
3. Select all text (Ctrl+A)
4. Copy (Ctrl+C)
5. Paste into file.txt
```

**API Export:**
```bash
# Get all chat history as JSON
curl http://localhost:5002/council/quickchat/history > chat_history.json

# In PowerShell:
Invoke-WebRequest -Uri "http://localhost:5002/council/quickchat/history" `
  -OutFile chat_history.json
```

---

### **2. Export Practice Logs**

**Location:**
```
C:\AI\idea\practice_session.log     (Current session)
C:\AI\idea\practice\shared\*.log    (Saved sessions)
```

**Backup:**
```powershell
# Copy all practice logs
Copy-Item -Path "C:\AI\idea\practice_session.log" `
          -Destination "C:\Backup\practice_$(Get-Date -Format 'yyyyMMdd').log"

Copy-Item -Path "C:\AI\idea\practice\shared\*" `
          -Destination "C:\Backup\practice_sessions\" -Recurse
```

---

### **3. Export Brother Upgrades & Lessons**

**Location:**
```
C:\AI\idea\upgrades\byte_upgrades.json
C:\AI\idea\upgrades\deepseek_upgrades.json
C:\AI\idea\upgrades\gemini_upgrades.json
C:\AI\idea\upgrades\advisor_upgrades.json
```

**View Upgrades:**
```bash
# Get all brothers' upgrade status
curl http://localhost:5002/api/upgrades/all

# Get specific brother
curl http://localhost:5002/api/upgrades/gemini/get
```

**Backup All:**
```powershell
# Backup entire upgrades folder
Copy-Item -Path "C:\AI\idea\upgrades" `
          -Destination "C:\Backup\upgrades_$(Get-Date -Format 'yyyyMMdd')" -Recurse
```

---

### **4. Export Complete Database (soul_brain.db)**

**Location:**
```
C:\Users\[USER]\.claude\projects\C--ai\memory\soul_brain.db
```

**Backup:**
```powershell
# Copy database file
Copy-Item -Path "C:\Users\$env:USERNAME\.claude\projects\C--ai\memory\soul_brain.db" `
          -Destination "C:\Backup\soul_brain_$(Get-Date -Format 'yyyyMMdd').db"
```

**Export as SQL:**
```bash
# On Windows (if sqlite3 installed):
sqlite3 C:\Users\[USER]\.claude\projects\C--ai\memory\soul_brain.db ".dump" > soul_brain_dump.sql

# Or via Python:
python -c "
import sqlite3
conn = sqlite3.connect(r'C:\Users\[USER]\.claude\projects\C--ai\memory\soul_brain.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\";')
for table in cursor.fetchall():
    print(f'Table: {table[0]}')
"
```

---

### **5. Export Drawing Board (PNG)**

**In Dojo:**
```
1. Click DRAWING BOARD tab
2. Draw your flowchart/diagram
3. Click "💾 SAVE PNG" button
4. Save to: C:\Downloads\drawing_[timestamp].png
```

**Batch Export (File system):**
```powershell
# Find all PNG exports
Get-ChildItem -Path "C:\Downloads" -Filter "drawing_*.png" | 
  Copy-Item -Destination "C:\Backup\drawings\"
```

---

### **6. Export Model Registry**

**API Export:**
```bash
# Get all registered models
curl http://localhost:5002/api/models/list > models_registry.json
```

**Manual View:**
```
1. DOJO → REGISTRY tab
2. See all adopted models
3. Copy model info
```

---

### **7. Full Council Backup**

**Create Complete Backup Script:**

```powershell
# backup_council.ps1

$BackupDir = "C:\Backups\Council_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $BackupDir | Out-Null

# 1. Database
Copy-Item -Path "$env:USERPROFILE\.claude\projects\C--ai\memory\soul_brain.db" `
          -Destination "$BackupDir\soul_brain.db" -ErrorAction SilentlyContinue

# 2. Upgrades
Copy-Item -Path "C:\AI\idea\upgrades" `
          -Destination "$BackupDir\upgrades" -Recurse -ErrorAction SilentlyContinue

# 3. Practice logs
Copy-Item -Path "C:\AI\idea\practice_session.log" `
          -Destination "$BackupDir\practice_session.log" -ErrorAction SilentlyContinue
Copy-Item -Path "C:\AI\idea\practice\shared" `
          -Destination "$BackupDir\practice_sessions" -Recurse -ErrorAction SilentlyContinue

# 4. Export chat history
$chat = Invoke-WebRequest -Uri "http://localhost:5002/council/quickchat/history" -UseBasicParsing
$chat.Content | Out-File "$BackupDir\chat_history.json" -Encoding UTF8

# 5. Export models
$models = Invoke-WebRequest -Uri "http://localhost:5002/api/models/list" -UseBasicParsing
$models.Content | Out-File "$BackupDir\models_registry.json" -Encoding UTF8

Write-Host "✓ Backup complete: $BackupDir"
```

**Run it:**
```powershell
. C:\backup_council.ps1
```

---

### **8. Export for Migration (Move to New PC)**

**What to move:**
```
1. soul_brain.db (all memories)
2. upgrades/ folder (brother improvements)
3. practice/ folder (training history)
4. .env file (API keys)
```

**Migration steps:**
```powershell
# On OLD PC:
Copy-Item -Path "C:\Users\$env:USERNAME\.claude\projects\C--ai\memory\soul_brain.db" `
          -Destination "C:\council_export\soul_brain.db"
Copy-Item -Path "C:\AI\idea\upgrades" -Destination "C:\council_export\upgrades" -Recurse
Copy-Item -Path "C:\AI\idea\practice" -Destination "C:\council_export\practice" -Recurse
Copy-Item -Path "C:\AI\council_v3\.env" -Destination "C:\council_export\.env"

# Transfer to NEW PC (USB/cloud/network)
# Then copy back to same locations

Write-Host "✓ Ready to move to new PC"
```

---

## Export Formats

### **JSON (Machine Readable)**

```bash
# Chat history
curl http://localhost:5002/council/quickchat/history | ConvertFrom-Json

# Models
curl http://localhost:5002/api/models/list | ConvertFrom-Json

# Brother upgrades
curl http://localhost:5002/api/upgrades/all | ConvertFrom-Json
```

### **CSV (Spreadsheet Ready)**

```powershell
# Export chat to CSV
$chat = Invoke-WebRequest "http://localhost:5002/council/quickchat/history" | ConvertFrom-Json
$chat.messages | Export-Csv -Path "chat_history.csv" -NoTypeInformation
```

### **SQL (Database Ready)**

```bash
# Dump entire database as SQL
sqlite3 soul_brain.db ".dump" > soul_brain.sql

# Can restore later:
sqlite3 new_database.db < soul_brain.sql
```

### **Text (Human Readable)**

```powershell
# Export chat as readable text
$chat = Invoke-WebRequest "http://localhost:5002/council/quickchat/history" | ConvertFrom-Json

$text = @()
foreach ($msg in $chat.messages) {
    $text += "$($msg.source.ToUpper()): $($msg.updated)`n$($msg.content)`n"
}
$text -join "`n`n" | Out-File "chat_readable.txt"
```

---

## Export Schedule (Automation)

**Daily Backup (Windows Task Scheduler):**

```powershell
# Create scheduled task
$trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\backup_council.ps1"
Register-ScheduledTask -TaskName "Council Daily Backup" -Trigger $trigger -Action $action -RunLevel Highest
```

**Weekly Full Export:**

```powershell
# Create weekly export
$Weekly = "C:\Backups\Weekly_$(Get-Date -Format 'yyyyMMdd')"
New-Item -ItemType Directory -Path $Weekly | Out-Null
# (Run full backup script above)
```

---

## What To Export When

| Situation | What to Export |
|---|---|
| **Before major update** | soul_brain.db + upgrades/ |
| **Share learning with team** | chat_history.json + upgrades/ |
| **Backup before new training** | practice/ + chat history |
| **Move to new PC** | Everything in council_export/ |
| **Document lessons learned** | upgrades/ + practice_logs |
| **Archive completed project** | All of above as ZIP |

---

## Share Your Council

**Export for others to learn from:**

```powershell
# Create shareable package
$share = New-Item -ItemType Directory -Path "C:\council_share"

# Include only non-sensitive data
Copy-Item -Path "C:\AI\idea\practice" -Destination "$share\practice" -Recurse
Copy-Item -Path "C:\AI\idea\upgrades" -Destination "$share\upgrades" -Recurse

# Exclude .env (API keys)
# Create README
"# Our Council's Learning

- Upgrades: What each brother learned
- Practice: Training sessions and results

Shared: $(Get-Date)" | Out-File "$share\README.txt"

# ZIP it
Compress-Archive -Path $share -DestinationPath "council_learnings.zip"

Write-Host "✓ Ready to share: council_learnings.zip"
```

---

## Restore from Export

**If you need to restore:**

```powershell
# Restore database
Copy-Item -Path "backup\soul_brain.db" `
          -Destination "$env:USERPROFILE\.claude\projects\C--ai\memory\soul_brain.db" -Force

# Restore upgrades
Copy-Item -Path "backup\upgrades\*" `
          -Destination "C:\AI\idea\upgrades\" -Recurse -Force

# Restart server
# All data is back
```

---

## Summary

**Export everything your council learned:**

```bash
# One-liner backup (PowerShell)
Copy-Item "$env:USERPROFILE\.claude\projects\C--ai\memory\soul_brain.db" "C:\Backup\" && 
Copy-Item "C:\AI\idea\upgrades" "C:\Backup\" -Recurse &&
Invoke-WebRequest "http://localhost:5002/council/quickchat/history" -OutFile "C:\Backup\chat.json"
```

**That's it. Your council's knowledge is saved.**

---

## File Locations Reference

```
Database:         C:\Users\[USER]\.claude\projects\C--ai\memory\soul_brain.db
Upgrades:         C:\AI\idea\upgrades\*.json
Practice logs:    C:\AI\idea\practice_session.log + shared\*.log
Models registry:  C:\AI\council_v3\models_api.py (data in DB)
Config:           C:\AI\council_v3\.env
Drawings:         Downloads\drawing_*.png
API keys:         .env file (KEEP SECURE)
```

---

**Keep your council's knowledge safe. Export regularly.**
