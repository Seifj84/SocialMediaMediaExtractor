"""
PySide6 Graphical User Interface for OmniMedia Extractor.
Modern, responsive desktop UI with folder picker dialog and real-time download tracking.
"""

import os
import sys
import subprocess
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QProgressBar, QTextEdit, QFileDialog, QGroupBox, QMessageBox
)
from PySide6.QtGui import QFont, QIcon, QClipboard

from ..core.models import MediaFilter, MediaQuality, ExtractionResult
from ..core.config import Config, get_config, save_config
from ..core.ffmpeg_finder import find_ffmpeg
from ..extractors.manager import ExtractorManager
from ..utils.file_utils import format_bytes


DARK_STYLE_SHEET = """
QMainWindow, QWidget {
    background-color: #12141a;
    color: #e2e8f0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #2d3748;
    border-radius: 8px;
    margin-top: 12px;
    font-weight: bold;
    color: #63b3ed;
    padding-top: 18px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
}
QLineEdit {
    background-color: #1a202c;
    border: 1px solid #4a5568;
    border-radius: 6px;
    padding: 8px 12px;
    color: #ffffff;
}
QLineEdit:focus {
    border: 1px solid #3182ce;
}
QPushButton {
    background-color: #2b6cb0;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #3182ce;
}
QPushButton:pressed {
    background-color: #2b6cb0;
}
QPushButton#actionBtn {
    background-color: #38a169;
    font-size: 14px;
    padding: 10px 20px;
}
QPushButton#actionBtn:hover {
    background-color: #48bb78;
}
QPushButton#secondaryBtn {
    background-color: #4a5568;
}
QPushButton#secondaryBtn:hover {
    background-color: #718096;
}
QComboBox {
    background-color: #1a202c;
    border: 1px solid #4a5568;
    border-radius: 6px;
    padding: 6px 12px;
    color: #ffffff;
}
QCheckBox {
    spacing: 8px;
}
QProgressBar {
    border: 1px solid #2d3748;
    border-radius: 6px;
    text-align: center;
    background-color: #1a202c;
    color: #ffffff;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: #3182ce;
    border-radius: 5px;
}
QTextEdit {
    background-color: #0d1117;
    border: 1px solid #2d3748;
    border-radius: 6px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    color: #a0aec0;
    padding: 8px;
}
"""


class ExtractionWorker(QThread):
    """Background worker thread for media extraction without freezing GUI."""
    progress_signal = Signal(int, int, str)
    finished_signal = Signal(object)
    error_signal = Signal(str)

    def __init__(self, url: str, output_dir: str, media_filter: MediaFilter, quality: MediaQuality, config: Config):
        super().__init__()
        self.url = url
        self.output_dir = output_dir
        self.media_filter = media_filter
        self.quality = quality
        self.config = config

    def run(self):
        try:
            manager = ExtractorManager(self.config)

            def callback(step, total, msg):
                self.progress_signal.emit(step, total, msg)

            result = manager.extract(
                url=self.url,
                output_dir=self.output_dir,
                media_filter=self.media_filter,
                quality=self.quality,
                progress_cb=callback,
            )
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))


class OmniMediaMainWindow(QMainWindow):
    """Main Application Window for OmniMedia."""

    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.worker: Optional[ExtractionWorker] = None
        self.last_destination: str = self.config.default_output_dir

        self.setWindowTitle("OmniMedia - Universal Social Media Media Extractor")
        self.resize(800, 680)
        self.setStyleSheet(DARK_STYLE_SHEET)

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(18, 18, 18, 18)

        # Header Title
        title_label = QLabel("OmniMedia Extractor")
        title_font = QFont("Segoe UI", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #63b3ed;")
        main_layout.addWidget(title_label)

        sub_label = QLabel("Extract high-quality photos, audio, and videos from Instagram, TikTok, YouTube, X, Reddit, and more.")
        sub_label.setStyleSheet("color: #a0aec0; margin-bottom: 6px;")
        main_layout.addWidget(sub_label)

        # 1. URL Input Box
        url_group = QGroupBox("1. Social Media Post Link")
        url_layout = QHBoxLayout(url_group)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste URL here (e.g. https://www.instagram.com/p/... or https://tiktok.com/@.../video/...)")
        self.paste_btn = QPushButton("Paste")
        self.paste_btn.clicked.connect(self.paste_from_clipboard)
        url_layout.addWidget(self.url_input, stretch=4)
        url_layout.addWidget(self.paste_btn, stretch=1)
        main_layout.addWidget(url_group)

        # 2. Destination Folder Selector Box
        dest_group = QGroupBox("2. Destination Folder (Save Location)")
        dest_layout = QHBoxLayout(dest_group)
        self.dest_input = QLineEdit()
        self.dest_input.setText(self.config.default_output_dir)
        self.browse_btn = QPushButton("Browse Folder...")
        self.browse_btn.clicked.connect(self.browse_folder)
        self.open_dir_btn = QPushButton("Open Folder")
        self.open_dir_btn.setObjectName("secondaryBtn")
        self.open_dir_btn.clicked.connect(self.open_output_folder)
        dest_layout.addWidget(self.dest_input, stretch=4)
        dest_layout.addWidget(self.browse_btn, stretch=1)
        dest_layout.addWidget(self.open_dir_btn, stretch=1)
        main_layout.addWidget(dest_group)

        # 3. Media Format & Quality Options
        opt_group = QGroupBox("3. Extraction Options")
        opt_layout = QHBoxLayout(opt_group)

        # Filter combo
        filter_label = QLabel("Filter:")
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Media (Photos + Videos)", MediaFilter.ALL)
        self.filter_combo.addItem("Photos / Images Only", MediaFilter.IMAGES_ONLY)
        self.filter_combo.addItem("Videos Only", MediaFilter.VIDEOS_ONLY)
        self.filter_combo.addItem("Audio Only (MP3)", MediaFilter.AUDIO_ONLY)

        # Quality combo
        qual_label = QLabel("Quality:")
        self.qual_combo = QComboBox()
        self.qual_combo.addItem("Highest Available (Best)", MediaQuality.BEST)
        self.qual_combo.addItem("1080p Full HD", MediaQuality.HIGH)
        self.qual_combo.addItem("720p HD", MediaQuality.MEDIUM)

        opt_layout.addWidget(filter_label)
        opt_layout.addWidget(self.filter_combo)
        opt_layout.addWidget(qual_label)
        opt_layout.addWidget(self.qual_combo)

        # Checkboxes
        self.activity_folder_check = QCheckBox("Name folder after Activity & Date")
        self.activity_folder_check.setChecked(self.config.organize_by_activity)
        self.jpg_convert_check = QCheckBox("Convert WebP to JPG")
        self.jpg_convert_check.setChecked(self.config.convert_webp_to_jpg)

        opt_layout.addWidget(self.activity_folder_check)
        opt_layout.addWidget(self.jpg_convert_check)
        main_layout.addWidget(opt_group)

        # Optional Activity Name Box
        act_group = QGroupBox("4. Activity Name (Optional Custom Override)")
        act_layout = QHBoxLayout(act_group)
        self.activity_input = QLineEdit()
        self.activity_input.setPlaceholderText("Leave blank to auto-detect from caption (e.g. Mkutano wa Jukwa la NGOs Mkoa Tanga - Date)")
        act_layout.addWidget(self.activity_input)
        main_layout.addWidget(act_group)

        # 4. Action Button
        self.download_btn = QPushButton("Extract & Download Media")
        self.download_btn.setObjectName("actionBtn")
        self.download_btn.clicked.connect(self.start_extraction)
        main_layout.addWidget(self.download_btn)

        # 5. Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(22)
        main_layout.addWidget(self.progress_bar)

        # 6. Log Console
        log_label = QLabel("Activity Log & Media Details:")
        log_label.setStyleSheet("color: #a0aec0; font-weight: bold;")
        main_layout.addWidget(log_label)

        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        main_layout.addWidget(self.log_console, stretch=1)

        self.log("OmniMedia ready. Paste a social media URL and click 'Extract & Download Media'.")

    def paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if text:
            self.url_input.setText(text)
            self.log(f"Pasted URL from clipboard: {text}")

    def browse_folder(self):
        current = self.dest_input.text().strip() or os.path.expanduser("~")
        chosen = QFileDialog.getExistingDirectory(self, "Select Save Location", current)
        if chosen:
            self.dest_input.setText(chosen)
            self.config.default_output_dir = chosen
            save_config(self.config)
            self.log(f"Destination folder set to: {chosen}")

    def open_output_folder(self):
        path = self.last_destination or self.dest_input.text().strip()
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        except Exception as e:
            self.log(f"Error opening folder: {e}")

    def log(self, message: str):
        self.log_console.append(message)
        self.log_console.verticalScrollBar().setValue(self.log_console.verticalScrollBar().maximum())

    def start_extraction(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Input Required", "Please enter or paste a valid social media URL.")
            return

        destination = self.dest_input.text().strip()
        if not destination:
            destination = self.config.default_output_dir
            self.dest_input.setText(destination)

        os.makedirs(destination, exist_ok=True)

        self.config.organize_by_activity = self.activity_folder_check.isChecked()
        self.config.convert_webp_to_jpg = self.jpg_convert_check.isChecked()
        custom_act = self.activity_input.text().strip()
        self.config.custom_folder_name = custom_act if custom_act else None

        filter_enum = self.filter_combo.currentData()
        quality_enum = self.qual_combo.currentData()

        self.download_btn.setEnabled(False)
        self.download_btn.setText("Extracting Media...")
        self.progress_bar.setValue(10)
        self.log(f"\n[START] Extracting from: {url}")
        self.log(f"Target folder: {destination}")

        self.worker = ExtractionWorker(
            url=url,
            output_dir=destination,
            media_filter=filter_enum,
            quality=quality_enum,
            config=self.config,
        )
        self.worker.progress_signal.connect(self.on_worker_progress)
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.error_signal.connect(self.on_worker_error)
        self.worker.start()

    def on_worker_progress(self, step: int, total: int, msg: str):
        if total > 0:
            val = int((step / total) * 100)
            self.progress_bar.setValue(val)
        self.log(f"[*] {msg}")

    def on_worker_finished(self, result: ExtractionResult):
        self.download_btn.setEnabled(True)
        self.download_btn.setText("Extract & Download Media")
        self.progress_bar.setValue(100)

        if result.success and result.downloaded_files:
            self.last_destination = result.target_dir
            self.log(f"\n[SUCCESS] Extracted {len(result.downloaded_files)} file(s) from {result.platform}!")
            if result.activity_name:
                self.log(f"Activity: {result.activity_name}")
            self.log(f"Saved into: {result.target_dir}")
            for fpath in result.downloaded_files:
                sz = format_bytes(os.path.getsize(fpath)) if os.path.exists(fpath) else ""
                self.log(f"  - {os.path.basename(fpath)} ({sz})")
            if result.post_content_file:
                self.log(f"  - post_content.txt saved")
            if result.metadata_file:
                self.log(f"  - metadata.json saved")
            QMessageBox.information(
                self,
                "Extraction Completed",
                f"Successfully extracted {len(result.downloaded_files)} media item(s) to:\n{result.target_dir}"
            )
        elif result.success and not result.downloaded_files:
            self.log("[!] Post processed successfully, but no items matched filter.")
            QMessageBox.warning(self, "No Items", "Extraction succeeded but no items matched your filter.")
        else:
            self.log(f"[ERROR] {result.error_message}")
            QMessageBox.critical(self, "Extraction Error", f"Extraction failed:\n{result.error_message}")

    def on_worker_error(self, err_msg: str):
        self.download_btn.setEnabled(True)
        self.download_btn.setText("Extract & Download Media")
        self.progress_bar.setValue(0)
        self.log(f"[ERROR] {err_msg}")
        QMessageBox.critical(self, "Error", f"Failed: {err_msg}")


def launch_gui():
    """Entry point to launch the PySide6 Qt GUI."""
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    window = OmniMediaMainWindow()
    window.show()
    sys.exit(app.exec())
