# Project Structure Guide

## Cấu trúc Folder Mới

```
Music-Downloader/
├── src/                          # Source code chính
│   ├── __init__.py
│   ├── constants.py              # Language dictionary, fonts, constants
│   ├── core/                     # Core logic (download, convert, analyze)
│   │   ├── __init__.py
│   │   ├── downloader.py         # YouTube download logic
│   │   ├── converter.py          # Audio conversion logic
│   │   └── analyzer.py           # BPM/Key detection
│   ├── ui/                       # UI components
│   │   ├── __init__.py
│   │   ├── animations.py         # Animation effects (3D sphere, waves)
│   │   └── tabs/                 # Tab modules (future)
│   │       └── __init__.py
│   └── utils/                    # Utility functions
│       ├── __init__.py
│       ├── config.py             # Config & history management
│       └── ffmpeg_helper.py      # FFmpeg path detection
│
├── assets/                       # Assets (theme, icons)
│   ├── studio_theme.json
│   └── app_icon.icns
│
├── bin/                          # Binary files
│   ├── ffmpeg.exe
│   └── ffprobe.exe
│
├── data/                         # Runtime data
│   ├── config.json
│   └── history.json
│
├── docs/                         # Documentation
│   └── ANIMATION_GUIDE.md
│
├── app.py                        # Main application entry point (updated)
├── demo_animations.py            # Animation demo
├── requirements.txt              # Dependencies
├── README.md                     # Main project README
└── .gitignore
```

## Module Organization

### `src/core/` - Core Business Logic
**Tách nhạc từ Logic:**
- **downloader.py**: Download từ YouTube/Spotify
  - `download_single_song()` - Tải một bài
  - `generate_search_query()` - Tạo query tìm kiếm
  - `get_spotify_track_name()` - Lấy tên từ Spotify

- **converter.py**: Chuyển đổi định dạng audio
  - `convert_file()` - Convert MP3/WAV/FLAC/M4A
  - `update_core_system()` - Update yt-dlp

- **analyzer.py**: Phát hiện BPM & Key
  - `detect_bpm_key()` - Phát hiện BPM & Key
  - `write_bpm_key_metadata()` - Lưu metadata

### `src/ui/` - User Interface
- **animations.py**: Hoạt ảnh 3D
  - `LoadingAnimation` - Quả cầu 3D nảy
  - `AnalyzingAnimation` - Hoạt ảnh phân tích
  - `ParticleExplosion` - Hiệu ứng hạt

### `src/utils/` - Utilities
- **config.py**: Quản lý cấu hình & lịch sử
  - `load_history()`, `add_to_history()`, `clear_history()`
  - `load_config()`, `save_config()`
  - `get_existing_playlists()`
  - Path management functions

- **ffmpeg_helper.py**: Tìm FFmpeg
  - `get_ffmpeg_path()` - Định vị FFmpeg (Windows/macOS/Linux)
  - `resource_path()` - Path cho tài nguyên bundled

### `src/constants.py` - Global Constants
- `LANGUAGES` - Language dictionary (VI/EN)
- `FONT_MAIN`, `FONT_BOLD`, `FONT_TITLE` - Font definitions

## Import Pattern

### Old (Logic Module)
```python
import logic
import animations

logic.download_single_song(...)
logic.convert_file(...)
logic.load_history()
animations.LoadingAnimation(...)
```

### New (Src Package)
```python
from src import core, constants, utils
from src.ui import animations

core.download_single_song(...)
core.convert_file(...)
utils.load_history()
animations.LoadingAnimation(...)
```

## Benefits of New Structure

✅ **Separation of Concerns**: Logic, UI, utilities tách biệt rõ ràng  
✅ **Scalability**: Dễ thêm tabs/modules mới  
✅ **Maintainability**: Code tổ chức, dễ bảo trì  
✅ **Testability**: Dễ viết unit tests cho từng module  
✅ **Reusability**: Modules có thể tái sử dụng trong projects khác  

## Migration Notes

- `app.py` - Main GUI, updated to use `src` package
- Old `logic.py` - Nên xóa/rename để tránh confusion
- Old `animations.py` - Nên xóa (moved to `src/ui/animations.py`)
- Constants extracted to `src/constants.py`
- Config/History moved to `src/utils/config.py`

## Future Improvements

- [ ] Split `app.py` tabs into separate modules in `src/ui/tabs/`
- [ ] Add unit tests in `tests/` folder
- [ ] Add CI/CD configuration
- [ ] Create `setup.py` for packaging
- [ ] Add type hints to modules
