$ErrorActionPreference = "Stop"
$Bootstrap = Join-Path $PSScriptRoot "..\scripts\bootstrap_windows.ps1"
if (-not (Test-Path -LiteralPath $Bootstrap)) { throw "bootstrap script missing" }
$Tokens = $null
$Errors = $null
$Ast = [System.Management.Automation.Language.Parser]::ParseFile($Bootstrap, [ref]$Tokens, [ref]$Errors)
if ($Errors.Count -ne 0) { throw "PowerShell parse errors: $($Errors | Out-String)" }
$Source = Get-Content -LiteralPath $Bootstrap -Raw
foreach ($Required in @(
    'if (Test-AurionReady)',
    '$ServerProcess = Start-Process',
    'if ($ServerProcess.HasExited)',
    'if (-not $Ready)',
    'Start-Process $PortalUrl',
    '$ServerProcess.WaitForExit()'
)) { if (-not $Source.Contains($Required)) { throw "Missing startup guard: $Required" } }
$IndexStart = $Source.IndexOf('$ServerProcess = Start-Process')
$IndexWait = $Source.IndexOf('for ($Attempt = 1;')
$IndexReady = $Source.IndexOf('Write-Host "[AURION] Health-check OK. Abrindo portal..."')
if ($IndexStart -lt 0 -or $IndexWait -le $IndexStart -or $IndexReady -le $IndexWait) {
    throw "Server startup and readiness confirmation are out of order"
}
$Def = $Ast.Find({ param($Node) $Node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $Node.Name -eq "Test-AurionReady" }, $true)
if (-not $Def) { throw "Test-AurionReady function not found" }
. ([scriptblock]::Create($Def.Extent.Text))
function Invoke-RestMethod { return [pscustomobject]@{service="aurion-home-node";status="online"} }
if (-not (Test-AurionReady)) { throw "Expected valid AURION health to pass" }
function Invoke-RestMethod { return [pscustomobject]@{service="foreign-service";status="online"} }
if (Test-AurionReady) { throw "Foreign service must not pass health check" }
function Invoke-RestMethod { return [pscustomobject]@{service="aurion-home-node";status="failed"} }
if (Test-AurionReady) { throw "Non-online AURION must not pass health check" }
function Invoke-RestMethod { throw "Connection refused" }
if (Test-AurionReady) { throw "Unreachable service must not pass health check" }
Write-Host "PASS: Windows PowerShell syntax, start-order and 4 simulated health outcomes"
