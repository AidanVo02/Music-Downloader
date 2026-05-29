## 🍎 Hướng dẫn cài đặt trên macOS

Do ứng dụng được phát triển bởi lập trình viên độc lập (chưa đăng ký chứng chỉ Apple Developer $99/năm), nên lần đầu mở App, macOS sẽ hiện cảnh báo bảo mật. **Đây là điều hoàn toàn bình thường.**

Vui lòng làm theo các bước sau để mở App:

### Bước 1: Tải và Giải nén
1.  Truy cập mục https://github.com/AidanVo02/Music-Downloader/releases/tag/v1.0 bên phải.
2.  Tải file `Music_Downloader_Mac.zip`.
3.  Click đúp vào file `.zip` để giải nén, bạn sẽ nhận được file `Music Downloader.app`.
4.  (Khuyên dùng) Kéo file App này vào thư mục **Applications** (Ứng dụng) của máy.

### Bước 2: Mở App lần đầu (Quan trọng)
Khi bạn click đúp để mở, macOS có thể báo lỗi: *"Music Downloader cannot be opened because the developer cannot be verified"* hoặc *"Move to Bin"*.

**Cách khắc phục:**
1.  **Click chuột phải** (hoặc nhấn 2 ngón tay trên Trackpad) vào biểu tượng **Music Downloader**.
2.  Chọn **Open** (Mở) trong menu hiện ra.
3.  Một hộp thoại cảnh báo xuất hiện, hãy chọn nút **Open** (Mở) một lần nữa.

*(Bạn chỉ cần làm thao tác này một lần duy nhất. Các lần sau mở bình thường).*

**Cách khác (Nếu cách trên không được):**
1.  Vào **System Settings** (Cài đặt hệ thống) -> **Privacy & Security** (Quyền riêng tư & Bảo mật).
2.  Cuộn xuống mục **Security**.
3.  Bạn sẽ thấy dòng thông báo *"Music Downloader was blocked..."*.
4.  Bấm nút **Open Anyway** (Vẫn mở).

---

## 🛠️ Convert file (mới)

Ứng dụng giờ hỗ trợ chuyển đổi file media sang audio (`mp3`, `wav`, `flac`, `m4a`) sử dụng `ffmpeg`.

- Cách dùng: mở tab **HISTORY**, bấm **Convert** kế bên file đã tải, nhập định dạng mục tiêu (`mp3`, `wav`, `flac`, `m4a`).
- Yêu cầu: cài `ffmpeg` và thêm vào `PATH` (Windows) hoặc cài qua Homebrew trên macOS:

```powershell
choco install ffmpeg    # Windows (chocolatey)
```

```bash
brew install ffmpeg     # macOS
```

Hoặc tải binary từ https://ffmpeg.org/ và thêm vào PATH. Ứng dụng sẽ tìm `ffmpeg` tự động.


## 🪟 Hướng dẫn cài đặt trên Windows

1.  Truy cập mục **[Releases](link-den-github-release-cua-ban)**.
2.  Tải file `Music Downloader.exe`.
3.  Mở file và sử dụng ngay (Portable, không cần cài đặt).

*Lưu ý: Nếu trình duyệt báo file lạ, hãy chọn "Keep" (Giữ lại) -> "Keep anyway". Đây là cảnh báo mặc định của Windows đối với các file .exe mới.*

---
