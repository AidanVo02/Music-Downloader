"""BPM and musical key detection module."""
import json
import os
import shlex
import subprocess

import numpy as np

from .essentia_analysis import (
    ESSENTIA_KEY_MIN_STRENGTH,
    analyze_file_with_essentia,
    normalize_bpm_octave,
)

# Key profiles for Krumhansl-Schmuckler correlation scoring.
KEY_PROFILES_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88], dtype=float)
KEY_PROFILES_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17], dtype=float)
KEY_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

SUPPORTED_EXTENSIONS = {".mp3", ".m4a", ".flac", ".wav", ".ogg"}
MIN_TRACK_SECONDS = 8
LIBROSA_SAMPLE_RATE = 22050
LIBROSA_ANALYSIS_SECONDS = 180
TEMPO_MIN = 70.0
TEMPO_MAX = 190.0
CHROMA_HOP_LENGTH = 512
KEY_WINDOW_SECONDS = 12
KEY_WINDOW_HOP_SECONDS = 6
ESSENTIA_COMMAND_ENV = "ESSENTIA_COMMAND"
ESSENTIA_PYTHON_ENV = "ESSENTIA_PYTHON"
ESSENTIA_RUNNER_TIMEOUT = 90
ESSENTIA_BPM_MIN_CONFIDENCE = 0.34
ESSENTIA_KEY_MIN_CONFIDENCE = 0.36
LIBROSA_DEFAULT_CONFIDENCE = 0.55
LIBROSA_MIN_KEY_CONFIDENCE = 0.18
FINAL_BPM_MIN_CONFIDENCE = 0.46
FINAL_KEY_MIN_CONFIDENCE = 0.44
BPM_CROSSCHECK_TOLERANCE = 3.0
BPM_CROSSCHECK_SOFT_MISMATCH = 5.0
BPM_CROSSCHECK_HARD_MISMATCH = 8.0


def get_detection_backend():
    """Return the highest-priority backend available in this environment."""
    if _has_native_essentia():
        return "essentia-native"
    if _build_external_essentia_command(__file__):
        return "essentia-external"
    try:
        import librosa  # noqa: F401
    except ImportError:
        return "unavailable"
    return "librosa"


def detect_bpm_key_details(file_path, progress_callback=None):
    """
    Detect BPM/key and return result details including backend/confidence.

    Prefers native Essentia when available, then an external Essentia runner,
    and finally falls back to a more robust librosa pipeline that separates
    harmonic/percussive content and uses multi-window voting for key estimation.
    """
    if not os.path.exists(file_path):
        return _empty_result("missing")

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return _empty_result("unsupported")

    def _cb(msg):
        if progress_callback:
            try:
                progress_callback(msg)
            except Exception:
                pass

    _cb("analyzing")

    primary_result = _safe_detect(_detect_with_essentia, file_path, "essentia-native")
    if not _result_has_payload(primary_result):
        primary_result = _safe_detect(_detect_with_external_essentia, file_path, "essentia-external")

    fallback_result = _safe_detect(_detect_with_librosa, file_path, "librosa")
    result = _merge_detection_results(primary_result, fallback_result)
    result = _validate_final_result(result, primary_result, fallback_result)
    if not _result_has_complete_payload(result):
        if not result.get("reject_reasons"):
            result["reject_reasons"] = _build_failure_reasons(primary_result, fallback_result)
        return result

    write_bpm_key_metadata(file_path, result["bpm"], result["key"])
    return result


def detect_bpm_key(file_path, progress_callback=None):
    """Detect BPM and musical key from an audio file."""
    result = detect_bpm_key_details(file_path, progress_callback=progress_callback)
    return result.get("bpm"), result.get("key")


def _detect_with_essentia(file_path):
    """Use Essentia when installed for the most accurate offline analysis."""
    return analyze_file_with_essentia(file_path, backend="essentia-native")


def _has_native_essentia():
    """Check whether the current Python runtime can import Essentia."""
    try:
        import essentia.standard as es  # noqa: F401
    except ImportError:
        return False
    return True


def _detect_with_external_essentia(file_path):
    """Run Essentia through a compatible external Python interpreter."""
    command = _build_external_essentia_command(file_path)
    if not command:
        return {"backend": "essentia-external", "reject_reasons": ["missing_external_command"]}

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=ESSENTIA_RUNNER_TIMEOUT,
        check=False,
    )
    if completed.returncode != 0:
        reason = completed.stderr.strip() or completed.stdout.strip() or f"exit_code:{completed.returncode}"
        return {
            "backend": "essentia-external",
            "reject_reasons": [f"external_runner_failed:{reason[:240]}"],
        }

    stdout = completed.stdout.strip()
    if not stdout:
        return _empty_result("essentia-external")

    payload = json.loads(stdout)
    return _normalize_result_payload(payload, "essentia-external")


def _build_external_essentia_command(file_path):
    """Create a subprocess command for an external Essentia-capable runtime."""
    runner_path = os.path.join(os.path.dirname(__file__), "essentia_runner.py")
    raw_command = os.environ.get(ESSENTIA_COMMAND_ENV, "").strip()
    if raw_command:
        try:
            base_command = shlex.split(raw_command, posix=False)
        except ValueError:
            return None
    else:
        python_path = os.environ.get(ESSENTIA_PYTHON_ENV, "").strip()
        if python_path:
            base_command = [python_path]
        else:
            base_command = _discover_default_external_essentia_command()

    if not base_command:
        return None

    if _is_wsl_command(base_command[0]):
        runner_path = _to_wsl_path(runner_path)
        file_path = _to_wsl_path(file_path)

    return [*base_command, runner_path, file_path]


def _discover_default_external_essentia_command():
    """Auto-detect the default WSL Essentia venv created by the setup script."""
    if os.name != "nt":
        return None

    try:
        completed = subprocess.run(
            [
                "wsl.exe",
                "-e",
                "sh",
                "-lc",
                'if [ -x "$HOME/.venvs/music-downloader-essentia/bin/python" ]; then printf %s "$HOME/.venvs/music-downloader-essentia/bin/python"; fi',
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except Exception:
        return None

    wsl_python = completed.stdout.strip()
    if completed.returncode != 0 or not wsl_python:
        return None
    return ["wsl.exe", "-e", wsl_python]


def _is_wsl_command(command_name):
    """Detect WSL invocations so Windows paths can be translated to /mnt/*."""
    basename = os.path.basename(command_name).lower()
    return basename in {"wsl", "wsl.exe"}


def _to_wsl_path(path):
    """Translate an absolute Windows path into the equivalent WSL mount path."""
    absolute_path = os.path.abspath(path)
    drive, tail = os.path.splitdrive(absolute_path)
    if not drive:
        return absolute_path.replace("\\", "/")

    drive_letter = drive[0].lower()
    return f"/mnt/{drive_letter}{tail.replace('\\', '/')}"


def _detect_with_librosa(file_path):
    """Fallback BPM/key detection using a stronger librosa-based pipeline."""
    try:
        import librosa
    except ImportError:
        return None, None

    y, sr = librosa.load(
        file_path,
        sr=LIBROSA_SAMPLE_RATE,
        mono=True,
        duration=LIBROSA_ANALYSIS_SECONDS,
    )
    if len(y) < sr * MIN_TRACK_SECONDS:
        return None, None

    y, _ = librosa.effects.trim(y, top_db=30)
    if len(y) < sr * MIN_TRACK_SECONDS:
        return None, None

    y_harmonic, y_percussive = librosa.effects.hpss(y)

    bpm, bpm_confidence = _detect_bpm_librosa(librosa, y_percussive, sr)
    key_str, key_confidence = _detect_key_librosa(librosa, y_harmonic, sr)
    return {
        "backend": "librosa",
        "bpm": bpm,
        "bpm_confidence": bpm_confidence,
        "key": key_str,
        "key_confidence": key_confidence,
        "key_strength": key_confidence,
    }


def _detect_bpm_librosa(librosa, y_percussive, sr):
    """Estimate BPM from the percussive signal using local tempo voting."""
    onset_env = librosa.onset.onset_strength(
        y=y_percussive,
        sr=sr,
        aggregate=np.median,
    )
    if onset_env.size < 16 or float(np.max(onset_env)) <= 0:
        return None, 0.0

    tempo_fn = getattr(librosa.feature, "tempo", None)
    if tempo_fn is None:
        tempo_fn = librosa.beat.tempo

    local_tempi = np.asarray(
        tempo_fn(onset_envelope=onset_env, sr=sr, aggregate=None),
        dtype=float,
    ).reshape(-1)
    if local_tempi.size == 0:
        return None, 0.0

    weights = onset_env[: local_tempi.size]
    if weights.size == 0 or float(np.sum(weights)) <= 0:
        weights = np.ones_like(local_tempi)

    normalized_tempi = np.array(
        [normalize_bpm_octave(value) for value in local_tempi],
        dtype=float,
    )
    valid_mask = np.isfinite(normalized_tempi) & (normalized_tempi > 0)
    if not np.any(valid_mask):
        return None, 0.0

    normalized_tempi = normalized_tempi[valid_mask]
    weights = weights[valid_mask]

    tempo_bins = np.rint(normalized_tempi).astype(int)
    tempo_votes = {}
    for tempo_bin, tempo_value, weight in zip(tempo_bins, normalized_tempi, weights):
        total_weight, total_value = tempo_votes.get(tempo_bin, (0.0, 0.0))
        tempo_votes[tempo_bin] = (
            total_weight + float(weight),
            total_value + float(weight) * float(tempo_value),
        )

    dominant_bin, (dominant_weight, dominant_sum) = max(
        tempo_votes.items(),
        key=lambda item: item[1][0],
    )
    dominant_tempo = dominant_sum / max(dominant_weight, 1e-9)

    try:
        beat_tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        beat_tempo = float(np.ravel(beat_tempo)[0])
    except Exception:
        beat_tempo = dominant_tempo

    beat_tempo = normalize_bpm_octave(beat_tempo)
    if beat_tempo and abs(beat_tempo - dominant_tempo) <= 4:
        dominant_tempo = (dominant_tempo * 0.65) + (beat_tempo * 0.35)
    elif beat_tempo:
        total_weight = float(np.sum(weights))
        dominant_share = dominant_weight / max(total_weight, 1e-9)
        if dominant_share < 0.22:
            dominant_tempo = beat_tempo

    agreement_weight = 0.0
    for tempo_value, weight in zip(normalized_tempi, weights):
        if abs(float(tempo_value) - dominant_tempo) <= 2.0:
            agreement_weight += float(weight)

    total_weight = float(np.sum(weights))
    confidence = min(
        1.0,
        ((dominant_weight / max(total_weight, 1e-9)) * 0.6)
        + ((agreement_weight / max(total_weight, 1e-9)) * 0.4),
    )
    return int(round(dominant_tempo)), float(confidence)


def _detect_key_librosa(librosa, y_harmonic, sr):
    """Estimate key from the harmonic signal using multi-window voting."""
    if len(y_harmonic) < sr * MIN_TRACK_SECONDS:
        return None, 0.0

    try:
        tuning = librosa.estimate_tuning(y=y_harmonic, sr=sr)
    except Exception:
        tuning = 0.0

    chroma = librosa.feature.chroma_cqt(
        y=y_harmonic,
        sr=sr,
        hop_length=CHROMA_HOP_LENGTH,
        bins_per_octave=36,
        n_chroma=12,
        tuning=tuning,
    )
    if chroma.size == 0:
        return None, 0.0

    rms = librosa.feature.rms(
        y=y_harmonic,
        frame_length=4096,
        hop_length=CHROMA_HOP_LENGTH,
    ).reshape(-1)
    frame_count = min(chroma.shape[1], rms.size)
    chroma = chroma[:, :frame_count]
    rms = rms[:frame_count]
    if frame_count == 0:
        return None, 0.0

    activity_floor = np.percentile(rms, 35) if np.any(rms > 0) else 0.0
    active_frames = rms > activity_floor
    if not np.any(active_frames):
        active_frames = rms > 0
    if not np.any(active_frames):
        return None, 0.0

    vote_scores = {}
    vote_confidences = {}
    for chroma_avg, window_energy in _iter_key_windows(chroma, rms, sr, active_frames):
        key_name, top_score, margin = _score_key_profile(chroma_avg)
        if key_name is None:
            continue
        vote_weight = max(window_energy, 1e-6) * max(margin, 1e-3) * max(top_score, 0.05)
        vote_scores[key_name] = vote_scores.get(key_name, 0.0) + vote_weight
        vote_confidences[key_name] = vote_confidences.get(key_name, 0.0) + max(margin, 0.0) + max(top_score, 0.0)

    full_track_avg = _weighted_chroma_average(chroma[:, active_frames], rms[active_frames])
    full_track_key, top_score, margin = _score_key_profile(full_track_avg)
    if full_track_key:
        vote_scores[full_track_key] = vote_scores.get(full_track_key, 0.0) + max(margin, 1e-3) * max(top_score, 0.05)
        vote_confidences[full_track_key] = vote_confidences.get(full_track_key, 0.0) + max(margin, 0.0) + max(top_score, 0.0)

    if not vote_scores:
        confidence = max(min((margin * 0.6) + (top_score * 0.4), 1.0), 0.0) if full_track_key else 0.0
        return full_track_key, float(confidence)

    best_key, best_weight = max(vote_scores.items(), key=lambda item: item[1])
    total_weight = sum(vote_scores.values())
    score_signal = vote_confidences.get(best_key, 0.0)
    confidence = min(
        1.0,
        ((best_weight / max(total_weight, 1e-9)) * 0.7)
        + (min(score_signal, 1.0) * 0.3),
    )
    if confidence < LIBROSA_MIN_KEY_CONFIDENCE:
        return full_track_key, float(max(confidence, 0.0))
    return best_key, float(confidence)


def _iter_key_windows(chroma, rms, sr, active_frames):
    """Yield weighted chroma averages over overlapping windows."""
    frames_per_second = sr / CHROMA_HOP_LENGTH
    window_size = max(int(KEY_WINDOW_SECONDS * frames_per_second), 1)
    hop_size = max(int(KEY_WINDOW_HOP_SECONDS * frames_per_second), 1)
    frame_count = chroma.shape[1]

    if frame_count <= window_size:
        weights = rms * active_frames.astype(float)
        if float(np.sum(weights)) > 0:
            yield _weighted_chroma_average(chroma, weights), float(np.sum(weights))
        return

    for start in range(0, frame_count - window_size + 1, hop_size):
        stop = start + window_size
        window_active = active_frames[start:stop]
        if int(np.sum(window_active)) < max(window_size // 5, 12):
            continue

        window_weights = rms[start:stop] * window_active.astype(float)
        if float(np.sum(window_weights)) <= 0:
            continue

        yield _weighted_chroma_average(chroma[:, start:stop], window_weights), float(np.sum(window_weights))


def _weighted_chroma_average(chroma, weights):
    """Compute a normalized weighted average chroma vector."""
    weights = np.asarray(weights, dtype=float).reshape(-1)
    if chroma.shape[1] != weights.size or float(np.sum(weights)) <= 0:
        return np.mean(chroma, axis=1)

    chroma_avg = np.average(chroma, axis=1, weights=weights)
    total = float(np.sum(chroma_avg))
    if total > 0:
        chroma_avg = chroma_avg / total
    return chroma_avg


def _score_key_profile(chroma_avg):
    """Return the best key plus confidence from correlation scoring."""
    chroma_avg = np.asarray(chroma_avg, dtype=float).reshape(-1)
    if chroma_avg.size != 12 or not np.any(np.isfinite(chroma_avg)):
        return None, -1.0, 0.0

    centered_chroma = chroma_avg - np.mean(chroma_avg)
    chroma_norm = np.linalg.norm(centered_chroma)
    if chroma_norm <= 0:
        return None, -1.0, 0.0

    scores = []
    for index in range(12):
        major_profile = np.roll(KEY_PROFILES_MAJOR, index)
        minor_profile = np.roll(KEY_PROFILES_MINOR, index)
        scores.append((f"{KEY_NAMES[index]} major", _normalized_correlation(centered_chroma, chroma_norm, major_profile)))
        scores.append((f"{KEY_NAMES[index]} minor", _normalized_correlation(centered_chroma, chroma_norm, minor_profile)))

    scores.sort(key=lambda item: item[1], reverse=True)
    best_key, best_score = scores[0]
    second_score = scores[1][1] if len(scores) > 1 else -1.0
    return best_key, float(best_score), float(best_score - second_score)


def _normalized_correlation(centered_chroma, chroma_norm, profile):
    """Normalize profile correlation to avoid NaN-heavy comparisons."""
    centered_profile = profile - np.mean(profile)
    profile_norm = np.linalg.norm(centered_profile)
    if chroma_norm <= 0 or profile_norm <= 0:
        return -1.0
    return float(np.dot(centered_chroma, centered_profile) / (chroma_norm * profile_norm))


def _safe_detect(detector, file_path, backend_name):
    """Run a detector and normalize failures into an empty result."""
    try:
        result = detector(file_path)
    except Exception as exc:
        failed = _empty_result(backend_name)
        failed["reject_reasons"] = [f"detector_exception:{type(exc).__name__}"]
        return failed
    return _normalize_result_payload(result, backend_name)


def _normalize_result_payload(payload, backend_name):
    """Normalize detector payloads into a consistent shape."""
    result = _empty_result(backend_name)
    if not isinstance(payload, dict):
        return result

    bpm = payload.get("bpm")
    if bpm is not None:
        normalized_bpm = normalize_bpm_octave(bpm)
        result["bpm"] = int(round(normalized_bpm)) if normalized_bpm else None
    result["bpm_confidence"] = float(max(payload.get("bpm_confidence", 0.0), 0.0))

    key_str = payload.get("key")
    if key_str:
        result["key"] = str(key_str)
    result["key_confidence"] = float(max(payload.get("key_confidence", 0.0), 0.0))
    result["key_strength"] = float(max(payload.get("key_strength", 0.0), 0.0))
    result["segment_count"] = int(max(payload.get("segment_count", 0), 0))
    reject_reasons = payload.get("reject_reasons", [])
    if isinstance(reject_reasons, list):
        result["reject_reasons"] = [str(reason) for reason in reject_reasons]
    return result


def _empty_result(backend_name):
    """Create an empty normalized detection result."""
    return {
        "backend": backend_name,
        "bpm": None,
        "bpm_confidence": 0.0,
        "key": None,
        "key_confidence": 0.0,
        "key_strength": 0.0,
        "segment_count": 0,
        "reject_reasons": [],
    }


def _result_has_payload(result):
    """Return True when a result contains a BPM or key candidate."""
    return bool(result and (result.get("bpm") is not None or result.get("key")))


def _field_is_confident(result, field_name, threshold):
    """Return whether a specific field is present with adequate confidence."""
    if not result:
        return False
    if result.get(field_name) in (None, ""):
        return False

    confidence = float(result.get(f"{field_name}_confidence", 0.0))
    if field_name == "key":
        strength = float(result.get("key_strength", 0.0))
        return confidence >= threshold and strength >= ESSENTIA_KEY_MIN_STRENGTH
    return confidence >= threshold


def _merge_detection_results(primary_result, fallback_result):
    """Prefer Essentia, but use fallback fields when confidence is weak."""
    primary_result = _normalize_result_payload(primary_result, primary_result.get("backend", "primary")) if primary_result else _empty_result("primary")
    fallback_result = _normalize_result_payload(fallback_result, fallback_result.get("backend", "fallback")) if fallback_result else _empty_result("fallback")

    if not _result_has_payload(primary_result) and _result_has_payload(fallback_result):
        return fallback_result

    result = _empty_result(primary_result["backend"])
    bpm_from_primary = _field_is_confident(primary_result, "bpm", ESSENTIA_BPM_MIN_CONFIDENCE)
    key_from_primary = _field_is_confident(primary_result, "key", ESSENTIA_KEY_MIN_CONFIDENCE)

    if bpm_from_primary or fallback_result.get("bpm") is None:
        result["bpm"] = primary_result.get("bpm")
        result["bpm_confidence"] = primary_result.get("bpm_confidence", 0.0)
    else:
        result["bpm"] = fallback_result.get("bpm")
        result["bpm_confidence"] = fallback_result.get("bpm_confidence", LIBROSA_DEFAULT_CONFIDENCE)

    if key_from_primary or fallback_result.get("key") is None:
        result["key"] = primary_result.get("key")
        result["key_confidence"] = primary_result.get("key_confidence", 0.0)
        result["key_strength"] = primary_result.get("key_strength", 0.0)
    else:
        result["key"] = fallback_result.get("key")
        result["key_confidence"] = fallback_result.get("key_confidence", LIBROSA_DEFAULT_CONFIDENCE)
        result["key_strength"] = fallback_result.get("key_confidence", LIBROSA_DEFAULT_CONFIDENCE)

    if result["bpm"] is None and primary_result.get("bpm") is not None:
        result["bpm"] = primary_result.get("bpm")
        result["bpm_confidence"] = primary_result.get("bpm_confidence", 0.0)

    if not result["key"] and primary_result.get("key"):
        result["key"] = primary_result.get("key")
        result["key_confidence"] = primary_result.get("key_confidence", 0.0)
        result["key_strength"] = primary_result.get("key_strength", 0.0)

    if fallback_result.get("bpm") is not None or fallback_result.get("key"):
        if not bpm_from_primary and fallback_result.get("bpm") is not None:
            result["backend"] = f"{primary_result['backend']}+{fallback_result['backend']}"
        if not key_from_primary and fallback_result.get("key"):
            result["backend"] = f"{primary_result['backend']}+{fallback_result['backend']}"

    result["segment_count"] = max(primary_result.get("segment_count", 0), fallback_result.get("segment_count", 0))
    return result


def _validate_final_result(result, primary_result, fallback_result):
    """Require both BPM and key with cross-checked confidence."""
    result = _normalize_result_payload(result, result.get("backend", "result")) if result else _empty_result("result")
    primary_result = _normalize_result_payload(primary_result, primary_result.get("backend", "primary")) if primary_result else _empty_result("primary")
    fallback_result = _normalize_result_payload(fallback_result, fallback_result.get("backend", "fallback")) if fallback_result else _empty_result("fallback")
    reject_reasons = []

    bpm_confidence = _crosscheck_bpm_confidence(
        result.get("bpm"),
        result.get("bpm_confidence", 0.0),
        primary_result.get("bpm"),
        fallback_result.get("bpm"),
    )
    key_confidence = _crosscheck_key_confidence(
        result.get("key"),
        result.get("key_confidence", 0.0),
        primary_result.get("key"),
        fallback_result.get("key"),
    )

    result["bpm_confidence"] = bpm_confidence
    result["key_confidence"] = key_confidence

    if result.get("bpm") is None or bpm_confidence < FINAL_BPM_MIN_CONFIDENCE:
        if result.get("bpm") is None:
            reject_reasons.append("missing_bpm")
        else:
            reject_reasons.append(f"low_bpm_confidence:{bpm_confidence:.3f}")
        result["bpm"] = None
        result["bpm_confidence"] = 0.0

    if not result.get("key") or key_confidence < FINAL_KEY_MIN_CONFIDENCE:
        if not result.get("key"):
            reject_reasons.append("missing_key")
        else:
            reject_reasons.append(f"low_key_confidence:{key_confidence:.3f}")
        result["key"] = None
        result["key_confidence"] = 0.0
        result["key_strength"] = 0.0

    if primary_result.get("bpm") is not None and fallback_result.get("bpm") is not None:
        bpm_delta = abs(float(primary_result["bpm"]) - float(fallback_result["bpm"]))
        if bpm_delta > BPM_CROSSCHECK_TOLERANCE:
            reject_reasons.append(f"bpm_disagreement:{bpm_delta:.2f}")

    if primary_result.get("key") and fallback_result.get("key") and str(primary_result["key"]) != str(fallback_result["key"]):
        reject_reasons.append(f"key_disagreement:{primary_result['key']}!={fallback_result['key']}")

    if not _result_has_complete_payload(result):
        rejected = _empty_result(f"{result['backend']}-rejected")
        rejected["reject_reasons"] = reject_reasons
        return rejected

    if _results_agree_on_bpm(primary_result, fallback_result) or _results_agree_on_key(primary_result, fallback_result):
        result["backend"] = f"{result['backend']}-validated"
    result["reject_reasons"] = reject_reasons
    return result


def _crosscheck_bpm_confidence(final_bpm, base_confidence, primary_bpm, fallback_bpm):
    """Adjust BPM confidence based on agreement between detectors."""
    confidence = float(max(base_confidence, 0.0))
    if final_bpm is None:
        return 0.0

    reference_values = [value for value in (primary_bpm, fallback_bpm) if value is not None]
    if len(reference_values) < 2:
        return confidence

    delta = abs(float(primary_bpm) - float(fallback_bpm))
    if delta <= BPM_CROSSCHECK_TOLERANCE:
        confidence += 0.18
    elif delta >= BPM_CROSSCHECK_HARD_MISMATCH:
        confidence -= 0.28
    elif delta >= BPM_CROSSCHECK_SOFT_MISMATCH:
        confidence -= 0.14

    return float(min(max(confidence, 0.0), 1.0))


def _crosscheck_key_confidence(final_key, base_confidence, primary_key, fallback_key):
    """Adjust key confidence based on agreement between detectors."""
    confidence = float(max(base_confidence, 0.0))
    if not final_key:
        return 0.0

    if primary_key and fallback_key:
        if str(primary_key) == str(fallback_key):
            confidence += 0.22
        else:
            confidence -= 0.20

    return float(min(max(confidence, 0.0), 1.0))


def _results_agree_on_bpm(primary_result, fallback_result):
    """Return True when both detectors agree closely on BPM."""
    primary_bpm = primary_result.get("bpm")
    fallback_bpm = fallback_result.get("bpm")
    if primary_bpm is None or fallback_bpm is None:
        return False
    return abs(float(primary_bpm) - float(fallback_bpm)) <= BPM_CROSSCHECK_TOLERANCE


def _results_agree_on_key(primary_result, fallback_result):
    """Return True when both detectors predict the same key."""
    primary_key = primary_result.get("key")
    fallback_key = fallback_result.get("key")
    return bool(primary_key and fallback_key and str(primary_key) == str(fallback_key))


def _result_has_complete_payload(result):
    """Return True when a result contains both BPM and key."""
    return bool(result and result.get("bpm") is not None and result.get("key"))


def _build_failure_reasons(primary_result, fallback_result):
    """Summarize why both backends failed to produce a usable result."""
    reasons = []
    for label, result in (("primary", primary_result), ("fallback", fallback_result)):
        if not result:
            reasons.append(f"{label}:missing_result")
            continue

        backend = result.get("backend", label)
        if result.get("bpm") is None:
            reasons.append(f"{backend}:no_bpm")
        if not result.get("key"):
            reasons.append(f"{backend}:no_key")

        extra_reasons = result.get("reject_reasons", [])
        if extra_reasons:
            reasons.extend(f"{backend}:{reason}" for reason in extra_reasons)

    deduped = []
    seen = set()
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        deduped.append(reason)
    return deduped


def write_bpm_key_metadata(file_path, bpm, key_str):
    """Write BPM and key metadata to audio files using mutagen."""
    try:
        from mutagen.flac import FLAC
        from mutagen.id3 import ID3, TBPM, TXXX
        from mutagen.mp4 import MP4
    except ImportError:
        return

    ext = os.path.splitext(file_path)[1].lower()
    bpm_str = str(bpm) if bpm else ""
    key_str = key_str or ""

    try:
        if ext == ".mp3":
            try:
                audio = ID3(file_path)
            except Exception:
                audio = ID3()
            if bpm_str:
                audio["TBPM"] = TBPM(encoding=3, text=[bpm_str])
            if key_str:
                audio["TXXX:Initial Key"] = TXXX(encoding=3, desc="Initial Key", text=[key_str])
            audio.save(file_path)

        elif ext == ".m4a":
            audio = MP4(file_path)
            if bpm_str:
                audio["\xa9BPM"] = [int(bpm)]
            if key_str:
                audio["----:com.apple.iTunes:KEY"] = [key_str]
            audio.save()

        elif ext == ".flac":
            audio = FLAC(file_path)
            if bpm_str:
                audio["BPM"] = bpm_str
            if key_str:
                audio["KEY"] = key_str
            audio.save()

    except Exception:
        pass
