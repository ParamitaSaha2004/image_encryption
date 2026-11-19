@echo off
title SecurePix Frontend
echo Starting SecurePix Dev Server on port 5173...
cd /d %~dp0frontend
npm run dev
pause
