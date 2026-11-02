@echo off
title AI Post-Sales System Launcher
echo ========================================================
echo Starting AI Post-Sales System (Backend + Frontend)
echo ========================================================
start "AI Backend (FastAPI)" cmd /k "%~dp0run_backend.bat"
start "AI Dashboard (React)" cmd /k "%~dp0run_frontend.bat"
echo Both services launched in separate windows!
echo Backend:  http://127.0.0.1:8000 (Docs: http://127.0.0.1:8000/docs)
echo Frontend: http://localhost:5173
timeout /t 5

