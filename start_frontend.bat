@echo off
title HICE Frontend Dev Server
echo Starting HICE React/Vite Dev Server on port 5173...
cd /d %~dp0frontend
npm run dev
pause
