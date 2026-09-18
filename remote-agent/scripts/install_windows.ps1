$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python Launcher não encontrado. Instale Python 3.11, 3.12 ou 3.13."
}

$Created = $false
foreach ($Version in @("3.13", "3.12", "3.11")) {
    py "-$Version" -m venv .venv 2>$null
    if ($LASTEXITCODE -eq 0) {
        $Created = $true
        Write-Host "Ambiente criado com Python $Version."
        break
    }
}
if (-not $Created) {
    throw "Python 3.11, 3.12 ou 3.13 não encontrado. Execute: py -0p"
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Falha ao atualizar pip." }

& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar dependências." }

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Arquivo .env criado. Troque AURION_API_TOKEN antes de iniciar."
}

Write-Host ""
Write-Host "Dependências instaladas em $Root."
Write-Host "Próximo comando: .\.venv\Scripts\python.exe run.py"
