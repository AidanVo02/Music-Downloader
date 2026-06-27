#!/usr/bin/env bash
set -euo pipefail

VENV_DIR="${HOME}/.venvs/music-downloader-essentia"

sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv python3-full ffmpeg libfftw3-dev libyaml-dev libtag1-dev libchromaprint-dev

mkdir -p "$(dirname "$VENV_DIR")"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install essentia

echo
echo "Essentia installed into: $VENV_DIR"
echo "Verifier:"
echo "  $VENV_DIR/bin/python -c 'import essentia.standard as es; print(\"essentia_ok\")'"
