@echo off
title COUNCIL OS v5 - THE DOJO
echo.
echo ========================================================
echo  COUNCIL OS v5 - Digital Symphony (The Dojo)
echo  Byte + DeepSeek + Gemini + Advisor
echo  Web Interface: http://localhost:5002
echo ========================================================
echo.

cd /d C:\AI\council_v3

:: Ensure Python uses UTF-8 for I/O
set PYTHONIOENCODING=utf-8

:: Ensure dependencies are present
if not exist .env (
    echo [!] Missing .env - run setup_wizard.py
    pause
    exit /b 1
)

:: Start the Bridge + Web Interface
echo [+] Initializing Symphony Web Engine...
python council_v3_bridge.py

pause
