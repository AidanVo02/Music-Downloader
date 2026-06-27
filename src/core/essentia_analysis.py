"""Shared Essentia analysis helpers for native and external runners."""
import math

import numpy as np

ESSENTIA_SAMPLE_RATE = 44100
MIN_TRACK_SECONDS = 8
TEMPO_MIN = 70.0
TEMPO_MAX = 190.0
ESSENTIA_SEGMENT_SECONDS = 35
ESSENTIA_SEGMENT_HOP_SECONDS = 20
ESSENTIA_EDGE_SKIP_SECONDS = 12
ESSENTIA_MIN_SEGMENT_SECONDS = 15
ESSENTIA_BPM_BIN_SIZE = 2.0
ESSENTIA_FULL_TRACK_WEIGHT = 1.35
ESSENTIA_KEY_MIN_STRENGTH = 0.18


def normalize_bpm_octave(bpm):
    """Fold tempo into the typical DJ/music BPM range."""
    if bpm is None:
        return None

    bpm = float(bpm)
    if not np.isfinite(bpm) or bpm <= 0:
        return None

    while bpm < TEMPO_MIN:
        bpm *= 2.0
    while bpm > TEMPO_MAX:
        bpm /= 2.0
    return bpm


def analyze_file_with_essentia(file_path, backend="essentia"):
    """Analyze a file with Essentia and return BPM/key plus confidence."""
    import essentia.standard as es

    audio = es.MonoLoader(filename=file_path, sampleRate=ESSENTIA_SAMPLE_RATE)()
    return analyze_audio_with_essentia(audio, es, backend=backend)


def analyze_audio_with_essentia(audio, es, backend="essentia"):
    """Analyze audio samples with Essentia using segment voting."""
    audio = np.asarray(audio, dtype=float).reshape(-1)
    if audio.size < ESSENTIA_SAMPLE_RATE * MIN_TRACK_SECONDS:
        return _empty_result(backend)

    rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
    key_extractor = es.KeyExtractor(
        sampleRate=ESSENTIA_SAMPLE_RATE,
        frameSize=4096,
        hopSize=2048,
        profileType="edma",
    )

    bpm_candidates = []
    key_votes = {}
    analyzed_segments = 0

    for segment_audio, base_weight, is_full_track in _iter_analysis_segments(audio):
        if segment_audio.size < ESSENTIA_SAMPLE_RATE * ESSENTIA_MIN_SEGMENT_SECONDS:
            continue

        analyzed_segments += 1
        segment_weight = max(base_weight, 1e-6)
        if is_full_track:
            segment_weight *= ESSENTIA_FULL_TRACK_WEIGHT

        bpm, _, _, _, _ = rhythm_extractor(segment_audio)
        bpm = normalize_bpm_octave(bpm)
        if bpm:
            bpm_candidates.append((float(bpm), segment_weight))

        key, scale, strength = key_extractor(segment_audio)
        strength = float(strength) if strength is not None else 0.0
        if key and strength > 0:
            label = f"{key} {scale}"
            weighted_strength = segment_weight * max(strength, 1e-3)
            total_weight, total_strength, total_count = key_votes.get(label, (0.0, 0.0, 0))
            key_votes[label] = (
                total_weight + weighted_strength,
                total_strength + strength,
                total_count + 1,
            )

    bpm, bpm_confidence = _aggregate_bpm_candidates(bpm_candidates)
    key_str, key_confidence, key_strength = _aggregate_key_votes(key_votes)

    return {
        "backend": backend,
        "bpm": bpm,
        "bpm_confidence": bpm_confidence,
        "key": key_str,
        "key_confidence": key_confidence,
        "key_strength": key_strength,
        "segment_count": analyzed_segments,
    }


def _empty_result(backend):
    return {
        "backend": backend,
        "bpm": None,
        "bpm_confidence": 0.0,
        "key": None,
        "key_confidence": 0.0,
        "key_strength": 0.0,
        "segment_count": 0,
    }


def _iter_analysis_segments(audio):
    """Yield full-track and mid-track segments for voting."""
    total_samples = audio.size
    yield audio, _segment_weight(audio), True

    segment_size = ESSENTIA_SAMPLE_RATE * ESSENTIA_SEGMENT_SECONDS
    hop_size = ESSENTIA_SAMPLE_RATE * ESSENTIA_SEGMENT_HOP_SECONDS
    edge_skip = ESSENTIA_SAMPLE_RATE * ESSENTIA_EDGE_SKIP_SECONDS
    min_segment = ESSENTIA_SAMPLE_RATE * ESSENTIA_MIN_SEGMENT_SECONDS

    if total_samples < max(segment_size, min_segment) + (2 * edge_skip):
        return

    start = min(edge_skip, max(total_samples - segment_size, 0))
    last_start = max(total_samples - segment_size - edge_skip, start)
    segment_starts = list(range(start, last_start + 1, hop_size))
    if not segment_starts or segment_starts[-1] != last_start:
        segment_starts.append(last_start)

    for start_index in segment_starts:
        end_index = min(start_index + segment_size, total_samples)
        segment_audio = audio[start_index:end_index]
        if segment_audio.size < min_segment:
            continue
        yield segment_audio, _segment_weight(segment_audio), False


def _segment_weight(segment_audio):
    """Use RMS energy and duration to weight segment votes."""
    if segment_audio.size == 0:
        return 0.0
    rms = math.sqrt(float(np.mean(np.square(segment_audio))))
    duration = segment_audio.size / ESSENTIA_SAMPLE_RATE
    duration_factor = max(min(duration / ESSENTIA_SEGMENT_SECONDS, 1.0), 0.45)
    return max(rms * duration_factor, 1e-6)


def _aggregate_bpm_candidates(candidates):
    """Cluster BPM candidates and return a dominant weighted tempo."""
    if not candidates:
        return None, 0.0

    total_weight = 0.0
    tempo_votes = {}
    for bpm, weight in candidates:
        total_weight += float(weight)
        bpm_bin = int(round(float(bpm) / ESSENTIA_BPM_BIN_SIZE))
        bucket_weight, bucket_value = tempo_votes.get(bpm_bin, (0.0, 0.0))
        tempo_votes[bpm_bin] = (
            bucket_weight + float(weight),
            bucket_value + float(weight) * float(bpm),
        )

    dominant_bin, (dominant_weight, dominant_sum) = max(
        tempo_votes.items(),
        key=lambda item: item[1][0],
    )
    dominant_bpm = dominant_sum / max(dominant_weight, 1e-9)
    dominant_center = dominant_bin * ESSENTIA_BPM_BIN_SIZE

    agreement_weight = 0.0
    for bpm, weight in candidates:
        if abs(float(bpm) - dominant_center) <= ESSENTIA_BPM_BIN_SIZE * 1.5:
            agreement_weight += float(weight)

    vote_share = dominant_weight / max(total_weight, 1e-9)
    agreement_share = agreement_weight / max(total_weight, 1e-9)
    confidence = min(1.0, (vote_share * 0.55) + (agreement_share * 0.45))
    return int(round(dominant_bpm)), float(confidence)


def _aggregate_key_votes(key_votes):
    """Select the most stable key from segment votes."""
    if not key_votes:
        return None, 0.0, 0.0

    total_weight = sum(weight for weight, _, _ in key_votes.values())
    best_key, (best_weight, strength_sum, sample_count) = max(
        key_votes.items(),
        key=lambda item: item[1][0],
    )
    average_strength = strength_sum / max(sample_count, 1)
    vote_share = best_weight / max(total_weight, 1e-9)
    confidence = min(1.0, (vote_share * 0.7) + (min(average_strength, 1.0) * 0.3))

    if average_strength < ESSENTIA_KEY_MIN_STRENGTH and confidence < 0.45:
        return None, float(confidence), float(average_strength)

    return best_key, float(confidence), float(average_strength)
