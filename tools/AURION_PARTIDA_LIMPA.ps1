# AURION ONE - partida leve; nao apaga, instala ou repete scan integral.
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$data = Join-Path $root 'remote-agent\data'
New-Item -ItemType Directory -Force -Path $data | Out-Null
$report = Join-Path $data 'partida_limpa_status.json'
$state = [ordered]@{ checked_at=(Get-Date).ToString('o'); inventory=''; inventory_observed_at=$null; scan=''; dependencies=[ordered]@{}; motors=''; chat=''; notes=@() }
function Check([string]$url) { try { $r=Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 3; return ($r.StatusCode -eq 200) } catch { return $false } }
function Stage([string]$name) { Write-Host "`n[AURION ETAPA] $name" }
try {
 Stage '1/5 - Inventario SALVO (nao e scan desta partida)'
 $inventory = Join-Path $data 'history_scan.json'
 if(Test-Path -LiteralPath $inventory) {
  try { $old=Get-Content -Raw -Encoding UTF8 -LiteralPath $inventory | ConvertFrom-Json; $state.inventory='historico_reutilizado'; $state.inventory_observed_at=$old.observed_at; Write-Host ('[CACHE] Inventario antigo: ' + $old.observed_at + '; arquivos registrados=' + $old.files_examined + '. Nenhum conteudo foi lido.') } catch { $state.inventory='historico_invalido'; $state.notes += 'history_scan.json invalido.' }
 } else { $state.inventory='historico_ausente'; Write-Host '[AVISO] Historico ausente; scan pesado nao sera repetido.' }
 Stage '2/5 - Verificacao ATUAL somente de caminhos conhecidos'
 $paths=@($root,'C:\COMFYUI','D:\ComfyUI','E:\AURION-QB-QUANTUN','E:\LUMEN#QUANTUM#AURION#Q6','F:\LUMEN#QUANTUM#AURION#Q6')
 $found=@(); foreach($p in $paths) { if(Test-Path -LiteralPath $p) { $found += $p; Write-Host ('[AGORA OK] ' + $p) } }
 $state.scan='verificacao_atual_de_caminhos_conhecidos_sem_varredura_de_arquivos'; $state.dependencies['known_paths']=$found
 Stage '3/5 - Dependencias e servicos AGORA (sem instalacao)'
 foreach($name in @('python','git','ollama','ffmpeg')) { $cmd=Get-Command $name -ErrorAction SilentlyContinue; $state.dependencies[$name]=if($cmd){'encontrado_no_PATH'}else{'nao_encontrado_no_PATH'}; Write-Host ('[CHECK] '+$name+': '+$state.dependencies[$name]) }
 $state.dependencies['portal_before']=Check 'http://127.0.0.1:8765/health'
 $state.dependencies['ollama_before']=Check 'http://127.0.0.1:11434/api/tags'
 $state.dependencies['comfyui_before']=Check 'http://127.0.0.1:8188/system_stats'
 Stage '4/5 - Motores: nao duplicar se todos responderem'
 if($state.dependencies['portal_before'] -and $state.dependencies['ollama_before'] -and $state.dependencies['comfyui_before']) { $state.motors='todos_ja_online_nenhum_launcher_executado'; Write-Host '[OK] Portal, Ollama e ComfyUI ja online. Nenhuma janela extra iniciada.' }
 else {
  $motors=Join-Path $root 'tools\AURION_MOTORES.ps1'
  if(Test-Path -LiteralPath $motors) { & $motors; $state.motors='orquestrador_executado_para_servicos_pendentes' }
  else { $state.motors='orquestrador_ausente'; $state.notes += 'AURION_MOTORES.ps1 ausente.' }
 }
 $state.dependencies['portal_after']=Check 'http://127.0.0.1:8765/health'
 $state.dependencies['ollama_after']=Check 'http://127.0.0.1:11434/api/tags'
 $state.dependencies['comfyui_after']=Check 'http://127.0.0.1:8188/system_stats'
 foreach($service in @('portal','ollama','comfyui')) { Write-Host ('[AGORA] '+$service+': '+ $(if($state.dependencies[$service+'_after']){'online'}else{'pendente'})) }
 Stage '5/5 - Chat local (somente se Ollama responder)'
 $chat=Join-Path $root 'tools\aurion_chat_local.py'; $py=Get-Command python -ErrorAction SilentlyContinue
 if($py -and (Test-Path -LiteralPath $chat) -and $state.dependencies['ollama_after']) { $state.chat='iniciando'; Write-Host '[AURION] Voce > recebe mensagens ou /sair, nao comandos CMD.' }
 else { $state.chat='bloqueado'; $state.notes += 'Chat requer Python, arquivo do chat e Ollama online.' }
} catch { $state.notes += ('Falha na partida: '+$_.Exception.Message); Write-Host ('[FALHOU] '+$_.Exception.Message) }
finally { $state.checked_at=(Get-Date).ToString('o'); $state | ConvertTo-Json -Depth 7 | Set-Content -Encoding UTF8 -LiteralPath $report; Write-Host ('[AURION] Relatorio privado: '+$report) }
if($state.chat -eq 'iniciando') { & $py.Source $chat }
