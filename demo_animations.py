"""
Demo Script for Animation Effects
Hiển thị các hiệu ứng hoạt ảnh mà không cần tải nhạc
"""

import customtkinter as ctk
from tkinter import Canvas
import animations
import threading
import time

class AnimationDemo(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Music Downloader - Animation Demo")
        self.geometry("600x800")
        
        # Title
        title_label = ctk.CTkLabel(
            self, 
            text="🎨 Animation Effects Demo", 
            font=("Segoe UI", 24, "bold"),
            text_color="#0ea5e9"
        )
        title_label.pack(pady=20)
        
        # Canvas for animations
        self.canvas = Canvas(
            self, 
            width=550, height=200, 
            bg="#212121", 
            highlightthickness=0
        )
        self.canvas.pack(pady=10, padx=25, fill="both", expand=False)
        
        # Control buttons frame
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=20, padx=20, fill="x")
        
        # Loading animation button
        btn_loading = ctk.CTkButton(
            button_frame,
            text="▶ Start Loading Animation",
            command=self.start_loading,
            fg_color="#0ea5e9",
            hover_color="#0284c7",
            height=45,
            font=("Segoe UI", 12, "bold")
        )
        btn_loading.pack(pady=10, fill="x")
        
        # Analyzing animation button
        btn_analyzing = ctk.CTkButton(
            button_frame,
            text="▶ Start Analyzing Animation",
            command=self.start_analyzing,
            fg_color="#a78bfa",
            hover_color="#9370db",
            height=45,
            font=("Segoe UI", 12, "bold")
        )
        btn_analyzing.pack(pady=10, fill="x")
        
        # Stop button
        btn_stop = ctk.CTkButton(
            button_frame,
            text="⏹ Stop Animation",
            command=self.stop_animation,
            fg_color="#ef4444",
            hover_color="#dc2626",
            height=45,
            font=("Segoe UI", 12, "bold")
        )
        btn_stop.pack(pady=10, fill="x")
        
        # Info text
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        info_label = ctk.CTkLabel(
            info_frame,
            text="📖 Feature Information:\n\n"
                 "🌐 Loading Animation:\n"
                 "  • 3D bouncing sphere with physics\n"
                 "  • Particle effects on bounce\n"
                 "  • Dynamic color cycling\n"
                 "  • Used during music download\n\n"
                 "🌊 Analyzing Animation:\n"
                 "  • Pulsing central sphere\n"
                 "  • Expanding wave rings\n"
                 "  • Represents BPM/Key analysis\n"
                 "  • Smooth multicolor transitions\n\n"
                 "💫 Particle System:\n"
                 "  • Physics-based particles\n"
                 "  • Gravity simulation\n"
                 "  • Automatic fade out",
            font=("Segoe UI", 11),
            justify="left",
            text_color="gray85"
        )
        info_label.pack(anchor="w", padx=10, pady=10, fill="both")
        
        # Animations
        self.loading_animation = None
        self.analyzing_animation = None
    
    def start_loading(self):
        """Start loading animation"""
        self.stop_animation()
        self.canvas.delete("all")
        
        self.loading_animation = animations.LoadingAnimation(
            self.canvas,
            canvas_width=self.canvas.winfo_width(),
            canvas_height=self.canvas.winfo_height()
        )
        self.loading_animation.start()
    
    def start_analyzing(self):
        """Start analyzing animation"""
        self.stop_animation()
        self.canvas.delete("all")
        
        self.analyzing_animation = animations.AnalyzingAnimation(
            self.canvas,
            canvas_width=self.canvas.winfo_width(),
            canvas_height=self.canvas.winfo_height()
        )
        self.analyzing_animation.start()
    
    def stop_animation(self):
        """Stop current animation"""
        if self.loading_animation:
            self.loading_animation.stop()
            self.loading_animation = None
        
        if self.analyzing_animation:
            self.analyzing_animation.stop()
            self.analyzing_animation = None
        
        self.canvas.delete("all")
    
    def on_closing(self):
        """Cleanup on close"""
        self.stop_animation()
        self.destroy()


if __name__ == "__main__":
    # Set dark theme
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    app = AnimationDemo()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
