@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Dependencies are missing. Run setup-windows.bat first.
  pause
  exit /b 1
)
if not exist "frontend\node_modules" (
  echo Frontend modules are missing. Run setup-windows.bat first.
  pause
  exit /b 1
)
start "PulseOps API" "%~dp0run-backend.bat"
start "PulseOps React" "%~dp0run-frontend.bat"
echo.
echo Backend:  http://127.0.0.1:8000/docs
echo Frontend: http://127.0.0.1:5173
echo.
echo Demo account: demo@pulseops.dev
 echo Demo password: Demo@12345
echo.
echo Close the two new terminal windows to stop the app.
exit /b 0
