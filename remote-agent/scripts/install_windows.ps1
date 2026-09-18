$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python Launcher não encontrado. Instale Python 3.11, 3.12 ou 3.13."
}

py -3.13 -m venv .venv
if ($LASTEXITCODE -ne 0) { py -3.12 -m venv .venv }
if ($LASTEXITCODE -ne 0) { py -3.11 -m venv .venv }
if ($LASTEXITCODE -ne 0) { throw "Não foi possível criar o ambiente virtual." }

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Edite remote-agent\.env e troque AURION_API_TOKEN antes de iniciar."
}

Write-Host "Dependências instaladas. O serviço ainda não foi registrado para iniciar com o Windows."
Write-Host "Teste: .\.venv\Scripts\python.exe run.py"

