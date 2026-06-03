"""FFmpeg utility functions."""
import os
import sys
import platform
import shutil


def get_ffmpeg_path():
    """
    Hàm tìm kiếm FFmpeg với hỗ trợ đầy đủ cho Windows, macOS, Linux.
    """
    if platform.system() == "Windows":
        # Windows: kiểm tra bin/ folder trước, sau đó hệ thống PATH
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        path = os.path.join(base_path, "../../bin", "ffmpeg.exe")
        if os.path.exists(path):
            return path
        return "ffmpeg"
    else:
        # macOS/Linux: kiểm tra các đường dẫn phổ biến
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
        
        # Thử hỏi hệ thống
        path = shutil.which("ffmpeg")
        if path:
            return path
            
        return "ffmpeg"  # Fallback


def resource_path(relative_path):
    """Get absolute path for bundled resources."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
