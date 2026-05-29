import customtkinter as ctk
from tkinter import messagebox, simpledialog, filedialog
import threading
import os
import sys
import json
import pyperclip 
import platform   # <--- Thêm thư viện này để check hệ điều hành
import subprocess # <--- Thêm thư viện này để chạy lệnh mở file trên Mac

try:
    import logic
except ImportError:
    messagebox.showerror("Error", "Thiếu file logic.py!")
    exit()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- BỘ TỪ ĐIỂN NGÔN NGỮ ---
LANGUAGES = {
    "vi": {
        "app_title": "MUSIC DOWNLOADER",
        "tab_dl": "TẢI NHẠC", "tab_his": "LỊCH SỬ", "tab_sys": "HỆ THỐNG", "tab_conv": "CHUYỂN ĐỔI",
        "guide": "Danh sách bài hát / Link nhạc:",
        "input_placeholder": "Sơn Tùng MTP\nĐen Vâu\n(Nhập mỗi dòng một bài...)",
        "chk_playlist": "Tạo thư mục riêng", "switch_paste": "Tự dán Link",
        "combo_placeholder": "Chọn hoặc Nhập tên...",
        "btn_download": "TẢI XUỐNG NGAY", "btn_downloading": "ĐANG TẢI...",
        "status_ready": "Sẵn sàng.", "status_monitoring": "Đang theo dõi Clipboard...",
        "status_detected": "Đã bắt Link:", "his_title": "LỊCH SỬ TẢI (100 BÀI)",
        "btn_clear": "Xóa Lịch Sử", "btn_open": "▶ Mở", "sys_title": "CÀI ĐẶT & CẬP NHẬT",
        "lbl_lang": "Ngôn ngữ / Language:", "btn_update": "KIỂM TRA CẬP NHẬT (Core)",
        "btn_updating": "ĐANG CẬP NHẬT...",         "msg_success": "Thành công",
        "msg_saved": "Đã lưu nhạc tại:", "msg_restart": "Cần khởi động lại App để đổi ngôn ngữ.\nThoát ngay?",
        "msg_missing_content": "Vui lòng nhập tên bài hoặc link!",
        "chk_bpm_key": "Phát hiện BPM & Key",
        "status_analyzing": "Đang phân tích BPM & Key...",
        "version": "Phiên bản: v2.1 (Mac Support)"
    },
    "en": {
        "app_title": "MUSIC DOWNLOADER",
        "tab_dl": "DOWNLOADER", "tab_his": "HISTORY", "tab_sys": "SYSTEM", "tab_conv": "CONVERT",
        "guide": "Song List / Links:",
        "input_placeholder": "Ed Sheeran\nTaylor Swift\n(Enter one song per line...)",
        "chk_playlist": "Create Playlist Folder", "switch_paste": "Auto-Paste",
        "combo_placeholder": "Select or Type Name...",
        "btn_download": "DOWNLOAD NOW", "btn_downloading": "DOWNLOADING...",
        "status_ready": "Ready.", "status_monitoring": "Monitoring Clipboard...",
        "status_detected": "Link Detected:", "his_title": "DOWNLOAD HISTORY (LAST 100)",
        "btn_clear": "Clear History", "btn_open": "▶ Open", "sys_title": "SETTINGS & UPDATES",
        "lbl_lang": "Language / Ngôn ngữ:", "btn_update": "CHECK FOR UPDATES (Core)",
        "btn_updating": "UPDATING...",         "msg_success": "Success",
        "msg_saved": "Music saved at:", "msg_restart": "Restart required to change language.\nExit now?",
        "msg_missing_content": "Please enter song name or link!",
        "chk_bpm_key": "Detect BPM & Key",
        "status_analyzing": "Detecting BPM & Key...",
        "version": "Version: v2.1 (Mac Support)"
    }
}

# Lấy đường dẫn config từ logic
CONFIG_FILE = getattr(logic, 'CONFIG_FILE_PATH', "config.json")

def load_config():
    if not os.path.exists(CONFIG_FILE): return {"language": "en"}
    try:
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    except: return {"language": "en"}

def save_config(lang_code):
    try:
        folder = os.path.dirname(CONFIG_FILE)
        if not os.path.exists(folder): os.makedirs(folder)
        with open(CONFIG_FILE, "w") as f: json.dump({"language": lang_code}, f)
    except: pass

# --- CẤU HÌNH THEME ---
ctk.set_appearance_mode("Dark")
try:
    theme_path = resource_path(os.path.join("assets", "studio_theme.json"))
    ctk.set_default_color_theme(theme_path)
except Exception:
    ctk.set_default_color_theme("blue")

FONT_MAIN = ("Segoe UI", 13)
FONT_BOLD = ("Segoe UI", 13, "bold")
FONT_TITLE = ("Segoe UI", 20, "bold")

class MusicApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.curr_lang_code = self.config.get("language", "en")
        self.txt = LANGUAGES[self.curr_lang_code]

        self.title(self.txt["app_title"])
        self.geometry("750x680")
        self.last_clipboard_text = ""

        # UI
        self.lbl_title = ctk.CTkLabel(self, text=self.txt["app_title"], font=FONT_TITLE, text_color="#0ea5e9")
        self.lbl_title.pack(pady=(20, 10))

        self.tabview = ctk.CTkTabview(self, width=700, height=520)
        self.tabview.pack(pady=10, padx=20, fill="both", expand=True)
        self.tab_download = self.tabview.add(self.txt["tab_dl"])
        self.tab_history = self.tabview.add(self.txt["tab_his"])
        self.tab_system = self.tabview.add(self.txt["tab_sys"])
        self.tab_convert = self.tabview.add(self.txt.get("tab_conv", "Convert"))

        self.setup_downloader_tab()
        self.setup_history_tab()
        self.setup_convert_tab()
        self.setup_system_tab()

    def setup_downloader_tab(self):
        parent = self.tab_download
        self.frame_input = ctk.CTkFrame(parent)
        self.frame_input.pack(pady=10, padx=10, fill="both")
        ctk.CTkLabel(self.frame_input, text=self.txt["guide"], font=FONT_BOLD).pack(anchor="w", padx=15, pady=15)
        self.txt_input = ctk.CTkTextbox(self.frame_input, height=140, font=FONT_MAIN)
        self.txt_input.pack(pady=5, padx=15, fill="x")
        self.txt_input.insert("0.0", self.txt["input_placeholder"])

        self.frame_options = ctk.CTkFrame(parent)
        self.frame_options.pack(pady=10, padx=10, fill="x")
        self.frame_options.columnconfigure((0, 1), weight=1)

        self.var_playlist = ctk.BooleanVar()
        self.chk_playlist = ctk.CTkCheckBox(self.frame_options, text=self.txt["chk_playlist"], font=FONT_MAIN,
                                            variable=self.var_playlist, command=self.toggle_playlist_entry)
        self.chk_playlist.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        self.var_monitor = ctk.BooleanVar(value=False)
        self.switch_monitor = ctk.CTkSwitch(self.frame_options, text=self.txt["switch_paste"], font=FONT_MAIN, 
                                            variable=self.var_monitor, command=self.toggle_monitor)
        self.switch_monitor.grid(row=0, column=1, padx=20, pady=15, sticky="e")

        self.var_bpm_key = ctk.BooleanVar(value=True)
        self.chk_bpm_key = ctk.CTkCheckBox(self.frame_options, text=self.txt["chk_bpm_key"], font=FONT_MAIN,
                                           variable=self.var_bpm_key)
        self.chk_bpm_key.grid(row=1, column=0, padx=20, pady=(0, 5), sticky="w")

        self.entry_playlist = ctk.CTkComboBox(self.frame_options, width=200, state="disabled", font=FONT_MAIN, values=[])
        self.entry_playlist.set(self.txt["combo_placeholder"])
        self.entry_playlist.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="ew")

        self.combo_format = ctk.CTkOptionMenu(self.frame_options, values=["MP3 (320kbps)", "M4A", "WAV", "FLAC"], font=FONT_MAIN)
        self.combo_format.grid(row=2, column=1, padx=20, pady=(0, 15), sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(parent, width=500, height=10); self.progress_bar.set(0)
        self.progress_bar.pack(pady=15)
        self.btn_download = ctk.CTkButton(parent, text=self.txt["btn_download"], height=45, font=("Segoe UI", 14, "bold"),
                                          command=self.start_download_thread)
        self.btn_download.pack(pady=15, padx=20, fill="x")
        self.lbl_status = ctk.CTkLabel(parent, text=self.txt["status_ready"], font=FONT_MAIN, text_color="gray")
        self.lbl_status.pack(pady=5)

    def setup_history_tab(self):
        parent = self.tab_history
        head = ctk.CTkFrame(parent, fg_color="transparent"); head.pack(fill="x", pady=10)
        ctk.CTkLabel(head, text=self.txt["his_title"], font=FONT_BOLD).pack(side="left", padx=10)
        ctk.CTkButton(head, text=self.txt["btn_clear"], width=100, fg_color="#ef4444", hover_color="#b91c1c",
                      command=self.clear_his).pack(side="right", padx=10)
        self.scroll_history = ctk.CTkScrollableFrame(parent); self.scroll_history.pack(fill="both", expand=True, padx=10, pady=5)
        self.refresh_his()

    def refresh_his(self):
        for w in self.scroll_history.winfo_children(): w.destroy()
        data = logic.load_history()
        if not data: ctk.CTkLabel(self.scroll_history, text="...", text_color="gray").pack(pady=20); return
        for item in data:
            row = ctk.CTkFrame(self.scroll_history, fg_color="transparent"); row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"[{item['time']}]", font=("Consolas", 11), text_color="gray", width=120).pack(side="left")
            name = item['name'][:37]+"..." if len(item['name'])>40 else item['name']
            ctk.CTkLabel(row, text=name, font=FONT_MAIN, anchor="w").pack(side="left", padx=10, fill="x", expand=True)
            # Truyền path vào hàm mở file an toàn
            ctk.CTkButton(row, text=self.txt["btn_open"], width=80, height=25, fg_color="#334155",
                          command=lambda p=item['path']: self.open_file_safe(p)).pack(side="right", padx=5)
            # Convert button
            ctk.CTkButton(row, text="Convert", width=80, height=25, fg_color="#16a34a",
                          command=lambda p=item['path']: self.ask_and_convert(p)).pack(side="right", padx=5)

    def setup_convert_tab(self):
        parent = self.tab_convert
        frame = ctk.CTkFrame(parent)
        frame.pack(pady=10, padx=10, fill="both")

        ctk.CTkLabel(frame, text="Select file to convert", font=FONT_BOLD).pack(anchor="w", padx=15, pady=10)
        row = ctk.CTkFrame(frame); row.pack(fill="x", padx=15, pady=5)
        self.entry_convert_path = ctk.CTkEntry(row, placeholder_text="Path to file...", width=420)
        self.entry_convert_path.pack(side="left", padx=(0,8), pady=6)
        ctk.CTkButton(row, text="Browse", width=80, command=self.browse_file).pack(side="left", padx=(0,6))

        # Options
        opt_row = ctk.CTkFrame(frame); opt_row.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(opt_row, text="Format:", font=FONT_MAIN).pack(side="left", padx=(0,8))
        self.conv_format = ctk.CTkOptionMenu(opt_row, values=["mp3", "wav", "flac", "m4a"], width=120)
        self.conv_format.set("mp3")
        self.conv_format.pack(side="left", padx=(0,14))
        ctk.CTkLabel(opt_row, text="Bitrate:", font=FONT_MAIN).pack(side="left", padx=(0,8))
        self.conv_bitrate = ctk.CTkEntry(opt_row, width=120)
        self.conv_bitrate.insert(0, "192k")
        self.conv_bitrate.pack(side="left")

        self.btn_convert = ctk.CTkButton(frame, text="Convert", height=40, fg_color="#16a34a", command=self.start_convert_thread)
        self.btn_convert.pack(pady=15, padx=15, fill="x")

    def browse_file(self):
        p = filedialog.askopenfilename(title="Select file", filetypes=[("Media files", "*.mp4 *.m4a *.mp3 *.wav *.flac *.mkv *.aac"), ("All files", "*")])
        if p:
            self.entry_convert_path.delete(0, 'end')
            self.entry_convert_path.insert(0, p)

    def start_convert_thread(self):
        path = self.entry_convert_path.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showwarning("Error", "File not found / Không tìm thấy file")
            return
        fmt = self.conv_format.get().strip().lower()
        if fmt not in ('mp3', 'wav', 'flac', 'm4a'):
            messagebox.showerror("Error", "Unsupported format")
            return
        bitrate = self.conv_bitrate.get().strip() or '192k'
        # Start background conversion
        self.btn_convert.configure(state="disabled")
        threading.Thread(target=self.run_convert, args=(path, fmt, bitrate)).start()

    # --- HÀM MỞ FILE ĐA NỀN TẢNG (QUAN TRỌNG) ---
    def open_file_safe(self, path):
        if not os.path.exists(path):
            messagebox.showwarning("Error", "File not found / Không tìm thấy file")
            return

        try:
            if platform.system() == "Windows":
                os.startfile(path) # Chỉ chạy trên Windows
            elif platform.system() == "Darwin": # macOS
                subprocess.call(["open", path])
            else: # Linux
                subprocess.call(["xdg-open", path])
        except Exception as e:
            print(f"Lỗi mở file: {e}")
    # ---------------------------------------------

    def clear_his(self):
        if messagebox.askyesno("Confirm", "Sure?"): logic.clear_history_data(); self.refresh_his()

    def ask_and_convert(self, path):
        if not os.path.exists(path):
            messagebox.showwarning("Error", "File not found / Không tìm thấy file")
            return
        # Ask user for target format
        choice = simpledialog.askstring("Convert", "Enter target format (mp3, wav, flac, m4a):", initialvalue="mp3")
        if not choice: return
        fmt = choice.strip().lower()
        if fmt not in ('mp3', 'wav', 'flac', 'm4a'):
            messagebox.showerror("Error", "Unsupported format")
            return
        # Run conversion in background (no bitrate requested here)
        threading.Thread(target=self.run_convert, args=(path, fmt, '192k')).start()

    def run_convert(self, path, fmt, bitrate='192k'):
        # Disable any relevant buttons
        btns = []
        if hasattr(self, 'btn_convert'): btns.append(self.btn_convert)
        if hasattr(self, 'btn_download'): btns.append(self.btn_download)
        for b in btns:
            try: b.configure(state='disabled')
            except: pass

        try:
            self.after(0, lambda: self.lbl_status.configure(text=f"Converting to {fmt}...", text_color="#f59e0b"))
            suc, msg = logic.convert_file(path, fmt, bitrate)
            if suc:
                self.after(0, lambda: messagebox.showinfo("OK", f"Converted:\n{msg}"))
            else:
                self.after(0, lambda: messagebox.showerror("Error", f"Conversion failed:\n{msg}"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.after(0, lambda: self.lbl_status.configure(text=self.txt["status_ready"], text_color="gray"))
            for b in btns:
                try: b.configure(state='normal')
                except: pass

    def setup_system_tab(self):
        parent = self.tab_system
        ctk.CTkLabel(parent, text=self.txt["sys_title"], font=FONT_BOLD, text_color="gray").pack(pady=20)
        frame_lang = ctk.CTkFrame(parent); frame_lang.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(frame_lang, text=self.txt["lbl_lang"], font=FONT_BOLD).pack(side="left", padx=20, pady=15)
        self.combo_lang = ctk.CTkComboBox(frame_lang, values=["Tiếng Việt", "English"], command=self.change_lang, state="readonly", width=150)
        self.combo_lang.set("Tiếng Việt" if self.curr_lang_code=="vi" else "English")
        self.combo_lang.pack(side="right", padx=20, pady=15)
        self.btn_update = ctk.CTkButton(parent, text=self.txt["btn_update"], height=45, fg_color="#334155",
                                        command=self.start_update_thread); self.btn_update.pack(pady=20)
        self.lbl_up_status = ctk.CTkLabel(parent, text="...", font=FONT_MAIN, text_color="gray"); self.lbl_up_status.pack(pady=5)
        ctk.CTkLabel(parent, text=self.txt["version"], font=("Arial", 10)).pack(side="bottom", pady=20)

    def change_lang(self, choice):
        new = "vi" if choice=="Tiếng Việt" else "en"
        if new != self.curr_lang_code:
            save_config(new)
            if messagebox.askyesno("Restart", self.txt["msg_restart"]): self.destroy(); exit()

    def toggle_monitor(self):
        if self.var_monitor.get():
            self.lbl_status.configure(text=self.txt["status_monitoring"], text_color="#eab308")
            self.monitor_loop()
        else: self.lbl_status.configure(text="...", text_color="gray")

    def monitor_loop(self):
        if not self.var_monitor.get(): return
        try:
            content = pyperclip.paste().strip()
            if content != self.last_clipboard_text:
                self.last_clipboard_text = content
                if any(x in content for x in ["youtube.com", "youtu.be", "spotify.com"]):
                    ph = "Sơn Tùng" if self.curr_lang_code=="vi" else "Ed Sheeran"
                    if ph in self.txt_input.get("0.0", "end"): self.txt_input.delete("0.0", "end"); self.txt_input.insert("0.0", f"{content}")
                    elif len(self.txt_input.get("0.0", "end").strip()) > 0: self.txt_input.insert("end", f"\n{content}")
                    else: self.txt_input.insert("0.0", f"{content}")
                    self.lbl_status.configure(text=f"{self.txt['status_detected']} {content[:20]}...", text_color="#22c55e")
        except: pass
        self.after(1500, self.monitor_loop)

    def toggle_playlist_entry(self):
        if self.var_playlist.get():
            self.entry_playlist.configure(state="normal")
            try: ex = logic.get_existing_playlists()
            except: ex = []
            if ex: self.entry_playlist.configure(values=ex); self.entry_playlist.set(ex[0])
            else: self.entry_playlist.configure(values=[]); self.entry_playlist.set("")
            self.entry_playlist.focus()
        else: self.entry_playlist.configure(state="disabled"); self.entry_playlist.set(self.txt["combo_placeholder"])

    def start_download_thread(self):
        raw = self.txt_input.get("0.0", "end")
        ph = "Nhập mỗi" if self.curr_lang_code=="vi" else "Enter one"
        lst = [l for l in raw.split('\n') if l.strip() and ph not in l]
        if not lst: messagebox.showwarning("!", self.txt["msg_missing_content"]); return
        
        pname = self.entry_playlist.get().strip()
        if self.var_playlist.get() and (not pname or pname==self.txt["combo_placeholder"]):
            messagebox.showwarning("!", "Nhập tên Playlist!"); return

        self.btn_download.configure(state="disabled", text=self.txt["btn_downloading"])
        threading.Thread(target=self.run_dl, args=(lst, pname, self.var_playlist.get(), self.combo_format.get(), self.var_bpm_key.get())).start()

    def run_dl(self, lst, pname, use_p, fmt, detect_bpm_key_flag=False):
        folder = logic.BASE_FOLDER
        if use_p and pname:
            folder = os.path.join(logic.BASE_FOLDER, pname)
            if not os.path.exists(folder): os.makedirs(folder)
        
        codec = 'mp3'
        if "WAV" in fmt: codec='wav'
        elif "FLAC" in fmt: codec='flac'
        elif "M4A" in fmt: codec='m4a'

        def on_progress(msg):
            if msg == "analyzing":
                self.after(0, lambda: self.lbl_status.configure(text=self.txt["status_analyzing"], text_color="#a78bfa"))

        cnt=0; total=len(lst); errors=[]
        for i, q in enumerate(lst):
            if not q.strip(): continue
            self.after(0, lambda i=i, q=q, t=total: self.lbl_status.configure(text=f"Loading ({i+1}/{t}): {q[:20]}...", text_color="#0ea5e9"))
            self.after(0, lambda i=i, t=total: self.progress_bar.set((i+1)/t))
            suc, msg = logic.download_single_song(q, folder, codec, detect_bpm_key_flag=detect_bpm_key_flag, progress_callback=on_progress)
            if suc: cnt+=1
            else: errors.append(f"{q[:30]}: {msg}")
        
        self.after(0, lambda: self.finish_dl(cnt, total, folder, errors))

    def finish_dl(self, cnt, total, folder, errors=None):
        self.lbl_status.configure(text=f"✅ {cnt}/{total}", text_color="white")
        self.btn_download.configure(state="normal", text=self.txt["btn_download"])
        self.progress_bar.set(0); self.refresh_his()
        err = errors or []
        if cnt > 0:
            msg = f"{self.txt['msg_saved']}\n{folder}"
            if err:
                msg += f"\n\n{len(err)} failed."
            messagebox.showinfo(self.txt["msg_success"], msg)
            try:
                if platform.system() == "Windows": os.startfile(folder)
                elif platform.system() == "Darwin": subprocess.call(["open", folder])
                else: subprocess.call(["xdg-open", folder])
            except: pass
        elif err:
            err_msg = "\n".join(err[:5]) + ("\n..." if len(err) > 5 else "")
            messagebox.showerror("Download Failed", f"Could not download:\n{err_msg}")

    def start_update_thread(self):
        self.btn_update.configure(state="disabled", text=self.txt["btn_updating"])
        self.lbl_up_status.configure(text="...", text_color="#eab308")
        threading.Thread(target=self.run_up).start()

    def run_up(self):
        suc, msg = logic.update_core_system()
        self.after(0, lambda: self.fin_up(suc, msg))

    def fin_up(self, suc, msg):
        self.lbl_up_status.configure(text=f"✅ {msg}" if suc else f"❌ {msg}", text_color="#22c55e" if suc else "#ef4444")
        if suc: messagebox.showinfo("OK", "Update Done!")
        else: messagebox.showerror("Err", msg)
        self.btn_update.configure(state="normal", text=self.txt["btn_update"])

if __name__ == "__main__":
    app = MusicApp()
    app.mainloop()