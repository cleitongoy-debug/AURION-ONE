# AURION ONE bootstrap v3. Preserves Git branches and existing environments.
$ErrorActionPreference='Stop'
$repo='C:\AURION-ONE'
$logDir=Join-Path $env:USERPROFILE 'Desktop\AURION_DIAGNOSTICO'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log=Join-Path $logDir ('execucao-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.txt')
Start-Transcript -Path $log | Out-Null
try {
 Write-Host 'AURION ONE - bootstrap v3'
 if(Test-Path -LiteralPath (Join-Path $repo '.git')){Write-Host ('Branch local: '+(& git -C $repo branch --show-current))}
 $jarvis=Join-Path $env:USERPROFILE 'Desktop\painelseguro#1 - Copia\models\OpenJarvis-main'
 if(-not(Test-Path -LiteralPath (Join-Path $jarvis 'pyproject.toml'))){throw 'Fonte OpenJarvis ausente no caminho conhecido.'}
 $candidates=@((Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),(Join-Path $repo '.venv\Scripts\python.exe'),(Join-Path $repo 'remote-agent\.venv\Scripts\python.exe'))
 $python=$null
 foreach($p in $candidates){
  if(-not(Test-Path -LiteralPath $p)){continue}
  try {
   $v=(& $p -c 'import sys;print(sys.version_info.major,sys.version_info.minor,sys.maxsize>2**32)' 2>&1 | Out-String).Trim()
   Write-Host ('Python: '+$p+' / '+$v)
   if($LASTEXITCODE -eq 0 -and $v -match '^3 (10|11|12|13) True$'){$python=$p;break}
  }catch{Write-Host ('Python falhou: '+$p+' / '+$_.Exception.Message)}
 }
 if(-not $python){throw 'Nenhum Python compativel confirmado; nao instalar automaticamente outro Python.'}
 $venv=Join-Path $env:LOCALAPPDATA 'AURION-ONE\jarvis-venv'
 $py=Join-Path $venv 'Scripts\python.exe'
 if(-not(Test-Path -LiteralPath $py)){
  Write-Host ('Criando ambiente Jarvis isolado: '+$venv)
  & $python -m venv $venv
  if($LASTEXITCODE -ne 0){throw ('Falha ao criar venv: '+$LASTEXITCODE)}
 }
 Write-Host 'Instalando OpenJarvis da fonte local; dependencias podem ser baixadas.'
 & $py -m pip install --disable-pip-version-check -e $jarvis
 if($LASTEXITCODE -ne 0){throw ('pip falhou: '+$LASTEXITCODE)}
 $exe=Join-Path $venv 'Scripts\jarvis.exe'
 if(-not(Test-Path -LiteralPath $exe)){throw 'jarvis.exe ausente apos pip'}
 Write-Host 'Testando jarvis --help'
 & $exe --help
 if($LASTEXITCODE -ne 0){throw ('jarvis --help falhou: '+$LASTEXITCODE)}
 Write-Host ('JARVIS CLI OK: '+$exe)
 Write-Host 'Chat PC/POCO e automacao ainda nao testados.'
}catch{Write-Host ('ERRO: '+$_.Exception.Message)}finally{Stop-Transcript|Out-Null;Write-Host ('Relatorio: '+$log)}
