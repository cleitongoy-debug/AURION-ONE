$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Worker = Join-Path $Root "scripts\telegram_titan_bridge.py"
$TaskName = "AURION-TITAN-Telegram"

if (-not (Test-Path $Python)) { throw "Python do ambiente virtual não encontrado: $Python" }
if (-not (Test-Path $Worker)) { throw "Worker Telegram não encontrado: $Worker" }
if (-not (Test-Path (Join-Path $Root ".env"))) { throw ".env não encontrado. Configure o bot e as chaves antes de instalar a tarefa." }

$Action = New-ScheduledTaskAction -Execute $Python -Argument "`"$Worker`"" -WorkingDirectory $Root
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Ponte independente Telegram -> TITAN com cache local e fallback Ollama." -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName
Write-Host "Tarefa $TaskName registrada e iniciada para o usuário atual."
