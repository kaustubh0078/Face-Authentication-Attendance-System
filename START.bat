@echo off
echo ================================================
echo   Face Authentication Attendance System
echo ================================================
echo.

:: Start Flask API in background
echo Starting Flask API server...
start "Flask API" cmd /k "cd /d "%~dp0" && python api.py"

:: Wait 2 seconds for Flask to start
timeout /t 2 /nobreak > nul

:: Start React Frontend
echo Starting React Frontend...
cd /d "%~dp0frontend"
start "React Frontend" cmd /k "npm run dev"

:: Wait 2 seconds
timeout /t 2 /nobreak > nul

:: Open browser
echo Opening browser...
start http://localhost:3000

echo.
echo ================================================
echo   Both servers are now running!
echo   - Flask API: http://localhost:5000
echo   - React App: http://localhost:3000
echo ================================================
echo.
echo Close this window when done.
pause
