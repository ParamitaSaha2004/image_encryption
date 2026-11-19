@echo off
title SecurePix
echo ========================================================
echo Starting SecurePix (Backend + Frontend)
echo ========================================================
start "SecurePix Backend (Port 8000)" cmd /k "cd /d %~dp0backend && (if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat) && python run.py"
start "SecurePix Frontend (Port 5173)" cmd /k "cd /d %~dp0frontend && npm run dev"
echo.
echo Backend API available at: http://localhost:8000/docs
echo Frontend Web Dashboard:   http://localhost:5173
echo.
echo Default Demo Logins:
echo   Username: dr_alice_radiology  (Password: Password123!)
echo   Username: dr_bob_oncology     (Password: Password123!)
echo   Username: sec_admin           (Password: SecAdmin#2026!)
echo   Username: superadmin          (Password: Password123!)
echo ========================================================
pause
