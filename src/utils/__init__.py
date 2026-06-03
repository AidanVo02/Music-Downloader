"""Utility modules for configuration, history, and FFmpeg management."""

from .config import (
    load_history, add_to_history, clear_history,
    load_config, save_config,
    get_existing_playlists,
    get_user_data_folder, get_base_music_folder, ensure_base_folder,
    DATA_FOLDER, HISTORY_FILE, CONFIG_FILE_PATH, BASE_FOLDER
)
from .ffmpeg_helper import get_ffmpeg_path, resource_path

__all__ = [
    'load_history',
    'add_to_history',
    'clear_history',
    'load_config',
    'save_config',
    'get_existing_playlists',
    'get_user_data_folder',
    'get_base_music_folder',
    'ensure_base_folder',
    'DATA_FOLDER',
    'HISTORY_FILE',
    'CONFIG_FILE_PATH',
    'BASE_FOLDER',
    'get_ffmpeg_path',
    'resource_path',
]
