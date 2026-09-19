# AURION ONE: inicializacao conservadora, sem pip, sem sobrescrever .env, sem instalar drivers/modelos.
# Execute somente depois de fechar os programas que voce realmente deseja encerrar.
$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$AgentRoot = Join-Path $RepoRoot 'remote-agent'
$Python = Join-Path $AgentRoot '.venv\Scripts\python.exe'
$Run = Join-Path $AgentRoot 'run.py'
$Bridge = Join-Path $AgentRoot 'scripts\start_bridge.ps1'
$DataDir = Join-Path $AgentRoot 'data'
function PingLocal([string]$Url) {
  try { return (Invoke-RestMethod -Uri $Url -TimeoutSec 3 -ErrorAction Stop) } catch { return $null }
}
Write-Host '[AURION] Reinicio conservador: preservando modelos, drivers, .env e outras aplicacoes.'
if (-not (Test-Path -LiteralPath $Python) -or -not (Test-Path -LiteralPath $Run)) {
  Write-Host '[PENDENTE] Ambiente instalado nao encontrado. Nao houve instalacao ou alteracao.'
  Write-Host ('[INFO] Verifique o ambiente em: ' + $AgentRoot)
  exit 2
}
$Current = PingLocal 'http://127.0.0.1:8765/health'
if ($Current -and $Current.status -eq 'online') {
  Write-Host '[OK] Portal ja responde em 127.0.0.1:8765. Sem iniciar duplicata.'
  Write-Host '[AVISO] Este comando nao reinicia processo antigo: confirme a versao antes de usar codigo recem-atualizado.'
} else {
  if (-not (Test-Path -LiteralPath $DataDir)) { New-Item -ItemType Directory -Path $DataDir -Force | Out-Null }
  Write-Host '[AURION] Iniciando SOMENTE o servidor do agente, sem bootstrap/pip...'
  $p = Start-Process -FilePath $Python -ArgumentList 'run.py' -WorkingDirectory $AgentRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $DataDir 'server_stdout.log') -RedirectStandardError (Join-Path $DataDir 'server_stderr.log') -PassThru
  Write-Host ('[AURION] Processo iniciado; PID=' + $p.Id)
  $ready = $false
  for ($i=0; $i -lt 10; $i++) { Start-Sleep -Seconds 2; $h = PingLocal 'http://127.0.0.1:8765/health'; if ($h -and $h.status -eq 'online') { $ready = $true; break } }
  if ($ready) { Write-Host '[OK] Portal local respondeu HTTP em http://127.0.0.1:8765' }
  else { Write-Host '[PENDENTE] Portal nao respondeu. Confira data/server_stderr.log localmente; nada sera reinstalado.' }
}
if (Test-Path -LiteralPath $Bridge) {
  try { & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Bridge; if ($LASTEXITCODE -ne 0) { Write-Host '[AVISO] Bridge nao confirmado.' } }
  catch { Write-Host '[AVISO] Bridge nao confirmado. Consulte log local.' }
}
$Ollama = PingLocal 'http://127.0.0.1:11434/api/tags'
if ($null -ne $Ollama) { Write-Host '[OK] Ollama respondeu; isto nao valida geracao de texto.' }
else { Write-Host '[PENDENTE] Ollama sem resposta nesta consulta; nao foi iniciado/reiniciado.' }
$Comfy = PingLocal 'http://127.0.0.1:8188/system_stats'
if ($null -ne $Comfy) { Write-Host '[OK] ComfyUI respondeu; isto nao valida geracao de imagem.' }
else { Write-Host '[PENDENTE] ComfyUI sem resposta nesta consulta; nao foi iniciado/reiniciado.' }
Write-Host '[AURION] Nenhuma porta publica, driver, modelo ou arquivo privado foi alterado por este script.'
