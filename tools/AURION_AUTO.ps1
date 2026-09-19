# AURION ONE: diagnostico e bootstrap local; preserva ambientes existentes.
$ErrorActionPreference='Stop'
$repo=Split-Path -Parent $PSScriptRoot
$logDir=Join-Path $env:USERPROFILE 'Desktop\AURION_DIAGNOSTICO'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log=Join-Path $logDir ('execucao-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.txt')
Start-Transcript -Path $log | Out-Null
try {
 Write-Host 'AURION ONE - diagnostico' -ForegroundColor Cyan
 Write-Host ('Branch local: '+(& git -C $repo branch --show-current))
 foreach($port in 11434,8188,8765,5000){$c=New-Object Net.Sockets.TcpClient;try{$a=$c.BeginConnect('127.0.0.1',$port,$null,$null);$ok=$a.AsyncWaitHandle.WaitOne(1000);if($ok){$c.EndConnect($a)};Write-Host "Porta ${port}: $(if($ok){'ABERTA'}else{'FECHADA'})"}catch{Write-Host "Porta ${port}: FECHADA"}finally{$c.Close()}}
 try{$m=Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 8;Write-Host ('Ollama: '+(($m.models|ForEach-Object name)-join ', '))}catch{Write-Host ('Ollama indisponivel: '+$_.Exception.Message)}
 $roots=@((Join-Path $env:USERPROFILE 'Desktop\painelseguro#1 - Copia\models'),'C:\COMFYUI\ComfyUI_windows_portable',$repo)
 foreach($d in (Get-PSDrive -PSProvider FileSystem)){$roots+=(Join-Path $d.Root 'models')}
 foreach($r in ($roots|Select-Object -Unique)){if(Test-Path -LiteralPath $r){Write-Host ('Encontrado: '+$r);Get-ChildItem -LiteralPath $r -Directory -ErrorAction SilentlyContinue|Where-Object Name -Match 'jarvis|opencode|comfy|model'|ForEach-Object{Write-Host (' Projeto: '+$_.FullName)}}}
 $jarvis=Join-Path $env:USERPROFILE 'Desktop\painelseguro#1 - Copia\models\OpenJarvis-main'
 if(-not(Test-Path -LiteralPath (Join-Path $jarvis 'pyproject.toml'))){Write-Host 'Fonte Jarvis ausente; nenhuma instalacao.';return}
 $candidates=@((Join-Path $repo '.venv\Scripts\python.exe'),(Join-Path $repo 'remote-agent\.venv\Scripts\python.exe'),'C:\Users\Public\Python312-32\python.exe')
 $python=$null
 foreach($p in $candidates){if(Test-Path -LiteralPath $p){$v=& $p -c 'import sys;print(sys.version_info.major,sys.version_info.minor,sys.maxsize>2**32)' 2>$null;Write-Host ('Python: '+$p+' / '+$v);if($v -match '^3 (1[0-3]) True$'){$python=$p;break}}}
 if(-not $python){Write-Host 'Python 64-bit 3.10-3.13 nao localizado; sem instalacao.';return}
 $venv=Join-Path $env:LOCALAPPDATA 'AURION-ONE\jarvis-venv';$py=Join-Path $venv 'Scripts\python.exe'
 if(-not(Test-Path -LiteralPath $py)){Write-Host 'Criando ambiente isolado Jarvis';& $python -m venv $venv;if($LASTEXITCODE -ne 0){throw 'Falha ao criar ambiente'}}
 Write-Host 'Instalando OpenJarvis no ambiente isolado; pode baixar dependencias.'
 & $py -m pip install --disable-pip-version-check -e $jarvis
 if($LASTEXITCODE -ne 0){Write-Host 'Instalacao falhou; consulte log. Outros ambientes intactos.';return}
 $exe=Join-Path $venv 'Scripts\jarvis.exe'
 if(Test-Path -LiteralPath $exe){Write-Host 'Jarvis instalado; testando ajuda:';& $exe --help;Write-Host ('Executavel: '+$exe)}
 Write-Host 'Nenhuma tarefa autonoma foi autorizada dentro do Jarvis; confirme comandos antes de executar.'
}catch{Write-Host ('ERRO: '+$_.Exception.Message)}finally{Stop-Transcript|Out-Null;Write-Host ('Relatorio: '+$log)}
