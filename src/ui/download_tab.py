"""
Download management tab for BiliDownload application.

This module provides the download interface including:
- Video URL input and title fetching
- Download path selection
- Download progress monitoring
- Log display and management
"""

import os
import random
import re
from datetime import datetime

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CardWidget,
    ComboBox,
    FluentIcon,
    LineEdit,
    PushButton,
    SubtitleLabel,
    TextEdit,
    PrimaryPushButton,
)

from src.core.managers.downloader import BiliDownloader
from src.core.managers.logger import get_logger


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

    def __init__(
        self, url, save_path, ffmpeg_path=None, is_series=False, download_type="full"
    ):
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
                self.download_finished.emit(True, "下载完成")
            else:
                self.download_finished.emit(False, "下载失败")

        except Exception as e:
            self.logger.error(f"下载过程中发生错误: {e}")
            self.download_finished.emit(False, f"错误: {str(e)}")


class SimulateDownloadWorker(QThread):
    """
    Simulates a download for testing the UI.

    Emits progress signals at regular intervals to test the UI without actual downloads.
    """

    progress_updated = pyqtSignal(int, str)
    download_finished = pyqtSignal(bool, str)
    log_message = pyqtSignal(str)

    def __init__(self, duration=10):
        """
        Initialize the simulation worker.

        Args:
            duration (int): Simulated download duration in seconds.
        """
        super().__init__()
        self.duration = duration
        self.is_cancelled = False

    def run(self):
        """
        Run the download simulation.

        Emits progress updates at regular intervals and finishes after the
        specified duration.

        Returns:
            None
        """
        self.log_message.emit("开始模拟下载...")
        steps = 20
        interval = self.duration / steps

        for i in range(steps + 1):
            if self.is_cancelled:
                self.download_finished.emit(False, "下载已取消")
                return

            progress = int(i * 100 / steps)
            self.progress_updated.emit(progress, f"下载中... {progress}%")
            self.log_message.emit(f"下载进度: {progress}%")
            self.sleep(int(interval * 1000))

        self.download_finished.emit(True, "模拟下载完成")
        self.log_message.emit("模拟下载完成")

    def cancel(self):
        """
        Cancel the simulation.

        Sets the cancelled flag to stop the simulation.

        Returns:
            None
        """
        self.is_cancelled = True


class DownloadTab(QWidget):
    """
    Download tab for the main application window.

    Provides interface for entering video URLs, selecting download options,
    and monitoring download progress.

    Attributes:
        download_requested (pyqtSignal): Emitted when a download is requested.
    """

    # 定义下载请求信号
    download_requested = pyqtSignal(str, str, str, str)

    def __init__(self, config_manager, task_manager, parent=None):
        """
        Initialize the download tab.

        Args:
            config_manager: Configuration manager instance.
            task_manager: Task manager instance.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.task_manager = task_manager
        self.logger = get_logger(__name__)
        self.download_worker = None
        self.current_download_path = ""
        self.series_url_list = []
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 标题
        title_label = SubtitleLabel("视频下载", self)
        title_label.setObjectName("DownloadTitle")
        main_layout.addWidget(title_label)

        # 创建标签按钮
        self._create_tab_buttons(main_layout)

        # 创建堆叠部件
        self.stacked_widget = QStackedWidget(self)
        main_layout.addWidget(self.stacked_widget)

        # 创建单视频下载页面
        self.single_video_page = self._create_single_video_page()
        self.stacked_widget.addWidget(self.single_video_page)

        # 创建系列视频下载页面
        self.series_video_page = self._create_series_video_page()
        self.stacked_widget.addWidget(self.series_video_page)

        # 创建日志区域
        self._create_log_area(main_layout)

        # 默认选中单视频标签
        self.single_video_tab.setChecked(True)
        self.stacked_widget.setCurrentIndex(0)

    def _create_tab_buttons(self, layout):
        """
        创建标签按钮，用于切换单视频和系列视频下载
        
        Args:
            layout: 父布局
        """
        # 标签按钮布局
        tab_layout = QHBoxLayout()
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(10)
        
        # 创建按钮组
        self.tab_button_group = QButtonGroup(self)
        self.tab_button_group.setExclusive(True)
        
        # 单视频标签
        self.single_video_tab = PushButton("单视频下载", self)
        self.single_video_tab.setCheckable(True)
        self.single_video_tab.setObjectName("SingleVideoTab")
        self.single_video_tab.setStyleSheet("""
            QPushButton:checked {
                background-color: #4a5bbf;
                color: white;
                border: none;
            }
        """)
        self.tab_button_group.addButton(self.single_video_tab)
        tab_layout.addWidget(self.single_video_tab)
        
        # 系列视频标签
        self.series_video_tab = PushButton("系列视频下载", self)
        self.series_video_tab.setCheckable(True)
        self.series_video_tab.setObjectName("SeriesVideoTab")
        self.series_video_tab.setStyleSheet("""
            QPushButton:checked {
                background-color: #4a5bbf;
                color: white;
                border: none;
            }
        """)
        self.tab_button_group.addButton(self.series_video_tab)
        tab_layout.addWidget(self.series_video_tab)
        
        # 添加弹性空间
        tab_layout.addStretch(1)
        
        # 连接信号
        self.single_video_tab.clicked.connect(
            lambda: self.on_tab_changed(self.single_video_tab)
        )
        self.series_video_tab.clicked.connect(
            lambda: self.on_tab_changed(self.series_video_tab)
        )
        
        layout.addLayout(tab_layout)

    def _create_single_video_page(self):
        """
        创建单视频下载页面
        
        Returns:
            QWidget: 单视频下载页面
        """
        # 创建单视频页面
        single_page = QWidget()
        single_layout = QVBoxLayout(single_page)
        single_layout.setContentsMargins(0, 10, 0, 0)
        single_layout.setSpacing(15)

        # 创建卡片
        single_card = CardWidget(single_page)
        card_layout = QVBoxLayout(single_card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        # URL输入
        url_layout = QHBoxLayout()
        url_layout.setContentsMargins(0, 0, 0, 0)
        url_layout.setSpacing(10)

        url_label = QLabel("视频链接:", single_card)
        url_layout.addWidget(url_label, 0)

        self.single_url_input = LineEdit(single_card)
        self.single_url_input.setPlaceholderText("请输入哔哩哔哩视频链接")
        url_layout.addWidget(self.single_url_input, 1)

        paste_button = PushButton(FluentIcon.PASTE, "", single_card)
        paste_button.setToolTip("粘贴")
        paste_button.clicked.connect(lambda: self.paste_url_to(self.single_url_input))
        url_layout.addWidget(paste_button, 0)

        card_layout.addLayout(url_layout)

        # 标题输入
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(10)

        title_label = QLabel("视频标题:", single_card)
        title_layout.addWidget(title_label, 0)

        self.single_title_input = LineEdit(single_card)
        self.single_title_input.setPlaceholderText("请输入视频标题或点击获取按钮自动获取")
        title_layout.addWidget(self.single_title_input, 1)

        get_title_button = PushButton("获取标题", single_card)
        get_title_button.clicked.connect(lambda: self.auto_get_title(self.single_url_input.text()))
        title_layout.addWidget(get_title_button, 0)

        card_layout.addLayout(title_layout)

        # 保存路径
        path_layout = QHBoxLayout()
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(10)

        path_label = QLabel("保存路径:", single_card)
        path_layout.addWidget(path_label, 0)

        self.single_path_input = LineEdit(single_card)
        self.single_path_input.setReadOnly(True)
        path_layout.addWidget(self.single_path_input, 1)

        browse_button = PushButton("浏览", single_card)
        browse_button.clicked.connect(lambda: self.browse_download_path(self.single_path_input))
        path_layout.addWidget(browse_button, 0)

        card_layout.addLayout(path_layout)

        # 下载类型
        type_layout = QHBoxLayout()
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_layout.setSpacing(10)

        type_label = QLabel("下载类型:", single_card)
        type_layout.addWidget(type_label, 0)

        self.single_type_combo = ComboBox(single_card)
        self.single_type_combo.addItem("完整视频 (视频+音频)", "full")
        self.single_type_combo.addItem("仅视频 (无音频)", "video")
        self.single_type_combo.addItem("仅音频 (MP3)", "audio")
        type_layout.addWidget(self.single_type_combo, 1)

        card_layout.addLayout(type_layout)

        # 下载按钮
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(10)

        button_layout.addStretch(1)

        self.single_download_button = PrimaryPushButton("开始下载", single_card)
        self.single_download_button.clicked.connect(self.start_single_download)
        button_layout.addWidget(self.single_download_button)

        card_layout.addLayout(button_layout)

        # 添加卡片到页面
        single_layout.addWidget(single_card)
        single_layout.addStretch(1)

        return single_page

    def _create_series_video_page(self):
        """
        创建系列视频下载页面
        
        Returns:
            QWidget: 系列视频下载页面
        """
        # 创建系列视频页面
        series_page = QWidget()
        series_layout = QVBoxLayout(series_page)
        series_layout.setContentsMargins(0, 10, 0, 0)
        series_layout.setSpacing(15)

        # 创建卡片
        series_card = CardWidget(series_page)
        card_layout = QVBoxLayout(series_card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        # URL输入
        url_layout = QHBoxLayout()
        url_layout.setContentsMargins(0, 0, 0, 0)
        url_layout.setSpacing(10)

        url_label = QLabel("系列链接:", series_card)
        url_layout.addWidget(url_label, 0)

        self.series_url_input = LineEdit(series_card)
        self.series_url_input.setPlaceholderText("请输入哔哩哔哩系列/播放列表链接")
        url_layout.addWidget(self.series_url_input, 1)

        paste_button = PushButton(FluentIcon.PASTE, "", series_card)
        paste_button.setToolTip("粘贴")
        paste_button.clicked.connect(lambda: self.paste_url_to(self.series_url_input))
        url_layout.addWidget(paste_button, 0)

        card_layout.addLayout(url_layout)

        # 系列标题
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(10)

        title_label = QLabel("系列标题:", series_card)
        title_layout.addWidget(title_label, 0)

        self.series_title_input = LineEdit(series_card)
        self.series_title_input.setPlaceholderText("请输入系列标题或点击获取按钮自动获取")
        title_layout.addWidget(self.series_title_input, 1)

        get_title_button = PushButton("获取标题", series_card)
        get_title_button.clicked.connect(lambda: self.auto_get_title(self.series_url_input.text()))
        title_layout.addWidget(get_title_button, 0)

        card_layout.addLayout(title_layout)

        # 保存路径
        path_layout = QHBoxLayout()
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(10)

        path_label = QLabel("保存路径:", series_card)
        path_layout.addWidget(path_label, 0)

        self.series_path_input = LineEdit(series_card)
        self.series_path_input.setReadOnly(True)
        path_layout.addWidget(self.series_path_input, 1)

        browse_button = PushButton("浏览", series_card)
        browse_button.clicked.connect(lambda: self.browse_download_path(self.series_path_input))
        path_layout.addWidget(browse_button, 0)

        card_layout.addLayout(path_layout)

        # 下载类型
        type_layout = QHBoxLayout()
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_layout.setSpacing(10)

        type_label = QLabel("下载类型:", series_card)
        type_layout.addWidget(type_label, 0)

        self.series_type_combo = ComboBox(series_card)
        self.series_type_combo.addItem("完整视频 (视频+音频)", "full")
        self.series_type_combo.addItem("仅视频 (无音频)", "video")
        self.series_type_combo.addItem("仅音频 (MP3)", "audio")
        type_layout.addWidget(self.series_type_combo, 1)

        card_layout.addLayout(type_layout)

        # 下载按钮
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(10)

        button_layout.addStretch(1)

        self.series_download_button = PrimaryPushButton("开始下载系列", series_card)
        self.series_download_button.clicked.connect(self.start_series_download)
        button_layout.addWidget(self.series_download_button)

        card_layout.addLayout(button_layout)

        # 添加卡片到页面
        series_layout.addWidget(series_card)
        series_layout.addStretch(1)

        return series_page

    def _create_log_area(self, layout):
        """
        Create the log area for displaying download progress and messages.

        Args:
            layout: Parent layout to add the log area to.
        """
        # 日志区域标题
        log_title_layout = QHBoxLayout()
        log_title_layout.setContentsMargins(0, 0, 0, 0)
        log_title_layout.setSpacing(10)

        log_title = SubtitleLabel("下载日志", self)
        log_title_layout.addWidget(log_title)

        log_title_layout.addStretch(1)

        clear_log_button = PushButton("清空日志", self)
        clear_log_button.setIcon(FluentIcon.DELETE)
        clear_log_button.clicked.connect(self.clear_log)
        log_title_layout.addWidget(clear_log_button)

        layout.addLayout(log_title_layout)

        # 日志文本区域
        self.log_text = TextEdit(self)
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(150)
        self.log_text.setPlaceholderText("下载日志将显示在这里...")
        layout.addWidget(self.log_text)

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
        self.series_url_input.textChanged.connect(
            lambda: self.auto_fetch_timer.start(1000)
        )
        url_layout.addWidget(self.series_url_input)

        paste_series_btn = QPushButton("粘贴")
        paste_series_btn.clicked.connect(
            lambda: self.paste_url_to(self.series_url_input)
        )
        url_layout.addWidget(paste_series_btn)

        layout.addLayout(url_layout)

        # 系列标题
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("系列标题:"))
        self.series_title_input = QLineEdit()
        self.series_title_input.setPlaceholderText("系列标题将自动获取...")
        title_layout.addWidget(self.series_title_input)

        get_series_title_btn = QPushButton("重新获取")
        get_series_title_btn.clicked.connect(
            lambda: self.get_series_title(self.series_url_input.text())
        )
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
        except ValueError:
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
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.No:
                return False

        # 生成任务ID
        task_id = (
            f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(0, 100)}"
        )

        # 发送任务创建信号
        self.task_created.emit(task_id, url, title, save_path, download_type)

        # 添加日志
        self.add_log_message(
            f"创建下载任务: {title}", task_id=task_id, task_title=title
        )
        self.add_log_message(
            f"下载类型: {download_type}", task_id=task_id, task_title=title
        )
        self.add_log_message(
            f"保存路径: {save_path}", task_id=task_id, task_title=title
        )

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

    def add_log_message(
        self, message, event_type=None, task_id=None, task_title=None, **kwargs
    ):
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
            from src.core.managers.logger import log_download_detail

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

    def log_message(self, message):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logger.info(message)
        
        # 将消息添加到日志文本框
        if hasattr(self, "log_text"):
            log_entry = f"[{timestamp}] {message}"
            self.log_text.append(log_entry)
            
            # 滚动到底部
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
    def clear_log(self):
        """清空日志"""
        if hasattr(self, "log_text"):
            self.log_text.clear()
            self.log_message("日志已清空")

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
        except ValueError:
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
        except ValueError:
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
        except ValueError:
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
        except ValueError:
            pass

    def paste_url(self):
        """粘贴URL"""
        clipboard = QApplication.clipboard()
        url = clipboard.text()
        if url:
            self.single_url_input.setText(url)
            self.log_message("URL已粘贴")

    def browse_download_path(self, input_field):
        """浏览下载路径"""
        from PyQt6.QtWidgets import QFileDialog
        
        # 获取当前路径
        current_path = input_field.text()
        if not current_path:
            current_path = self.config_manager.get_download_path()
        
        # 打开文件夹选择对话框
        path = QFileDialog.getExistingDirectory(
            self,
            "选择下载路径",
            current_path
        )
        
        # 如果选择了路径，则更新输入框
        if path:
            input_field.setText(path)
            self.log_message(f"下载路径已设置: {path}")

    def paste_url_to(self, target_input):
        """粘贴URL到指定输入框"""
        clipboard = QApplication.clipboard()
        url = clipboard.text()
        if url:
            target_input.setText(url)
            self.log_message("URL已粘贴")

    def auto_get_title(self, url):
        """自动获取标题（简化版，仅记录日志）"""
        if url:
            self.log_message(f"尝试从URL获取标题: {url}")
            # 实际获取标题的功能在这里实现
            # 由于当前版本兼容性问题，我们只记录日志而不实际获取

    def start_single_download(self):
        """开始单个视频下载"""
        # 简化版本，仅记录日志
        url = self.single_url_input.text().strip()
        title = self.single_title_input.text().strip()
        save_path = self.single_path_input.text().strip()
        download_type = self.single_type_combo.currentData()
        
        if not url:
            self.log_message("错误: 请输入视频URL")
            return
            
        if not title:
            title = "未命名视频"
            
        if not save_path:
            save_path = self.config_manager.get_download_path()
            
        # 发出下载请求信号
        self.download_requested.emit(url, title, save_path, download_type)
        self.log_message(f"已请求下载: {title}")
        
        # 清空输入框
        self.single_url_input.clear()
        self.single_title_input.clear()

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
        if (
            self.series_title_input.text().strip()
            and not self.series_title_input.text().startswith("系列标题将自动获取")
        ):
            reply = QMessageBox.question(
                self,
                "确认覆盖",
                "标题已被手动编辑，是否用获取到的标题覆盖？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return

        try:
            # Create temporary downloader to get title
            temp_downloader = BiliDownloader()
            video_info = temp_downloader.get_video_info(url)

            if video_info and video_info.get("title"):
                self.series_title_input.setText(video_info["title"])
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
            if hasattr(self, "series_save_path"):
                self.series_save_path.setText(path)

    def update_download_path(self):
        """更新下载路径"""
        download_path = self.config_manager.get_download_path()
        self.single_path_input.setText(download_path)
        self.series_path_input.setText(download_path)
        self.log_message(f"下载路径已更新: {download_path}")

    def check_ffmpeg_status(self):
        """检查FFmpeg状态"""
        try:
            ffmpeg_path = self.config_manager.get_ffmpeg_path()
            if ffmpeg_path and os.path.exists(ffmpeg_path):
                self.ffmpeg_status_label.setText("✅ 可用")
                self.series_ffmpeg_status_label.setText("✅ 可用")
            else:
                self.ffmpeg_status_label.setText("❌ 未配置")
                self.series_ffmpeg_status_label.setText("❌ 未配置")
        except Exception as e:
            self.ffmpeg_status_label.setText("❓ 未知")
            self.series_ffmpeg_status_label.setText("❓ 未知")
            self.log_message(f"检查FFmpeg状态失败: {e}")

    def on_tab_changed(self, button):
        """
        处理标签页切换
        
        Args:
            button: 被点击的按钮
        """
        # 设置按钮选中状态
        button.setChecked(True)
        
        # 根据按钮类型切换界面
        if button == self.single_video_tab:
            self.stacked_widget.setCurrentIndex(0)
            self.log_message("切换到单视频下载")
        elif button == self.series_video_tab:
            self.stacked_widget.setCurrentIndex(1)
            self.log_message("切换到系列视频下载")

    def check_ffmpeg(self):
        """
        检查FFmpeg是否可用

        Returns:
            bool: FFmpeg是否可用
        """
        if not self.config_manager:
            return False

        ffmpeg_path = self.config_manager.get_ffmpeg_path()
        if (
            not ffmpeg_path
            or not os.path.exists(ffmpeg_path)
            or not os.access(ffmpeg_path, os.X_OK)
        ):
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

    def browse_series_download_path(self):
        """浏览系列下载路径"""
        from PyQt6.QtWidgets import QFileDialog
        
        # 获取当前路径
        current_path = self.series_path_input.text()
        if not current_path:
            current_path = self.config_manager.get_download_path()
        
        # 打开文件夹选择对话框
        path = QFileDialog.getExistingDirectory(
            self,
            "选择系列下载路径",
            current_path
        )
        
        # 如果选择了路径，则更新输入框
        if path:
            self.series_path_input.setText(path)
            self.log_message(f"系列下载路径已设置: {path}")

    def start_series_download(self):
        """开始系列视频下载"""
        # 简化版本，仅记录日志
        url = self.series_url_input.text().strip()
        title = self.series_title_input.text().strip()
        save_path = self.series_path_input.text().strip()
        download_type = self.series_type_combo.currentData()
        
        if not url:
            self.log_message("错误: 请输入系列URL")
            return
            
        if not title:
            title = "未命名系列"
            
        if not save_path:
            save_path = self.config_manager.get_download_path()
            
        # 发出下载请求信号
        self.download_requested.emit(url, title, save_path, download_type)
        self.log_message(f"已请求下载: {title}")
        
        # 清空输入框
        self.series_url_input.clear()
        self.series_title_input.clear()
