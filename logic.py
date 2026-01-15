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

# --- CẤU HÌNH ---
BASE_FOLDER = "Downloads"
HISTORY_FILE = "history.json" # File lưu lịch sử

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_ffmpeg_filename():
    return "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"

def create_base_folder():
    if not os.path.exists(BASE_FOLDER):
        os.makedirs(BASE_FOLDER)

# --- QUẢN LÝ LỊCH SỬ (HISTORY LOGIC) ---
def load_history():
    """Đọc file json trả về danh sách"""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def add_to_history(song_name, file_path):
    """Thêm một bài hát mới vào đầu danh sách"""
    history = load_history()
    
    # Tạo bản ghi mới
    new_record = {
        "name": song_name,
        "path": file_path,
        "time": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    
    # Thêm vào đầu danh sách (Mới nhất lên trên)
    history.insert(0, new_record)
    
    # Giới hạn lưu 100 bài gần nhất thôi cho nhẹ
    if len(history) > 100:
        history = history[:100]
        
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Lỗi lưu lịch sử: {e}")

def clear_history_data():
    """Xóa sạch lịch sử"""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return True
    except:
        return False

# --- CÁC HÀM XỬ LÝ LINK ---
def get_spotify_track_name(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            page_title = soup.title.string
            return page_title.replace(" | Spotify", "").replace("Song by ", "")
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
        if not search_query: raise Exception("Không đọc được link/tên bài hát")

        ffmpeg_file = get_ffmpeg_filename()
        ffmpeg_path = resource_path(ffmpeg_file) 
        if platform.system() != "Windows" and os.path.exists(ffmpeg_path):
             os.chmod(ffmpeg_path, 0o755)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{save_folder}/%(title)s.%(ext)s',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.youtube.com/',
                'Accept-Language': 'en-US,en;q=0.9',
            },
            'writethumbnail': False, 
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': codec, 'preferredquality': quality}],
            'ffmpeg_location': ffmpeg_path,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=True)
            
            # Xử lý tên file để lưu vào lịch sử
            if 'entries' in info: info = info['entries'][0]
            filename_base = ydl.prepare_filename(info).rsplit('.', 1)[0]
            final_path = f"{filename_base}.{codec}"
            song_title = info.get('title', query)
            
            # --- LƯU VÀO HISTORY ---
            add_to_history(song_title, final_path)

        return True, "Thành công"

    except Exception as e:
        error_msg = str(e)
        print(f"LỖI: {error_msg}")
        if "403" in error_msg: return False, "Bị chặn (403). Hãy update Core."
        return False, error_msg

def get_existing_playlists():
    """Trả về danh sách các thư mục con trong folder Downloads"""
    create_base_folder() # Đảm bảo folder Downloads tồn tại
    try:
        # Lấy tất cả các mục trong folder Downloads
        items = os.listdir(BASE_FOLDER)
        # Chỉ lấy những mục là Thư mục (Folder)
        playlists = [item for item in items if os.path.isdir(os.path.join(BASE_FOLDER, item))]
        return playlists
    except:
        return []

def update_core_system():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
        return True, "Đã cập nhật yt-dlp lên bản mới nhất!"
    except subprocess.CalledProcessError:
        return False, "Lỗi khi chạy lệnh Update (Check mạng/Quyền Admin)."
    except Exception as e:
        return False, f"Lỗi không xác định: {str(e)}"