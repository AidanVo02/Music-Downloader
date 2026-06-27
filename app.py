import customtkinter as ctk
from tkinter import Canvas, filedialog, messagebox, simpledialog
import threading
import os
import pyperclip
import platform
import subprocess

try:
    from src import core, constants, utils
    from src.core import analyzer as analyzer_module
    from src.ui import animations
except ImportError as e:
    messagebox.showerror("Error", f"Missing module: {e}")
    raise SystemExit(1)


LANGUAGES = constants.LANGUAGES
FONT_MAIN = constants.FONT_MAIN
FONT_BOLD = constants.FONT_BOLD
FONT_TITLE = constants.FONT_TITLE

COLOR_ACCENT = "#0ea5e9"
COLOR_ACCENT_HOVER = "#0284c7"
COLOR_SUCCESS = "#22c55e"
COLOR_WARNING = "#f59e0b"
COLOR_DANGER = "#ef4444"
COLOR_SURFACE = "#0f172a"
COLOR_SURFACE_ALT = "#111827"
COLOR_CARD = "#1f2937"
COLOR_CARD_BORDER = "#334155"
COLOR_MUTED = "#94a3b8"
COLOR_TEXT_SOFT = "#cbd5e1"


ctk.set_appearance_mode("Dark")
try:
    theme_path = utils.resource_path(os.path.join("assets", "studio_theme.json"))
    ctk.set_default_color_theme(theme_path)
except Exception:
    ctk.set_default_color_theme("blue")


class MusicApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config = utils.load_config()
        self.curr_lang_code = self.config.get("language", "en")
        self.txt = LANGUAGES[self.curr_lang_code]

        self.loading_animation = None
        self.analyzing_animation = None
        self.last_clipboard_text = ""

        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.title(self.txt["app_title"])
        self.geometry("980x760")
        self.minsize(920, 720)
        self.configure(fg_color=COLOR_SURFACE_ALT)

        self.main_shell = ctk.CTkFrame(self, fg_color=COLOR_SURFACE_ALT)
        self.main_shell.pack(fill="both", expand=True, padx=22, pady=18)

        self._build_header()
        self._build_tabs()
        self.refresh_backend_badges()

    def _build_header(self):
        header = ctk.CTkFrame(self.main_shell, corner_radius=22, fg_color=COLOR_SURFACE)
        header.pack(fill="x", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)

        title_block = self.create_subframe(header)
        title_block.grid(row=0, column=0, sticky="w", padx=22, pady=20)

        self.lbl_title = ctk.CTkLabel(
            title_block,
            text=self.txt["app_title"],
            font=("Segoe UI", 28, "bold"),
            text_color="#67e8f9",
        )
        self.lbl_title.pack(anchor="w")
        self.lbl_subtitle = ctk.CTkLabel(
            title_block,
            text="Download, convert and validate tracks inside one studio-like workspace.",
            font=("Segoe UI", 13),
            text_color=COLOR_TEXT_SOFT,
        )
        self.lbl_subtitle.pack(anchor="w", pady=(4, 0))

        badge_block = self.create_subframe(header)
        badge_block.grid(row=0, column=1, sticky="e", padx=22, pady=18)
        self.backend_badge = ctk.CTkLabel(
            badge_block,
            text="Analyzer: ...",
            font=("Segoe UI", 12, "bold"),
            fg_color="#172554",
            text_color="#e2e8f0",
            corner_radius=999,
            padx=14,
            pady=8,
        )
        self.backend_badge.pack(anchor="e")
        self.queue_badge = ctk.CTkLabel(
            badge_block,
            text="Queue: 0 tracks",
            font=("Segoe UI", 12),
            fg_color="#1e293b",
            text_color=COLOR_TEXT_SOFT,
            corner_radius=999,
            padx=14,
            pady=8,
        )
        self.queue_badge.pack(anchor="e", pady=(10, 0))

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(
            self.main_shell,
            width=880,
            height=620,
            corner_radius=20,
            fg_color=COLOR_SURFACE_ALT,
            border_width=1,
            border_color=COLOR_CARD_BORDER,
            segmented_button_fg_color=COLOR_SURFACE,
            segmented_button_selected_color=COLOR_CARD,
            segmented_button_selected_hover_color="#374151",
            segmented_button_unselected_color=COLOR_SURFACE,
            segmented_button_unselected_hover_color="#1e293b",
        )
        self.tabview.pack(fill="both", expand=True)

        self.tab_download = self.tabview.add(self.txt["tab_dl"])
        self.tab_history = self.tabview.add(self.txt["tab_his"])
        self.tab_system = self.tabview.add(self.txt["tab_sys"])
        self.tab_convert = self.tabview.add(self.txt.get("tab_conv", "Convert"))
        for tab in (self.tab_download, self.tab_history, self.tab_system, self.tab_convert):
            tab.configure(fg_color=COLOR_SURFACE_ALT)

        self.setup_downloader_tab()
        self.setup_history_tab()
        self.setup_convert_tab()
        self.setup_system_tab()

    def create_card(self, parent, **kwargs):
        options = {
            "corner_radius": 18,
            "fg_color": COLOR_CARD,
            "border_width": 1,
            "border_color": COLOR_CARD_BORDER,
        }
        options.update(kwargs)
        return ctk.CTkFrame(parent, **options)

    def create_subframe(self, parent, **kwargs):
        parent_color = kwargs.pop("fg_color", None)
        if parent_color is None:
            try:
                parent_color = parent.cget("fg_color")
            except Exception:
                parent_color = COLOR_SURFACE_ALT
        return ctk.CTkFrame(parent, fg_color=parent_color, **kwargs)

    def create_section_title(self, parent, title, subtitle=None):
        block = self.create_subframe(parent)
        block.pack(fill="x", padx=18, pady=(16, 10))
        ctk.CTkLabel(block, text=title, font=("Segoe UI", 17, "bold")).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(block, text=subtitle, font=("Segoe UI", 12), text_color=COLOR_MUTED).pack(anchor="w", pady=(2, 0))
        return block

    def create_metric_chip(self, parent, title):
        chip = ctk.CTkFrame(
            parent,
            corner_radius=16,
            fg_color=COLOR_SURFACE,
            border_width=1,
            border_color=COLOR_CARD_BORDER,
        )
        chip.pack(side="left", fill="x", expand=True, padx=6)
        ctk.CTkLabel(chip, text=title, font=("Segoe UI", 11), text_color=COLOR_MUTED).pack(anchor="w", padx=12, pady=(9, 0))
        value = ctk.CTkLabel(chip, text="...", font=("Segoe UI", 15, "bold"))
        value.pack(anchor="w", padx=12, pady=(0, 10))
        return value

    def get_backend_name(self):
        return analyzer_module.get_detection_backend()

    def refresh_backend_badges(self):
        backend = self.get_backend_name()
        self.backend_badge.configure(text=f"Analyzer: {backend}")
        if hasattr(self, "metric_backend"):
            self.metric_backend.configure(text=backend)
        if hasattr(self, "system_backend_value"):
            self.system_backend_value.configure(text=backend)

    def set_status(self, text, color=COLOR_MUTED):
        if hasattr(self, "lbl_status"):
            self.lbl_status.configure(text=text, text_color=color)

    def update_download_summary(self):
        raw = self.txt_input.get("0.0", "end").strip()
        placeholder_lines = {line.strip() for line in self.txt["input_placeholder"].splitlines() if line.strip()}
        tracks = [line for line in raw.splitlines() if line.strip() and line.strip() not in placeholder_lines]
        if hasattr(self, "metric_tracks"):
            self.metric_tracks.configure(text=str(len(tracks)))
        if hasattr(self, "metric_format"):
            self.metric_format.configure(text=self.combo_format.get())
        if hasattr(self, "metric_backend"):
            self.metric_backend.configure(text=self.get_backend_name())
        self.queue_badge.configure(text=f"Queue: {len(tracks)} tracks")

    def setup_downloader_tab(self):
        parent = self.tab_download
        parent.grid_columnconfigure(0, weight=5)
        parent.grid_columnconfigure(1, weight=3)
        parent.grid_rowconfigure(0, weight=1)

        left_col = self.create_subframe(parent, fg_color=COLOR_SURFACE_ALT)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(10, 8), pady=10)
        right_col = self.create_subframe(parent, fg_color=COLOR_SURFACE_ALT)
        right_col.grid(row=0, column=1, sticky="nsew", padx=(8, 10), pady=10)

        input_card = self.create_card(left_col)
        input_card.pack(fill="x")
        self.create_section_title(
            input_card,
            self.txt["guide"],
            "Paste song names or supported links. One line equals one queued download.",
        )
        self.txt_input = ctk.CTkTextbox(input_card, height=220, font=FONT_MAIN)
        self.txt_input.pack(padx=18, pady=(0, 18), fill="x")
        self.txt_input.insert("0.0", self.txt["input_placeholder"])
        self.txt_input.bind("<KeyRelease>", lambda _event: self.update_download_summary())

        summary_row = self.create_subframe(left_col, fg_color=COLOR_SURFACE_ALT)
        summary_row.pack(fill="x", pady=12)
        self.metric_tracks = self.create_metric_chip(summary_row, "Tracks")
        self.metric_format = self.create_metric_chip(summary_row, "Format")
        self.metric_backend = self.create_metric_chip(summary_row, "Analyzer")

        progress_card = self.create_card(left_col)
        progress_card.pack(fill="both", expand=True)
        self.create_section_title(progress_card, "Live Progress", "Downloads and BPM/key analysis update here in real time.")

        self.canvas_animation = Canvas(
            progress_card,
            width=700,
            height=120,
            bg=COLOR_SURFACE_ALT,
            highlightthickness=0,
            relief="flat",
        )

        self.progress_shell = self.create_subframe(progress_card)
        self.progress_shell.pack(fill="x", padx=18, pady=(0, 18))
        self.progress_bar = ctk.CTkProgressBar(self.progress_shell, height=12)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x")
        self.lbl_status = ctk.CTkLabel(self.progress_shell, text=self.txt["status_ready"], font=FONT_MAIN, text_color=COLOR_MUTED)
        self.lbl_status.pack(anchor="w", pady=(10, 0))

        self.frame_options = self.create_card(right_col)
        self.frame_options.pack(fill="x")
        self.create_section_title(self.frame_options, "Download Settings", "Tune output format, queue behavior and metadata analysis.")
        self.options_body = self.create_subframe(self.frame_options)
        self.options_body.pack(fill="x", padx=18, pady=(0, 18))
        self.options_body.columnconfigure(0, weight=1)

        self.var_playlist = ctk.BooleanVar()
        self.chk_playlist = ctk.CTkCheckBox(
            self.options_body,
            text=self.txt["chk_playlist"],
            font=FONT_MAIN,
            variable=self.var_playlist,
            command=self.toggle_playlist_entry,
        )
        self.chk_playlist.grid(row=0, column=0, pady=(0, 10), sticky="w")

        self.var_monitor = ctk.BooleanVar(value=False)
        self.switch_monitor = ctk.CTkSwitch(
            self.options_body,
            text=self.txt["switch_paste"],
            font=FONT_MAIN,
            variable=self.var_monitor,
            command=self.toggle_monitor,
        )
        self.switch_monitor.grid(row=1, column=0, pady=(0, 10), sticky="w")

        self.var_bpm_key = ctk.BooleanVar(value=True)
        self.chk_bpm_key = ctk.CTkCheckBox(
            self.options_body,
            text=self.txt["chk_bpm_key"],
            font=FONT_MAIN,
            variable=self.var_bpm_key,
        )
        self.chk_bpm_key.grid(row=2, column=0, pady=(0, 14), sticky="w")

        ctk.CTkLabel(self.options_body, text="Playlist", font=("Segoe UI", 12, "bold"), text_color=COLOR_MUTED).grid(row=3, column=0, sticky="w")
        self.entry_playlist = ctk.CTkComboBox(self.options_body, width=200, state="disabled", font=FONT_MAIN, values=[])
        self.entry_playlist.set(self.txt["combo_placeholder"])
        self.entry_playlist.grid(row=4, column=0, pady=(6, 14), sticky="ew")

        ctk.CTkLabel(self.options_body, text="Output Format", font=("Segoe UI", 12, "bold"), text_color=COLOR_MUTED).grid(row=5, column=0, sticky="w")
        self.combo_format = ctk.CTkOptionMenu(
            self.options_body,
            values=["MP3 (320kbps)", "M4A", "WAV", "FLAC"],
            font=FONT_MAIN,
            command=lambda _choice: self.update_download_summary(),
        )
        self.combo_format.grid(row=6, column=0, pady=(6, 18), sticky="ew")

        self.btn_download = ctk.CTkButton(
            self.options_body,
            text=self.txt["btn_download"],
            height=48,
            font=("Segoe UI", 15, "bold"),
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            command=self.start_download_thread,
        )
        self.btn_download.grid(row=7, column=0, pady=(0, 0), sticky="ew")

        tips_card = self.create_card(right_col, fg_color=COLOR_SURFACE)
        tips_card.pack(fill="both", expand=True, pady=(12, 0))
        self.create_section_title(tips_card, "Tips", "Sharper input keeps the queue cleaner and faster.")
        tips = [
            "Use one line per track or paste direct YouTube and Spotify links.",
            "WAV and FLAC take longer but give the cleanest input for analyzer backends.",
            "Files are renamed only when both BPM and key pass validation.",
        ]
        for tip in tips:
            ctk.CTkLabel(
                tips_card,
                text=f"• {tip}",
                justify="left",
                wraplength=260,
                anchor="w",
                text_color=COLOR_TEXT_SOFT,
            ).pack(fill="x", padx=18, pady=4)

        self.update_download_summary()

    def setup_history_tab(self):
        parent = self.tab_history
        summary_card = self.create_card(parent)
        summary_card.pack(fill="x", padx=10, pady=10)
        summary_card.grid_columnconfigure(0, weight=1)

        title_block = self.create_subframe(summary_card)
        title_block.grid(row=0, column=0, sticky="w", padx=18, pady=16)
        ctk.CTkLabel(title_block, text=self.txt["his_title"], font=("Segoe UI", 17, "bold")).pack(anchor="w")
        self.history_count_label = ctk.CTkLabel(title_block, text="0 items", text_color=COLOR_MUTED)
        self.history_count_label.pack(anchor="w", pady=(4, 0))
        ctk.CTkButton(summary_card, text=self.txt["btn_clear"], width=110, fg_color=COLOR_DANGER, hover_color="#b91c1c", command=self.clear_his).grid(row=0, column=1, padx=18, pady=16)

        self.scroll_history = ctk.CTkScrollableFrame(parent)
        self.scroll_history.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.refresh_his()

    def refresh_his(self):
        for widget in self.scroll_history.winfo_children():
            widget.destroy()

        data = utils.load_history()
        self.history_count_label.configure(text=f"{len(data)} items")
        if not data:
            empty = self.create_card(self.scroll_history, fg_color=COLOR_SURFACE)
            empty.pack(fill="x", pady=18, padx=6)
            ctk.CTkLabel(empty, text="No downloads yet.", font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=18, pady=(18, 4))
            ctk.CTkLabel(empty, text="Completed tracks will appear here with quick open and convert actions.", text_color=COLOR_MUTED).pack(anchor="w", padx=18, pady=(0, 18))
            return

        for item in data:
            row = self.create_card(self.scroll_history, fg_color=COLOR_SURFACE)
            row.pack(fill="x", pady=6, padx=6)
            row.grid_columnconfigure(0, weight=1)

            meta = self.create_subframe(row)
            meta.grid(row=0, column=0, sticky="nsew", padx=16, pady=14)
            ctk.CTkLabel(meta, text=item["name"], font=("Segoe UI", 14, "bold"), anchor="w").pack(fill="x")
            ctk.CTkLabel(meta, text=item["path"], text_color=COLOR_MUTED, anchor="w", justify="left", wraplength=560).pack(fill="x", pady=(4, 6))
            ctk.CTkLabel(meta, text=item["time"], font=("Consolas", 11), text_color=COLOR_TEXT_SOFT).pack(anchor="w")

            actions = self.create_subframe(row)
            actions.grid(row=0, column=1, sticky="e", padx=16, pady=14)
            ctk.CTkButton(actions, text="Convert", width=88, height=30, fg_color="#16a34a", command=lambda p=item["path"]: self.ask_and_convert(p)).pack(side="right", padx=(8, 0))
            ctk.CTkButton(actions, text=self.txt["btn_open"], width=88, height=30, fg_color="#334155", command=lambda p=item["path"]: self.open_file_safe(p)).pack(side="right")

    def setup_convert_tab(self):
        parent = self.tab_convert
        frame = self.create_card(parent)
        frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.create_section_title(frame, "Convert Local Files", "Repackage existing media into audio formats used by the app.")
        row = self.create_subframe(frame)
        row.pack(fill="x", padx=18, pady=(0, 12))
        self.entry_convert_path = ctk.CTkEntry(row, placeholder_text="Path to file...", width=420)
        self.entry_convert_path.pack(side="left", padx=(0, 8), pady=6)
        ctk.CTkButton(row, text="Browse", width=90, command=self.browse_file).pack(side="left")

        opt_row = ctk.CTkFrame(frame, fg_color=COLOR_SURFACE)
        opt_row.pack(fill="x", padx=18, pady=8)
        ctk.CTkLabel(opt_row, text="Format:", font=FONT_MAIN).pack(side="left", padx=(16, 8), pady=14)
        self.conv_format = ctk.CTkOptionMenu(opt_row, values=["mp3", "wav", "flac", "m4a"], width=120)
        self.conv_format.set("mp3")
        self.conv_format.pack(side="left", padx=(0, 14))
        ctk.CTkLabel(opt_row, text="Bitrate:", font=FONT_MAIN).pack(side="left", padx=(0, 8))
        self.conv_bitrate = ctk.CTkEntry(opt_row, width=120)
        self.conv_bitrate.insert(0, "192k")
        self.conv_bitrate.pack(side="left")

        ctk.CTkLabel(frame, text="Tip: use WAV or FLAC before re-running analyzer checks on local files.", text_color=COLOR_MUTED).pack(anchor="w", padx=18, pady=(8, 0))
        self.btn_convert = ctk.CTkButton(frame, text="Convert", height=46, fg_color="#16a34a", command=self.start_convert_thread)
        self.btn_convert.pack(pady=18, padx=18, fill="x")

    def browse_file(self):
        path = filedialog.askopenfilename(
            title="Select file",
            filetypes=[("Media files", "*.mp4 *.m4a *.mp3 *.wav *.flac *.mkv *.aac"), ("All files", "*")],
        )
        if path:
            self.entry_convert_path.delete(0, "end")
            self.entry_convert_path.insert(0, path)

    def start_convert_thread(self):
        path = self.entry_convert_path.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showwarning("Error", "File not found / Khong tim thay file")
            return
        fmt = self.conv_format.get().strip().lower()
        if fmt not in ("mp3", "wav", "flac", "m4a"):
            messagebox.showerror("Error", "Unsupported format")
            return
        bitrate = self.conv_bitrate.get().strip() or "192k"
        self.btn_convert.configure(state="disabled")
        threading.Thread(target=self.run_convert, args=(path, fmt, bitrate), daemon=True).start()

    def open_file_safe(self, path):
        if not os.path.exists(path):
            messagebox.showwarning("Error", "File not found / Khong tim thay file")
            return

        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.call(["open", path])
            else:
                subprocess.call(["xdg-open", path])
        except Exception as exc:
            print(f"Open file error: {exc}")

    def clear_his(self):
        if messagebox.askyesno("Confirm", "Sure?"):
            utils.clear_history()
            self.refresh_his()

    def ask_and_convert(self, path):
        if not os.path.exists(path):
            messagebox.showwarning("Error", "File not found / Khong tim thay file")
            return
        choice = simpledialog.askstring("Convert", "Enter target format (mp3, wav, flac, m4a):", initialvalue="mp3")
        if not choice:
            return
        fmt = choice.strip().lower()
        if fmt not in ("mp3", "wav", "flac", "m4a"):
            messagebox.showerror("Error", "Unsupported format")
            return
        threading.Thread(target=self.run_convert, args=(path, fmt, "192k"), daemon=True).start()

    def run_convert(self, path, fmt, bitrate="192k"):
        buttons = []
        if hasattr(self, "btn_convert"):
            buttons.append(self.btn_convert)
        if hasattr(self, "btn_download"):
            buttons.append(self.btn_download)
        for button in buttons:
            try:
                button.configure(state="disabled")
            except Exception:
                pass

        try:
            self.after(0, lambda: self.set_status(f"Converting to {fmt}...", COLOR_WARNING))
            success, message = core.convert_file(path, fmt, bitrate)
            if success:
                self.after(0, lambda: messagebox.showinfo("OK", f"Converted:\n{message}"))
            else:
                self.after(0, lambda: messagebox.showerror("Error", f"Conversion failed:\n{message}"))
        except Exception as exc:
            self.after(0, lambda: messagebox.showerror("Error", str(exc)))
        finally:
            self.after(0, lambda: self.set_status(self.txt["status_ready"], COLOR_MUTED))
            for button in buttons:
                try:
                    button.configure(state="normal")
                except Exception:
                    pass

    def setup_system_tab(self):
        parent = self.tab_system
        sys_card = self.create_card(parent)
        sys_card.pack(fill="both", expand=True, padx=10, pady=10)

        self.create_section_title(sys_card, self.txt["sys_title"], "Language, analyzer routing and core maintenance controls.")

        frame_lang = ctk.CTkFrame(sys_card, fg_color=COLOR_SURFACE)
        frame_lang.pack(fill="x", padx=18, pady=(0, 12))
        ctk.CTkLabel(frame_lang, text=self.txt["lbl_lang"], font=FONT_BOLD).pack(side="left", padx=20, pady=15)
        self.combo_lang = ctk.CTkComboBox(frame_lang, values=["Tiáº¿ng Viá»‡t", "English"], command=self.change_lang, state="readonly", width=150)
        self.combo_lang.set("Tiáº¿ng Viá»‡t" if self.curr_lang_code == "vi" else "English")
        self.combo_lang.pack(side="right", padx=20, pady=15)

        backend_card = ctk.CTkFrame(sys_card, fg_color=COLOR_SURFACE)
        backend_card.pack(fill="x", padx=18, pady=(0, 12))
        ctk.CTkLabel(backend_card, text="Analyzer Backend", font=FONT_BOLD).pack(anchor="w", padx=20, pady=(16, 4))
        self.system_backend_value = ctk.CTkLabel(backend_card, text="...", font=("Segoe UI", 15, "bold"), text_color="#67e8f9")
        self.system_backend_value.pack(anchor="w", padx=20, pady=(0, 14))

        self.btn_update = ctk.CTkButton(sys_card, text=self.txt["btn_update"], height=45, fg_color="#334155", command=self.start_update_thread)
        self.btn_update.pack(fill="x", padx=18, pady=14)
        self.lbl_up_status = ctk.CTkLabel(sys_card, text="...", font=FONT_MAIN, text_color=COLOR_MUTED)
        self.lbl_up_status.pack(anchor="w", padx=18, pady=(0, 8))
        ctk.CTkLabel(sys_card, text=self.txt["version"], font=("Segoe UI", 10), text_color=COLOR_MUTED).pack(anchor="w", padx=18, pady=(8, 18))

    def change_lang(self, choice):
        new_code = "vi" if choice == "Tiáº¿ng Viá»‡t" else "en"
        if new_code != self.curr_lang_code:
            utils.save_config(new_code)
            if messagebox.askyesno("Restart", self.txt["msg_restart"]):
                self.destroy()
                raise SystemExit(0)

    def toggle_monitor(self):
        if self.var_monitor.get():
            self.set_status(self.txt["status_monitoring"], COLOR_WARNING)
            self.monitor_loop()
        else:
            self.set_status(self.txt["status_ready"], COLOR_MUTED)

    def monitor_loop(self):
        if not self.var_monitor.get():
            return
        try:
            content = pyperclip.paste().strip()
            if content != self.last_clipboard_text:
                self.last_clipboard_text = content
                if any(token in content for token in ["youtube.com", "youtu.be", "spotify.com"]):
                    placeholder_hint = "SÆ¡n TÃ¹ng" if self.curr_lang_code == "vi" else "Ed Sheeran"
                    if placeholder_hint in self.txt_input.get("0.0", "end"):
                        self.txt_input.delete("0.0", "end")
                        self.txt_input.insert("0.0", content)
                    elif len(self.txt_input.get("0.0", "end").strip()) > 0:
                        self.txt_input.insert("end", f"\n{content}")
                    else:
                        self.txt_input.insert("0.0", content)
                    self.set_status(f"{self.txt['status_detected']} {content[:24]}...", COLOR_SUCCESS)
                    self.update_download_summary()
        except Exception:
            pass
        self.after(1500, self.monitor_loop)

    def toggle_playlist_entry(self):
        if self.var_playlist.get():
            self.entry_playlist.configure(state="normal")
            try:
                playlists = utils.get_existing_playlists()
            except Exception:
                playlists = []
            if playlists:
                self.entry_playlist.configure(values=playlists)
                self.entry_playlist.set(playlists[0])
            else:
                self.entry_playlist.configure(values=[])
                self.entry_playlist.set("")
            self.entry_playlist.focus()
        else:
            self.entry_playlist.configure(state="disabled")
            self.entry_playlist.set(self.txt["combo_placeholder"])
        self.update_download_summary()

    def start_download_thread(self):
        raw = self.txt_input.get("0.0", "end")
        placeholder_token = "Nháº­p má»—i" if self.curr_lang_code == "vi" else "Enter one"
        lines = [line for line in raw.split("\n") if line.strip() and placeholder_token not in line]
        if not lines:
            messagebox.showwarning("!", self.txt["msg_missing_content"])
            return

        playlist_name = self.entry_playlist.get().strip()
        if self.var_playlist.get() and (not playlist_name or playlist_name == self.txt["combo_placeholder"]):
            messagebox.showwarning("!", "Nhap ten Playlist!")
            return

        self.btn_download.configure(state="disabled", text=self.txt["btn_downloading"])
        self.update_download_summary()
        threading.Thread(
            target=self.run_dl,
            args=(lines, playlist_name, self.var_playlist.get(), self.combo_format.get(), self.var_bpm_key.get()),
            daemon=True,
        ).start()

    def run_dl(self, items, playlist_name, use_playlist, fmt, detect_bpm_key_flag=False):
        folder = utils.BASE_FOLDER
        if use_playlist and playlist_name:
            folder = os.path.join(utils.BASE_FOLDER, playlist_name)
            if not os.path.exists(folder):
                os.makedirs(folder)

        codec = "mp3"
        if "WAV" in fmt:
            codec = "wav"
        elif "FLAC" in fmt:
            codec = "flac"
        elif "M4A" in fmt:
            codec = "m4a"

        self.after(0, self._start_loading_animation)

        def on_progress(message):
            if message == "analyzing":
                self.after(0, self._start_analyzing_animation)

        success_count = 0
        total = len(items)
        errors = []

        for index, query in enumerate(items):
            if not query.strip():
                continue
            self.after(0, lambda i=index, q=query, t=total: self.set_status(f"Loading ({i + 1}/{t}): {q[:24]}...", COLOR_ACCENT))
            self.after(0, lambda i=index, t=total: self.progress_bar.set((i + 1) / t))
            success, message = core.download_single_song(query, folder, codec, detect_bpm_key_flag=detect_bpm_key_flag, progress_callback=on_progress)
            if success:
                success_count += 1
            else:
                errors.append(f"{query[:30]}: {message}")

        self.after(0, self._stop_animations)
        self.after(0, lambda: self.finish_dl(success_count, total, folder, errors))

    def finish_dl(self, success_count, total, folder, errors=None):
        self.set_status(f"Completed {success_count}/{total}", "#f8fafc")
        self.btn_download.configure(state="normal", text=self.txt["btn_download"])
        self.progress_bar.set(0)
        self.refresh_his()
        self.update_download_summary()
        errors = errors or []

        if success_count > 0:
            message = f"{self.txt['msg_saved']}\n{folder}"
            if errors:
                message += f"\n\n{len(errors)} failed."
            messagebox.showinfo(self.txt["msg_success"], message)
            try:
                if platform.system() == "Windows":
                    os.startfile(folder)
                elif platform.system() == "Darwin":
                    subprocess.call(["open", folder])
                else:
                    subprocess.call(["xdg-open", folder])
            except Exception:
                pass
        elif errors:
            error_message = "\n".join(errors[:5]) + ("\n..." if len(errors) > 5 else "")
            messagebox.showerror("Download Failed", f"Could not download:\n{error_message}")

    def _start_loading_animation(self):
        try:
            self.canvas_animation.pack(pady=(0, 14), padx=18, fill="x", before=self.progress_shell)
            self.canvas_animation.delete("all")
            self.loading_animation = animations.LoadingAnimation(
                self.canvas_animation,
                canvas_width=self.canvas_animation.winfo_width(),
                canvas_height=self.canvas_animation.winfo_height(),
            )
            self.loading_animation.start()
        except Exception as exc:
            print(f"Error starting loading animation: {exc}")

    def _start_analyzing_animation(self):
        try:
            if not self.canvas_animation.winfo_manager():
                self.canvas_animation.pack(pady=(0, 14), padx=18, fill="x", before=self.progress_shell)
            self.canvas_animation.delete("all")
            if self.loading_animation:
                self.loading_animation.stop()
            self.analyzing_animation = animations.AnalyzingAnimation(
                self.canvas_animation,
                canvas_width=self.canvas_animation.winfo_width(),
                canvas_height=self.canvas_animation.winfo_height(),
            )
            self.analyzing_animation.start()
        except Exception as exc:
            print(f"Error starting analyzing animation: {exc}")

    def _stop_animations(self):
        try:
            if self.loading_animation:
                self.loading_animation.stop()
                self.loading_animation = None
            if self.analyzing_animation:
                self.analyzing_animation.stop()
                self.analyzing_animation = None
            self.canvas_animation.delete("all")
            self.canvas_animation.pack_forget()
        except Exception as exc:
            print(f"Error stopping animations: {exc}")

    def _on_closing(self):
        self._stop_animations()
        self.destroy()

    def start_update_thread(self):
        self.btn_update.configure(state="disabled", text=self.txt["btn_updating"])
        self.lbl_up_status.configure(text="...", text_color=COLOR_WARNING)
        threading.Thread(target=self.run_up, daemon=True).start()

    def run_up(self):
        success, message = core.update_core_system()
        self.after(0, lambda: self.fin_up(success, message))

    def fin_up(self, success, message):
        self.lbl_up_status.configure(text=f"OK {message}" if success else f"ERR {message}", text_color=COLOR_SUCCESS if success else COLOR_DANGER)
        if success:
            messagebox.showinfo("OK", "Update Done!")
        else:
            messagebox.showerror("Err", message)
        self.btn_update.configure(state="normal", text=self.txt["btn_update"])


if __name__ == "__main__":
    app = MusicApp()
    app.mainloop()
