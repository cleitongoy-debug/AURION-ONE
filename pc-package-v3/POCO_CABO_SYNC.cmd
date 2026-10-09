@echo off
setlocal
chcp 65001 >nul
title AURION ONE - PREPARAR USB POCO / PC
set "ADB=%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"
if not exist "%ADB%" (
  for /f "delims=" %%I in ('where adb 2^>nul') do if not exist "%ADB%" set "ADB=%%I"
)
if not exist "%ADB%" (
  echo [BLOQUEADO] ADB nao encontrado. Nenhuma instalacao foi executada.
  echo Instale/configure Android Platform Tools manualmente e tente novamente.
  pause
  exit /b 2
)
echo [1/3] Verificando POCO via USB...
"%ADB%" -d get-state
if errorlevel 1 (
  echo [BLOQUEADO] Conecte POCO e autorize a depuracao USB na tela do aparelho.
  pause
  exit /b 3
)
echo [2/3] Ligando portas privadas 5060-5069 do Super Studio...
for /L %%P in (5060,1,5069) do (
  "%ADB%" -d reverse tcp:%%P tcp:%%P
  if errorlevel 1 echo [AVISO] Reverse %%P indisponivel.
)
echo [3/3] Ligando porta do painel V14 sem iniciar o painel...
"%ADB%" -d reverse tcp:5058 tcp:5058
if errorlevel 1 echo [AVISO] Reverse 5058 nao ficou disponivel. Sync 5060 continua independente.
echo.
echo TUNEIS ATIVOS:
"%ADB%" -d reverse --list
echo.
echo Abra PC Super Studio na porta 5060 (se estiver iniciado).
echo No AURION do POCO: CONEXOES ^> SYNC POCO ^<^> PC
echo URL inicial: http://127.0.0.1:5060 (se Super Studio usar 5061-5069, ajuste URL)
echo Cole o token exibido LOCALMENTE no painel PC. Nao mande o token pelo chat.
echo Toque em SYNC POCO ^<^> PC - AGORA e confira recibos em ambos.
echo.
echo NENHUM APK INSTALADO. NENHUM EXE/BAT DA BASE EXECUTADO PELO SCRIPT.
pause
endlocal
