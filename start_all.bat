@echo off
title HICE - Hybrid Image Security Platform
echo ========================================================
echo Starting HICE Platform (Backend + Frontend)
echo ========================================================
start "HICE Backend (Port 8000)" cmd /k "cd /d %~dp0backend && python run.py"
start "HICE Frontend (Port 5173)" cmd /k "cd /d %~dp0frontend && npm run dev"
echo.
echo Backend API available at: http://localhost:8000/docs
echo Frontend Web Dashboard:   http://localhost:5173
echo.
echo Default Demo Logins:
echo   Username: dr_alice_radiology
echo   Password: Password123!
echo.
echo   Username: dr_bob_oncology
echo   Password: Password123!
echo.
echo   Username: superadmin
echo   Password: Password123!
echo ========================================================
pause
