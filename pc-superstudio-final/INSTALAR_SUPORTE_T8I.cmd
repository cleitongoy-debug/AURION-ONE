@echo off
setlocal
title AURION ONE - Suporte Canon T8i
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [ERRO] Execute primeiro INSTALAR_E_ABRIR_SUPER_STUDIO_PC.cmd.
  pause
  exit /b 1
)
echo [AURION] Instalando rawpy/LibRaw, NumPy, imageio e tifffile no ambiente isolado...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check --no-input -r requirements-t8i.txt
if errorlevel 1 (
  echo [ERRO] Suporte T8i nao foi instalado. O painel principal permanece intacto.
) else (
  echo [OK] Suporte T8i instalado no modulo Super Studio.
)
pause

