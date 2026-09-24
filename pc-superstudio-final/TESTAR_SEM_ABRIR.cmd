@echo off
setlocal
title AURION ONE - Testes Super Studio
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check --no-input -r requirements.txt
)
set "AURION_PANEL_ROOT=%TEMP%\AURION_SUPERSTUDIO_TEST"
".venv\Scripts\python.exe" -m unittest discover -s tests -v
pause

