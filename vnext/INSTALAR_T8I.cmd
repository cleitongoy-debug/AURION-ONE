@echo off
setlocal
cd /d "%~dp0.."
echo ============================================================
echo AURION ONE - FERRAMENTAS T8i / CR3
echo ============================================================
if not exist ".venv_t8i\Scripts\python.exe" (
  echo [1/4] Criando ambiente isolado .venv_t8i...
  py -3 -m venv .venv_t8i 2>nul || python -m venv .venv_t8i
)
if not exist ".venv_t8i\Scripts\python.exe" (
  echo ERRO: nao foi possivel criar .venv_t8i
  pause
  exit /b 1
)
echo [2/4] Atualizando pip...
".venv_t8i\Scripts\python.exe" -m pip install --upgrade pip
echo [3/4] Instalando dependencias RAW...
".venv_t8i\Scripts\python.exe" -m pip install -r "vnext\t8i_requirements.txt"
echo [4/4] Testando...
".venv_t8i\Scripts\python.exe" -c "import rawpy, PIL, numpy, exifread; print('T8i tools OK | rawpy',rawpy.__version__,'| Pillow',PIL.__version__)"
echo.
echo Concluido. Nenhum RAW foi alterado.
pause
