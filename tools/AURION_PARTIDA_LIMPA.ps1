# AURION ONE: partida em etapas, sem limpeza destrutiva ou scan integral repetido.
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$data = Join-Path $root 'remote-agent\data'
New-Item -ItemType Directory -Force -Path $data | Out-Null
$report = Join-Path $data 'partida_limpa_status.json'
$state = [ordered]@{ checked_at=(Get-Date).ToString('o'); inventory=''; scan=''; dependencies=[ordered]@{}; motors=''; chat=''; notes=@() }
function Check([string]$url) { try { $r=Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 3; return ($r.StatusCode -eq 200) } catch { return $false } }
function Stage([string]$name) { Write-Host "`n[AURION ETAPA] $name" }
try {
 Stage '1/5 - Inventario existente (sem varredura completa)'
 $inventory = Join-Path $data 'history_scan.json'
 if(Test-Path $inventory) {
  try { $old=Get-Content -Raw -Encoding UTF8 $inventory | ConvertFrom-Json; $state.inventory='historico_reutilizado'; Write-Host ('[OK] Scan historico reutilizado: ' + $old.observed_at + '; arquivos=' + $old.files_examined) } catch { $state.inventory='arquivo_presente_mas_invalido'; $state.notes += 'history_scan.json nao pode ser interpretado.' }
 } else { $state.inventory='historico_ausente'; Write-Host '[AVISO] Historico nao localizado; nao repetir scan pesado automaticamente.' }
 Stage '2/5 - Scan leve e limitado dos pontos conhecidos'
 $paths=@($root,'C:\COMFYUI','D:\ComfyUI','E:\AURION-QB-QUANTUN','E:\LUMEN#QUANTUM#AURION#Q6','F:\LUMEN#QUANTUM#AURION#Q6')
 $found=@(); foreach($p in $paths) { if(Test-Path -LiteralPath $p) { $found += $p; Write-Host ('[OK] ' + $p) } }
 $state.scan='somente_caminhos_conhecidos'; $state.dependencies['known_paths']=$found
 Stage '3/5 - Dependencias essenciais, sem instalacao automatica'
 foreach($name in @('python','git','ollama','ffmpeg')) { $cmd=Get-Command $name -ErrorAction SilentlyContinue; $state.dependencies[$name]=if($cmd){'encontrado'}else{'nao_encontrado_no_PATH'}; Write-Host ('[CHECK] '+$name+': '+$state.dependencies[$name]) }
 $state.dependencies['portal_before']=Check 'http://127.0.0.1:8765/health'
 $state.dependencies['ollama_before']=Check 'http://127.0.0.1:11434/api/tags'
 $state.dependencies['comfyui_before']=Check 'http://127.0.0.1:8188/system_stats'
 Stage '4/5 - Iniciar motores existentes apenas se necessario'
 if(-not $state.dependencies['portal_before']) {
  $launcher=Join-Path $root 'LIGAR_AURION_PC.cmd'
  if(Test-Path $launcher) { Start-Process -FilePath 'cmd.exe' -ArgumentList @('/d','/c',('"'+$launcher+'"')) -WorkingDirectory $root -WindowStyle Minimized; $state.notes += 'Launcher iniciado em janela separada; pode exibir pause nessa janela.' }
  else { $state.notes += 'Launcher ausente.' }
 }
 $motors=Join-Path $root 'tools\AURION_MOTORES.ps1'
 if(Test-Path $motors) { & $motors; $state.motors='orquestrador_executado' } else { $state.motors='orquestrador_ausente' }
 $state.dependencies['portal_after']=Check 'http://127.0.0.1:8765/health'
 $state.dependencies['ollama_after']=Check 'http://127.0.0.1:11434/api/tags'
 $state.dependencies['comfyui_after']=Check 'http://127.0.0.1:8188/system_stats'
 Stage '5/5 - Chat local no mesmo CMD'
 $chat=Join-Path $root 'tools\aurion_chat_local.py'
 $py=Get-Command python -ErrorAction SilentlyContinue
 if($py -and (Test-Path $chat) -and $state.dependencies['ollama_after']) { $state.chat='iniciando'; Write-Host '[AURION] Proxima tela: Voce > recebe mensagens e /sair; NAO recebe comandos CMD.' }
 else { $state.chat='bloqueado'; $state.notes += 'Chat depende de python, script e Ollama online.' }
} catch { $state.notes += ('Falha na partida: '+$_.Exception.Message); Write-Host ('[FALHOU] '+$_.Exception.Message) }
finally { $state.checked_at=(Get-Date).ToString('o'); $state | ConvertTo-Json -Depth 7 | Set-Content -Encoding UTF8 -Path $report; Write-Host ('[AURION] Relatorio privado: '+$report) }
if($state.chat -eq 'iniciando') { & $py.Source $chat }
