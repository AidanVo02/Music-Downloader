import yt_dlp
import os
import sys
import platform
import requests
import urllib.parse
import subprocess
import json
from datetime import datetime
from bs4 import BeautifulSoup 

# --- CẤU HÌNH ĐƯỜNG DẪN CỐ ĐỊNH ---
def get_app_path():
    """
    Hàm xác định vị trí file EXE đang chạy.
    Dùng hàm này để lưu file Config/History vĩnh viễn, không bị xóa khi tắt App.
    """
    if getattr(sys, 'frozen', False):
        # Nếu đang chạy bằng file .exe
        return os.path.dirname(sys.executable)
    else:
        # Nếu đang chạy bằng file code .py
        return os.path.dirname(os.path.abspath(__file__))

# Xác định các thư mục quan trọng
APP_PATH = get_app_path()
BASE_FOLDER = os.path.join(APP_PATH, "Downloads")
DATA_FOLDER = os.path.join(APP_PATH, "data")
HISTORY_FILE = os.path.join(DATA_FOLDER, "history.json")

# Đảm bảo folder 'data' luôn tồn tại để chứa file lịch sử
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# ----------------------------------

def resource_path(relative_path):
    """
    Hàm này chỉ dùng để lấy tài nguyên TĨNH (như icon, theme, ffmpeg)
    được đóng gói BÊN TRONG file exe.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_ffmpeg_path():
    """Tìm FFmpeg thông minh (như phiên bản trước)"""
    if platform.system() == "Windows":
        exe_name = "ffmpeg.exe"
        # 1. Tìm trong folder 'bin' cạnh file exe (Ưu tiên)
        path_in_bin = os.path.join(APP_PATH, "bin", exe_name)
        if os.path.exists(path_in_bin): return path_in_bin
            
        # 2. Tìm trong folder nội bộ (resource)
        path_internal = resource_path(os.path.join("bin", exe_name))
        if os.path.exists(path_internal): return path_internal
            
        return "ffmpeg"
    else:
        return "ffmpeg"

def create_base_folder():
    if not os.path.exists(BASE_FOLDER):
        os.makedirs(BASE_FOLDER)

def get_existing_playlists():
    create_base_folder()
    try:
        items = os.listdir(BASE_FOLDER)
        playlists = [item for item in items if os.path.isdir(os.path.join(BASE_FOLDER, item))]
        return playlists
    except:
        return []

# --- QUẢN LÝ LỊCH SỬ (ĐÃ SỬA LỖI MẤT FILE) ---
def load_history():
    # Đọc trực tiếp từ đường dẫn cố định HISTORY_FILE
    if not os.path.exists(HISTORY_FILE): 
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f: 
            return json.load(f)
    except: 
        return []

def add_to_history(song_name, file_path):
    current_hist = load_history()

    new_record = {
        "name": song_name,
        "path": file_path,
        "time": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    
    current_hist.insert(0, new_record)
    if len(current_hist) > 100: current_hist = current_hist[:100]
    
    try:
        # Ghi vào đường dẫn cố định
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(current_hist, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Lỗi lưu history: {e}")

def clear_history_data():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f: json.dump([], f)
        return True
    except: return False

# --- CÁC HÀM XỬ LÝ MẠNG (GIỮ NGUYÊN) ---
def get_spotify_track_name(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup.title.string.replace(" | Spotify", "").replace("Song by ", "")
        return None
    except: return None

def generate_search_query(query):
    final_keyword = query
    if "spotify.com" in query:
        track_name = get_spotify_track_name(query)
        if track_name: final_keyword = f"{track_name} Official Audio"
        else: return None 
    elif "youtube.com" in query or "youtu.be" in query:
        return query 
    else:
        final_keyword = f"{query} Official Audio"
    return f"ytsearch1:{final_keyword}"

def download_single_song(query, save_folder, codec='mp3', quality='320'):
    try:
        create_base_folder()
        search_query = generate_search_query(query)
        if not search_query: raise Exception("Không tìm thấy bài hát")

        ffmpeg_location = get_ffmpeg_path()
        print(f"DEBUG: Dùng FFmpeg tại: {ffmpeg_location}")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{save_folder}/%(title)s.%(ext)s',
            'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
            'writethumbnail': False, 
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': codec, 'preferredquality': quality}],
            'ffmpeg_location': ffmpeg_location,
            'noplaylist': True, 'quiet': True, 'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=True)
            if 'entries' in info: info = info['entries'][0]
            
            filename_base = ydl.prepare_filename(info).rsplit('.', 1)[0]
            final_path = f"{filename_base}.{codec}"
            
            # Ghi lịch sử
            add_to_history(info.get('title', query), final_path)

        return True, "Thành công"

    except Exception as e:
        error_msg = str(e)
        print(f"LỖI: {error_msg}")
        if "403" in error_msg: return False, "Lỗi 403 (Bị chặn). Hãy Update Core."
        if "ffmpeg" in error_msg.lower(): return False, "Lỗi: Không tìm thấy FFmpeg (Check folder bin)."
        return False, error_msg

def update_core_system():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
        return True, "Cập nhật thành công!"
    except: return False, "Lỗi cập nhật."