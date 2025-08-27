"""
Download management tab for BiliDownload application.

This module provides the download interface including:
- Video URL input and title fetching
- Download path selection
- Download progress monitoring
- Log display and management
"""

import os
import re
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QProgressBar, QTextEdit, QSplitter, QFrame, QGroupBox, QCheckBox,
    QFileDialog, QMessageBox, QTimer
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from src.core.downloader import BiliDownloader
from src.core.logger import get_logger


class DownloadWorker(QThread):
    """
    Background download worker thread.
    
    Handles video downloading in a separate thread to keep the UI responsive.
    
    Attributes:
        progress_updated (pyqtSignal): Emitted with (int percentage, str message).
        download_finished (pyqtSignal): Emitted with (bool success, str message).
        log_message (pyqtSignal): Emitted with (str message) for log updates.
    """
    
    progress_updated = pyqtSignal(int, str)
    download_finished = pyqtSignal(bool, str)
    log_message = pyqtSignal(str)
    
    def __init__(self, url, save_path, ffmpeg_path=None, is_series=False):
        """
        Initialize the download worker.
        
        Args:
            url (str): Video URL to download.
            save_path (str): Absolute directory path where files will be saved.
            ffmpeg_path (str | None): Optional path to FFmpeg executable.
            is_series (bool): Whether to download as a series (multi-part).
        """
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.ffmpeg_path = ffmpeg_path
        self.is_series = is_series
        self.downloader = BiliDownloader()
        self.logger = get_logger(__name__)
    
    def run(self):
        """
        Execute the download task.
        
        Downloads the video and emits progress and completion signals.
        
        Returns:
            None
        """
        try:
            self.log_message.emit("Starting download...")
            
            if self.is_series:
                success = self.downloader.download_series(
                    self.url, self.save_path, self.ffmpeg_path
                )
            else:
                success = self.downloader.download_video(
                    self.url, self.save_path, self.ffmpeg_path
                )
            
            if success:
                self.download_finished.emit(True, "Download completed successfully!")
            else:
                self.download_finished.emit(False, "Download failed!")
                
        except Exception as e:
            self.logger.error(f"Download error: {e}")
            self.download_finished.emit(False, f"Download error: {str(e)}")


class DownloadTab(QWidget):
    """
    Download management tab page.
    
    Provides interface for video downloading including URL input,
    path selection, progress monitoring, and log display.
    """
    
    def __init__(self, config_manager):
        """
        Initialize the download tab.
        
        Args:
            config_manager: Configuration manager instance providing paths and settings.
        """
        super().__init__()
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.download_worker = None
        
        # Initialize UI
        self.init_ui()
        
        # Load configuration
        self.load_config()
        
        # Create timer for FFmpeg status checking
        self.ffmpeg_check_timer = QTimer()
        self.ffmpeg_check_timer.timeout.connect(self.update_ffmpeg_status)
        self.ffmpeg_check_timer.start(5000)  # Check every 5 seconds
    
    def init_ui(self):
        """
        Initialize the user interface.
        
        Creates all UI components including input fields, controls,
        progress display, and log panel.
        
        Returns:
            None
        """
        # Apply soft theme styles
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9ff;
                color: #4a5bbf;
            }
            QLineEdit, QTextEdit {
                border: 1px solid #e1e8ff;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
            }
            QPushButton {
                background-color: #e8f0ff;
                color: #5a6acf;
                border: 1px solid #d1d8ff;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #d8e8ff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e1e8ff;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Download control panel
        left_panel = self.create_download_control_panel()
        splitter.addWidget(left_panel)
        
        # Right: Download log
        right_panel = self.create_log_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter ratio
        splitter.setSizes([400, 300])
        
        # Bottom: Progress bar
        progress_panel = self.create_progress_panel()
        
        layout.addWidget(splitter)
        layout.addWidget(progress_panel)
    
    def create_download_control_panel(self):
        """
        Create the download control panel.
        
        Returns:
            QWidget: Download control panel with input fields and buttons.
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Download Management")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Video URL input
        url_group = QGroupBox("Video URL")
        url_layout = QVBoxLayout(url_group)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter Bilibili video URL here...")
        url_layout.addWidget(self.url_input)
        
        # Connect URL input text change signal for auto title fetching
        self.url_input.textChanged.connect(self.on_url_changed)
        
        # Create timer for delayed auto-fetching
        self.auto_fetch_timer = QTimer()
        self.auto_fetch_timer.setSingleShot(True)
        self.auto_fetch_timer.timeout.connect(self.auto_get_title)
        
        layout.addWidget(url_group)
        
        # Video title input
        title_group = QGroupBox("Video Title")
        title_layout = QVBoxLayout(title_group)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Video title will be auto-fetched...")
        self.title_input.setReadOnly(False)  # Allow user editing
        title_layout.addWidget(self.title_input)
        
        # Add clear title button
        clear_title_btn = QPushButton("Clear Title")
        clear_title_btn.clicked.connect(self.clear_title)
        title_layout.addWidget(clear_title_btn)
        
        layout.addWidget(title_group)
        
        # Quick operation buttons
        quick_btn_layout = QHBoxLayout()
        
        paste_btn = QPushButton("Paste URL")
        paste_btn.clicked.connect(self.paste_url)
        quick_btn_layout.addWidget(paste_btn)
        
        get_title_btn = QPushButton("Get Title")
        get_title_btn.clicked.connect(self.get_video_title)
        quick_btn_layout.addWidget(get_title_btn)
        
        layout.addLayout(quick_btn_layout)
        
        # Save path settings
        path_group = QGroupBox("Save Path")
        path_layout = QVBoxLayout(path_group)
        
        # Save path selection
        path_input_layout = QHBoxLayout()
        self.save_path_input = QLineEdit()
        self.save_path_input.setPlaceholderText("Select save path...")
        path_input_layout.addWidget(self.save_path_input)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_save_path)
        path_input_layout.addWidget(browse_btn)
        
        path_layout.addLayout(path_input_layout)
        
        # Quick path selection
        quick_path_layout = QHBoxLayout()
        
        default_btn = QPushButton("Default")
        default_btn.clicked.connect(self.set_default_path)
        quick_path_layout.addWidget(default_btn)
        
        video_btn = QPushButton("Video")
        video_btn.clicked.connect(self.set_video_category_path)
        quick_path_layout.addWidget(video_btn)
        
        music_btn = QPushButton("Music")
        music_btn.clicked.connect(self.set_music_category_path)
        quick_path_layout.addWidget(music_btn)
        
        doc_btn = QPushButton("Document")
        doc_btn.clicked.connect(self.set_document_category_path)
        quick_path_layout.addWidget(doc_btn)
        
        path_layout.addLayout(quick_path_layout)
        layout.addWidget(path_group)
        
        # Download options
        options_group = QGroupBox("Download Options")
        options_layout = QVBoxLayout(options_group)
        
        # Series download option
        self.series_checkbox = QCheckBox("Download as series (multi-part videos)")
        options_layout.addWidget(self.series_checkbox)
        
        # Advanced options
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QVBoxLayout(advanced_group)
        
        # FFmpeg status display
        self.ffmpeg_status_label = QLabel("FFmpeg: Checking...")
        advanced_layout.addWidget(self.ffmpeg_status_label)
        
        options_layout.addWidget(advanced_group)
        layout.addWidget(options_group)
        
        # Download button
        self.download_btn = QPushButton("Start Download")
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a5bbf;
                color: white;
                font-weight: bold;
                padding: 12px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3a4baf;
            }
        """)
        self.download_btn.clicked.connect(self.start_download)
        layout.addWidget(self.download_btn)
        
        layout.addStretch()
        return panel
    
    def create_log_panel(self):
        """
        Create the download log panel.
        
        Returns:
            QWidget: Log display panel with text area and controls.
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Download Log")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(300)
        layout.addWidget(self.log_text)
        
        # Clear log button
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.clear_log)
        layout.addWidget(clear_log_btn)
        
        layout.addStretch()
        return panel
    
    def create_progress_panel(self):
        """
        Create the progress display panel.
        
        Returns:
            QWidget: Progress bar panel.
        """
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(15, 10, 15, 10)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        return panel
    
    def load_config(self):
        """
        Load configuration settings.
        
        Sets save path and updates FFmpeg status display.
        
        Returns:
            None
        """
        # Set save path
        try:
            default_path = self.config_manager.get_download_path()
            self.save_path_input.setText(default_path)
        except:
            pass
        
        # Update FFmpeg status display
        self.update_ffmpeg_status()
        
        # Load categories
        self.refresh_categories()
    
    def refresh_categories(self):
        """
        Refresh the category list.
        
        This method now updates the quick path selection button states.
        Category selection has been changed to path selection, so we no longer
        need to refresh a category dropdown.
        
        Returns:
            None
        """
        pass
    
    def browse_save_path(self):
        """
        Browse for save path.
        
        Opens a directory dialog for selecting the download save location.
        
        Returns:
            None
        """
        path = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if path:
            self.save_path_input.setText(path)
    
    def start_download(self):
        """
        Start the download process.
        
        Validates input, creates download worker, and starts the download.
        
        Returns:
            None
        """
        # Validate input
        if not self.validate_input():
            return
        
        # Get download parameters
        url = self.url_input.text().strip()
        title = self.title_input.text().strip()
        save_path = self.save_path_input.text().strip()
        is_series = self.series_checkbox.isChecked()
        
        # Save path is already set in save_path_input, no need for additional adjustment
        # User can directly select or input save path
        
        # Create download worker thread (FFmpeg path auto-fetched from config)
        self.download_worker = DownloadWorker(url, save_path, None, is_series)
        
        # Connect signals
        self.download_worker.progress_updated.connect(self.update_progress)
        self.download_worker.download_finished.connect(self.download_finished)
        self.download_worker.log_message.connect(self.add_log_message)
        
        # Start download
        self.download_worker.start()
        
        # Update UI state
        self.download_btn.setEnabled(False)
        self.download_btn.setText("Downloading...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
    
    def stop_download(self):
        """
        Stop the current download.
        
        Terminates the download worker thread if active.
        
        Returns:
            None
        """
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.terminate()
            self.download_worker.wait()
            self.download_btn.setEnabled(True)
            self.download_btn.setText("Start Download")
            self.progress_bar.setVisible(False)
    
    def validate_input(self):
        """
        Validate user input before starting download.
        
        Returns:
            bool: True if input is valid, False otherwise.
        """
        if not self.url_input.text().strip():
            QMessageBox.warning(self, "Input Error", "Please enter a video URL")
            return False
        
        if not self.save_path_input.text().strip():
            QMessageBox.warning(self, "Input Error", "Please select a save path")
            return False
        
        return True
    
    def update_progress(self, value, message):
        """
        Update download progress display.
        
        Args:
            value (int): Progress percentage in range [0, 100].
            message (str): Progress message for the log.
        
        Returns:
            None
        """
        self.progress_bar.setValue(value)
        self.add_log_message(message)
    
    def download_finished(self, success, message):
        """
        Handle download completion.
        
        Args:
            success (bool): Whether download was successful.
            message (str): Completion message.
        
        Returns:
            None
        """
        # Update UI state
        self.download_btn.setEnabled(True)
        self.download_btn.setText("Start Download")
        self.progress_bar.setVisible(False)
        
        # Show result
        if success:
            QMessageBox.information(self, "Download Complete", message)
        else:
            QMessageBox.warning(self, "Download Failed", message)
        
        # Add log message
        self.add_log_message(message)
        
        # Auto-scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def add_log_message(self, message):
        """
        Add a message to the log display.
        
        Args:
            message (str): Message to add to log.
        
        Returns:
            None
        """
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def clear_log(self):
        """
        Clear the log display.
        
        Removes all messages from the log text area.
        
        Returns:
            None
        """
        self.log_text.clear()
    
    def show_quick_download_dialog(self):
        """
        Show quick download dialog.
        
        This could implement a simplified download dialog for quick access.
        
        Returns:
            None
        """
        # Here you could implement a simplified quick download dialog
        pass
    
    def set_default_path(self):
        """
        Set the default download path.
        
        Sets the save path to the configured default download location.
        
        Returns:
            None
        """
        try:
            default_path = self.config_manager.get_download_path()
            self.save_path_input.setText(default_path)
        except:
            pass
    
    def set_video_category_path(self):
        """
        Set video category path.
        
        Sets the save path to the video category directory.
        
        Returns:
            None
        """
        try:
            video_path = self.config_manager.get_category_path("video")
            self.save_path_input.setText(video_path)
        except:
            pass
    
    def set_music_category_path(self):
        """
        Set music category path.
        
        Sets the save path to the music category directory.
        
        Returns:
            None
        """
        try:
            music_path = self.config_manager.get_category_path("music")
            self.save_path_input.setText(music_path)
        except:
            pass
    
    def set_document_category_path(self):
        """
        Set document category path.
        
        Sets the save path to the document category directory.
        
        Returns:
            None
        """
        try:
            doc_path = self.config_manager.get_category_path("document")
            self.save_path_input.setText(doc_path)
        except:
            pass
    
    def paste_url(self):
        """
        Paste URL from clipboard.
        
        Automatically fetches title after pasting.
        
        Returns:
            None
        """
        clipboard = QApplication.clipboard()
        url = clipboard.text().strip()
        if url:
            self.url_input.setText(url)
            self.auto_get_title()
    
    def on_url_changed(self):
        """
        Handle URL input changes.
        
        When user manually inputs or modifies URL, delays auto title fetching.
        Uses timer to delay execution, avoiding frequent requests during user input.
        
        Returns:
            None
        """
        # Use timer to delay execution, avoiding frequent requests during user input
        self.auto_fetch_timer.start(1000)  # 1 second delay
    
    def auto_get_title(self):
        """
        Automatically fetch video title from URL.
        
        Fetches the video title when URL is entered, with user confirmation
        if the title field has been manually edited.
        
        Returns:
            None
        """
        url = self.url_input.text().strip()
        if not url:
            return
        
        # Check if it's a valid Bilibili link
        if not re.search(r'bilibili\.com', url):
            return
        
        # If user has manually edited title, don't auto-overwrite
        if self.title_input.text().strip() and not self.title_input.text().startswith("Video title will be auto-fetched"):
            return
        
        # Auto-fetch title
        self.get_video_title()
    
    def get_video_title(self):
        """
        Fetch video title from Bilibili URL.
        
        Retrieves the video title and asks for confirmation if the title
        field has been manually edited by the user.
        
        Returns:
            None
        """
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a video URL first")
            return
        
        # If user has edited title, ask for confirmation
        if self.title_input.text().strip() and not self.title_input.text().startswith("Video title will be auto-fetched"):
            reply = QMessageBox.question(
                self, "Confirm Overwrite", 
                "The title field has been edited. Do you want to overwrite it with the fetched title?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        try:
            # Create temporary downloader to get title
            temp_downloader = BiliDownloader()
            video_info = temp_downloader.get_video_info(url)
            
            if video_info and video_info.get('title'):
                self.title_input.setText(video_info['title'])
                self.add_log_message(f"Title fetched: {video_info['title']}")
            else:
                QMessageBox.warning(self, "Title Fetch Failed", "Could not fetch video title")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to fetch title: {str(e)}")
    
    def clear_title(self):
        """
        Clear the title input field.
        
        Resets the title input to empty state.
        
        Returns:
            None
        """
        self.title_input.clear()
    
    def update_ffmpeg_status(self):
        """
        Update FFmpeg status display.
        
        Checks FFmpeg availability and updates the status label.
        
        Returns:
            None
        """
        try:
            ffmpeg_path = self.config_manager.get('DEFAULT', 'ffmpeg_path')
            if ffmpeg_path and os.path.exists(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
                self.ffmpeg_status_label.setText("FFmpeg: Available")
                self.ffmpeg_status_label.setStyleSheet("color: green;")
            else:
                self.ffmpeg_status_label.setText("FFmpeg: Not available")
                self.ffmpeg_status_label.setStyleSheet("color: red;")
        except:
            self.ffmpeg_status_label.setText("FFmpeg: Status unknown")
            self.ffmpeg_status_label.setStyleSheet("color: orange;") 