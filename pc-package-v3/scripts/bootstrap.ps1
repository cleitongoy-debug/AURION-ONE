$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$Root = Split-Path -Parent $PSScriptRoot
$Logs = Join-Path $Root "logs"
New-Item -ItemType Directory -Force $Logs | Out-Null
$Log = Join-Path $Logs "startup.log"
function Say([string]$Text) { Write-Host $Text; Add-Content $Log "$(Get-Date -Format o) $Text" -Encoding UTF8 }
function FindPython {
  foreach ($p in @("$Root\.venv\Scripts\python.exe", "C:\Python313\python.exe", "C:\Python312\python.exe", "C:\Python311\python.exe")) { if (Test-Path $p) { return $p } }
  if (Get-Command py -ErrorAction SilentlyContinue) { foreach ($v in @("3.13","3.12","3.11")) { $x = cmd /d /c "py -$v -c `"import sys;print(sys.executable)`" 2>nul"; if ($LASTEXITCODE -eq 0 -and $x) { return $x.Trim() } } }
  $x = Get-Command python -ErrorAction SilentlyContinue; if ($x -and $x.Source -notlike "*WindowsApps*") { return $x.Source }
  return $null
}
try {
  Set-Location $Root
  Say "[AURION] Verificando o PC..."
  $Python = FindPython
  if (-not $Python -and (Get-Command winget -ErrorAction SilentlyContinue)) {
    Say "[AURION] Instalando Python 3.12..."
    winget install --id Python.Python.3.12 -e --silent --accept-source-agreements --accept-package-agreements
    $Python = FindPython
  }
  if (-not $Python) { throw "Python 3.11 a 3.13 não foi encontrado. Instale Python 3.12 e execute novamente." }
  $Venv = Join-Path $Root ".venv\Scripts\python.exe"
  if (-not (Test-Path $Venv)) { Say "[AURION] Criando ambiente isolado..."; & $Python -m venv (Join-Path $Root ".venv") }
  Say "[AURION] Instalando dependências..."
  & $Venv -m pip install --disable-pip-version-check --no-input -r requirements.txt
  if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar dependências (código $LASTEXITCODE)." }
  Say "[AURION] Executando apenas os testes desta versão..."
  # PowerShell 5 transforma stderr de programas nativos em NativeCommandError
  # quando ErrorActionPreference=Stop. unittest usa stderr até quando passa.
  $PreviousPreference = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  & $Venv -m unittest discover -s (Join-Path $Root "tests") -p "test_superstudio.py" -v 2>&1 | Tee-Object -FilePath $Log -Append
  $TestExit = $LASTEXITCODE
  $ErrorActionPreference = $PreviousPreference
  if ($TestExit -ne 0) { throw "Os testes internos desta versão falharam (código $TestExit)." }
  $env:AURION_PANEL_ROOT = $Root
  $env:AURION_BIND_HOST = "0.0.0.0"
  Say "[AURION] Scan, aquecimento e abertura do painel..."
  & $Venv AURION_PREVOO.py 2>&1 | Tee-Object -FilePath $Log -Append
  exit $LASTEXITCODE
} catch {
  $Detail = $_ | Out-String
  Add-Content (Join-Path $Logs "aurion-errors.log") "$(Get-Date -Format o)`r`n$Detail" -Encoding UTF8
  Write-Host "[ERRO] $Detail" -ForegroundColor Red
  Write-Host "Diagnóstico: $Logs\aurion-errors.log"
  exit 1
}
