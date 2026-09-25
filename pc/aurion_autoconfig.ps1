$ErrorActionPreference='Continue'
$base=Split-Path -Parent $MyInvocation.MyCommand.Path
$log=Join-Path $base 'logs';New-Item -ItemType Directory -Force $log|Out-Null
function Say($s){Write-Host "[AURION] $s" -ForegroundColor Yellow;Add-Content (Join-Path $log 'autoconfig.log') "$(Get-Date -Format o) $s"}
Say 'AUTO CONFIG iniciado'
$ip=(Get-NetIPAddress -AddressFamily IPv4|Where-Object{$_.IPAddress -like '192.168.*' -or $_.IPAddress -like '10.*'}|Select-Object -First 1 -ExpandProperty IPAddress)
$tail='';if(Get-Command tailscale -ErrorAction SilentlyContinue){$tail=(& tailscale ip -4 2>$null|Select-Object -First 1)}
$ollama=Get-Command ollama -ErrorAction SilentlyContinue
if($ollama){Say 'Ollama encontrado';$models=(& ollama list 2>&1|Out-String);$models|Set-Content (Join-Path $log 'MODELOS_OLLAMA.txt')}else{Say 'Ollama ausente'}
$adb=Get-Command adb -ErrorAction SilentlyContinue
if(!$adb){
 $pt=Join-Path $base 'platform-tools\adb.exe'
 if(Test-Path $pt){$adb=Get-Item $pt}
 else{Say 'Baixando Android Platform Tools oficial';$z=Join-Path $env:TEMP 'platform-tools.zip';Invoke-WebRequest 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip' -OutFile $z;Expand-Archive -Force $z $base;$adb=Get-Item (Join-Path $base 'platform-tools\adb.exe')}
}
if($adb){& $adb.FullName start-server|Out-Null;(& $adb.FullName devices -l 2>&1|Out-String)|Set-Content (Join-Path $log 'POCO_ADB.txt');Say 'ADB pronto - autorize a depuracao USB no POCO se aparecer'}
$svc=[ordered]@{aurion='http://127.0.0.1:5000';openwebui='http://127.0.0.1:8080';comfy='http://127.0.0.1:8188/system_stats';ollama='http://127.0.0.1:11434/api/tags'}
$out=[ordered]@{time=(Get-Date).ToString('o');lan=$ip;tailscale=$tail;services=@{};models=@()}
foreach($k in $svc.Keys){try{$q=Invoke-WebRequest -UseBasicParsing $svc[$k] -TimeoutSec 4;$out.services[$k]=@{ok=$true;http=[int]$q.StatusCode}}catch{$out.services[$k]=@{ok=$false;error=$_.Exception.Message}}}
try{$tags=Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 4;$out.models=@($tags.models|ForEach-Object{$_.name})}catch{}
$out|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 (Join-Path $log 'AURION_RUNTIME.json')
$envfile=Join-Path $base 'aurion.env'
@("AURION_LAN=$ip","AURION_TAILSCALE=$tail","AURION_GATEWAY_PORT=5060","OLLAMA=http://127.0.0.1:11434","COMFYUI=http://127.0.0.1:8188","OPENWEBUI=http://127.0.0.1:8080")|Set-Content $envfile
$gw=Join-Path $base 'gateway.py'
if(Test-Path $gw){
 $old=Get-NetTCPConnection -LocalPort 5060 -State Listen -ErrorAction SilentlyContinue
 if(!$old){Say 'Ligando Gateway PC-POCO na porta 5060';Start-Process -WindowStyle Hidden python -ArgumentList @($gw)}
}
Start-Sleep 2
if($adb){
 $apk=Get-ChildItem $base -Filter '*.apk'|Sort-Object LastWriteTime -Descending|Select-Object -First 1
 if($apk){Say "Instalando/atualizando APK: $($apk.Name)";& $adb.FullName install -r $apk.FullName}
}
Say "LAN=$ip TAILSCALE=$tail"
Say 'Concluido. Logs em .\logs'
