# AURION ONE | Pre-voo PC + POCO, sem excluir apps, sem instalar dependencias.
# Fonte: AURION-ONE PR #41, protocolo JSON#13. Somente USB ADB e loopback.
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$root=Join-Path $env:LOCALAPPDATA 'AURION_ONE_QA'
$logs=Join-Path $root 'reports'
New-Item -Path $logs -ItemType Directory -Force | Out-Null
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$report=Join-Path $logs ("AURION_PREVOO_"+$stamp+".txt")
$lines=New-Object 'System.Collections.Generic.List[string]'
function Say([string]$msg) {
  Write-Host $msg
  [void]$lines.Add($msg)
}
function Check([string]$label,[string]$url) {
  try {
    $response=Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 4
    $ok=([int]$response.StatusCode -ge 200 -and [int]$response.StatusCode -lt 300)
    if ($ok) { Say ("[PASSOU] "+$label+" HTTP "+[int]$response.StatusCode); return $true }
    Say ("[BLOQUEADO] "+$label+" HTTP "+[int]$response.StatusCode)
  } catch { Say ("[NAO TESTADO / SEM RESPOSTA] "+$label) }
  return $false
}
Say '========================================================'
Say ' AURION ONE | PRE-VOO PC + POCO | NAO DESTRUTIVO'
Say '========================================================'
Say ("Data local: "+(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
Say 'Sem instalar APK, sem apagar apps, sem atualizar firmware.'
Say 'NENHUMA chave, token ou conversa sera impressa no relatorio.'
Say ''
Say '[1/5] Painel original e nos locais'
$v14=Check 'V14 porta 5058 /api/one/health' 'http://127.0.0.1:5058/api/one/health'
$st=Check 'Super Studio porta 5060 /api/health' 'http://127.0.0.1:5060/api/health'
$ol=Check 'Ollama porta 11434 /api/tags' 'http://127.0.0.1:11434/api/tags'
$cf=Check 'ComfyUI porta 8188 /system_stats' 'http://127.0.0.1:8188/system_stats'
Say ''
Say '[2/5] Caminhos historicos (somente existencia)'
$known=@(
  'C:\AURION-ONE',
  'C:\AURION',
  'C:\######AGENTE#####STATUS######\#BASE##177#\SKILL#PAINEL\AURION_ONE_CENTRAL_V14',
  (Join-Path $env:USERPROFILE 'Desktop\painelseguro#1 - Copia')
)
foreach($k in $known) {
  if(Test-Path -LiteralPath $k -PathType Container) { Say ("[ENCONTRADO] "+$k) }
  else { Say ("[AUSENTE] "+$k) }
}
Say ''
Say '[3/5] ADB e aparelhos Android'
$adb=$null
$candidates=@((Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'), 'C:\platform-tools\adb.exe')
foreach($path in $candidates) {if(Test-Path -LiteralPath $path -PathType Leaf){$adb=$path;break}}
if(-not $adb){
  $c=Get-Command 'adb.exe' -ErrorAction SilentlyContinue
  if($c){$adb=$c.Source}
}
if(-not $adb){
  Say '[BLOQUEADO] adb.exe nao encontrado. Nenhuma instalacao automatica.'
}else{
  $usb=$false
  try {
    $dev=(& $adb -d get-state 2>$null | Out-String).Trim()
    $usb=($LASTEXITCODE -eq 0 -and $dev -eq 'device')
  }catch{}
  if(-not $usb){
    Say '[BLOQUEADO] Nao ha exatamente um Android USB autorizado. Confira depuracao no POCO.'
  }else{
    Say '[PASSOU] POCO/Android USB autorizado via ADB (ID oculto)'
    $packages= @(& $adb -d shell pm list packages -3 2>$null) | ForEach-Object { $_.Trim() } |
      Where-Object { $_ -match '(?i)aurion|anark|digitalpen|one\.aurion' } |
      ForEach-Object { $_ -replace '^package:','' } | Sort-Object -Unique
    if($packages.Count -eq 0){
      Say '[SEM BASE] Nenhum pacote com nome AURION encontrado neste filtro.'
    }else{
      Say ("[INVENTARIO] "+@($packages).Count+" pacote(s) AURION encontrado(s):")
      foreach($pkg in $packages){
        if($pkg -notmatch '^[A-Za-z][A-Za-z0-9_.]+$'){continue}
        $version='versao_indeterminada'
        try {
          $desc=@(& $adb -d shell dumpsys package $pkg 2>$null)
          $match=@($desc | Select-String -Pattern '^\s*versionName=' | Select-Object -First 1)
          if($match.Count -gt 0){$version=$match[0].ToString().Trim()}
        }catch{}
        Say ("  "+$pkg+" | "+$version+" | MANTER ate backup e confirmacao")
      }
    }
    foreach($port in @(5060,5058)){
      try {
        $null=& $adb -d reverse ("tcp:"+$port) ("tcp:"+$port) 2>&1
        if($LASTEXITCODE -eq 0){Say ("[PASSOU] ADB reverse "+$port+" USB local")}
        else{Say ("[BLOQUEADO] ADB reverse "+$port)}
      }catch{Say ("[BLOQUEADO] ADB reverse "+$port)}
    }
    Say '[AVISO] ADB reverse liga celular ao loopback PC; nao repara o WebView e nao prova sincronizacao.'
  }
}
Say ''
Say '[4/5] Super Studio isolado (se ainda nao existir)'
if(-not $st){
  $cmd=Get-Command 'python.exe' -ErrorAction SilentlyContinue
  $pyExe=$null
  $pyPrefix=@()
  if($cmd){$pyExe=$cmd.Source}
  else {
    $launcher=Get-Command 'py.exe' -ErrorAction SilentlyContinue
    if($launcher){$pyExe=$launcher.Source;$pyPrefix=@('-3')}
  }
  if(-not $pyExe){Say '[BLOQUEADO] Python nao encontrado, nao sera instalado.'}
  else {
    $probeArgs=@($pyPrefix)+@('-c','import flask, requests, PIL; print("dependencias_ok")')
    $ok=$false
    try{ $null= & $pyExe @probeArgs 2>$null; $ok=($LASTEXITCODE -eq 0)}catch{}
    if(-not $ok){Say '[BLOQUEADO] Python/Flask/requests/Pillow incompletos; nao instalar automaticamente.'}
    else {
      $pinned='fbde6c0ac0f6ab660fa2c1d9578153c213dc53a1'
      $src=Join-Path $root ("source_"+$pinned.Substring(0,12))
      $module=Join-Path $src 'pc-package-v3\aurion_superstudio\app.py'
      if(-not (Test-Path -LiteralPath $module)){
        try {
          $zip=Join-Path $root ("source_"+$pinned.Substring(0,12)+'.zip')
          $unpack=Join-Path $root 'unpack_pinned'
          Say '[DOWNLOAD] Codigo PC publico fixado em commit GitHub, sem instaladores.'
          Invoke-WebRequest -UseBasicParsing -Uri ("https://github.com/cleitongoy-debug/AURION-ONE/archive/"+$pinned+".zip") -OutFile $zip -TimeoutSec 45
          Expand-Archive -LiteralPath $zip -DestinationPath $unpack -Force
          $found=Get-ChildItem -LiteralPath $unpack -Directory | Where-Object {$_.Name -like 'AURION-ONE-*'} | Select-Object -First 1
          if(-not $found){throw 'Arquivo Git nao reconhecido'}
          Move-Item -LiteralPath $found.FullName -Destination $src -Force
        }catch{
          Say '[BLOQUEADO] Download ou extracao do Git falhou. Nenhum painel antigo alterado.'
        }
      }
      if(Test-Path -LiteralPath $module){
        $package=Join-Path $src 'pc-package-v3'
        $runtime=Join-Path $root 'runtime'
        New-Item -ItemType Directory -Path $runtime -Force | Out-Null
        $env:AURION_PANEL_ROOT=$runtime
        $env:AURION_BIND_HOST='127.0.0.1'
        $env:AURION_STUDIO_PORT='5060'
        try{
          $args=@($pyPrefix)+@('-m','aurion_superstudio.app')
          $out=Join-Path $logs 'superstudio_out.log'
          $err=Join-Path $logs 'superstudio_err.log'
          Start-Process -FilePath $pyExe -ArgumentList $args -WorkingDirectory $package -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden | Out-Null
          Start-Sleep -Seconds 3
          $st=Check 'Super Studio isolado 5060' 'http://127.0.0.1:5060/api/health'
        }catch{Say '[BLOQUEADO] Nao foi possivel iniciar o Super Studio; logs separados.'}
      }
    }
  }
}
Say ''
Say '[5/5] Proximos testes e seguranca'
if($st){
  Say '[PRONTO] Super Studio local 5060. Token exibido somente no painel local.'
  Say '[PROXIMO] No APK: Conexoes > SYNC POCO-PC. O PC deve responder com contagens e readback.'
}
if($v14){Say '[PRONTO] V14 5058 respondeu nesta rodada, sem reiniciar.'}
else{Say '[PENDENTE] V14 nao respondeu; nao executar launcher desconhecido.'}
Say '[PENDENTE] Assinaturas e dados dos APKs devem ser verificados ANTES de desinstalar duplicatas.'
Say '[PENDENTE] Nenhum pareamento Band/Notify Pro foi alterado.'
Say '[PENDENTE] Scan de pastas privadas nao realizado sem autorizacao.'
$lines | Out-File -LiteralPath $report -Encoding UTF8
Say ("RELATORIO SALVO: "+$report)
if($st){Start-Process 'http://127.0.0.1:5060'}
elseif($v14){Start-Process 'http://127.0.0.1:5058'}
Say 'FIM. Nenhum aplicativo foi removido.'
