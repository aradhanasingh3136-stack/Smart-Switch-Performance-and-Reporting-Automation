param([string]$Python = "python")
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $ProjectRoot
try {
    & $Python (Join-Path $ProjectRoot "run.py")
    if ($LASTEXITCODE -ne 0) { throw "SmartSwitch pipeline failed" }
} finally { Pop-Location }
