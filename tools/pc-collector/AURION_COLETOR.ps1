# AURION ONE - indexador local, somente leitura nas fontes. Windows PowerShell 5.1+.
param(
    [ValidateSet('Scan','AddLink','CheckLinks','OpenConfig','OpenReport','Schedule','Unschedule')]
    [string]$Mode = 'Scan',
    [string]$Root = '',
    [switch]$TestRootOnly
)
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($Root)) { $Root = Split-Path -Parent $PSCommandPath }
$Root = [System.IO.Path]::GetFullPath($Root)
$Out = Join-Path $Root 'AURION_COLETA'
$Machine = ($env:COMPUTERNAME -replace '[^A-Za-z0-9_-]','_')
$MachineOut = Join-Path $Out $Machine
$ConfigPath = Join-Path $Out 'CONFIGURAR_LINKS_E_PERFIS.json'
$Utf8 = New-Object System.Text.UTF8Encoding($false)
New-Item -ItemType Directory -Path $Out,$MachineOut -Force | Out-Null

function Write-SafeJson($Path, $Object) {
    $temp = "$Path.tmp"
    [System.IO.File]::WriteAllText($temp, ($Object | ConvertTo-Json -Depth 10), $Utf8)
    Move-Item -LiteralPath $temp -Destination $Path -Force
}
function New-Config {
    $links = @()
    foreach ($kind in @('drive','drive','drive','drive','github','github','github','huggingface','huggingface','portfolio','social','other')) {
        $links += [ordered]@{ kind=$kind; label=''; url=''; owner='UNASSIGNED'; notes='' }
    }
    [ordered]@{
        schema=1; device_owner='UNASSIGNED'; links=$links
        profile_roots=[ordered]@{ ANARK=@(); DS=@(); DAVI=@(); SPECTRA=@() }
        extra_roots=@(); excluded_directories=@('Windows','Program Files','Program Files (x86)','ProgramData','AppData','$Recycle.Bin','System Volume Information','.git','node_modules','.venv','venv','__pycache__','AURION_COLETA')
        max_new_files_per_run=20000; max_minutes_per_run=25; max_text_bytes_per_file=1048576
        max_total_text_bytes_per_run=52428800; max_hash_bytes_per_file=33554432
        note='Adicione raizes explicitas de perfil antes de atribuir autoria. Nao escreva senhas/tokens aqui. Links sao consultados apenas na opcao 3.'
    }
}
if (!(Test-Path -LiteralPath $ConfigPath)) { Write-SafeJson $ConfigPath (New-Config) }
try { $Config = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json }
catch { throw "Configuração inválida: $ConfigPath. Corrija o JSON; nenhum arquivo foi varrido." }

function Clean-Text([string]$Value) {
    if ($null -eq $Value) { return '' }
    $rows = $Value -split "`r?`n"
    $safe = foreach ($row in $rows) {
        if ($row -match '(?i)(api.?key|token|senha|password|secret|authorization|bearer|private.?key|client.?secret|storepass|keypass|gsk_[a-z0-9]|sk-proj-|nvapi-|hf_[A-Za-z0-9]{12}|ghp_[A-Za-z0-9]{20}|github_pat_|AIza[A-Za-z0-9_-]{20}|-----BEGIN [A-Z ]*PRIVATE KEY-----|eyJ[A-Za-z0-9_-]{30})') { '[LINHA DE CREDENCIAL OMITIDA]' }
        else { $row }
    }
    return ($safe -join "`n")
}
function Safe-Error([string]$Message) { (Clean-Text $Message).Substring(0,[Math]::Min(400,(Clean-Text $Message).Length)) }
function Is-SecretFile([string]$Name) {
    return $Name -match '(?i)(\.jks$|\.keystore$|\.p12$|\.pfx$|\.pem$|\.key$|\.env($|\.)|secret|credential|senha|password|token|chaves?-privad|local#server)'
}
function Valid-Https([string]$Raw) {
    $u = $null
    if (![System.Uri]::TryCreate($Raw,[System.UriKind]::Absolute,[ref]$u)) { return $false }
    if ($u.Scheme -ne 'https' -or $u.UserInfo) { return $false }
    if (($u.Query + $u.Fragment) -match '(?i)(token|key|secret|password|senha|sig|access_token|auth|credential)') { return $false }
    return $true
}
function Profile-For([string]$Path) {
    foreach ($id in @('ANARK','DS','DAVI','SPECTRA')) {
        foreach ($prefix in @($Config.profile_roots.$id)) {
            if (!$prefix) { continue }
            try {
                $p = [System.IO.Path]::GetFullPath([Environment]::ExpandEnvironmentVariables([string]$prefix)).TrimEnd('\') + '\'
                $candidate = [System.IO.Path]::GetFullPath($Path)
                if ($candidate.StartsWith($p,[System.StringComparison]::OrdinalIgnoreCase)) { return $id }
            } catch {}
        }
    }
    return 'UNASSIGNED'
}
function Hint-For([string]$Path) {
    if ($Path -match '(?i)(daiane|ds20|#ds\b)') { return 'DS? (pista no caminho, autoria não confirmada)' }
    if ($Path -match '(?i)(doutor#davi|\bdavi\b|nexus)') { return 'DAVI? (pista no caminho, autoria não confirmada)' }
    if ($Path -match '(?i)(spectra|brenda)') { return 'SPECTRA? (pista no caminho, autoria não confirmada)' }
    if ($Path -match '(?i)(anark|cleiton|painelseguro|aurion-one)') { return 'ANARK? (pista no caminho, autoria não confirmada)' }
    return ''
}
function Topics-For([string]$Value) {
    $topics = @()
    $rules = [ordered]@{
        '3D/VFX'='(?i)\b(c4d|cinema\s*4d|octane|blender|unreal|vfx|3d|rigging|composit)\b'
        'Imagem/Cor'='(?i)\b(cr3|t8i|camera|câmera|fotografia|raw|lut|color|correção|photoshop)\b'
        'Vídeo/Áudio'='(?i)\b(clipe|premiere|davinci|after\s*effects|audio|áudio|motion|timeline)\b'
        'IA/Software'='(?i)\b(comfyui|ollama|python|flask|github|huggingface|agente|modelo|api|workflow)\b'
        'Curso/Estudo'='(?i)\b(curso|certificado|aula|estudo|professor|ementa|conclu[ií]d)\b'
        'Cliente/Projeto'='(?i)\b(cliente|briefing|entrega|portf[oó]lio|projeto|orçamento|contrato)\b'
    }
    foreach ($key in $rules.Keys) { if ($Value -match $rules[$key]) { $topics += $key } }
    return @($topics)
}
function Extract-Text([string]$Path, [string]$Ext, [long]$Size) {
    if (Is-SecretFile ([System.IO.Path]::GetFileName($Path))) { return @{status='credencial_omitida';text=''} }
    if ($Size -gt [long]$Config.max_text_bytes_per_file) { return @{status='grande_demais';text=''} }
    try {
        if ($Ext -in @('.txt','.md','.csv','.tsv','.json','.jsonl','.xml','.html','.htm','.py','.ps1','.bat','.cmd','.js','.kt','.java','.gradle','.yaml','.yml','.ini','.log','.srt')) {
            return @{status='texto';text=[System.IO.File]::ReadAllText($Path)}
        }
        if ($Ext -eq '.docx') {
            Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue
            $z = [System.IO.Compression.ZipFile]::OpenRead($Path)
            try {
                $entry = $z.GetEntry('word/document.xml')
                if (!$entry -or $entry.Length -gt [long]$Config.max_text_bytes_per_file) { return @{status='docx_sem_texto';text=''} }
                $reader = New-Object System.IO.StreamReader($entry.Open())
                try { $xml = $reader.ReadToEnd() } finally { $reader.Dispose() }
                return @{status='docx';text=([System.Net.WebUtility]::HtmlDecode(($xml -replace '</w:p>',"`n" -replace '<[^>]*>','')))}
            } finally { $z.Dispose() }
        }
        if ($Ext -eq '.pdf') {
            $pdf = Get-Command 'pdftotext.exe' -ErrorAction SilentlyContinue
            if ($pdf) { return @{status='pdf';text=((& $pdf.Source -f 1 -l 30 -layout $Path - 2>$null | Out-String))} }
            return @{status='pdf_sem_extrator';text=''}
        }
    } catch { return @{status='falha_extracao';text=''} }
    return @{status='metadados';text=''}
}
function Image-Info([string]$Path, [string]$Ext, [long]$Size) {
    if ($Ext -notin @('.jpg','.jpeg','.png','.webp','.bmp','.gif','.tif','.tiff') -or $Size -gt 33554432) { return $null }
    try {
        Add-Type -AssemblyName System.Drawing -ErrorAction SilentlyContinue
        $img = [System.Drawing.Image]::FromFile($Path)
        try { return @{width=$img.Width;height=$img.Height} } finally { $img.Dispose() }
    } catch { return $null }
}
function Append-Json($Writer, $Value) { $Writer.WriteLine(($Value | ConvertTo-Json -Depth 8 -Compress)) }
function Open-Writer([string]$Path) { [System.IO.StreamWriter]::new($Path,$true,$Utf8) }
function Scan-System {
    $software=@();$services=@();$processes=@();$events=@();$adapters=@()
    foreach ($reg in @('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*')) {
        try { Get-ItemProperty $reg -ErrorAction SilentlyContinue | Where-Object DisplayName | ForEach-Object {
            $software += @{name=$_.DisplayName;version=$_.DisplayVersion;publisher=$_.Publisher;installed=$_.InstallDate}
        } } catch {}
    }
    try { Get-Service | ForEach-Object { $services += @{name=$_.Name;display=$_.DisplayName;status=[string]$_.Status} } } catch {}
    try { Get-Process | ForEach-Object { $processes += @{name=$_.ProcessName;id=$_.Id;started= $(try{$_.StartTime.ToString('o')}catch{''})} } } catch {}
    try { Get-NetAdapter -ErrorAction SilentlyContinue | ForEach-Object { $adapters += @{name=$_.Name;status=[string]$_.Status;description=$_.InterfaceDescription} } } catch {}
    try {
        Get-WinEvent -FilterHashtable @{LogName=@('Application','System');Level=@(2,3);StartTime=(Get-Date).AddDays(-7)} -MaxEvents 200 -ErrorAction Stop |
          ForEach-Object { $events += @{time=$_.TimeCreated.ToString('o');id=$_.Id;provider=$_.ProviderName;level=$_.LevelDisplayName;message=(Safe-Error ([string]$_.Message))} }
    } catch {}
    Write-SafeJson (Join-Path $MachineOut 'PROGRAMAS_INSTALADOS.json') @($software | Sort-Object name,version -Unique)
    Write-SafeJson (Join-Path $MachineOut 'SERVICOS_E_PROCESSOS.json') @{services=$services;processes=$processes;adapters=$adapters}
    Write-SafeJson (Join-Path $MachineOut 'ERROS_WINDOWS_7_DIAS.json') $events
    return @{software=$software.Count;services=$services.Count;processes=$processes.Count;errors=$events.Count}
}
function Install-Schedule {
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -File "{0}" -Mode Scan -Root "{1}"' -f $PSCommandPath,$Root) -WorkingDirectory $Root
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 365)
    Register-ScheduledTask -TaskName 'AURION-COLETOR-LOCAL' -Action $action -Trigger $trigger -Description 'Índice local AURION; sem upload; varredura retomável' -Force | Out-Null
    Write-Host 'Ciclo local de 15 minutos ativado no Agendador de Tarefas.'
}

switch ($Mode) {
    'OpenConfig' { Start-Process notepad.exe -ArgumentList ('"{0}"' -f $ConfigPath); return }
    'OpenReport' { Start-Process explorer.exe -ArgumentList ('"{0}"' -f $MachineOut); return }
    'Schedule' { Install-Schedule; return }
    'Unschedule' { Unregister-ScheduledTask -TaskName 'AURION-COLETOR-LOCAL' -Confirm:$false -ErrorAction SilentlyContinue; Write-Host 'Ciclo automático desativado.'; return }
    'AddLink' {
        $kind = Read-Host 'Tipo (drive/github/huggingface/portfolio/social/other)'
        if ($kind -notin @('drive','github','huggingface','portfolio','social','other')) { throw 'Tipo desconhecido.' }
        $label = Read-Host 'Nome curto'
        $url = Read-Host 'URL HTTPS (sem token na URL)'
        if (!(Valid-Https $url)) { throw 'Use HTTPS válido, sem usuário/senha no endereço.' }
        $owner = Read-Host 'Dono confirmado (ANARK/DS/DAVI/SPECTRA/UNASSIGNED)'
        if ($owner -notin @('ANARK','DS','DAVI','SPECTRA')) { $owner='UNASSIGNED' }
        $empty = @($Config.links | Where-Object { !$_.url -and $_.kind -eq $kind } | Select-Object -First 1)
        if ($empty.Count) { $empty[0].label=$label; $empty[0].url=$url; $empty[0].owner=$owner }
        else { $Config.links += [pscustomobject]@{kind=$kind;label=$label;url=$url;owner=$owner;notes=''} }
        Write-SafeJson $ConfigPath $Config
        Write-Host 'Link salvo localmente. Nenhum arquivo foi enviado.'
        return
    }
    'CheckLinks' {
        $results=@()
        foreach ($item in @($Config.links | Where-Object { $_.url })) {
            if (!(Valid-Https $item.url)) { $results += @{label=$item.label;status='URL_INVALIDA'}; continue }
            try {
                $response=Invoke-WebRequest -Uri $item.url -Method Head -TimeoutSec 8 -MaximumRedirection 2 -UseBasicParsing
                $results += @{label=$item.label;owner=$item.owner;status=[int]$response.StatusCode;at=(Get-Date).ToString('o')}
            } catch { $results += @{label=$item.label;owner=$item.owner;status='INDISPONIVEL_OU_EXIGE_LOGIN';at=(Get-Date).ToString('o')} }
        }
        Write-SafeJson (Join-Path $MachineOut 'LINKS_ESTADO.json') $results
        $results | Format-Table -AutoSize
        return
    }
}

# Exclusão mútua impede ciclos simultâneos, sem mexer nas fontes.
$mutex = New-Object System.Threading.Mutex($false, 'Global\AURION_COLETOR_LOCAL')
$locked = $false
try { $locked = $mutex.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $locked = $true }
if (!$locked) { Write-Host 'Outro ciclo ainda está em execução. Nada duplicado.'; exit 0 }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$manifestPath = Join-Path $MachineOut 'ARQUIVOS.jsonl'
$textPath = Join-Path $MachineOut 'TRECHOS_E_PISTAS.jsonl'
$logPath = Join-Path $MachineOut 'ERROS_DE_LEITURA.log'
$manifest = $null; $texts = $null
try {
    $seen = @{}; $hashes = @{}; $topicCount = @{}; $profileCount = @{}; $byExt = @{}
    if (Test-Path $manifestPath) {
        Get-Content -LiteralPath $manifestPath -ReadCount 500 -Encoding UTF8 | ForEach-Object {
            foreach ($line in $_) { try {
                $old = $line.TrimStart([char]0xfeff) | ConvertFrom-Json
                $seen[[string]$old.path] = [string]$old.signature
                if ($old.sha256) { $h=[string]$old.sha256; if (!$hashes.ContainsKey($h)) { $hashes[$h]=New-Object System.Collections.ArrayList }; if ($hashes[$h].Count -lt 8) { [void]$hashes[$h].Add([string]$old.path) } }
            } catch {} }
        }
    }
    $manifest=Open-Writer $manifestPath; $texts=Open-Writer $textPath
    $keys=Open-Writer (Join-Path $MachineOut 'CHAVES_INVENTARIO.jsonl')
    $roots=New-Object System.Collections.ArrayList
    if (!$TestRootOnly) { foreach ($drive in [System.IO.DriveInfo]::GetDrives()) {
        try { if ($drive.IsReady -and $drive.DriveType -in @([System.IO.DriveType]::Fixed,[System.IO.DriveType]::Removable,[System.IO.DriveType]::Network)) { [void]$roots.Add($drive.RootDirectory.FullName) } } catch {}
    } }
    $extras=if ($TestRootOnly) { @($Root) } else { @($Root)+@($Config.extra_roots) }
    foreach ($extra in $extras) { if ($extra -and (Test-Path -LiteralPath $extra)) { [void]$roots.Add([System.IO.Path]::GetFullPath($extra)) } }
    $roots=@($roots | Select-Object -Unique)
    $queue=New-Object 'System.Collections.Generic.Queue[string]'
    foreach ($r in $roots) { $queue.Enqueue($r) }
    $visited=[System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    $new=0; $unchanged=0; $denied=0; $textBytes=0L; $start=Get-Date; $stopReason='fila concluída'
    $repos=New-Object System.Collections.ArrayList
    $system=if ($TestRootOnly) { @{software=0;services=0;processes=0;errors=0} } else { Scan-System }
    $skippedDirs=@($Config.excluded_directories)
    while ($queue.Count -gt 0) {
        if ($new -ge [int]$Config.max_new_files_per_run) { $stopReason='limite de arquivos novos'; break }
        if (((Get-Date)-$start).TotalMinutes -ge [int]$Config.max_minutes_per_run) { $stopReason='limite de tempo'; break }
        $dir=$queue.Dequeue()
        try {
            $full=[System.IO.Path]::GetFullPath($dir)
            if (!$visited.Add($full)) { continue }
            $di=Get-Item -LiteralPath $full -Force -ErrorAction Stop
            if (($di.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { continue }
            foreach ($sub in [System.IO.Directory]::EnumerateDirectories($full)) {
                try {
                    $name=[System.IO.Path]::GetFileName($sub)
                    if ($name -eq '.git') { if ($repos.Count -lt 2000) { [void]$repos.Add($full) }; continue }
                    if ($name -in $skippedDirs -or $sub.StartsWith($Out,[System.StringComparison]::OrdinalIgnoreCase)) { continue }
                    $queue.Enqueue($sub)
                } catch { $denied++ }
            }
            foreach ($path in [System.IO.Directory]::EnumerateFiles($full)) {
                try {
                    $fi=New-Object System.IO.FileInfo($path)
                    $sig='{0}|{1}' -f $fi.Length,$fi.LastWriteTimeUtc.Ticks
                    if ($seen.ContainsKey($path) -and $seen[$path] -eq $sig) { $unchanged++; continue }
                    $ext=$fi.Extension.ToLowerInvariant();$secret=Is-SecretFile $fi.Name
                    $profile=Profile-For $path; $hint=Hint-For $path
                    $sha=''; if (!$secret -and $fi.Length -le [long]$Config.max_hash_bytes_per_file) {
                        try { $sha=(Get-FileHash -LiteralPath $path -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant() } catch {}
                    }
                    $image=Image-Info $path $ext $fi.Length
                    $record=[ordered]@{scan=$stamp;device=$Machine;path=$path;name=$fi.Name;extension=$ext;bytes=$fi.Length;createdUtc=$fi.CreationTimeUtc.ToString('o');modifiedUtc=$fi.LastWriteTimeUtc.ToString('o');signature=$sig;sha256=$sha;profile=$profile;profileHint=$hint;credentialInventory=$secret;image=$image}
                    Append-Json $manifest $record
                    if ($secret) { Append-Json $keys ([ordered]@{scan=$stamp;path=$path;name=$fi.Name;bytes=$fi.Length;modifiedUtc=$fi.LastWriteTimeUtc.ToString('o');note='Somente existência; valor e hash não coletados'}) }
                    $seen[$path]=$sig; $new++
                    if ($sha) { if (!$hashes.ContainsKey($sha)) { $hashes[$sha]=New-Object System.Collections.ArrayList }; if ($hashes[$sha].Count -lt 8 -and !$hashes[$sha].Contains($path)) { [void]$hashes[$sha].Add($path) } }
                    if (!$byExt.ContainsKey($ext)) {$byExt[$ext]=0};$byExt[$ext]++
                    if (!$profileCount.ContainsKey($profile)) {$profileCount[$profile]=0};$profileCount[$profile]++
                    if (!$secret -and $textBytes -lt [long]$Config.max_total_text_bytes_per_run) {
                        $ex=Extract-Text $path $ext $fi.Length
                        if ($ex.text) {
                            $textBytes += [Math]::Min($fi.Length,[long]$Config.max_text_bytes_per_file)
                            $safe=Clean-Text ([string]$ex.text)
                            $topics=Topics-For ($fi.Name+' '+$safe.Substring(0,[Math]::Min($safe.Length,12000)))
                            foreach($t in $topics) {if (!$topicCount.ContainsKey($t)) {$topicCount[$t]=0};$topicCount[$t]++}
                            $lines=@($safe -split "`n" | Where-Object { $_ -match '(?i)(curso|certificado|\b\d{1,3}(?:[,.]\d+)?\s*(?:h|horas)\b|cliente|projeto|professor|erro|traceback)' } | Select-Object -First 12)
                            $lines=@($lines | ForEach-Object { $_.Substring(0,[Math]::Min($_.Length,220)) })
                            Append-Json $texts ([ordered]@{scan=$stamp;path=$path;profile=$profile;profileHint=$hint;extractor=$ex.status;topics=$topics;excerpt=$safe.Substring(0,[Math]::Min($safe.Length,3000));evidenceLines=$lines})
                        }
                    }
                    if ($new % 500 -eq 0) { Write-Host ("{0} novos / {1} sem mudanças / {2} pastas restantes" -f $new,$unchanged,$queue.Count) }
                    if (($new+$unchanged) % 500 -eq 0 -and ((Get-Date)-$start).TotalMinutes -ge [int]$Config.max_minutes_per_run) { $stopReason='limite de tempo';$queue.Clear();break }
                    if ($new -ge [int]$Config.max_new_files_per_run) { break }
                } catch { $denied++;[System.IO.File]::AppendAllText($logPath,($stamp+' '+(Safe-Error $_.Exception.Message)+"`n"),$Utf8) }
            }
        } catch { $denied++;[System.IO.File]::AppendAllText($logPath,($stamp+' '+(Safe-Error $_.Exception.Message)+"`n"),$Utf8) }
    }
    $duplicates=@();foreach ($h in $hashes.Keys) { if ($hashes[$h].Count -gt 1 -and $duplicates.Count -lt 1000) { $duplicates+=@{sha256=$h;paths=@($hashes[$h])} } }
    Write-SafeJson (Join-Path $MachineOut 'CRUZAMENTOS_DUPLICATAS.json') $duplicates
    $git=Get-Command git.exe -ErrorAction SilentlyContinue
    $repoIndex=@();if ($git) { foreach ($repo in @($repos | Select-Object -Unique | Select-Object -First 100)) {
        try { $head=(& $git.Source -C $repo rev-parse HEAD 2>$null | Select-Object -First 1)
            $repoIndex+=@{path=$repo;head=$head;profile=(Profile-For $repo);profileHint=(Hint-For $repo)}
        } catch {}
    } }
    Write-SafeJson (Join-Path $MachineOut 'REPOSITORIOS_LOCAIS.json') $repoIndex
    $summary=[ordered]@{scan=$stamp;device=$Machine;started=$start.ToString('o');finished=(Get-Date).ToString('o');roots=$roots;newOrChanged=$new;unchanged=$unchanged;readErrors=$denied;stopReason=$stopReason;directoriesRemaining=$queue.Count;profiles=$profileCount;extensions=$byExt;topics=$topicCount;duplicateGroups=$duplicates.Count;localRepositories=$repoIndex.Count;system=$system;method='Tempos de arquivo nao sao horas estudadas; pistas nao confirmam autoria. Nenhum token foi copiado.'}
    Write-SafeJson (Join-Path $MachineOut 'RESUMO_ATUAL.json') $summary
    Write-SafeJson (Join-Path $MachineOut ("RESUMO_{0}.json" -f $stamp)) $summary
    Write-Host ("Concluído: {0} novos/alterados; {1} sem mudanças; {2} erros. Motivo: {3}" -f $new,$unchanged,$denied,$stopReason)
    Write-Host "Relatórios: $MachineOut"
} finally {
    if ($manifest) { $manifest.Dispose() }; if ($texts) { $texts.Dispose() }; if ($keys) { $keys.Dispose() }
    if ($locked) { $mutex.ReleaseMutex() }; $mutex.Dispose()
}
