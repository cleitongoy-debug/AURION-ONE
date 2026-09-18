$ErrorActionPreference = "Stop"
$AgentRoot = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent $AgentRoot
$VenvPython = Join-Path $AgentRoot ".venv\Scripts\python.exe"
Set-Location $AgentRoot

Write-Host "[AURION] Detectando Python..."
$Python = $null
$Known = @(
    (Join-Path $RepoRoot ".venv\Scripts\python.exe"),
    "C:\Python313\python.exe", "C:\Python312\python.exe", "C:\Python311\python.exe"
)
foreach ($Item in $Known) { if (Test-Path $Item) { $Python = $Item; break } }

if (-not $Python -and (Get-Command py -ErrorAction SilentlyContinue)) {
    foreach ($Version in @("3.13", "3.12", "3.11")) {
        $Found = cmd.exe /d /c "py -$Version -c `"import sys;print(sys.executable)`" 2>nul"
        if ($LASTEXITCODE -eq 0 -and $Found) { $Python = $Found.Trim(); break }
    }
}
if (-not $Python) {
    $Command = Get-Command python -ErrorAction SilentlyContinue
    if ($Command) { $Python = $Command.Source }
}
if (-not $Python) { throw "Python 3.11-3.13 nao encontrado." }

if (-not (Test-Path $VenvPython)) {
    Write-Host "[AURION] Criando ambiente isolado com $Python..."
    & $Python -m venv (Join-Path $AgentRoot ".venv")
}

Write-Host "[AURION] Sincronizando dependencias..."
& $VenvPython -m pip install --disable-pip-version-check -q -e "."

if (-not (Test-Path ".env")) {
    $Bytes = New-Object byte[] 32
    $Rng = New-Object Security.Cryptography.RNGCryptoServiceProvider
    $Rng.GetBytes($Bytes)
    $Rng.Dispose()
    $Token = [Convert]::ToHexString($Bytes).ToLowerInvariant()
    $Template = Get-Content ".env.example" -Raw
    $Template = $Template.Replace("troque-por-um-token-longo-e-aleatorio", $Token)
    Set-Content ".env" $Template -Encoding UTF8
}

try {
    $Tags = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 3
    $Candidates = @($Tags.models | Where-Object { $_.size -le 5905580032 } | Sort-Object size -Descending)
    if ($Candidates.Count -eq 0) { $Candidates = @($Tags.models | Sort-Object size) }
    if ($Candidates.Count -gt 0) {
        $Model = $Candidates[0].name
        $EnvText = Get-Content ".env" -Raw
        $EnvText = [regex]::Replace($EnvText, "(?m)^AURION_OLLAMA_MODEL=.*$", "AURION_OLLAMA_MODEL=$Model")
        Set-Content ".env" $EnvText -Encoding UTF8
        Write-Host "[AURION] Modelo local selecionado: $Model"
    }
} catch {
    Write-Host "[AURION] Ollama ainda nao respondeu. O portal abrira mesmo assim."
}

Write-Host "[AURION] Escaneando hardware, modelos e programas..."
& $VenvPython "scripts\scan_system.py"

Write-Host "[AURION] Abrindo portal..."
Start-Process "http://127.0.0.1:8765"
& $VenvPython "run.py"
