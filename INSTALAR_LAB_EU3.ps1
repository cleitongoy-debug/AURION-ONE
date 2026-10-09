param([string]$Serial = $env:ADB_SERIAL)
$ErrorActionPreference = 'Stop'
$base = $PSScriptRoot
$adb = Join-Path $base 'platform-tools\adb.exe'
$apk = Join-Path $base 'AURION_LAB_EU3_PREVIEW_v7.0.2.apk'
$package = 'one.aurion.poco.v6.preview.quickfix'
$expectedHash = '23138ba5d7e71cdbecd1cf818253662c7e8568b96d5dc867bb70ca528c4fd3b5'
$logDir = Join-Path $base 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir ('instalacao_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.txt')
function Record([string]$text) { $line = '[' + (Get-Date -Format 'o') + '] ' + $text; Write-Host $line; Add-Content -LiteralPath $log -Value $line -Encoding UTF8 }
function Invoke-Adb([string[]]$Arguments) {
    $output = & $adb @Arguments 2>&1
    $code = $LASTEXITCODE
    foreach ($line in $output) { Record ([string]$line) }
    if ($code -ne 0) { throw "ADB retornou $code. Consulte o registro; nenhuma desinstalacao sera feita." }
    return $output
}
try {
    Record 'AURION LAB EU3: instalacao da previa. O pacote principal e seus dados permanecem.'
    if (!(Test-Path -LiteralPath $adb) -or !(Test-Path -LiteralPath $apk)) { throw 'Extraia o pacote ZIP inteiro antes de executar.' }
    if ((Get-FileHash -LiteralPath $apk -Algorithm SHA256).Hash -ne $expectedHash) { throw 'Hash do APK divergente. Instalacao bloqueada.' }
    $null = Invoke-Adb @('start-server')
    $rows = Invoke-Adb @('devices')
    $devices = @($rows | ForEach-Object { if ([string]$_ -match '^([^\s]+)\s+device\s*$') { $Matches[1] } })
    if ($Serial) { if ($Serial -notin $devices) { throw 'O aparelho selecionado nao esta conectado e autorizado.' } }
    elseif ($devices.Count -eq 1) { $Serial = $devices[0] }
    elseif ($devices.Count -eq 0) { throw 'Conecte o POCO por USB, ative depuracao USB e aceite a autorizacao no aparelho. Execute este comando novamente.' }
    else { throw 'Ha mais de um aparelho. Defina ADB_SERIAL para escolher o destino.' }
    Record 'Verificando o estado do aparelho.'
    $null = Invoke-Adb @('-s', $Serial, 'get-state')
    Record 'Instalando com preservacao de dados. Assinatura divergente interrompe este passo.'
    $result = Invoke-Adb @('-s', $Serial, 'install', '-r', $apk)
    if (!($result | Where-Object { [string]$_ -match '^Success\s*$' })) { throw 'ADB nao confirmou Success. Confira o registro.' }
    Record 'Instalacao confirmada. Abrindo a previa.'
    $null = Invoke-Adb @('-s', $Serial, 'shell', 'am', 'start', '-n', "$package/one.aurion.app.MainActivity")
    Record 'Abra Lab IA > Pesquisa metodo EU3. Fila e tempo ficam neste aparelho. Teste fisico e sincronizacao Drive ainda devem ser conferidos.'
    Record ('Registro: ' + $log)
    exit 0
} catch {
    Record ('INTERROMPIDO: ' + $_.Exception.Message)
    Record ('Registro: ' + $log)
    exit 1
}
