@echo off
echo Building Council OS brother models...

set OLLAMA=C:\Users\acidz\AppData\Local\Programs\Ollama\ollama.exe

echo [1/4] Byte (dolphin-llama3)...
%OLLAMA% create council-byte -f modelfiles\Modelfile.byte

echo [2/4] DeepSeek (dolphin-llama3)...
%OLLAMA% create council-deepseek -f modelfiles\Modelfile.deepseek

echo [3/4] Gemini (qwen3.5:4b)...
%OLLAMA% create council-gemini -f modelfiles\Modelfile.gemini

echo [4/4] Advisor (qwen3.5:9b)...
%OLLAMA% create council-advisor -f modelfiles\Modelfile.advisor

echo.
echo Done. Run: ollama list
%OLLAMA% list
pause
