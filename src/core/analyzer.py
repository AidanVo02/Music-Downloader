"""BPM and Musical Key detection module."""
import os
import numpy as np

# Key profiles for Krumhansl-Schmuckler algorithm
KEY_PROFILES_MAJOR = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
KEY_PROFILES_MINOR = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
KEY_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def detect_bpm_key(file_path, progress_callback=None):
    """
    Detect BPM and musical key from audio file.
    Returns (bpm, key_str) or (None, None) on failure.
    Uses onset-based tempo and chroma_cens for key detection.
    """
    try:
        import librosa
    except ImportError:
        return None, None

    if not os.path.exists(file_path):
        return None, None

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ('.mp3', '.m4a', '.flac', '.wav', '.ogg'):
        return None, None

    def _cb(msg):
        if progress_callback:
            try:
                progress_callback(msg)
            except:
                pass

    try:
        _cb("analyzing")
        # Load audio: 45 sec, skip first 10 sec (intro) for key
        y_full, sr = librosa.load(file_path, sr=22050, duration=55, mono=True)
        if len(y_full) < sr * 8:
            return None, None

        # Skip intro (first ~10 sec) for key analysis
        skip = min(int(sr * 10), len(y_full) // 4)
        y_key = y_full[skip: skip + int(sr * 30)]  # 30 sec after intro
        y_bpm = y_full  # Use full for BPM

        # --- BPM: onset strength + beat_track ---
        onset_env = librosa.onset.onset_strength(y=y_bpm, sr=sr)
        tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        bpm = float(tempo) if isinstance(tempo, (int, float)) else float(tempo[0])
        
        # Sanity check: typical music 60-200 BPM
        if 0 < bpm < 60:
            bpm *= 2
        elif bpm > 200:
            bpm /= 2

        # --- KEY: chroma_cens + Krumhansl-Schmuckler ---
        chroma = librosa.feature.chroma_cens(y=y_key, sr=sr)
        chroma_avg = np.mean(chroma, axis=1)

        best_key = None
        best_corr = -999
        for i in range(12):
            major_profile = np.roll(KEY_PROFILES_MAJOR, i)
            minor_profile = np.roll(KEY_PROFILES_MINOR, i)
            corr_maj = np.corrcoef(chroma_avg, major_profile)[0, 1]
            corr_min = np.corrcoef(chroma_avg, minor_profile)[0, 1]
            corr_maj = corr_maj if not np.isnan(corr_maj) else -999
            corr_min = corr_min if not np.isnan(corr_min) else -999
            
            if corr_maj > best_corr:
                best_corr = corr_maj
                best_key = f"{KEY_NAMES[i]} major"
            if corr_min > best_corr:
                best_corr = corr_min
                best_key = f"{KEY_NAMES[i]} minor"

        write_bpm_key_metadata(file_path, int(round(bpm)), best_key)
        return int(round(bpm)), best_key

    except Exception:
        return None, None


def write_bpm_key_metadata(file_path, bpm, key_str):
    """Write BPM and Key to audio file metadata using mutagen."""
    try:
        from mutagen.id3 import ID3, TBPM, TXXX
        from mutagen.mp4 import MP4
        from mutagen.flac import FLAC
    except ImportError:
        return

    ext = os.path.splitext(file_path)[1].lower()
    bpm_str = str(bpm) if bpm else ""
    key_str = key_str or ""

    try:
        if ext == '.mp3':
            try:
                audio = ID3(file_path)
            except Exception:
                audio = ID3()
            if bpm_str:
                audio["TBPM"] = TBPM(encoding=3, text=[bpm_str])
            if key_str:
                audio["TXXX:Initial Key"] = TXXX(encoding=3, desc="Initial Key", text=[key_str])
            audio.save(file_path)

        elif ext == '.m4a':
            audio = MP4(file_path)
            if bpm_str:
                audio["\xa9BPM"] = [int(bpm)]
            if key_str:
                audio["----:com.apple.iTunes:KEY"] = [key_str]
            audio.save()

        elif ext == '.flac':
            audio = FLAC(file_path)
            if bpm_str:
                audio["BPM"] = bpm_str
            if key_str:
                audio["KEY"] = key_str
            audio.save()

    except Exception:
        pass
