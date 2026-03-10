@echo off
setlocal

cd /d "%~dp0"

start "Emotion Tracker" cmd /k "python -m streamlit run app.py"
ping 127.0.0.1 -n 4 >nul
start "" http://localhost:8501
