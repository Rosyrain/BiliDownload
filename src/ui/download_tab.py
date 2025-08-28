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
import random
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QProgressBar, QTextEdit, QSplitter, QFrame, QGroupBox, QCheckBox,
    QFileDialog, QMessageBox, QApplication, QScrollArea, QComboBox,
    QButtonGroup, QStackedWidget
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
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
    
    def __init__(self, url, save_path, ffmpeg_path=None, is_series=False, download_type="full"):
        """
        Initialize the download worker.
        
        Args:
            url (str): Video URL to download.
            save_path (str): Absolute directory path where files will be saved.
            ffmpeg_path (str | None): Optional path to FFmpeg executable.
            is_series (bool): Whether to download as a series (multi-part).
            download_type (str): Type of download ("full", "audio", "video").
        """
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.ffmpeg_path = ffmpeg_path
        self.is_series = is_series
        self.download_type = download_type
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
            self.log_message.emit("开始下载...")
            
            if self.is_series:
                success = self.downloader.download_series(
                    self.url, self.save_path, self.ffmpeg_path
                )
            else:
                success = self.downloader.download_video(
                    self.url, self.save_path, self.ffmpeg_path, self.download_type
                )
            
            if success:
                self.download_finished.emit(True, "下载完成！")
            else:
                self.download_finished.emit(False, "下载失败！")
                
        except Exception as e:
            self.logger.error(f"Download error: {e}")
            self.download_finished.emit(False, f"下载出错：{str(e)}")


class DownloadTab(QWidget):
    """
    下载标签页，提供视频下载功能
    
    Attributes:
        config_manager (ConfigManager): 配置管理器
        file_manager (FileManager): 文件管理器
        logger: 日志记录器
    """
    
    # 定义信号
    task_created = pyqtSignal(str, str, str, str, str)  # task_id, url, title, save_path, download_type
    show_task_list_requested = pyqtSignal()  # 请求显示任务列表
    
    def __init__(self, config_manager, file_manager=None, logger=None):
        """
        Initialize the download tab.
        
        Args:
            config_manager: Configuration manager instance providing paths and settings.
            file_manager (optional): File manager instance for file operations.
            logger (optional): Logger instance for logging.
        """
        super().__init__()
        self.config_manager = config_manager
        self.file_manager = file_manager
        self.logger = logger or get_logger(__name__)
        self.download_worker = None
        
        # Auto-fetch title timer
        self.auto_fetch_timer = QTimer()
        self.auto_fetch_timer.setSingleShot(True)
        self.auto_fetch_timer.timeout.connect(self.auto_get_title)
        
        # Series checkbox for compatibility with MainWindow
        self.series_checkbox = QCheckBox()
        self.series_checkbox.setVisible(False)
        
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
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Main horizontal layout: controls on left, log on right
        main_layout = QHBoxLayout()
        layout.addLayout(main_layout)
        
        # Left side: Controls in scroll area
        controls_scroll = QScrollArea()
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setFrameShape(QFrame.Shape.NoFrame)
        controls_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        controls_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        controls_panel = self.create_download_control_panel()
        controls_scroll.setWidget(controls_panel)
        controls_scroll.setMinimumHeight(300)
        
        # Right side: Log in scroll area
        log_panel = self.create_log_panel()
        log_panel.setMinimumHeight(120)
        
        # Add to main horizontal layout
        main_layout.addWidget(controls_scroll, 3)
        main_layout.addWidget(log_panel, 2)
        
        # Bottom: Progress bar
        progress_panel = self.create_progress_panel()
        layout.addWidget(progress_panel, 0)
    
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
        title_label = QLabel("下载管理")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Download type tabs
        tab_container = QWidget()
        tab_layout = QHBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(8)
        
        # Create tab style
        tab_style = """
            QPushButton {
                background-color: #e8f0ff;
                color: #5a6acf;
                border: 1px solid #d1d8ff;
                border-radius: 15px;
                padding: 6px 12px;
                font-size: 13px;
                min-width: 100px;
                min-height: 30px;
                max-height: 30px;
            }
            QPushButton:hover {
                background-color: #d8e8ff;
            }
            QPushButton:checked {
                background-color: #4a5bbf;
                color: white;
                border: 1px solid #4a5bbf;
            }
        """
        
        # Create button group for tabs
        self.tab_group = QButtonGroup(self)
        self.tab_group.setExclusive(True)
        
        # Single video tab
        self.single_video_tab = QPushButton("单个视频")
        self.single_video_tab.setCheckable(True)
        self.single_video_tab.setChecked(True)
        self.single_video_tab.setStyleSheet(tab_style)
        self.tab_group.addButton(self.single_video_tab, 1)
        tab_layout.addWidget(self.single_video_tab)
        
        # Series video tab
        self.series_video_tab = QPushButton("系列视频")
        self.series_video_tab.setCheckable(True)
        self.series_video_tab.setStyleSheet(tab_style)
        self.tab_group.addButton(self.series_video_tab, 2)
        tab_layout.addWidget(self.series_video_tab)
        
        # Connect tab change signal
        self.tab_group.buttonClicked.connect(self.on_tab_changed)
        
        # Add stretch to fill remaining space
        tab_layout.addStretch()
        
        # Add tab container to layout
        layout.addWidget(tab_container)
        
        # Create stacked widget for different download types
        self.download_stack = QStackedWidget()
        
        # Single video download page
        single_video_page = self.create_single_video_page()
        self.download_stack.addWidget(single_video_page)
        
        # Series video download page
        series_video_page = self.create_series_video_page()
        self.download_stack.addWidget(series_video_page)
        
        # Add stacked widget to layout
        layout.addWidget(self.download_stack)
        
        # Download button - make it larger and more prominent
        download_btn_container = QWidget()
        download_btn_layout = QHBoxLayout(download_btn_container)
        download_btn_layout.setContentsMargins(0, 10, 0, 10)
        
        self.download_btn = QPushButton("开始下载")
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a5bbf;
                color: white;
                font-weight: bold;
                padding: 12px 24px;
                font-size: 16px;
                min-height: 48px;
                min-width: 180px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #3a4baf;
            }
            QPushButton:disabled {
                background-color: #a0a0a0;
            }
        """)
        self.download_btn.clicked.connect(self.start_download)
        
        # Center the button with stretch on both sides
        download_btn_layout.addStretch(1)
        download_btn_layout.addWidget(self.download_btn)
        download_btn_layout.addStretch(1)
        
        layout.addWidget(download_btn_container)
        
        return panel
    
    def create_single_video_page(self):
        """创建单个视频下载页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 视频链接
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("视频链接:"))
        self.single_url_input = QLineEdit()
        self.single_url_input.setPlaceholderText("输入Bilibili视频链接...")
        self.single_url_input.textChanged.connect(self.on_url_changed)
        url_layout.addWidget(self.single_url_input)
        
        paste_btn = QPushButton("粘贴")
        paste_btn.clicked.connect(self.paste_url)
        url_layout.addWidget(paste_btn)
        
        layout.addLayout(url_layout)
        
        # 视频标题
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("视频标题:"))
        self.single_title_input = QLineEdit()
        self.single_title_input.setPlaceholderText("视频标题将自动获取...")
        title_layout.addWidget(self.single_title_input)
        
        get_title_btn = QPushButton("重新获取")
        get_title_btn.clicked.connect(self.auto_get_title)
        title_layout.addWidget(get_title_btn)
        
        layout.addLayout(title_layout)
        
        # 保存路径
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("保存路径:"))
        self.single_save_path = QLineEdit()
        self.single_save_path.setReadOnly(True)  # 路径由左侧分类树选择
        self.single_save_path.setToolTip("保存路径由左侧分类树选择")
        path_layout.addWidget(self.single_save_path)
        
        layout.addLayout(path_layout)
        
        # 下载类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("下载类型:"))
        self.single_download_type_combo = QComboBox()
        self.single_download_type_combo.setMinimumWidth(120)  # 增加宽度确保内容完全显示
        self.single_download_type_combo.setMinimumHeight(30)  # 设置最小高度
        self.single_download_type_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
                min-width: 120px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border-left: none;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #e6f2ff;
                selection-color: #409eff;
                padding: 4px;
            }
        """)
        self.single_download_type_combo.addItem("完整视频 (视频+音频)", "full")
        self.single_download_type_combo.addItem("仅音频", "audio")
        self.single_download_type_combo.addItem("无声视频", "video")
        type_layout.addWidget(self.single_download_type_combo)
        
        # FFmpeg状态
        self.ffmpeg_status_label = QLabel("FFmpeg: 检查中...")
        self.ffmpeg_status_label.setMinimumWidth(120)  # 确保状态标签有足够宽度
        type_layout.addWidget(self.ffmpeg_status_label)
        type_layout.addStretch()
        
        layout.addLayout(type_layout)
        
        # 添加一个弹性空间，使内容向上对齐
        layout.addStretch()
        
        return page
    
    def create_series_video_page(self):
        """创建系列视频下载页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 系列链接
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("系列链接:"))
        self.series_url_input = QLineEdit()
        self.series_url_input.setPlaceholderText("输入Bilibili系列视频链接...")
        self.series_url_input.textChanged.connect(lambda: self.auto_fetch_timer.start(1000))
        url_layout.addWidget(self.series_url_input)
        
        paste_series_btn = QPushButton("粘贴")
        paste_series_btn.clicked.connect(lambda: self.paste_url_to(self.series_url_input))
        url_layout.addWidget(paste_series_btn)
        
        layout.addLayout(url_layout)
        
        # 系列标题
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("系列标题:"))
        self.series_title_input = QLineEdit()
        self.series_title_input.setPlaceholderText("系列标题将自动获取...")
        title_layout.addWidget(self.series_title_input)
        
        get_series_title_btn = QPushButton("重新获取")
        get_series_title_btn.clicked.connect(lambda: self.get_series_title(self.series_url_input.text()))
        title_layout.addWidget(get_series_title_btn)
        
        layout.addLayout(title_layout)
        
        # 保存路径
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("保存路径:"))
        self.series_save_path = QLineEdit()
        self.series_save_path.setReadOnly(True)  # 路径由左侧分类树选择
        self.series_save_path.setToolTip("保存路径由左侧分类树选择")
        path_layout.addWidget(self.series_save_path)
        
        layout.addLayout(path_layout)
        
        # 下载类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("下载类型:"))
        self.series_download_type_combo = QComboBox()
        self.series_download_type_combo.setMinimumWidth(120)  # 增加宽度确保内容完全显示
        self.series_download_type_combo.setMinimumHeight(30)  # 设置最小高度
        self.series_download_type_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
                min-width: 120px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border-left: none;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #e6f2ff;
                selection-color: #409eff;
                padding: 4px;
            }
        """)
        self.series_download_type_combo.addItem("完整视频 (视频+音频)", "full")
        self.series_download_type_combo.addItem("仅音频", "audio")
        self.series_download_type_combo.addItem("无声视频", "video")
        type_layout.addWidget(self.series_download_type_combo)
        
        # FFmpeg状态
        self.series_ffmpeg_status_label = QLabel("FFmpeg: 检查中...")
        self.series_ffmpeg_status_label.setMinimumWidth(120)  # 确保状态标签有足够宽度
        type_layout.addWidget(self.series_ffmpeg_status_label)
        type_layout.addStretch()
        
        layout.addLayout(type_layout)
        
        # 添加一个弹性空间，使内容向上对齐
        layout.addStretch()
        
        return page
    
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
        title_label = QLabel("下载日志")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Log text area - increase height and make it more prominent
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(120)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #e1e8ff;
                border-radius: 6px;
                padding: 8px;
                font-family: monospace;
                min-height: 120px;
            }
        """)
        layout.addWidget(self.log_text, 1)  # Give it stretch factor
        
        # Clear log button
        clear_log_btn = QPushButton("清空日志")
        clear_log_btn.clicked.connect(self.clear_log)
        layout.addWidget(clear_log_btn)
        
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
            self.single_save_path.setText(default_path)
            self.series_save_path.setText(default_path)
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
        path = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if path:
            self.single_save_path.setText(path)
    
    def start_download(self):
        """
        开始下载
        
        根据当前选择的下载页面（单个视频/系列视频）获取参数，
        验证输入，然后创建下载任务
        
        Returns:
            bool: 是否成功开始下载
        """
        # 获取当前活动的下载页面
        current_index = self.download_stack.currentIndex()
        
        # 根据当前页面获取参数
        if current_index == 0:  # 单个视频
            # 验证输入
            if not self.validate_single_video_input():
                return False
            
            url = self.single_url_input.text().strip()
            title = self.single_title_input.text().strip()
            save_path = self.single_save_path.text().strip()
            download_type = self.get_download_type(self.single_download_type_combo)
            
        else:  # 系列视频
            # 验证输入
            if not self.validate_series_video_input():
                return False
            
            url = self.series_url_input.text().strip()
            title = self.series_title_input.text().strip()
            save_path = self.series_save_path.text().strip()
            download_type = self.get_download_type(self.series_download_type_combo)
        
        # 检查FFmpeg可用性（如果需要）
        if download_type == "full" and not self.check_ffmpeg():
            reply = QMessageBox.question(
                self,
                "FFmpeg未找到",
                "下载完整视频需要FFmpeg，但未找到有效的FFmpeg路径。\n\n是否继续下载？(将保存为分离的音视频文件)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return False
        
        # 生成任务ID
        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(0, 100)}"
        
        # 发送任务创建信号
        self.task_created.emit(task_id, url, title, save_path, download_type)
        
        # 添加日志
        self.add_log_message(f"创建下载任务: {title}", task_id=task_id, task_title=title)
        self.add_log_message(f"下载类型: {download_type}", task_id=task_id, task_title=title)
        self.add_log_message(f"保存路径: {save_path}", task_id=task_id, task_title=title)
        
        # 显示任务列表
        self.show_task_list_requested.emit()
        
        # 清空输入
        if current_index == 0:  # 单个视频
            self.single_url_input.clear()
            self.single_title_input.clear()
        else:  # 系列视频
            self.series_url_input.clear()
            self.series_title_input.clear()
        
        return True
    
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
            self.download_btn.setText("开始下载")
            self.progress_bar.setVisible(False)
    
    def validate_single_video_input(self):
        """
        Validate single video input fields.
        
        Returns:
            bool: True if input is valid, False otherwise
        """
        # Check URL
        url = self.single_url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "输入错误", "请输入视频链接")
            return False
        
        # Check title
        title = self.single_title_input.text().strip()
        if not title:
            # Try to get title automatically
            self.get_video_title()
            title = self.single_title_input.text().strip()
            if not title:
                QMessageBox.warning(self, "输入错误", "请输入视频标题")
                return False
        
        # Check save path
        save_path = self.single_save_path.text().strip()
        if not save_path:
            QMessageBox.warning(self, "输入错误", "请先在左侧选择保存分类")
            return False
        
        return True
    
    def validate_series_video_input(self):
        """
        Validate series video input fields.
        
        Returns:
            bool: True if input is valid, False otherwise
        """
        # Check URL
        url = self.series_url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "输入错误", "请输入合集链接")
            return False
        
        # Check title
        title = self.series_title_input.text().strip()
        if not title:
            # Try to get title automatically
            self.get_series_title()
            title = self.series_title_input.text().strip()
            if not title:
                QMessageBox.warning(self, "输入错误", "请输入合集标题")
                return False
        
        # Check save path
        save_path = self.series_save_path.text().strip()
        if not save_path:
            QMessageBox.warning(self, "输入错误", "请先在左侧选择保存分类")
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
        self.download_btn.setText("开始下载")
        self.progress_bar.setVisible(False)
        
        # Show result
        if success:
            QMessageBox.information(self, "下载完成", message)
        else:
            QMessageBox.warning(self, "下载失败", message)
        
        # Add log message
        self.add_log_message(message)
        
        # Auto-scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def add_log_message(self, message, event_type=None, task_id=None, task_title=None, **kwargs):
        """
        添加日志消息到日志显示区域，并记录到日志文件。
        
        Args:
            message (str): 要添加的消息
            event_type (str, optional): 事件类型，如'title', 'video', 'audio', 'ffmpeg'
            task_id (str, optional): 任务ID，用于在多任务下载时标识不同任务
            task_title (str, optional): 任务标题，用于在多任务下载时标识不同任务
            **kwargs: 附加信息，如URL、路径等
        
        Returns:
            None
        """
        from datetime import datetime
        
        # 添加任务标识前缀
        task_identifier = ""
        if task_title:
            # 如果标题太长，截断显示
            if len(task_title) > 20:
                task_identifier = f"[{task_title[:18]}..] "
            else:
                task_identifier = f"[{task_title}] "
        elif task_id:
            task_identifier = f"[{task_id}] "
        
        # 如果提供了事件类型，使用专用的日志记录函数
        if event_type:
            from src.core.logger import log_download_detail
            formatted_msg = log_download_detail(event_type, message, **kwargs)
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.append(f"[{timestamp}] {task_identifier}{formatted_msg}")
        else:
            # 普通消息直接添加到日志区域
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.append(f"[{timestamp}] {task_identifier}{message}")
        
        # 自动滚动到底部
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
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
            self.single_save_path.setText(default_path)
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
            self.single_save_path.setText(video_path)
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
            self.single_save_path.setText(music_path)
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
            self.single_save_path.setText(doc_path)
        except:
            pass
    
    def paste_url(self):
        """
        Paste URL from clipboard.
        
        Automatically fetches title after pasting.
        
        Returns:
            None
        """
        # 使用通用方法粘贴到当前活动的URL输入框
        current_tab_index = self.download_stack.currentIndex()
        if current_tab_index == 0:
            self.paste_url_to(self.single_url_input)
        else:
            self.paste_url_to(self.series_url_input)
    
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
        url = self.single_url_input.text().strip()
        if not url:
            return
        
        # Check if it's a valid Bilibili link
        if not re.search(r'bilibili\.com', url):
            return
        
        # If user has manually edited title, don't auto-overwrite
        if self.single_title_input.text().strip() and not self.single_title_input.text().startswith("视频标题将自动获取"):
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
        url = self.single_url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "输入错误", "请先输入视频链接")
            return
        
        # If user has edited title, ask for confirmation
        if self.single_title_input.text().strip() and not self.single_title_input.text().startswith("视频标题将自动获取"):
            reply = QMessageBox.question(
                self, "确认覆盖", 
                "标题已被手动编辑，是否用获取到的标题覆盖？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        try:
            # Create temporary downloader to get title
            temp_downloader = BiliDownloader()
            video_info = temp_downloader.get_video_info(url)
            
            if video_info and video_info.get('title'):
                self.single_title_input.setText(video_info['title'])
                self.add_log_message(f"已获取标题：{video_info['title']}")
            else:
                QMessageBox.warning(self, "获取失败", "无法获取视频标题")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"获取标题失败：{str(e)}")
    
    def clear_title(self):
        """
        Clear the title input field.
        
        Resets the title input to empty state.
        
        Returns:
            None
        """
        self.single_title_input.clear()
    
    def update_ffmpeg_status(self):
        """
        Update FFmpeg status display.
        
        Checks FFmpeg availability and updates the status label.
        
        Returns:
            None
        """
        try:
            ffmpeg_path = self.config_manager.get_ffmpeg_path()
            if ffmpeg_path and os.path.exists(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
                self.ffmpeg_status_label.setText("FFmpeg: 可用")
                self.ffmpeg_status_label.setStyleSheet("color: green;")
                
                # 更新系列视频标签页的FFmpeg状态
                if hasattr(self, 'series_ffmpeg_status_label'):
                    self.series_ffmpeg_status_label.setText("FFmpeg: 可用")
                    self.series_ffmpeg_status_label.setStyleSheet("color: green;")
            else:
                self.ffmpeg_status_label.setText("FFmpeg: 不可用")
                self.ffmpeg_status_label.setStyleSheet("color: red;")
                
                # 更新系列视频标签页的FFmpeg状态
                if hasattr(self, 'series_ffmpeg_status_label'):
                    self.series_ffmpeg_status_label.setText("FFmpeg: 不可用")
                    self.series_ffmpeg_status_label.setStyleSheet("color: red;")
                
                # 如果当前选择的是完整视频但FFmpeg不可用，显示警告
                if self.single_download_type_combo.currentData() == "full":
                    self.add_log_message("警告: FFmpeg不可用，无法合成完整视频。请在设置中配置FFmpeg路径。")
                
                # 系列视频页面也检查
                if hasattr(self, 'series_download_type_combo') and self.series_download_type_combo.currentData() == "full":
                    self.add_log_message("警告: FFmpeg不可用，无法合成完整视频。请在设置中配置FFmpeg路径。")
        except Exception as e:
            self.ffmpeg_status_label.setText("FFmpeg: 状态未知")
            self.ffmpeg_status_label.setStyleSheet("color: orange;") 
            
            # 更新系列视频标签页的FFmpeg状态
            if hasattr(self, 'series_ffmpeg_status_label'):
                self.series_ffmpeg_status_label.setText("FFmpeg: 状态未知")
                self.series_ffmpeg_status_label.setStyleSheet("color: orange;")
                
            self.logger.error(f"检查FFmpeg状态时出错: {e}")

    def on_tab_changed(self, button):
        """
        Handle tab change events.
        
        Args:
            button: The button that was clicked
            
        Returns:
            None
        """
        if button == self.single_video_tab:
            self.download_stack.setCurrentIndex(0)
            # Update series checkbox state
            self.series_checkbox.setChecked(False)
        elif button == self.series_video_tab:
            self.download_stack.setCurrentIndex(1)
            # Update series checkbox state
            self.series_checkbox.setChecked(True)
    
    def paste_url_to(self, target_input):
        """
        Paste URL from clipboard to a specific input field.
        
        Args:
            target_input: The input field to paste to
            
        Returns:
            None
        """
        clipboard = QApplication.clipboard()
        url = clipboard.text().strip()
        if url:
            target_input.setText(url)
            
            # If pasting to main URL input, also try to get title
            if target_input == self.single_url_input:
                self.auto_get_title()
    
    def get_series_title(self, url):
        """
        Fetch series title from Bilibili URL.
        
        Returns:
            None
        """
        if not url:
            QMessageBox.warning(self, "输入错误", "请先输入合集链接")
            return
        
        # If user has edited title, ask for confirmation
        if self.series_title_input.text().strip() and not self.series_title_input.text().startswith("系列标题将自动获取"):
            reply = QMessageBox.question(
                self, "确认覆盖", 
                "标题已被手动编辑，是否用获取到的标题覆盖？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        try:
            # Create temporary downloader to get title
            temp_downloader = BiliDownloader()
            video_info = temp_downloader.get_video_info(url)
            
            if video_info and video_info.get('title'):
                self.series_title_input.setText(video_info['title'])
                self.add_log_message(f"已获取合集标题：{video_info['title']}")
            else:
                QMessageBox.warning(self, "获取失败", "无法获取合集标题")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"获取标题失败：{str(e)}") 

    def on_category_changed(self, path):
        """
        Handle category change event.
        
        Updates the save path input field when a category is selected.
        
        Args:
            path (str): New save path
            
        Returns:
            None
        """
        if path:
            self.single_save_path.setText(path)
            
            # 同时更新系列视频页面的保存路径
            if hasattr(self, 'series_save_path'):
                self.series_save_path.setText(path) 

    def check_ffmpeg(self):
        """
        检查FFmpeg是否可用
        
        Returns:
            bool: FFmpeg是否可用
        """
        if not self.config_manager:
            return False
            
        ffmpeg_path = self.config_manager.get_ffmpeg_path()
        if not ffmpeg_path or not os.path.exists(ffmpeg_path) or not os.access(ffmpeg_path, os.X_OK):
            return False
            
        return True
    
    def get_download_type(self, combo_box):
        """
        获取下载类型
        
        Args:
            combo_box (QComboBox): 下载类型选择框
            
        Returns:
            str: 下载类型 (full/audio/video)
        """
        return combo_box.currentData() 