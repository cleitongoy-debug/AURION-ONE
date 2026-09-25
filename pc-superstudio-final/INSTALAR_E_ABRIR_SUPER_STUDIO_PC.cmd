@echo off
setlocal EnableExtensions
title NOVO AURION FINAL PART - Super Studio PC v2.0
cd /d "%~dp0"

set "PAINEL_REAL=C:\Users\ADM_PESS\Desktop\painelseguro#1 - Copia"
if exist "%PAINEL_REAL%\ADAPTA.py" (
  set "AURION_PANEL_ROOT=%PAINEL_REAL%"
) else (
  set "AURION_PANEL_ROOT=%~dp0"
  echo [AVISO] Base real nao encontrada no caminho conhecido.
  echo [AVISO] O Studio abrira isolado e mostrara a base como nao verificada.
)

echo [AURION] Base selecionada: %AURION_PANEL_ROOT%
echo [AURION] ADAPTA.py e ADAPTA_BASE_TRAVADA.py nao serao alterados.

where py >nul 2>&1
if errorlevel 1 (
  echo [ERRO] Python Launcher "py" nao encontrado.
  echo Instale Python 3.11 ou 3.12 e marque "Add Python to PATH".
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [AURION] Criando ambiente isolado...
  py -3 -m venv .venv
  if errorlevel 1 goto :erro
)

echo [AURION] Instalando/confirmando somente dependencias do modulo isolado...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check --no-input -r requirements.txt
if errorlevel 1 goto :erro

if not exist "%AURION_PANEL_ROOT%\_aurion_superstudio\workspace" mkdir "%AURION_PANEL_ROOT%\_aurion_superstudio\workspace"
echo [AURION] Abrindo http://127.0.0.1:5060
start "" "http://127.0.0.1:5060"
".venv\Scripts\python.exe" -m aurion_superstudio.app
exit /b %errorlevel%

:erro
echo.
echo [ERRO] A inicializacao falhou. Nenhum arquivo do painel real foi substituido.
pause
exit /b 1
