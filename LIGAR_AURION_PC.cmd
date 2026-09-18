@echo off
setlocal
cd /d "%~dp0"
title AURION ONE - Inicializacao PC
where git >nul 2>&1
if errorlevel 1 (echo [ERRO] Git nao encontrado. & pause & exit /b 1)
echo [AURION] Conferindo alteracoes locais...
git status --short
echo [AURION] Atualizando sem descartar arquivos locais...
git pull --ff-only
if errorlevel 1 (echo [ERRO] Git pull falhou. Nada sera iniciado com codigo possivelmente antigo. & pause & exit /b 1)
echo [AURION] Verificando servidor local...
powershell.exe -NoProfile -Command "try { $r=Invoke-RestMethod 'http://127.0.0.1:8765/health' -TimeoutSec 3; if($r.status -eq 'online'){exit 0}else{exit 1} } catch {exit 1}"
if errorlevel 1 (
  echo [AURION] Iniciando servidor em janela minimizada. Nao feche essa janela enquanto estiver usando o servidor.
  start "AURION SERVER" /min cmd.exe /d /k "cd /d ""%~dp0"" && call START_AURION.cmd"
) else (echo [AURION] Servidor ja responde; sem duplicar.)
echo [AURION] Iniciando observador local GitHub/servicos...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0remote-agent\scripts\start_bridge.ps1"
if errorlevel 1 echo [AVISO] Observador nao iniciou; veja mensagem acima.
echo [AURION] Aguardando servidor ate 20 segundos...
powershell.exe -NoProfile -Command "$ok=$false; 1..10 | ForEach-Object { if(-not $ok){try{$r=Invoke-RestMethod 'http://127.0.0.1:8765/health' -TimeoutSec 1; $ok=($r.status -eq 'online')}catch{}; if(-not $ok){Start-Sleep -Seconds 2}} }; if($ok){Write-Host '[OK] Portal local: http://127.0.0.1:8765'}else{Write-Host '[PENDENTE] Servidor nao respondeu; consulte janela AURION SERVER.'}"
echo [AURION] Estado do observador (se disponivel):
if exist "%~dp0remote-agent\data\bridge_status.json" type "%~dp0remote-agent\data\bridge_status.json"
echo.
echo [AURION] Este comando nao instala APK, nao configura acesso remoto nem inicia automaticamente com Windows.
echo [AURION] Para atualizar o POCO, consulte GitHub Actions e instale apenas APK de build concluida, mantendo o app existente ate validar o novo.
pause
