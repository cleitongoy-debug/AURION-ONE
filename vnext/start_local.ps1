$ErrorActionPreference='Continue'
$log=Join-Path $PSScriptRoot 'data\logs\startup.txt'
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
function Note($message){Add-Content -LiteralPath $log -Encoding UTF8 -Value "$(Get-Date -Format o) $message"}
function Healthy($url){try{$r=Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2;return ($r.StatusCode -eq 200)}catch{return $false}}
function PortUsed($port){try{$client=New-Object Net.Sockets.TcpClient;$client.Connect('127.0.0.1',$port);$client.Close();return $true}catch{return $false}}
function Launch($name,$url,$port,$exe,$arg,$work){
 if(Healthy $url){Note "$name online; reutilizado";return}
 if(PortUsed $port){Note "$name porta $port ocupada, mas endpoint sem resposta; nao duplicado";return}
 if(-not $exe -or -not (Test-Path -LiteralPath $exe -PathType Leaf)){Note "$name executavel nao localizado";return}
 try{
  $p=Start-Process -FilePath $exe -ArgumentList $arg -WorkingDirectory $work -PassThru -WindowStyle Hidden
  Note "$name iniciado PID $($p.Id); aguardando endpoint"
 }catch{Note "$name falhou: $($_.Exception.Message)"}
}
Set-Content -LiteralPath $log -Encoding UTF8 -Value "Partida AURION vNext $(Get-Date -Format o)"
$ollama=Get-Command ollama.exe -ErrorAction SilentlyContinue | Select-Object -First 1
if($ollama){Launch 'Ollama' 'http://127.0.0.1:11434/api/tags' 11434 $ollama.Source 'serve' (Split-Path $ollama.Source)}
elseif(Healthy 'http://127.0.0.1:11434/api/tags'){Note 'Ollama online; reutilizado'}
else{Note 'Ollama executavel ausente do PATH'}
$root='C:\COMFYUI\ComfyUI_windows_portable'
$python=Join-Path $root 'python_embeded\python.exe'
$main=Join-Path $root 'ComfyUI\main.py'
if((Test-Path -LiteralPath $python) -and (Test-Path -LiteralPath $main)){
 Launch 'ComfyUI' 'http://127.0.0.1:8188/system_stats' 8188 $python ('-s "'+$main+'" --windows-standalone-build --listen 127.0.0.1 --port 8188') $root
}elseif(Healthy 'http://127.0.0.1:8188/system_stats'){Note 'ComfyUI online; reutilizado'}
else{Note 'ComfyUI portatil nao localizado no caminho conhecido'}
$web=Get-Command open-webui.exe -ErrorAction SilentlyContinue | Select-Object -First 1
if($web){
 $work=if(Test-Path -LiteralPath 'C:\Windows\System32\.webui_secret_key'){'C:\Windows\System32'}else{$PSScriptRoot}
 Launch 'Open WebUI' 'http://127.0.0.1:8080/health' 8080 $web.Source 'serve' $work
}elseif(Healthy 'http://127.0.0.1:8080/health'){Note 'Open WebUI online; reutilizado'}
else{Note 'Open WebUI executavel ausente do PATH'}
