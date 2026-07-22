@echo off
REM ── Industrial Knowledge Intelligence — one-command launcher (Windows) ──
REM Runs through cmd.exe, so the PowerShell script-execution policy that
REM blocks npm.ps1 never applies here.
cd /d "%~dp0"

echo Starting BACKEND (FastAPI + 9 agents) on http://127.0.0.1:8000 ...
echo   (first boot computes document embeddings, ~10-20s)
start "IKI backend" cmd /k python -m uvicorn backend.app:app --port 8000

echo Starting FRONTEND (Industrial HMI) on http://localhost:3000 ...
start "IKI frontend" cmd /k "cd /d "%~dp0frontend" && npm.cmd run dev"

echo.
echo Two windows opened. When the frontend says "Ready", open:
echo   http://localhost:3000
echo.
pause
