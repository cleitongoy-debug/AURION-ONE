$ErrorActionPreference="SilentlyContinue"
$root=Join-Path $env:USERPROFILE "Desktop\AURION_SCAN"
New-Item -ItemType Directory -Force $root|Out-Null
$r=[ordered]@{time=(Get-Date).ToString("o");os=@{};hardware=@{};gpu=@();disks=@();processes=@();ports=@();software=@();tools=@{};adb=@{};ollama=@{};services=@{};paths=@()}
$os=Get-CimInstance Win32_OperatingSystem;$cs=Get-CimInstance Win32_ComputerSystem;$cpu=Get-CimInstance Win32_Processor
$r.os=@{caption=$os.Caption;version=$os.Version;build=$os.BuildNumber};$r.hardware=@{cpu=($cpu.Name -join "; ");ramGB=[math]::Round($cs.TotalPhysicalMemory/1GB,2)}
$r.gpu=@(Get-CimInstance Win32_VideoController|%{@{name=$_.Name;driver=$_.DriverVersion}})
$r.disks=@(Get-CimInstance Win32_LogicalDisk|%{@{drive=$_.DeviceID;label=$_.VolumeName;sizeGB=[math]::Round($_.Size/1GB,2);freeGB=[math]::Round($_.FreeSpace/1GB,2)}})
$rx="python|comfy|ollama|lm studio|cinema|octane|ffmpeg|node|git|adb|java|davinci|resolve|premiere|photoshop|afterfx|tailscale|aurion|openwebui|docker|wsl"
$r.processes=@(Get-Process|?{$_.ProcessName -match $rx -or $_.Path -match $rx}|%{@{name=$_.ProcessName;pid=$_.Id;path=$_.Path}})
$r.ports=@(Get-NetTCPConnection -State Listen|Sort LocalPort|%{$p=Get-Process -Id $_.OwningProcess;@{address=$_.LocalAddress;port=$_.LocalPort;pid=$_.OwningProcess;process=$p.ProcessName;path=$p.Path}})
$u=@("HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*","HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*","HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*")
$r.software=@(Get-ItemProperty $u|?{$_.DisplayName}|Sort DisplayName -Unique|%{@{name=$_.DisplayName;version=$_.DisplayVersion;location=$_.InstallLocation}})
foreach($x in "python","py","git","node","npm","java","ffmpeg","adb","ollama","nvidia-smi","docker","wsl","tailscale"){$c=Get-Command $x;if($c){$r.tools[$x]=@{path=$c.Source;version=((& $x --version 2>&1|Select -First 3)-join " ")}}else{$r.tools[$x]=@{found=$false}}}
if(Get-Command nvidia-smi){$r.nvidia=((& nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free,utilization.gpu,temperature.gpu --format=csv,noheader 2>&1)-join " | ")}
if(Get-Command adb){$r.adb.devices=((& adb devices -l 2>&1)-join " | ");$r.adb.model=((& adb shell getprop ro.product.model 2>&1)-join "");$r.adb.android=((& adb shell getprop ro.build.version.release 2>&1)-join "");$r.adb.packages=((& adb shell pm list packages 2>&1|Select-String "aurion|termux|xiaomi|fitness|health|tailscale")-join " | ")}
if(Get-Command ollama){$r.ollama.list=((& ollama list 2>&1)-join " | ");$r.ollama.ps=((& ollama ps 2>&1)-join " | ")}
$checks=[ordered]@{ComfyUI="http://127.0.0.1:8188/system_stats";Ollama="http://127.0.0.1:11434/api/tags";OpenWebUI="http://127.0.0.1:8080";Aurion5000="http://127.0.0.1:5000";Aurion8765="http://127.0.0.1:8765/health";P5055="http://127.0.0.1:5055";P5056="http://127.0.0.1:5056";P5057="http://127.0.0.1:5057"}
foreach($k in $checks.Keys){try{$q=Invoke-WebRequest -UseBasicParsing $checks[$k] -TimeoutSec 3;$r.services[$k]=@{url=$checks[$k];ok=$true;http=[int]$q.StatusCode;sample=$q.Content.Substring(0,[Math]::Min(800,$q.Content.Length))}}catch{$r.services[$k]=@{url=$checks[$k];ok=$false;error=$_.Exception.Message}}}
$roots=@("C:\AURION-ONE","C:\AURION-QB-QUANTUN","D:\AURION-QB-QUANTUN","E:\AURION_SYNC","F:\LUMEN#QUANTUM#AURION#Q6","C:\COMFYUI","D:\ComfyUI","C:\######AGENTE#####STATUS######\base#777\models","C:\Program Files\Maxon Cinema 4D 2023")
foreach($p in $roots){if(Test-Path -LiteralPath $p){$r.paths+=@{path=$p;exists=$true;items=(Get-ChildItem -LiteralPath $p -Force|Measure).Count}}}
$r|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 (Join-Path $root "AURION_SCAN_MASTER.json")
$r.services.GetEnumerator()|%{"$($_.Key) = $(if($_.Value.ok){'ONLINE HTTP '+$_.Value.http}else{'OFFLINE'})"}|Set-Content -Encoding UTF8 (Join-Path $root "AURION_SERVICOS.txt")
$r.ports|%{"$($_.address):$($_.port) $($_.process) PID=$($_.pid)"}|Set-Content -Encoding UTF8 (Join-Path $root "AURION_PORTAS.txt")
$r.software|%{"$($_.name) | $($_.version) | $($_.location)"}|Set-Content -Encoding UTF8 (Join-Path $root "AURION_SOFTWARE.txt")
Write-Host "AURION SCAN CONCLUIDO" -ForegroundColor Yellow
Write-Host $root -ForegroundColor Cyan
Start-Process explorer.exe $root
