param(
    [switch]$Install
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if ($Install) {
    python -m pip install -r requirements.txt
}

python scripts/run_a1.py

