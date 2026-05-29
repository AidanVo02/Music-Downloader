import yt_dlp
import os
import sys
import platform
import requests
import subprocess
import json
import shutil 
from datetime import datetime
from bs4 import BeautifulSoup

# --- BPM & KEY DETECTION (Krumhansl-Schmuckler) ---
# Key profiles: C, C#, D, Eb, E, F, F#, G, Ab, A, Bb, B
KEY_PROFILES_MAJOR = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
KEY_PROFILES_MINOR = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
KEY_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'] 

# --- CẤU HÌNH ĐƯỜNG DẪN DỮ LIỆU ---
def get_user_data_folder():
    app_name = "MusicDownloader"
    if platform.system() == "Windows":
        base_path = os.getenv('APPDATA')
    elif platform.system() == "Darwin": # macOS
        base_path = os.path.expanduser("~/Library/Application Support")
    else: 
        base_path = os.path.expanduser("~/.local/share")
        
    data_folder = os.path.join(base_path, app_name)
    if not os.path.exists(data_folder):
        try: os.makedirs(data_folder)
        except: pass
    return data_folder

DATA_FOLDER = get_user_data_folder()
HISTORY_FILE = os.path.join(DATA_FOLDER, "history.json")
CONFIG_FILE_PATH = os.path.join(DATA_FOLDER, "config.json") 
BASE_FOLDER = os.path.abspath(os.path.join(os.path.expanduser("~"), "Downloads", "Music_Downloaded"))

# ----------------------------------

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def _sanitize_filename(name):
    """Remove invalid filename chars for Windows/macOS/Linux."""
    invalid = '<>:"/\\|?*'
    for c in invalid:
        name = name.replace(c, '_')
    return name.strip() or "track"

def get_ffmpeg_path():
    """
    Hàm tìm kiếm FFmpeg 'tận cùng ngõ hẻm' cho macOS
    """
    if platform.system() == "Windows":
        # Windows giữ nguyên logic cũ
        if getattr(sys, 'frozen', False): base_path = os.path.dirname(sys.executable)
        else: base_path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_path, "bin", "ffmpeg.exe")
        if os.path.exists(path): return path
        return "ffmpeg"
    else:
        # --- LOGIC MỚI CHO MAC ---
        # 1. Kiểm tra các đường dẫn Homebrew phổ biến (Ưu tiên số 1)
        mac_paths = [
            "/opt/homebrew/bin/ffmpeg",  # Mac M1/M2/M3
            "/usr/local/bin/ffmpeg",     # Mac Intel
            "/usr/bin/ffmpeg",           # System
            "/bin/ffmpeg"
        ]
        
        for p in mac_paths:
            if os.path.exists(p):
                print(f"DEBUG: Tìm thấy FFmpeg tại {p}")
                return p
        
        # 2. Nếu không thấy, thử hỏi hệ thống
        path = shutil.which("ffmpeg")
        if path: return path
            
        return "ffmpeg" # Fallback

def create_base_folder():
    if not os.path.exists(BASE_FOLDER): os.makedirs(BASE_FOLDER)

def get_existing_playlists():
    create_base_folder()
    try:
        items = os.listdir(BASE_FOLDER)
        return [i for i in items if os.path.isdir(os.path.join(BASE_FOLDER, i))]
    except: return []

# --- QUẢN LÝ LỊCH SỬ ---
def load_history():
    if not os.path.exists(HISTORY_FILE): return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return []

def add_to_history(song_name, file_path):
    current_hist = load_history()
    new_record = {
        "name": song_name, "path": file_path,
        "time": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    current_hist.insert(0, new_record)
    if len(current_hist) > 100: current_hist = current_hist[:100]
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(current_hist, f, indent=4, ensure_ascii=False)
    except: pass

def clear_history_data():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f: json.dump([], f); return True
    except: return False

# --- BPM & KEY DETECTION (improved accuracy) ---
def detect_bpm_key(file_path, progress_callback=None):
    """
    Detect BPM and musical key from audio file. Writes results to file metadata.
    Returns (bpm, key_str) or (None, None) on failure.
    Uses: onset-based tempo, chroma_cens for key, skips intro for better accuracy.
    """
    try:
        import librosa
        import numpy as np
    except ImportError:
        return None, None

    if not os.path.exists(file_path):
        return None, None

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ('.mp3', '.m4a', '.flac', '.wav', '.ogg'):
        return None, None

    def _cb(msg):
        if progress_callback:
            try: progress_callback(msg)
            except: pass

    try:
        _cb("analyzing")
        # Load audio: 45 sec, skip first 10 sec (intro) for key - use main section
        y_full, sr = librosa.load(file_path, sr=22050, duration=55, mono=True)
        if len(y_full) < sr * 8:
            return None, None

        # Skip intro (first ~10 sec) for key - chorus/verse usually more representative
        skip = min(int(sr * 10), len(y_full) // 4)
        y_key = y_full[skip: skip + int(sr * 30)]  # 30 sec after intro
        y_bpm = y_full  # Use full for BPM (more stable)

        # --- BPM: onset strength + beat_track for stability ---
        onset_env = librosa.onset.onset_strength(y=y_bpm, sr=sr)
        tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        bpm = float(tempo) if isinstance(tempo, (int, float)) else float(tempo[0])
        # Sanity: typical music 60-200 BPM; half/double tempo is common error
        if 0 < bpm < 60: bpm *= 2
        elif bpm > 200: bpm /= 2

        # --- KEY: chroma_cens (more robust) + Krumhansl-Schmuckler ---
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

# --- XỬ LÝ TẢI ---
def get_spotify_track_name(url):
    try:
        h = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=h)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            return soup.title.string.replace(" | Spotify", "").replace("Song by ", "")
    except: return None

def generate_search_query(query):
    final = query
    if "spotify.com" in query:
        name = get_spotify_track_name(query)
        if name: final = f"{name} Official Audio"
        else: return None
    elif "youtube.com" in query or "youtu.be" in query: return query
    else: final = f"{query} Official Audio"
    return f"ytsearch1:{final}"

def download_single_song(query, save_folder, codec='mp3', quality='320', detect_bpm_key_flag=False, progress_callback=None):
    try:
        create_base_folder()
        q = generate_search_query(query)
        if not q: raise Exception("Not found")

        ffmpeg_loc = get_ffmpeg_path()
        
        # Ensure folder exists and use absolute path
        save_folder = os.path.abspath(save_folder)
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

        # Cấu hình chuyển đổi (Post-processing)
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(save_folder, '%(title)s.%(ext)s'),
            'http_headers': {'User-Agent': 'Mozilla/5.0'},
            'writethumbnail': False, 
            'ffmpeg_location': ffmpeg_loc,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': codec,
                'preferredquality': quality
            }],
            'noplaylist': True, 'quiet': True, 'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(q, download=True)
            if 'entries' in info: info = info['entries'][0]
            
            # Lấy tên file kết quả (đã đổi đuôi)
            fname = ydl.prepare_filename(info).rsplit('.', 1)[0]
            final_path = f"{fname}.{codec}"

            # Detect BPM & Key, write to metadata, and rename file with BPM/Key in filename
            if detect_bpm_key_flag:
                bpm, key_str = detect_bpm_key(final_path, progress_callback=progress_callback)
                if bpm is not None and key_str:
                    dir_path = os.path.dirname(final_path)
                    base = os.path.splitext(os.path.basename(final_path))[0]
                    safe_suffix = f" - {bpm} BPM - {key_str}"
                    new_name = _sanitize_filename(base + safe_suffix) + f".{codec}"
                    new_path = os.path.join(dir_path, new_name)
                    if new_path != final_path and not os.path.exists(new_path):
                        try:
                            os.rename(final_path, new_path)
                            final_path = new_path
                        except OSError:
                            pass
            
            add_to_history(info.get('title', query), final_path)

        return True, "Success"

    except Exception as e:
        return False, str(e)

def update_core_system():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
        return True, "Updated!"
    except: return False, "Failed."


def convert_file(input_path, output_format, bitrate='192k'):
    """
    Convert an input media file to an audio file using ffmpeg.
    output_format: 'mp3', 'wav', 'flac', 'm4a'
    Returns (True, output_path) on success or (False, error_message) on failure.
    """
    try:
        if not os.path.exists(input_path):
            return False, "Input file not found"

        fmt = output_format.lower().lstrip('.')
        if fmt not in ('mp3', 'wav', 'flac', 'm4a'):
            return False, "Unsupported output format"

        ffmpeg = get_ffmpeg_path()

        base = os.path.splitext(input_path)[0]
        out_path = f"{base}.{fmt}"

        # Build ffmpeg command depending on target format
        # Use -y to overwrite and -vn to drop video streams
        if fmt == 'mp3':
            cmd = [ffmpeg, '-y', '-i', input_path, '-vn', '-acodec', 'libmp3lame', '-ab', bitrate, out_path]
        elif fmt == 'wav':
            cmd = [ffmpeg, '-y', '-i', input_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', out_path]
        elif fmt == 'flac':
            cmd = [ffmpeg, '-y', '-i', input_path, '-vn', '-acodec', 'flac', out_path]
        elif fmt == 'm4a':
            cmd = [ffmpeg, '-y', '-i', input_path, '-vn', '-c:a', 'aac', '-b:a', bitrate, out_path]
        else:
            return False, "Unsupported format"

        # Run ffmpeg
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            err = proc.stderr.decode('utf-8', errors='ignore') or 'ffmpeg failed'
            return False, err

        # If conversion produced file, add to history
        if os.path.exists(out_path):
            add_to_history(os.path.basename(out_path), out_path)
            return True, out_path
        else:
            return False, 'Output file not created'

    except Exception as e:
        return False, str(e)