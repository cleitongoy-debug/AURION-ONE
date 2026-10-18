# SPYDR / VIGIA 2026-10-18 — unica entrada. Nao substitui AURION_COLETOR.
param([switch]$RunOnly,[switch]$NoSchedule)
$ErrorActionPreference = 'Stop'
$Here=Split-Path -Parent $PSCommandPath
$TaskName='AURION_SPYDR_VIGIA_UNICO'
$Python=$null; $Prefix=@()
$Launch=Get-Command 'py.exe' -ErrorAction SilentlyContinue
if($Launch){$Python=$Launch.Source;$Prefix=@('-3')}
else {$Launch=Get-Command 'python.exe' -ErrorAction SilentlyContinue; if($Launch){$Python=$Launch.Source}}
if(-not $Python){ Write-Host '[SPYDR] Python nao localizado. Nenhum arquivo alterado.'; exit 2 }
$Roots=@(
 'C:\######AGENTE#####STATUS######\#BASE##177#',
 'C:\######AGENTE#####STATUS######\##BASE#777',
 'C:\AURION',
 'C:\AURION-ONE'
)
$ValidRoots=@($Roots | Where-Object { Test-Path -LiteralPath $_ -PathType Container })
if(-not $ValidRoots.Count){ Write-Host '[SPYDR] Nenhuma base AURION reconhecida no PC. Nenhum scan arbitrario.'; exit 3 }
$Script=Join-Path $Here 'SPYDR_VIGIA.py'
if(-not (Test-Path -LiteralPath $Script)){Write-Host '[SPYDR] Motor ausente.'; exit 4}
# Agenda depois do primeiro run, nao pede administrador nem toca no agendamento original.
if(-not $RunOnly -and -not $NoSchedule){
 try{
  $Exists=Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
  if(-not $Exists){
   $Arg='-NoProfile -ExecutionPolicy Bypass -File "' + (Join-Path $Here 'REACENDER_SPYDR.ps1') + '" -RunOnly'
   $Action=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $Arg -WorkingDirectory $Here
   $Trigger=New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(15)) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 365)
   Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Description 'AURION SPYDR: varredura limitada, local, sem segredos, a cada 15 min' -ErrorAction Stop | Out-Null
   Write-Host '[SPYDR] Agendamento a cada 15 min criado (apenas enquanto Windows ligado).'
  } else {Write-Host '[SPYDR] Agendamento ja existe. Nenhuma alteracao no registro.'}
 }catch{ Write-Host ('[SPYDR] Agendamento nao instalado: '+$_.Exception.GetType().Name+'; executando uma unica rodada.') }
}
$ArgsList= @($Prefix)+@($Script)
foreach($R in $ValidRoots){$ArgsList+=@('--root',$R)}
Write-Host ('[SPYDR] Raizes autorizadas: '+$ValidRoots.Count+' · Leitura de metadados, sem comandos remotos')
& $Python @ArgsList
exit $LASTEXITCODE