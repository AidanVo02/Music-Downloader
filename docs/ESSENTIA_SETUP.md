# Essentia Setup

`src/core/analyzer.py` already prefers `Essentia` over `librosa` for BPM/key detection.

## Native install

Use a supported Python environment:

- Linux: `pip install essentia`
- macOS: `pip install essentia`

If `essentia` is importable in the same interpreter that runs the app, no extra setup is needed.

## Windows

Native Windows Python bindings for `essentia` are not supported. The project now supports an external runner so Windows can still use `Essentia` from another environment.

## What I can and cannot automate from this repo

The repo now includes helper scripts, but enabling WSL itself still requires an elevated Windows session outside the current app terminal.

- Admin bootstrap: `scripts/setup_essentia_wsl.ps1`
- WSL package install: `scripts/install_essentia_in_wsl.sh`
- Launch app with WSL runner: `scripts/run_app_with_essentia_wsl.ps1`
- Smoke test backend/analyzer: `scripts/test_analyzer.py`

### Option 1: External Python interpreter

Set `ESSENTIA_PYTHON` to a Python executable that already has `essentia` installed.

```powershell
$env:ESSENTIA_PYTHON = "C:\path\to\python.exe"
python app.py
```

### Option 2: WSL

1. Open an **Administrator PowerShell** and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_essentia_wsl.ps1
```

2. Restart Windows if prompted.
3. Install Ubuntu:

```powershell
wsl.exe --install -d Ubuntu
```

4. Inside Ubuntu, run:

```bash
cd /mnt/c/Users/TuVo/Documents/Codex/2026-06-27/tr/work/Music-Downloader
bash ./scripts/install_essentia_in_wsl.sh
```

Ubuntu 24.04 may block `pip install` into the system interpreter with an `externally-managed-environment` error. The script now creates a Linux-side virtual environment at `~/.venvs/music-downloader-essentia` and installs `essentia` there.

You can verify inside WSL with:

```bash
~/.venvs/music-downloader-essentia/bin/python -c 'import essentia.standard as es; print("essentia_ok")'
```

5. Launch the app from Windows with the WSL-backed runner:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_app_with_essentia_wsl.ps1
```

Shortcuts added in the repo root:

```powershell
.\run-app.ps1
```

or:

```powershell
.\run-app.cmd
```

When `ESSENTIA_COMMAND` starts with `wsl` or `wsl.exe`, the app automatically converts Windows file paths into WSL `/mnt/...` paths before invoking `src/core/essentia_runner.py`.

6. Verify the analyzer backend:

```powershell
python .\scripts\test_analyzer.py
python .\scripts\test_analyzer.py "C:\path\to\track.mp3"
```

If setup is correct, the first command should print `backend=essentia-external`.

## Fallback behavior

If native `Essentia` and the external runner are both unavailable, the app falls back to the `librosa` pipeline automatically.
