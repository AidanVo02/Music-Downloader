"""YouTube music downloader module."""
import yt_dlp
import os
import requests
from bs4 import BeautifulSoup

from ..utils.config import add_to_history, ensure_base_folder, BASE_FOLDER
from ..utils.ffmpeg_helper import get_ffmpeg_path
from .analyzer import detect_bpm_key


def _sanitize_filename(name):
    """Remove invalid filename characters for Windows/macOS/Linux."""
    invalid = '<>:"/\\|?*'
    for c in invalid:
        name = name.replace(c, '_')
    return name.strip() or "track"


def get_spotify_track_name(url):
    """Extract track name from Spotify URL."""
    try:
        h = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=h, timeout=5)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            title = soup.title.string
            if title:
                return title.replace(" | Spotify", "").replace("Song by ", "")
    except:
        pass
    return None


def generate_search_query(query):
    """Generate appropriate search query for yt-dlp."""
    final = query
    if "spotify.com" in query:
        name = get_spotify_track_name(query)
        if name:
            final = f"{name} Official Audio"
        else:
            return None
    elif "youtube.com" in query or "youtu.be" in query:
        return query
    else:
        final = f"{query} Official Audio"
    return f"ytsearch1:{final}"


def download_single_song(query, save_folder, codec='mp3', quality='320', 
                        detect_bpm_key_flag=False, progress_callback=None):
    """
    Download a single song from YouTube.
    
    Args:
        query: Song name or YouTube/Spotify URL
        save_folder: Destination folder
        codec: Output format ('mp3', 'wav', 'flac', 'm4a')
        quality: Bitrate for MP3 ('128', '192', '320', etc.)
        detect_bpm_key_flag: Whether to detect BPM and key
        progress_callback: Callback function for progress updates
        
    Returns:
        (success: bool, message: str)
    """
    try:
        ensure_base_folder()
        q = generate_search_query(query)
        if not q:
            raise Exception("Not found")

        ffmpeg_loc = get_ffmpeg_path()
        
        # Ensure folder exists
        save_folder = os.path.abspath(save_folder)
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

        # Configure yt-dlp with optimized settings
        ydl_opts = {
            # Prefer Opus codec for best quality
            'format': 'bestaudio[acodec=opus]/bestaudio',
            'outtmpl': os.path.join(save_folder, '%(title)s.%(ext)s'),
            'http_headers': {'User-Agent': 'Mozilla/5.0'},
            'writethumbnail': False,
            'ffmpeg_location': ffmpeg_loc,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': codec,
                'preferredquality': quality
            }],
            # Add loudness normalization (except for WAV to preserve raw audio)
            'postprocessor_args': [
                '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11'
            ] if codec != 'wav' else [],
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(q, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            
            # Get resulting filename
            fname = ydl.prepare_filename(info).rsplit('.', 1)[0]
            final_path = f"{fname}.{codec}"

            # Detect BPM & Key if requested
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
