@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
title AURION ONE - Inicializador seguro
color 0E

rem Coloque este BAT junto ao painel. Nao copie chaves para o BAT nem para Git.
set "BASE=%~dp0"
set "LOGDIR=%BASE%_aurion_logs"
set "STAMP=%DATE:/=-%_%TIME::=-%"
set "STAMP=%STAMP: =0%"
set "LOG=%LOGDIR%\inicializacao_%STAMP%.log"
if not exist "%LOGDIR%" mkdir "%LOGDIR%" 2>nul
if not exist "%LOGDIR%" (
  echo [ERRO] Sem permissao para gravar em "%BASE%".
  pause
  exit /b 2
)

if /i "%~1"=="--selftest" goto selftest
if /i "%~1"=="--diagnostico" goto diagnostico

call :note "Inicio em %BASE%"
echo.
echo AURION ONE - INICIALIZACAO SEGURA
echo Base: %BASE%
echo Registro: %LOG%
echo.
echo [1/5] Configuracao existente
if exist "%BASE%config\aurion_config.json" (
  call :note "Config existente preservada. Nenhuma chave lida ou copiada."
) else (
  call :note "Config nao encontrada. Cadastre chaves somente no cofre/config local do painel."
)

echo [2/5] Coleta local
if exist "%BASE%AURION_COLETOR.bat" (
  start "AURION Coletor" /min "%BASE%AURION_COLETOR.bat" --scan
  if errorlevel 1 (call :note "Falha ao abrir coletor.") else (call :note "Coletor iniciado em paralelo; consulte AURION_COLETA para resultado.")
) else (
  call :note "Coletor ausente; painel pode iniciar sem ele."
)

echo [3/5] Ollama / ComfyUI / Open WebUI
call :health "http://127.0.0.1:11434/api/tags" OLLAMA_OK
if not defined OLLAMA_OK (
  set "OLLAMA_EXE="
  for %%F in ("%LOCALAPPDATA%\Programs\Ollama\ollama.exe" "C:\Program Files\Ollama\ollama.exe") do if exist "%%~F" set "OLLAMA_EXE=%%~F"
  if not defined OLLAMA_EXE for /f "delims=" %%F in ('where ollama.exe 2^>nul') do if not defined OLLAMA_EXE set "OLLAMA_EXE=%%F"
  if defined OLLAMA_EXE (
    start "AURION Ollama" /min "!OLLAMA_EXE!" serve
    call :note "Ollama acionado; aguardando resposta."
  ) else (call :note "Ollama nao localizado; sem instalacao automatica.")
) else (call :note "Ollama responde na porta 11434.")

call :health "http://127.0.0.1:8188/system_stats" COMFY_OK
if not defined COMFY_OK (
  set "COMFY_MAIN="
  if defined AURION_COMFY_MAIN if exist "%AURION_COMFY_MAIN%" set "COMFY_MAIN=%AURION_COMFY_MAIN%"
  if not defined COMFY_MAIN for %%D in (C D E F G H I) do (
    if exist "%%D:\COMFYUI\ComfyUI_windows_portable\ComfyUI\main.py" set "COMFY_MAIN=%%D:\COMFYUI\ComfyUI_windows_portable\ComfyUI\main.py"
    if exist "%%D:\ComfyUI\ComfyUI_windows_portable\ComfyUI\main.py" set "COMFY_MAIN=%%D:\ComfyUI\ComfyUI_windows_portable\ComfyUI\main.py"
    if exist "%%D:\ComfyUI\main.py" set "COMFY_MAIN=%%D:\ComfyUI\main.py"
  )
  if defined COMFY_MAIN (
    for %%F in ("!COMFY_MAIN!") do set "COMFY_DIR=%%~dpF"
    set "COMFY_PY="
    if exist "!COMFY_DIR!..\python_embeded\python.exe" set "COMFY_PY=!COMFY_DIR!..\python_embeded\python.exe"
    if not defined COMFY_PY if exist "!COMFY_DIR!..\python_embedded\python.exe" set "COMFY_PY=!COMFY_DIR!..\python_embedded\python.exe"
    if not defined COMFY_PY for /f "delims=" %%F in ('where python.exe 2^>nul') do if not defined COMFY_PY set "COMFY_PY=%%F"
    if defined COMFY_PY (
      start "AURION ComfyUI" /min /D "!COMFY_DIR!" "!COMFY_PY!" "!COMFY_MAIN!" --listen 127.0.0.1 --port 8188
      call :note "ComfyUI acionado em !COMFY_MAIN!."
    ) else (call :note "ComfyUI localizado, mas Python nao encontrado.")
  ) else (call :note "ComfyUI nao localizado; configure AURION_COMFY_MAIN com caminho de main.py.")
) else (call :note "ComfyUI responde na porta 8188.")

call :health "http://127.0.0.1:8080" WEBUI_OK
if not defined WEBUI_OK (
  set "WEBUI_EXE="
  for /f "delims=" %%F in ('where open-webui.exe 2^>nul') do if not defined WEBUI_EXE set "WEBUI_EXE=%%F"
  if defined WEBUI_EXE (
    start "AURION Open WebUI" /min "!WEBUI_EXE!" serve
    call :note "Open WebUI acionado."
  ) else (call :note "Open WebUI nao localizado; sem instalacao automatica.")
) else (call :note "Open WebUI responde na porta 8080.")

echo [4/5] POCO / ADB
set "ADB_EXE="
for %%F in ("%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe" "C:\Android\Sdk\platform-tools\adb.exe") do if exist "%%~F" set "ADB_EXE=%%~F"
if not defined ADB_EXE for /f "delims=" %%F in ('where adb.exe 2^>nul') do if not defined ADB_EXE set "ADB_EXE=%%F"
if defined ADB_EXE (
  "!ADB_EXE!" devices -l
  call :note "ADB consultado. Nenhum APK instalado automaticamente."
) else (call :note "ADB nao localizado; painel continua.")
if exist "%BASE%AURION-ONE-POCO.apk" call :note "APK local encontrado; confira versao e assinatura antes de instalar."

echo [5/5] Painel
call :health "http://127.0.0.1:5000" PANEL_OK
if not defined PANEL_OK call :health "http://127.0.0.1:5057" PANEL_OK
if defined PANEL_OK (
  call :note "Painel ja responde em 5000 ou 5057; nenhuma segunda instancia aberta."
) else (
  set "PANEL="
  for %%F in ("%BASE%FUNCIONANDO.py" "%BASE%2027_FUNCIONANDO.py" "%BASE%ADAPTA.py") do if not defined PANEL if exist "%%~F" set "PANEL=%%~F"
  if defined PANEL (
    set "PY_EXE="
    for /f "delims=" %%F in ('where python.exe 2^>nul') do if not defined PY_EXE set "PY_EXE=%%F"
    if not defined PY_EXE if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    if defined PY_EXE (
      call :note "Painel escolhido: !PANEL!"
      echo Uma janela separada mostrara erros do Python sem fechar imediatamente.
      start "AURION Painel - diagnostico" /D "%BASE%" "%ComSpec%" /k ""!PY_EXE!" "!PANEL!""
    ) else (call :note "Python nao localizado; painel nao iniciado.")
  ) else (call :note "Nenhum FUNCIONANDO.py, 2027_FUNCIONANDO.py ou ADAPTA.py nesta base.")
)
echo.
echo Concluido. Este BAT nao instala APK nem baixa executaveis desconhecidos.
echo Registro local: %LOG%
echo Se a janela do painel mostrar erro, copie somente o erro; o BAT permanecera aqui.
pause
exit /b 0

:health
set "%~2="
where curl.exe >nul 2>&1
if errorlevel 1 exit /b 1
curl.exe -sS -f --max-time 2 -o NUL "%~1" >nul 2>&1
if not errorlevel 1 set "%~2=1"
exit /b 0

:note
echo %~1
>> "%LOG%" echo %DATE% %TIME%  %~1
exit /b 0

:diagnostico
echo Base: %BASE%
echo Registro: %LOG%
where python.exe
where curl.exe
where adb.exe
pause
exit /b 0

:selftest
if not "%BASE:~0,3%"=="C:\" if not exist "%BASE%" exit /b 3
if not exist "%~f0" exit /b 4
call :note "Autoteste do BAT na pasta %BASE%: OK"
exit /b 0
