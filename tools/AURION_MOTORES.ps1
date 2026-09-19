# AURION ONE - inicializador local conservador. Nao instala, apaga, publica nem altera credenciais.
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $root 'remote-agent\data'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$log = Join-Path $logDir 'motores_status.json'
$state = [ordered]@{ checked_at = (Get-Date).ToString('o'); portal = 'pendente'; ollama = 'pendente'; comfyui = 'pendente'; agente = 'pendente'; drive = 'nao_configurado'; poco = 'nao_verificado'; notes = @() }
function Test-Endpoint([string]$url) {
  try { $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 4; return ($r.StatusCode -eq 200) } catch { return $false }
}
function Wait-Endpoint([string]$url, [int]$attempts = 12) {
  for ($i=0; $i -lt $attempts; $i++) { if (Test-Endpoint $url) { return $true }; Start-Sleep -Seconds 2 }; return $false
}
Write-Host '[AURION] Orquestrador: verifica antes de iniciar; sem processos duplicados intencionais.'
try {
  if (-not (Test-Endpoint 'http://127.0.0.1:8765/health')) {
    $launcher = Join-Path $root 'LIGAR_AURION_PC.cmd'
    if (Test-Path $launcher) { Start-Process -FilePath 'cmd.exe' -ArgumentList @('/d','/c',('"' + $launcher + '"')) -WorkingDirectory $root; $state.notes += 'Iniciador do portal acionado.' }
    else { $state.notes += 'LIGAR_AURION_PC.cmd ausente.' }
  }
  if (Wait-Endpoint 'http://127.0.0.1:8765/health') { $state.portal = 'online'; Start-Process 'http://127.0.0.1:8765' } else { $state.notes += 'Portal nao respondeu: conferir janela AURION SERVER.' }
  if (Test-Endpoint 'http://127.0.0.1:11434/api/tags') { $state.ollama = 'online' } else { $state.notes += 'Ollama nao respondeu; iniciar pelo aplicativo oficial antes de usar o agente.' }
  if (-not (Test-Endpoint 'http://127.0.0.1:8188/system_stats')) {
    $comfyRoot = 'C:\COMFYUI\ComfyUI_windows_portable'
    $python = Join-Path $comfyRoot 'python_embeded\python.exe'
    $main = Join-Path $comfyRoot 'ComfyUI\main.py'
    if ((Test-Path $python) -and (Test-Path $main)) {
      Start-Process -FilePath $python -ArgumentList @('-s',('"' + $main + '"'),'--windows-standalone-build') -WorkingDirectory $comfyRoot
      $state.notes += 'ComfyUI iniciado com GPU quando disponivel.'
    } else { $state.notes += 'ComfyUI nao encontrado no caminho conhecido; nao baixar modelos automaticamente.' }
  }
  if (Wait-Endpoint 'http://127.0.0.1:8188/system_stats' 15) { $state.comfyui = 'online'; Start-Process 'http://127.0.0.1:8188' } else { $state.notes += 'ComfyUI nao respondeu: conferir erros CUDA/dependencias.' }
  if ($state.ollama -eq 'online') {
    $ollama = Get-Command ollama.exe -ErrorAction SilentlyContinue
    if (-not $ollama) { $candidate = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'; if (Test-Path $candidate) { $ollama = Get-Item $candidate } }
    if ($ollama) {
      $ollamaPath = if ($ollama.Source) { $ollama.Source } else { $ollama.FullName }
      Start-Process -FilePath 'cmd.exe' -ArgumentList @('/d','/k',('"' + $ollamaPath + '" run qwen3.5:4b')) -WorkingDirectory $root
      $state.agente = 'console_ollama_aberto_nao_testado'
      $state.notes += 'Console local do modelo aberto; nao e integracao ChatGPT/Gemini nem agente autonomo de reparo.'
    } else { $state.notes += 'Ollama API online, mas executavel nao localizado para console.' }
  }
} catch { $state.notes += ('Erro inesperado: ' + $_.Exception.Message) }
finally {
  $state.checked_at = (Get-Date).ToString('o')
  $state | ConvertTo-Json -Depth 5 | Set-Content -Path $log -Encoding UTF8
  Write-Host ('[AURION] Estado salvo localmente: ' + $log)
  $state | ConvertTo-Json -Depth 5 | Write-Host
  Write-Host '[AURION] Drive, POCO e OAuth permanecem pendentes ate verificacao e autorizacao especifica.'
}
