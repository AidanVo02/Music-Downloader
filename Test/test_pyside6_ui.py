from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QComboBox, QLineEdit
)
from PySide6.QtCore import Qt


class TestPyside6UI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Downloader - PySide6 Test")
        self.resize(720, 520)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        title = QLabel("Music Downloader - PySide6 Test")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        main_layout.addWidget(title)

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Nhập tên bài hát hoặc link YouTube/Spotify...\nEnter song name or link...")
        main_layout.addWidget(self.input_box)

        options_layout = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp3", "wav", "flac", "m4a"])
        self.format_combo.setCurrentText("mp3")
        options_layout.addWidget(QLabel("Format:"))
        options_layout.addWidget(self.format_combo)

        self.bitrate_edit = QLineEdit("192k")
        options_layout.addWidget(QLabel("Bitrate:"))
        options_layout.addWidget(self.bitrate_edit)
        main_layout.addLayout(options_layout)

        button_layout = QHBoxLayout()
        self.download_btn = QPushButton("Test Download")
        self.download_btn.clicked.connect(self.on_download_clicked)
        button_layout.addWidget(self.download_btn)

        self.convert_btn = QPushButton("Test Convert")
        self.convert_btn.clicked.connect(self.on_convert_clicked)
        button_layout.addWidget(self.convert_btn)
        main_layout.addLayout(button_layout)

        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: gray;")
        main_layout.addWidget(self.status_label)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Log output...\nThis is a UI test stub, not a full downloader.")
        main_layout.addWidget(self.log_box)

    def on_download_clicked(self):
        text = self.input_box.toPlainText().strip()
        if not text:
            self.status_label.setText("Status: Enter song name or link")
            return
        self.status_label.setText("Status: Simulating download...")
        self.log_box.append(f"[Download] Query: {text}")
        self.log_box.append(f"[Download] Format: {self.format_combo.currentText()}")
        self.log_box.append("[Download] This is just a UI test stub.")

    def on_convert_clicked(self):
        text = self.input_box.toPlainText().strip()
        if not text:
            self.status_label.setText("Status: Enter file path or name")
            return
        self.status_label.setText("Status: Simulating convert...")
        self.log_box.append(f"[Convert] Input: {text}")
        self.log_box.append(f"[Convert] Output format: {self.format_combo.currentText()}")
        self.log_box.append("[Convert] This is just a UI test stub.")


if __name__ == "__main__":
    app = QApplication([])
    window = TestPyside6UI()
    window.show()
    app.exec()
