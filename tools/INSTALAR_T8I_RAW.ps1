$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { throw "Python nao encontrado no PATH." }
Write-Host "[AURION T8I] Python: $py"
& $py -m pip install --disable-pip-version-check --no-input -r (Join-Path $root "requirements-t8i.txt")
if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar dependencias T8I." }
& $py -c "import rawpy, numpy, PIL; print('T8I RAW LAB OK', rawpy.__version__, numpy.__version__, PIL.__version__)"
if ($LASTEXITCODE -ne 0) { throw "Dependencias instaladas, mas o teste de importacao falhou." }
Write-Host "[AURION T8I] Dependencias validadas."
