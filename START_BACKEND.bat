@echo off
echo Starting Delhi Flood API Backend...
cd /d "%~dp0backend"
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
pause
