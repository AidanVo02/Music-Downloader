"""CLI bridge for running Essentia analysis from another Python runtime."""
import json
import os
import sys

from essentia_analysis import analyze_file_with_essentia


def _emit(payload, exit_code=0):
    sys.stdout.write(json.dumps(payload))
    raise SystemExit(exit_code)


def main():
    if len(sys.argv) != 2:
        _emit({"bpm": None, "key": None, "error": "usage"}, exit_code=1)

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        _emit({"bpm": None, "key": None, "error": "missing_file"}, exit_code=1)

    try:
        payload = analyze_file_with_essentia(file_path, backend="essentia-external")
    except ImportError:
        _emit({"bpm": None, "key": None, "error": "essentia_unavailable"}, exit_code=2)
    _emit(payload)


if __name__ == "__main__":
    main()
