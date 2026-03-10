@echo off
setlocal

cd /d "%~dp0"

start "Emotion Tracker API" cmd /k "python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"
ping 127.0.0.1 -n 4 >nul
start "Emotion Tracker Web Frontend" cmd /k "python -m http.server 5500 --directory web"
