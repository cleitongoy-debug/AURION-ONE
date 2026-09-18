@echo off
setlocal
cd /d "%~dp0"
title AURION ONE
echo [AURION] Atualizando projeto...
git pull --ff-only origin feature/remote-agent-foundation
if errorlevel 1 echo [AURION] Sem atualizacao. Continuando com a copia local.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0remote-agent\scripts\bootstrap_windows.ps1"
if errorlevel 1 pause

