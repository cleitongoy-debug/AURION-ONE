# AURION ONE bridge launcher. Starts one non-persistent, read-only worker.
$ErrorActionPreference = 'Stop'
$AgentRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $AgentRoot '.venv\Scripts\python.exe'
$Worker = Join-Path $PSScriptRoot 'aurion_bridge_worker.py'
$Data = Join-Path $AgentRoot 'data'
if (-not (Test-Path -LiteralPath $Python)) { throw 'Ambiente Python do agente nao encontrado. Inicie START_AURION.cmd primeiro.' }
if (-not (Test-Path -LiteralPath $Worker)) { throw 'Worker ausente; execute git pull --ff-only.' }
New-Item -ItemType Directory -Path $Data -Force | Out-Null
# Avoid duplicate workers. No other process command lines are printed or stored.
$Existing = @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -and $_.CommandLine.Contains('aurion_bridge_worker.py') })
if ($Existing.Count -gt 0) {
    Write-Host '[AURION BRIDGE] Ja iniciado; nenhum processo duplicado.'
    exit 0
}
$OutLog = Join-Path $Data 'bridge_worker.log'
$ErrLog = Join-Path $Data 'bridge_worker_errors.log'
$Process = Start-Process -FilePath $Python -ArgumentList ('"' + $Worker + '"') -WorkingDirectory $AgentRoot -WindowStyle Hidden -RedirectStandardOutput $OutLog -RedirectStandardError $ErrLog -PassThru
Write-Host ('[AURION BRIDGE] Processo iniciado em segundo plano. PID=' + $Process.Id)
Write-Host ('[AURION BRIDGE] Estado local: ' + (Join-Path $Data 'bridge_status.json'))
Write-Host '[AURION BRIDGE] Nao configura inicializacao automatica com Windows.'
