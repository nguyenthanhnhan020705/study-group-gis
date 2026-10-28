@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Missing .venv. Follow README setup instructions first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" "scripts\run_local.py" %*
if errorlevel 1 (
  echo Check .local-tests\local-server logs and README troubleshooting.
  pause
  exit /b 1
)
