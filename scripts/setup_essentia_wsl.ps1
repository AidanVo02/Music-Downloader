$ErrorActionPreference = "Stop"

Write-Host "Enabling WSL prerequisites..."
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

Write-Host "Installing WSL..."
wsl.exe --install --no-distribution

Write-Host ""
Write-Host "WSL prerequisites are installed."
Write-Host "Restart Windows, then run:"
Write-Host "  wsl.exe --install -d Ubuntu"
