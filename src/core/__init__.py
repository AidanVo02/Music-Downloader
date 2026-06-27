"""Core modules for music downloading, conversion, and analysis."""

from .downloader import download_single_song, get_spotify_track_name, generate_search_query
from .converter import convert_file, update_core_system
from .analyzer import detect_bpm_key, detect_bpm_key_details, write_bpm_key_metadata

__all__ = [
    'download_single_song',
    'get_spotify_track_name',
    'generate_search_query',
    'convert_file',
    'update_core_system',
    'detect_bpm_key',
    'detect_bpm_key_details',
    'write_bpm_key_metadata',
]
