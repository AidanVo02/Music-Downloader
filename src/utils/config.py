"""Configuration and history management."""
import os
import json
import platform
from datetime import datetime


def get_user_data_folder():
    """Get platform-specific data folder."""
    app_name = "MusicDownloader"
    if platform.system() == "Windows":
        base_path = os.getenv('APPDATA')
    elif platform.system() == "Darwin":  # macOS
        base_path = os.path.expanduser("~/Library/Application Support")
    else:  # Linux
        base_path = os.path.expanduser("~/.local/share")
        
    data_folder = os.path.join(base_path, app_name)
    if not os.path.exists(data_folder):
        try:
            os.makedirs(data_folder)
        except:
            pass
    return data_folder


def get_base_music_folder():
    """Get base folder for downloaded music."""
    return os.path.abspath(os.path.join(os.path.expanduser("~"), "Downloads", "Music_Downloaded"))


def ensure_base_folder():
    """Create base folder if it doesn't exist."""
    folder = get_base_music_folder()
    if not os.path.exists(folder):
        os.makedirs(folder)


# Paths
DATA_FOLDER = get_user_data_folder()
HISTORY_FILE = os.path.join(DATA_FOLDER, "history.json")
CONFIG_FILE_PATH = os.path.join(DATA_FOLDER, "config.json")
BASE_FOLDER = get_base_music_folder()


# --- History Management ---
def load_history():
    """Load download history from file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def add_to_history(song_name, file_path):
    """Add entry to download history."""
    current_hist = load_history()
    new_record = {
        "name": song_name,
        "path": file_path,
        "time": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    current_hist.insert(0, new_record)
    # Keep only last 100 entries
    if len(current_hist) > 100:
        current_hist = current_hist[:100]
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(current_hist, f, indent=4, ensure_ascii=False)
    except:
        pass


def clear_history():
    """Clear all history."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return True
    except:
        return False


# --- Config Management ---
def load_config():
    """Load config from file."""
    if not os.path.exists(CONFIG_FILE_PATH):
        return {}
    try:
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_config(config):
    """Save config to file."""
    try:
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except:
        return False


def get_existing_playlists():
    """Get list of existing playlist folders."""
    ensure_base_folder()
    try:
        items = os.listdir(BASE_FOLDER)
        return [i for i in items if os.path.isdir(os.path.join(BASE_FOLDER, i))]
    except:
        return []
