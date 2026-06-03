"""Audio file converter module."""
import subprocess
import os
import sys

from ..utils.config import add_to_history
from ..utils.ffmpeg_helper import get_ffmpeg_path


def convert_file(input_path, output_format, bitrate='192k'):
    """
    Convert audio file to target format using ffmpeg.
    
    Args:
        input_path: Path to input audio file
        output_format: Target format ('mp3', 'wav', 'flac', 'm4a')
        bitrate: Bitrate for MP3/M4A (default '192k')
        
    Returns:
        (success: bool, output_path_or_error: str)
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

        # Build ffmpeg command based on output format
        if fmt == 'mp3':
            cmd = [ffmpeg, '-y', '-i', input_path, '-vn', '-acodec', 'libmp3lame', 
                   '-ab', bitrate, out_path]
        elif fmt == 'wav':
            # Preserve original sample rate and channels
            cmd = [ffmpeg, '-y', '-i', input_path, '-vn', '-acodec', 'pcm_s16le', out_path]
        elif fmt == 'flac':
            cmd = [ffmpeg, '-y', '-i', input_path, '-vn', '-acodec', 'flac', out_path]
        elif fmt == 'm4a':
            cmd = [ffmpeg, '-y', '-i', input_path, '-vn', '-c:a', 'aac', '-b:a', bitrate, out_path]
        else:
            return False, "Unsupported format"

        # Execute ffmpeg
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            err = proc.stderr.decode('utf-8', errors='ignore') or 'ffmpeg failed'
            return False, err

        # Verify output file was created
        if os.path.exists(out_path):
            add_to_history(os.path.basename(out_path), out_path)
            return True, out_path
        else:
            return False, 'Output file not created'

    except Exception as e:
        return False, str(e)


def update_core_system():
    """Update yt-dlp to latest version."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
        return True, "Updated!"
    except:
        return False, "Failed."
