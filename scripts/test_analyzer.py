"""Quick analyzer smoke test for BPM/key backend selection."""
from __future__ import annotations

import argparse
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.core.analyzer import detect_bpm_key_details, get_detection_backend


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("audio_file", nargs="?")
    args = parser.parse_args()

    backend = get_detection_backend()
    print(f"backend={backend}")

    if not args.audio_file:
        return

    audio_file = os.path.abspath(args.audio_file)
    result = detect_bpm_key_details(audio_file)
    print(f"file={audio_file}")
    print(f"backend_used={result.get('backend')}")
    print(f"bpm={result.get('bpm')}")
    print(f"bpm_confidence={result.get('bpm_confidence')}")
    print(f"key={result.get('key')}")
    print(f"key_confidence={result.get('key_confidence')}")
    print(f"reject_reasons={result.get('reject_reasons')}")


if __name__ == "__main__":
    main()
