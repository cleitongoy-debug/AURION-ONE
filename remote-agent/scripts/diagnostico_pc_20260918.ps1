# AURION ONE - diagnostico somente leitura. Nao imprime tokens nem .env.
$ErrorActionPreference = 'Continue'
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Write-Host '=== AURION PC: diagnostico somente leitura ==='
Write-Host ('Data local: ' + (Get-Date -Format o))
Write-Host ('Repositorio: ' + $Root)
Write-Host '=== PORTAS LOCAIS ==='
foreach ($Port in @(8765,11434,8188)) {
  try {
    $Connections = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction Stop)
    if ($Connections.Count -eq 0) { Write-Host ("Porta ${Port}: sem listener") }
    else { foreach ($Connection in $Connections) { Write-Host ("Porta ${Port}: {0} PID={1}" -f $Connection.LocalAddress,$Connection.OwningProcess) } }
  } catch { Write-Host ("Porta ${Port}: sem listener ou consulta indisponivel") }
}
Write-Host '=== ENDPOINTS SOMENTE LEITURA ==='
foreach ($Endpoint in @('http://127.0.0.1:8765/health','http://127.0.0.1:11434/api/tags','http://127.0.0.1:8188/system_stats')) {
  try {
    $Response = Invoke-WebRequest -Uri $Endpoint -UseBasicParsing -TimeoutSec 3
    Write-Host ("{0}: HTTP {1}" -f $Endpoint,[int]$Response.StatusCode)
  } catch { Write-Host ("{0}: indisponivel ({1})" -f $Endpoint,$_.Exception.GetType().Name) }
}
Write-Host '=== PROCESSOS (SEM ARGUMENTOS OU CREDENCIAIS) ==='
Get-Process -Name ollama,python,pythonw -ErrorAction SilentlyContinue | Select-Object ProcessName,Id,Path | Format-Table -AutoSize
Write-Host '=== INVENTARIO EXISTENTE ==='
$Inventory = Join-Path $Root 'remote-agent\data\inventory.json'
if (Test-Path $Inventory) {
  try {
    $Data = Get-Content $Inventory -Raw | ConvertFrom-Json
    Write-Host ('Escaneado em: ' + $Data.scanned_at)
    Write-Host ('GPU: ' + $Data.gpu)
    Write-Host ('Projetos: ' + (($Data.known_projects) -join '; '))
    Write-Host ('Modelos Ollama encontrados: ' + @($Data.ollama.models).Count)
  } catch { Write-Host 'Inventario invalido; nao foi modificado.' }
} else { Write-Host 'Inventario ainda nao encontrado.' }
Write-Host '=== FIM: nenhum servico iniciado, arquivo removido ou configuracao alterada ==='
