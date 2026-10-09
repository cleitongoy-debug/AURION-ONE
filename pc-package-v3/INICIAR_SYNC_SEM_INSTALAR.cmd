@echo off
setlocal
chcp 65001 >nul
title AURION ONE Super Studio - SYNC POCO PC sem instalar
cd /d "%~dp0"
echo Verificando Python e Flask ja instalados...
where python >nul 2>nul
if errorlevel 1 (
  echo [BLOQUEADO] Python nao encontrado. Nada foi instalado.
  pause
  exit /b 2
)
python -c "import flask; print('Flask disponivel')" 
if errorlevel 1 (
  echo [BLOQUEADO] Flask ausente. Este modo NAO instala dependencias.
  echo Use seu Super Studio PC ja existente ou configure o ambiente separado.
  pause
  exit /b 3
)
set "AURION_PANEL_ROOT=%~dp0"
set "AURION_BIND_HOST=127.0.0.1"
set "AURION_STUDIO_PORT=5060"
echo Abrindo Super Studio somente na porta local 5060...
echo No PC acesse http://127.0.0.1:5060
python -m aurion_superstudio.app
echo Servidor finalizado; nenhum programa instalado.
pause
endlocal
