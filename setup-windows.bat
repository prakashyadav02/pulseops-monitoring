@echo off
setlocal
cd /d "%~dp0"
echo.
echo  ===============================================
echo          PulseOps - Windows Setup
 echo ===============================================
echo.
where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python was not found. Install Python 3.11+ and add it to PATH.
  echo https://www.python.org/downloads/
  pause
  exit /b 1
)
where npm >nul 2>&1
if errorlevel 1 (
  echo ERROR: npm was not found. Install Node.js 22 LTS.
  echo https://nodejs.org/
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo [1/4] Creating Python virtual environment...
  python -m venv .venv
  if errorlevel 1 goto failed
)
echo [2/4] Installing backend Python dependencies...
".venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
if errorlevel 1 goto failed
if not exist "backend\.env" copy /Y "backend\.env.example" "backend\.env" >nul
if not exist "frontend\.env" copy /Y "frontend\.env.example" "frontend\.env" >nul
echo [3/4] Installing React dependencies...
pushd frontend
call npm install
if errorlevel 1 (
  popd
  goto failed
)
popd
echo [4/4] Opening backend and frontend terminals...
call run-windows.bat
exit /b 0
:failed
echo.
echo Setup failed. Read README.md - Troubleshooting.
pause
exit /b 1
