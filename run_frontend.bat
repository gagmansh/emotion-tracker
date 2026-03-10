@echo off
setlocal

cd /d "%~dp0"
start "Emotion Tracker Web Frontend" cmd /k "python -m http.server 5500 --bind 127.0.0.1 --directory web"
