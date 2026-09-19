@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem AURION ONE: execute in Windows CMD. No scan, git pull, process termination or Tailscale changes.
set "ROOT=%~dp0..\.."
if not exist "%ROOT%\run.py" (
  echo ERRO: run.py nao encontrado em "%ROOT%".
  exit /b 2
)
if not exist "%ROOT%\.venv\Scripts\python.exe" (
  echo ERRO: Python do ambiente virtual nao encontrado. Nenhuma instalacao automatica sera feita.
  exit /b 3
)
set "PY=%ROOT%\.venv\Scripts\python.exe"
"%PY%" -c "import aurion_remote.app; print('IMPORT_OK')" 2>nul
if errorlevel 1 (
  echo ERRO: backend nao importa. Consulte as dependencias locais antes de iniciar.
  exit /b 4
)
curl.exe --fail --silent --show-error --max-time 5 --output NUL --write-out "AURION /health HTTP %%{http_code}\n" http://127.0.0.1:8765/health
if errorlevel 1 (
  echo ERRO: API local nao respondeu com HTTP 2xx. Este script NAO inicia outra instancia automaticamente.
  exit /b 5
)
echo ATENCAO: HTTP 2xx nao comprova autenticacao, acesso do POCO ou ComfyUI.
exit /b 0
