@echo off
echo ============================================
echo   RESTARTING FRONTEND (localhost:3000)
echo ============================================
echo.
echo Step 1: Finding and stopping old frontend process...
echo.

REM Find process on port 3000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    echo Stopping process %%a...
    taskkill /F /PID %%a 2>nul
)

timeout /t 2 /nobreak >nul

echo.
echo Step 2: Starting new frontend...
echo.
cd /d "%~dp0"
start cmd /k "cd frontend && npm run dev"

echo.
echo ============================================
echo   Frontend restarting in new window...
echo   Wait 10 seconds, then visit:
echo   http://localhost:3000
echo ============================================
echo.
pause
