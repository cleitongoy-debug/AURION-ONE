@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
set "BASE=%~dp0"
set "ENGINE=%BASE%AURION_COLETOR.ps1"
if not exist "%ENGINE%" (
  echo FALTA AURION_COLETOR.ps1 na mesma pasta deste BAT.
  pause
  exit /b 2
)
if /i "%~1"=="--scan" goto scan
if /i "%~1"=="--selftest" goto selftest
:menu
cls
echo ================================================
echo AURION ONE - COLETOR LOCAL DE HISTORIA E PROVAS
echo ================================================
echo 1 - Varrer PC e discos externos (retomavel)
echo 2 - Adicionar link Drive / Git / Hug / outro
echo 3 - Conferir links cadastrados (sem baixar)
echo 4 - Abrir configuracao de perfis e limites
echo 5 - Abrir relatorios locais
echo 6 - Ativar ciclo automatico de 15 minutos
echo 7 - Desativar ciclo automatico
echo 0 - Sair
echo.
set /p "OP=Escolha: "
if "%OP%"=="1" goto scanmenu
if "%OP%"=="2" goto link
if "%OP%"=="3" goto links
if "%OP%"=="4" goto config
if "%OP%"=="5" goto report
if "%OP%"=="6" goto schedule
if "%OP%"=="7" goto unschedule
if "%OP%"=="0" exit /b 0
goto menu
:scanmenu
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ENGINE%" -Mode Scan
pause
goto menu
:scan
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ENGINE%" -Mode Scan
exit /b %errorlevel%
:selftest
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ENGINE%" -Mode Scan -TestRootOnly
exit /b %errorlevel%
:link
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ENGINE%" -Mode AddLink
pause
goto menu
:links
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ENGINE%" -Mode CheckLinks
pause
goto menu
:config
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ENGINE%" -Mode OpenConfig
goto menu
:report
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ENGINE%" -Mode OpenReport
goto menu
:schedule
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ENGINE%" -Mode Schedule
pause
goto menu
:unschedule
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ENGINE%" -Mode Unschedule
pause
goto menu
