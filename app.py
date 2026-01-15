import customtkinter as ctk
from tkinter import messagebox
import threading
import os
import sys
import json
import pyperclip 

try:
    import logic
except ImportError:
    messagebox.showerror("Error", "Missing 'logic.py' file!")
    exit()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- BỘ TỪ ĐIỂN NGÔN NGỮ (DICTIONARY) ---
LANGUAGES = {
    "vi": {
        "app_title": "MUSIC DOWNLOADER",
        "tab_dl": "TẢI NHẠC",
        "tab_his": "LỊCH SỬ",
        "tab_sys": "HỆ THỐNG",
        "guide": "Danh sách bài hát / Link nhạc:",
        "input_placeholder": "Sơn Tùng MTP\nĐen Vâu\n(Nhập mỗi dòng một bài...)",
        "chk_playlist": "Tạo thư mục riêng",
        "switch_paste": "Tự dán Link",
        "combo_placeholder": "Chọn hoặc Nhập tên...",
        "btn_download": "TẢI XUỐNG NGAY",
        "btn_downloading": "ĐANG TẢI...",
        "status_ready": "Trạng thái: Sẵn sàng.",
        "status_monitoring": "Đang theo dõi Clipboard...",
        "status_detected": "Đã bắt Link:",
        "his_title": "LỊCH SỬ TẢI (100 BÀI)",
        "btn_clear": "Xóa Lịch Sử",
        "btn_open": "▶ Mở",
        "sys_title": "CÀI ĐẶT & CẬP NHẬT",
        "lbl_lang": "Ngôn ngữ / Language:",
        "btn_update": "KIỂM TRA CẬP NHẬT (Core)",
        "btn_updating": "ĐANG CẬP NHẬT...",
        "msg_missing_info": "Thiếu thông tin",
        "msg_missing_content": "Vui lòng nhập tên bài hát hoặc link!",
        "msg_missing_name": "Vui lòng nhập tên Playlist!",
        "msg_success": "Thành công",
        "msg_saved": "Đã lưu nhạc tại:",
        "msg_confirm_clear": "Bạn có chắc muốn xóa lịch sử?",
        "msg_restart": "Thay đổi ngôn ngữ cần khởi động lại App.\nBạn có muốn thoát App ngay không?",
        "version": "Phiên bản: v2.0 (Multi-Language)"
    },
    "en": {
        "app_title": "MUSIC DOWNLOADER",
        "tab_dl": "DOWNLOADER",
        "tab_his": "HISTORY",
        "tab_sys": "SYSTEM",
        "guide": "Song List / Links:",
        "input_placeholder": "Ed Sheeran\nTaylor Swift\n(Enter one song per line...)",
        "chk_playlist": "Create Playlist Folder",
        "switch_paste": "Auto-Paste",
        "combo_placeholder": "Select or Type Name...",
        "btn_download": "DOWNLOAD NOW",
        "btn_downloading": "DOWNLOADING...",
        "status_ready": "Status: Ready.",
        "status_monitoring": "Monitoring Clipboard...",
        "status_detected": "Link Detected:",
        "his_title": "DOWNLOAD HISTORY (LAST 100)",
        "btn_clear": "Clear History",
        "btn_open": "▶ Open",
        "sys_title": "SETTINGS & UPDATES",
        "lbl_lang": "Language / Ngôn ngữ:",
        "btn_update": "CHECK FOR UPDATES (Core)",
        "btn_updating": "UPDATING...",
        "msg_missing_info": "Missing Info",
        "msg_missing_content": "Please enter songs or links!",
        "msg_missing_name": "Please enter a Playlist name!",
        "msg_success": "Success",
        "msg_saved": "Music saved at:",
        "msg_confirm_clear": "Are you sure you want to clear history?",
        "msg_restart": "Changing language requires restart.\nDo you want to exit now?",
        "version": "Version: v2.0 (Multi-Language)"
    }
}

# --- CẤU HÌNH GIAO DIỆN & CONFIG ---
CONFIG_FILE = "config.json"

def load_config():
    """Đọc file config để lấy ngôn ngữ đã lưu"""
    default_config = {"language": "vi"} # Mặc định là Tiếng Việt
    if not os.path.exists(CONFIG_FILE):
        return default_config
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return default_config

def save_config(lang_code):
    """Lưu ngôn ngữ vào file"""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"language": lang_code}, f)
    except: pass

ctk.set_appearance_mode("Dark")
try:
    theme_path = resource_path("studio_theme.json")
    ctk.set_default_color_theme(theme_path)
except Exception:
    ctk.set_default_color_theme("blue")

FONT_MAIN = ("Segoe UI", 13)
FONT_BOLD = ("Segoe UI", 13, "bold")
FONT_TITLE = ("Segoe UI", 20, "bold")

class MusicApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. LOAD NGÔN NGỮ
        self.config = load_config()
        self.curr_lang_code = self.config.get("language", "vi")
        # Biến self.txt sẽ chứa toàn bộ từ điển của ngôn ngữ đang chọn
        self.txt = LANGUAGES[self.curr_lang_code]

        self.title(self.txt["app_title"])
        self.geometry("750x680") # Tăng chiều cao xíu cho phần chọn ngôn ngữ
        self.last_clipboard_text = ""

        # HEADER
        self.lbl_title = ctk.CTkLabel(self, text=self.txt["app_title"], font=FONT_TITLE, text_color="#0ea5e9")
        self.lbl_title.pack(pady=(20, 10))

        # TABS
        self.tabview = ctk.CTkTabview(self, width=700, height=520)
        self.tabview.pack(pady=10, padx=20, fill="both", expand=True)

        self.tab_download = self.tabview.add(self.txt["tab_dl"])
        self.tab_history = self.tabview.add(self.txt["tab_his"])
        self.tab_system = self.tabview.add(self.txt["tab_sys"])

        self.setup_downloader_tab()
        self.setup_history_tab()
        self.setup_system_tab()

    # ========================== TAB 1: DOWNLOADER ==========================
    def setup_downloader_tab(self):
        parent = self.tab_download
        
        # Input
        self.frame_input = ctk.CTkFrame(parent)
        self.frame_input.pack(pady=10, padx=10, fill="both")
        self.lbl_guide = ctk.CTkLabel(self.frame_input, text=self.txt["guide"], font=FONT_BOLD)
        self.lbl_guide.pack(anchor="w", padx=15, pady=(15, 5))
        self.txt_input = ctk.CTkTextbox(self.frame_input, height=140, font=FONT_MAIN, border_width=0)
        self.txt_input.pack(pady=5, padx=15, fill="x")
        self.txt_input.insert("0.0", self.txt["input_placeholder"])

        # Options
        self.frame_options = ctk.CTkFrame(parent)
        self.frame_options.pack(pady=10, padx=10, fill="x")
        self.frame_options.columnconfigure(0, weight=1)
        self.frame_options.columnconfigure(1, weight=1)

        self.var_playlist = ctk.BooleanVar()
        self.chk_playlist = ctk.CTkCheckBox(self.frame_options, text=self.txt["chk_playlist"], font=FONT_MAIN,
                                            variable=self.var_playlist, command=self.toggle_playlist_entry)
        self.chk_playlist.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        self.var_monitor = ctk.BooleanVar(value=False)
        self.switch_monitor = ctk.CTkSwitch(self.frame_options, text=self.txt["switch_paste"], 
                                            font=FONT_MAIN, variable=self.var_monitor, 
                                            command=self.toggle_monitor)
        self.switch_monitor.grid(row=0, column=1, padx=20, pady=15, sticky="e")

        self.entry_playlist = ctk.CTkComboBox(self.frame_options, width=200, state="disabled", font=FONT_MAIN, values=[]) 
        self.entry_playlist.set(self.txt["combo_placeholder"])
        self.entry_playlist.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")

        self.formats = ["MP3 (320kbps)", "M4A (Fast)", "WAV (Original)", "FLAC"]
        self.combo_format = ctk.CTkOptionMenu(self.frame_options, values=self.formats, font=FONT_MAIN)
        self.combo_format.grid(row=1, column=1, padx=20, pady=(0, 15), sticky="ew")

        # Footer
        self.progress_bar = ctk.CTkProgressBar(parent, width=500, height=10)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(15, 5))

        self.btn_download = ctk.CTkButton(parent, text=self.txt["btn_download"], height=45, font=("Segoe UI", 14, "bold"),
                                          command=self.start_download_thread)
        self.btn_download.pack(pady=15, padx=20, fill="x")

        self.lbl_status = ctk.CTkLabel(parent, text=self.txt["status_ready"], font=FONT_MAIN, text_color="gray")
        self.lbl_status.pack(pady=5)

    # ========================== TAB 2: HISTORY ==========================
    def setup_history_tab(self):
        parent = self.tab_history
        
        frame_head = ctk.CTkFrame(parent, fg_color="transparent")
        frame_head.pack(fill="x", pady=10)
        
        ctk.CTkLabel(frame_head, text=self.txt["his_title"], font=FONT_BOLD).pack(side="left", padx=10)
        ctk.CTkButton(frame_head, text=self.txt["btn_clear"], width=100, fg_color="#ef4444", hover_color="#b91c1c",
                      command=self.clear_history_ui).pack(side="right", padx=10)

        self.scroll_history = ctk.CTkScrollableFrame(parent, label_text="List")
        self.scroll_history.pack(fill="both", expand=True, padx=10, pady=5)
        self.refresh_history_ui()

    def refresh_history_ui(self):
        for widget in self.scroll_history.winfo_children():
            widget.destroy()
        history_data = logic.load_history()
        if not history_data:
            ctk.CTkLabel(self.scroll_history, text="...", text_color="gray").pack(pady=20)
            return
        for item in history_data:
            self.create_history_row(item)

    def create_history_row(self, item):
        row_frame = ctk.CTkFrame(self.scroll_history, fg_color="transparent")
        row_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(row_frame, text=f"[{item['time']}]", font=("Consolas", 11), text_color="gray", width=120).pack(side="left")
        name = item['name']
        if len(name) > 40: name = name[:37] + "..."
        ctk.CTkLabel(row_frame, text=name, font=FONT_MAIN, anchor="w").pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkButton(row_frame, text=self.txt["btn_open"], width=80, height=25, font=("Segoe UI", 11),
                      fg_color="#334155", hover_color="#0ea5e9",
                      command=lambda p=item['path']: self.open_file_safe(p)).pack(side="right", padx=5)

    def open_file_safe(self, path):
        if os.path.exists(path):
            try: os.startfile(path)
            except: messagebox.showerror("Error", "Cannot open file.")
        else: messagebox.showwarning("Error", "File not found.")

    def clear_history_ui(self):
        if messagebox.askyesno("Confirm", self.txt["msg_confirm_clear"]):
            logic.clear_history_data()
            self.refresh_history_ui()

    # ========================== TAB 3: SYSTEM (CHỖ ĐỔI NGÔN NGỮ) ==========================
    def setup_system_tab(self):
        parent = self.tab_system
        ctk.CTkLabel(parent, text=self.txt["sys_title"], font=FONT_BOLD, text_color="gray").pack(pady=20)
        
        # --- KHUNG CHỌN NGÔN NGỮ ---
        frame_lang = ctk.CTkFrame(parent)
        frame_lang.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(frame_lang, text=self.txt["lbl_lang"], font=FONT_BOLD).pack(side="left", padx=20, pady=15)
        
        self.combo_lang = ctk.CTkComboBox(frame_lang, values=["Tiếng Việt", "English"], 
                                          command=self.change_language, state="readonly", width=150)
        
        # Set giá trị hiển thị hiện tại
        current_display = "Tiếng Việt" if self.curr_lang_code == "vi" else "English"
        self.combo_lang.set(current_display)
        self.combo_lang.pack(side="right", padx=20, pady=15)
        # ---------------------------

        self.btn_update = ctk.CTkButton(parent, text=self.txt["btn_update"], height=45, 
                                        fg_color="#334155", font=("Segoe UI", 12, "bold"),
                                        command=self.start_update_thread) 
        self.btn_update.pack(pady=20)
        
        self.lbl_update_status = ctk.CTkLabel(parent, text="...", font=FONT_MAIN, text_color="gray")
        self.lbl_update_status.pack(pady=5)
        ctk.CTkLabel(parent, text=self.txt["version"], font=("Arial", 10)).pack(side="bottom", pady=20)

    def change_language(self, choice):
        """Hàm xử lý khi chọn ngôn ngữ mới"""
        new_code = "vi" if choice == "Tiếng Việt" else "en"
        
        # Nếu chọn khác với ngôn ngữ hiện tại
        if new_code != self.curr_lang_code:
            save_config(new_code) # Lưu vào file
            if messagebox.askyesno("Restart Required", self.txt["msg_restart"]):
                self.destroy() # Thoát App
                exit()

    # ========================== LOGIC CHUNG ==========================
    def toggle_monitor(self):
        if self.var_monitor.get():
            self.lbl_status.configure(text=self.txt["status_monitoring"], text_color="#eab308")
            self.monitor_loop()
        else:
            self.lbl_status.configure(text="Auto-Paste Disabled.", text_color="gray")

    def monitor_loop(self):
        if not self.var_monitor.get(): return
        try:
            content = pyperclip.paste().strip()
            if content != self.last_clipboard_text:
                self.last_clipboard_text = content
                if "youtube.com" in content or "youtu.be" in content or "spotify.com" in content:
                    current_text = self.txt_input.get("0.0", "end").strip()
                    # Logic: Xóa placeholder nếu đang hiển thị placeholder
                    placeholder_check = "Sơn Tùng" if self.curr_lang_code == "vi" else "Ed Sheeran"
                    
                    if placeholder_check in self.txt_input.get("0.0", "end"):
                        self.txt_input.delete("0.0", "end")
                        self.txt_input.insert("0.0", f"{content}")
                    elif len(current_text) > 0:
                        self.txt_input.insert("end", f"\n{content}")
                    else:
                        self.txt_input.insert("0.0", f"{content}")
                    
                    msg_detected = self.txt["status_detected"]
                    self.lbl_status.configure(text=f"{msg_detected} {content[:20]}...", text_color="#22c55e")
        except: pass
        self.after(1500, self.monitor_loop)

    def toggle_playlist_entry(self):
        if self.var_playlist.get():
            self.entry_playlist.configure(state="normal")
            try: existing = logic.get_existing_playlists()
            except: existing = []
            if existing:
                self.entry_playlist.configure(values=existing)
                self.entry_playlist.set(existing[0]) 
            else:
                self.entry_playlist.configure(values=[])
                self.entry_playlist.set("") 
            self.entry_playlist.focus()
        else:
            self.entry_playlist.configure(state="disabled")
            self.entry_playlist.set(self.txt["combo_placeholder"])

    def start_download_thread(self):
        raw_text = self.txt_input.get("0.0", "end")
        placeholder_check = "Enter one" if self.curr_lang_code == "en" else "Nhập mỗi dòng"
        song_list = [line for line in raw_text.split('\n') if line.strip() and placeholder_check not in line]
        
        if not song_list:
            messagebox.showwarning(self.txt["msg_missing_info"], self.txt["msg_missing_content"])
            return
            
        playlist_name = self.entry_playlist.get().strip()
        use_playlist = self.var_playlist.get()
        format_choice = self.combo_format.get()
        
        if use_playlist and (not playlist_name or playlist_name == self.txt["combo_placeholder"]):
            messagebox.showwarning(self.txt["msg_missing_info"], self.txt["msg_missing_name"])
            return
            
        self.btn_download.configure(state="disabled", text=self.txt["btn_downloading"])
        t = threading.Thread(target=self.run_logic, args=(song_list, playlist_name, use_playlist, format_choice))
        t.start()

    def run_logic(self, song_list, playlist_name, use_playlist, format_choice):
        save_folder = logic.BASE_FOLDER
        if use_playlist and playlist_name:
            save_folder = os.path.join(logic.BASE_FOLDER, playlist_name)
            if not os.path.exists(save_folder): os.makedirs(save_folder)
        
        codec = 'mp3'
        if "WAV" in format_choice: codec = 'wav'
        elif "FLAC" in format_choice: codec = 'flac'
        elif "M4A" in format_choice: codec = 'm4a'

        total = len(song_list)
        success_count = 0
        for i, query in enumerate(song_list):
            if not query.strip(): continue
            current_num = i + 1
            status_txt = "Downloading" if self.curr_lang_code == "en" else "Đang tải"
            self.after(0, lambda: self.lbl_status.configure(text=f"{status_txt} ({current_num}/{total}): {query[:25]}...", text_color="#0ea5e9"))
            self.after(0, lambda: self.progress_bar.set(current_num / total))

            success, msg = logic.download_single_song(query, save_folder, codec)
            if success: success_count += 1
            else: print(msg)

        self.after(0, lambda: self.finish_download(success_count, total, save_folder))

    def finish_download(self, success, total, folder):
        completed_txt = "Completed" if self.curr_lang_code == "en" else "Hoàn thành"
        self.lbl_status.configure(text=f"✅ {completed_txt} {success}/{total}.", text_color="white")
        self.btn_download.configure(state="normal", text=self.txt["btn_download"])
        self.progress_bar.set(0)
        self.refresh_history_ui()
        
        title_suc = self.txt["msg_success"]
        body_suc = f"{self.txt['msg_saved']}\n{folder}"
        messagebox.showinfo(title_suc, body_suc)
        try: os.startfile(folder)
        except: pass

    def start_update_thread(self):
        self.btn_update.configure(state="disabled", text=self.txt["btn_updating"])
        self.lbl_update_status.configure(text="...", text_color="#eab308")
        t = threading.Thread(target=self.run_update_logic)
        t.start()

    def run_update_logic(self):
        success, msg = logic.update_core_system()
        self.after(0, self.finish_update_process, success, msg)

    def finish_update_process(self, success, msg):
        if success:
            self.lbl_update_status.configure(text=f"✅ {msg}", text_color="#22c55e")
            messagebox.showinfo(self.txt["msg_success"], "Update complete!")
        else:
            self.lbl_update_status.configure(text=f"❌ {msg}", text_color="#ef4444")
            messagebox.showerror("Failed", msg)
        self.btn_update.configure(state="normal", text=self.txt["btn_update"])

if __name__ == "__main__":
    app = MusicApp()
    app.mainloop()