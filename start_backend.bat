@echo off
title SecurePix Backend API
echo Starting SecurePix FastAPI Backend Server on port 8000...
cd /d %~dp0backend
if exist ".venv\Scripts\python.exe" (
    call .venv\Scripts\activate.bat
    python run.py
) else (
    python run.py
)
pause
