@echo off
echo ============================================
echo   STARTING DELHI FLOOD SYSTEM
echo ============================================
echo.
echo Starting Backend on port 8000...
echo.
cd /d "%~dp0"
start "Delhi Flood Backend" cmd /k "python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000"

echo Waiting 10 seconds for backend to start...
timeout /t 10 /nobreak >nul

echo.
echo Starting Frontend on port 3000...
echo.
start "Delhi Flood Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ============================================
echo   SYSTEM STARTING!
echo ============================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Wait 15 seconds, then open:
echo http://localhost:3000
echo.
echo Press any key to continue...
pause >nul
