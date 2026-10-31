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
if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar as dependencias do AURION." }

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

$EnvMigration = Get-Content ".env" -Raw
$EnvMigration = $EnvMigration.Replace("Biblia_da_Inteligencia_Artificial_AURION_ONE.txt", "Biblia_da_Inteligencia_Artificial_AURION_ONE.docx")
Set-Content ".env" $EnvMigration -Encoding UTF8

$CurrentTokenLine = Get-Content ".env" | Where-Object { $_ -like "AURION_API_TOKEN=*" } | Select-Object -First 1
$CurrentToken = if ($CurrentTokenLine) { $CurrentTokenLine.Substring("AURION_API_TOKEN=".Length).Trim() } else { "" }
if ($CurrentToken.Length -lt 32 -or $CurrentToken -like "troque-por-*") {
    $Bytes = New-Object byte[] 32
    $Rng = New-Object Security.Cryptography.RNGCryptoServiceProvider
    $Rng.GetBytes($Bytes)
    $Rng.Dispose()
    $Token = [BitConverter]::ToString($Bytes).Replace("-", "").ToLowerInvariant()
    $EnvText = Get-Content ".env" -Raw
    if ($CurrentTokenLine) {
        $EnvText = [regex]::Replace($EnvText, "(?m)^AURION_API_TOKEN=.*$", "AURION_API_TOKEN=$Token")
    } else {
        $EnvText = "AURION_API_TOKEN=$Token`r`n" + $EnvText
    }
    Set-Content ".env" $EnvText -Encoding UTF8
}

$OllamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
$OllamaExe = if ($OllamaCommand) { $OllamaCommand.Source } else { Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe" }
try {
    Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 2 | Out-Null
} catch {
    if (Test-Path $OllamaExe) {
        Write-Host "[AURION] Iniciando Ollama local..."
        Start-Process -FilePath $OllamaExe -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 4
    }
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

$TokenLine = Get-Content ".env" | Where-Object { $_ -like "AURION_API_TOKEN=*" } | Select-Object -First 1
if ($TokenLine) {
    $LocalToken = $TokenLine.Substring("AURION_API_TOKEN=".Length).Trim()
    if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) {
        Set-Clipboard -Value $LocalToken
        Write-Host "[AURION] Token local copiado. Cole no portal com Ctrl+V."
    }
}

Write-Host "[AURION] Escaneando hardware, modelos e programas..."
& $VenvPython "scripts\scan_system.py"

# The health endpoint is public but returns only service identity and status.
# Do not treat an arbitrary HTTP 200 from a different app as AURION readiness.
function Test-AurionReady {
    try {
        $Health = Invoke-RestMethod -Uri "http://127.0.0.1:8765/health" -TimeoutSec 2 -ErrorAction Stop
        return ($Health.service -eq "aurion-home-node" -and $Health.status -eq "online")
    } catch {
        return $false
    }
}

$PortalUrl = "http://127.0.0.1:8765/#token=$LocalToken"
if (Test-AurionReady) {
    Write-Host "[AURION] Portal ja ativo. Nao abrirei outra instancia."
    Start-Process $PortalUrl
    exit 0
}

Write-Host "[AURION] Iniciando servidor; aguardando health-check local..."
$ServerProcess = Start-Process -FilePath $VenvPython -ArgumentList "run.py" -WorkingDirectory $AgentRoot -NoNewWindow -PassThru
$Ready = $false
for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
    Start-Sleep -Seconds 1
    $ServerProcess.Refresh()
    if ($ServerProcess.HasExited) {
        throw "[AURION] O servidor encerrou antes de ficar pronto (codigo $($ServerProcess.ExitCode)). Consulte o erro exibido acima."
    }
    if (Test-AurionReady) { $Ready = $true; break }
}
if (-not $Ready) {
    $ServerProcess.Refresh()
    if (-not $ServerProcess.HasExited) {
        # Stop only the child spawned here, never an existing external service.
        Stop-Process -Id $ServerProcess.Id -ErrorAction SilentlyContinue
    }
    throw "[AURION] Servidor nao respondeu em 30s. Portal NAO aberto. Verifique dependencias e logs."
}

Write-Host "[AURION] Health-check OK. Abrindo portal..."
Start-Process $PortalUrl
$ServerProcess.WaitForExit()
exit $ServerProcess.ExitCode
