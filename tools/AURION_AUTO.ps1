# AURION ONE bootstrap v2. Run from any location; never modifies existing venvs or git branches.
$ErrorActionPreference='Stop'
$repo='C:\AURION-ONE'
$logDir=Join-Path $env:USERPROFILE 'Desktop\AURION_DIAGNOSTICO'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log=Join-Path $logDir ('execucao-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.txt')
Start-Transcript -Path $log | Out-Null
try {
 Write-Host 'AURION ONE - bootstrap v2'
 if(Test-Path -LiteralPath (Join-Path $repo '.git')){Write-Host ('Branch local: '+(& git -C $repo branch --show-current))}else{Write-Host 'Repositorio local nao localizado; preservando Git.'}
 foreach($port in 11434,8188,8765,5000){$c=New-Object Net.Sockets.TcpClient;try{$a=$c.BeginConnect('127.0.0.1',$port,$null,$null);$ok=$a.AsyncWaitHandle.WaitOne(800);if($ok){$c.EndConnect($a)};Write-Host "Porta ${port}: $(if($ok){'ABERTA'}else{'FECHADA'})"}catch{Write-Host "Porta ${port}: FECHADA"}finally{$c.Close()}}
 try{$m=Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 8;Write-Host ('Ollama: '+(($m.models|ForEach-Object name)-join ', '))}catch{Write-Host ('Ollama indisponivel: '+$_.Exception.Message)}
 $jarvis=Join-Path $env:USERPROFILE 'Desktop\painelseguro#1 - Copia\models\OpenJarvis-main'
 foreach($r in @($jarvis,(Join-Path $env:USERPROFILE 'Desktop\painelseguro#1 - Copia\models\opencode-dev'),'C:\COMFYUI\ComfyUI_windows_portable','F:\models')){Write-Host "Projeto $r : $(Test-Path -LiteralPath $r)"}
 if(-not(Test-Path -LiteralPath (Join-Path $jarvis 'pyproject.toml'))){throw 'Fonte OpenJarvis ausente no caminho conhecido.'}
 $candidates=New-Object 'System.Collections.Generic.List[string]'
 foreach($p in @((Join-Path $repo '.venv\Scripts\python.exe'),(Join-Path $repo 'remote-agent\.venv\Scripts\python.exe'),(Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'),(Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),(Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe'),'C:\Python313\python.exe','C:\Python312\python.exe','C:\Python311\python.exe')){if(Test-Path -LiteralPath $p){$candidates.Add($p)}}
 try{$found=where.exe python 2>$null;foreach($p in $found){if(Test-Path -LiteralPath $p){$candidates.Add($p)}}}catch{}
 try{$found=& py -0p 2>$null;foreach($line in $found){if($line -match '([A-Za-z]:\\[^\r\n]*?python(?:\.exe)?)\s*$'){$p=$matches[1];if(Test-Path -LiteralPath $p){$candidates.Add($p)}}}}catch{}
 $python=$null
 foreach($p in ($candidates|Select-Object -Unique)){try{$v=(& $p -c 'import sys;print("%s.%s %s"%(sys.version_info.major,sys.version_info.minor,64 if sys.maxsize>2**32 else 32))' 2>$null | Out-String).Trim();Write-Host ('Python: '+$p+' / '+$v);if($v -match '^3\.(10|11|12|13) 64$'){$python=$p;break}}catch{Write-Host ('Python nao utilizavel: '+$p)}}
 if(-not $python){Write-Host 'Python 64-bit 3.10-3.13 nao encontrado. Instalacao automatica nao realizada: verifique arquitetura/instalador do Python.';return}
 $venv=Join-Path $env:LOCALAPPDATA 'AURION-ONE\jarvis-venv';$py=Join-Path $venv 'Scripts\python.exe'
 if(-not(Test-Path -LiteralPath $py)){Write-Host 'Criando ambiente isolado Jarvis';& $python -m venv $venv;if($LASTEXITCODE -ne 0){throw 'Falha ao criar ambiente Jarvis'}}
 Write-Host 'Instalando OpenJarvis no ambiente isolado (pode baixar dependencias)'
 & $py -m pip install --disable-pip-version-check -e $jarvis
 if($LASTEXITCODE -ne 0){throw ('pip falhou com codigo '+$LASTEXITCODE)}
 $exe=Join-Path $venv 'Scripts\jarvis.exe'
 if(-not(Test-Path -LiteralPath $exe)){throw 'Instalacao terminou mas jarvis.exe nao foi encontrado'}
 Write-Host 'Testando Jarvis --help';& $exe --help;if($LASTEXITCODE -ne 0){throw ('jarvis --help falhou: '+$LASTEXITCODE)}
 Write-Host ('JARVIS CLI OK: '+$exe)
 Write-Host 'ATENCAO: CLI testada; chat do painel, conexao POCO e automacao de tarefas ainda nao verificados.'
}catch{Write-Host ('ERRO: '+$_.Exception.Message)}finally{Stop-Transcript|Out-Null;Write-Host ('Relatorio: '+$log)}
