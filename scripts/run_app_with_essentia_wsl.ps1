$ErrorActionPreference = "Stop"

$wslHome = (wsl.exe -e sh -lc 'printf %s "$HOME"' 2>$null).Trim()
if (-not $wslHome) {
    throw "Could not resolve WSL home directory."
}

$wslPython = "$wslHome/.venvs/music-downloader-essentia/bin/python"

$env:ESSENTIA_COMMAND = "wsl.exe -e $wslPython"
python app.py
