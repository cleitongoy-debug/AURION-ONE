@echo off
setlocal
cd /d "%~dp0"
title AURION ONE - RECOMECO SEGURO
echo [AURION] Recomeço sem apagar modelos, drivers, ambientes ou configuracoes.
where git >nul 2>&1
if errorlevel 1 (echo [ERRO] Git nao encontrado. Nenhuma alteracao realizada. & pause & exit /b 1)
echo [AURION] Conferindo alteracoes locais rastreadas...
git diff --quiet
if errorlevel 1 (echo [ATENCAO] Existem alteracoes locais. Nao vou sobrescrever. & git status --short & pause & exit /b 2)
git diff --cached --quiet
if errorlevel 1 (echo [ATENCAO] Existem alteracoes preparadas. Nao vou sobrescrever. & git status --short & pause & exit /b 2)
echo [AURION] Atualizando sem forcar nem apagar arquivos locais...
git pull --ff-only
if errorlevel 1 (echo [ERRO] Atualizacao nao concluida. Nao inicio versao incerta. & pause & exit /b 3)
if not exist "%~dp0remote-agent\scripts\iniciar_sem_reinstalar.ps1" (echo [ERRO] Inicializador seguro ausente. & pause & exit /b 4)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0remote-agent\scripts\iniciar_sem_reinstalar.ps1"
echo.
echo [AURION] Diagnostico concluido. Nunca cole tokens, .env ou inventario privado no Git publico.
pause
