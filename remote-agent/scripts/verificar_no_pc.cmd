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
pushd "%ROOT%" || exit /b 4
"%PY%" -c "import aurion_remote.app; print('IMPORT_OK')" 2>nul
if errorlevel 1 (
  echo ERRO: backend nao importa. Consulte as dependencias locais antes de iniciar.
  popd
  exit /b 4
)
"%PY%" -c "import json,urllib.request; u=urllib.request.urlopen('http://127.0.0.1:8765/health',timeout=5); d=json.load(u); assert u.status==200 and d.get('service')=='aurion-home-node' and d.get('status')=='online'; print('AURION /health HTTP 200; identificacao e status conferidos')"
if errorlevel 1 (
  echo ERRO: API local nao respondeu com JSON /health esperado. Este script NAO inicia outra instancia automaticamente.
  popd
  exit /b 5
)
popd
echo ATENCAO: health nao comprova autenticacao, acesso do POCO ou ComfyUI.
exit /b 0
