@echo off
title COUNCIL OS v3 - DOJO (Web Interface)
echo.
echo ========================================================
echo  COUNCIL OS v3 - DOJO TRAINING SYSTEM
echo  Models Family - Practice - Learning - No Cutoffs
echo  WebBase: http://localhost:5002/dojo
echo ========================================================
echo.

cd /d C:\AI\council_v3

:: Ensure Python uses UTF-8 for I/O
set PYTHONIOENCODING=utf-8

:: First-run check
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
echo [*] Starting Council OS v3 Bridge on port 5002...
start "Council Bridge" cmd /k "cd /d C:\AI\council_v3 && set PYTHONIOENCODING=utf-8 && python council_v3_bridge.py"

:: Wait for bridge to start
timeout /t 3 /nobreak > nul

:: Open Dojo in default browser
echo [*] Opening Dojo in browser...
start http://localhost:5002/dojo

echo.
echo ========================================================
echo [OK] Bridge running on http://localhost:5002
echo [OK] Dojo UI opening in browser...
echo [OK] Terminal shows bridge logs (Ctrl+C to stop)
echo ========================================================
echo.

pause
