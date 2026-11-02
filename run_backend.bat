@echo off
title AI Post-Sales Feedback Intelligence Backend (FastAPI)
cd /d "%~dp0backend"
echo ========================================================
echo Starting AI Post-Sales Feedback Analysis & Failure Prediction API
echo Backend running on http://127.0.0.1:8000
echo Swagger API Docs: http://127.0.0.1:8000/docs
echo ========================================================
"C:\Users\severa\AppData\Local\Programs\Python\Python313\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause

