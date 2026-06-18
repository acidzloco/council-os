@echo off
title COUNCIL OS v3 — THE OG COUNCIL
echo.
echo ========================================================
echo  COUNCIL OS v3 — Native APIs
echo  Byte (Anthropic) + DeepSeek (native) + Gemini (Google)
echo  Bridge: port 5002   UI: PyQt6
echo ========================================================
echo.

cd /d C:\AI\council_v3

:: First-run check — run wizard if no .env exists
if not exist .env (
    echo [!] No .env found. Running setup wizard first...
    echo.
    python setup_wizard.py
    if errorlevel 1 (
        echo [!] Setup failed. Fix the errors above and try again.
        pause
        exit /b 1
    )
    echo.
)

:: Start bridge in background
start "Council v3 Bridge" cmd /k "cd /d C:\AI\council_v3 && python council_v3_bridge.py"

:: Wait for bridge to come up
timeout /t 3 /nobreak > nul

:: Start UI
python council_v3_qt.py

pause
