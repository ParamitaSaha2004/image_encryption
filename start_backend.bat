@echo off
title HICE Backend API
echo Starting HICE FastAPI Backend Server on port 8000...
cd /d %~dp0backend
python run.py
pause
