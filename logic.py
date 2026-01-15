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
BASE_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads", "Music_Downloaded")

# ----------------------------------

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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

def download_single_song(query, save_folder, codec='mp3', quality='320'):
    try:
        create_base_folder()
        q = generate_search_query(query)
        if not q: raise Exception("Not found")

        ffmpeg_loc = get_ffmpeg_path()
        
        # Cấu hình chuyển đổi (Post-processing)
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{save_folder}/%(title)s.%(ext)s',
            'http_headers': {'User-Agent': 'Mozilla/5.0'},
            'writethumbnail': False, 
            'ffmpeg_location': ffmpeg_loc, # <--- Quan trọng
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': codec,   # Ép chuyển sang mp3/m4a...
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
            
            add_to_history(info.get('title', query), final_path)

        return True, "Success"

    except Exception as e:
        return False, str(e)

def update_core_system():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
        return True, "Updated!"
    except: return False, "Failed."