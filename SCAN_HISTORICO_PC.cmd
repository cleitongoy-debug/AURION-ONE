@echo off
setlocal
cd /d "%~dp0"
title AURION ONE - Historico PC (somente leitura)
echo [AURION] Scanner historico local: metadados agregados, sem ler conteudo de arquivos.
echo [AURION] Examina unidades presentes com limites de 250000 arquivos ou 120 segundos.
echo [AURION] Exclui diretorios de sistema e dados de aplicativos; pode terminar parcial.
if not exist "remote-agent\scripts\scan_historico_pc.py" (
  echo [ERRO] Arquivo do scanner ausente. Atualize o Git e tente novamente.
  pause
  exit /b 1
)
if exist "remote-agent\.venv\Scripts\python.exe" (
  "remote-agent\.venv\Scripts\python.exe" "remote-agent\scripts\scan_historico_pc.py"
) else (
  where py >nul 2>&1
  if not errorlevel 1 (
    py -3 "remote-agent\scripts\scan_historico_pc.py"
  ) else (
    where python >nul 2>&1
    if errorlevel 1 (echo [ERRO] Python nao encontrado. & pause & exit /b 1)
    python "remote-agent\scripts\scan_historico_pc.py"
  )
)
if errorlevel 1 (echo [ERRO] Scan nao concluido. Consulte a mensagem acima. & pause & exit /b 1)
echo [AURION] Resultado privado: remote-agent\data\history_scan.json
echo [AURION] Para carregar no app: PC online ^> AURION ^> Historia ^> Consultar resumo do PC.
echo [AURION] Nao publica dados no GitHub, nao instala drivers e nao inicia servicos.
pause
