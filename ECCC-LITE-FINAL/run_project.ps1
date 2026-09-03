param(
    [switch]$Install
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = "1"
Set-Location $PSScriptRoot

if ($Install) {
    python -m pip install -r requirements.txt
}

python -X utf8 scripts/run_full_project.py

