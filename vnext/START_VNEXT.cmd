@echo off
setlocal
cd /d "%~dp0"
title AURION ONE vNext
echo [AURION] Iniciando servicos locais conhecidos, sem instalar ou atualizar...
start "AURION - servicos" /min powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_local.ps1"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%~dp0server.py"
) else (
  python "%~dp0server.py"
)
if errorlevel 1 (
  echo [AURION] Falha ao abrir. Verifique se Python 3 esta instalado e porta 8766 livre.
  pause
)
