$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "scripts\run_app_with_essentia_wsl.ps1"
& powershell -ExecutionPolicy Bypass -File $scriptPath
