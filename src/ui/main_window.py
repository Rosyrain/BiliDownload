"""
Main application window for BiliDownload.

This module provides the primary application interface including:
- Main window layout and styling
- Top download-type bar and left sidebar (7-shaped structure)
- File management display linked with category tree
- Configuration panel entry points
"""

import os
import platform
import re
import subprocess
import sys
from datetime import datetime

from PyQt6.QtCore import QSize, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QFont,
    QIcon,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.config_manager import ConfigManager
from src.core.file_manager import FileManager
from src.core.logger import Logger, get_logger

from .category_tab import CategoryTab
from .download_tab import DownloadTab
from .file_manager_tab import FileManagerTab
from .settings_tab import SettingsTab
from .task_list_tab import TaskListTab, TaskManager


class DownloadWorker(QThread):
    """
    下载工作线程，用于异步处理下载任务

    Signals:
        progress_updated (str, float, str): 发送进度更新信号 (任务ID, 进度百分比, 消息)
        video_progress_updated (str, float): 视频下载进度信号 (任务ID, 进度百分比)
        audio_progress_updated (str, float): 音频下载进度信号 (任务ID, 进度百分比)
        merge_progress_updated (str, float): 合并进度信号 (任务ID, 进度百分比)
        download_finished (str, bool, str): 下载完成信号 (任务ID, 是否成功, 消息)
        log_message (str, str, dict): 日志消息信号 (任务ID, 消息, 额外参数)
    """

    # 定义信号
    progress_updated = pyqtSignal(str, float, str)  # 任务ID, 进度, 消息
    video_progress_updated = pyqtSignal(str, float)  # 任务ID, 视频进度
    audio_progress_updated = pyqtSignal(str, float)  # 任务ID, 音频进度
    merge_progress_updated = pyqtSignal(str, float)  # 任务ID, 合并进度
    download_finished = pyqtSignal(str, bool, str)  # 任务ID, 成功标志, 消息
    log_message = pyqtSignal(str, str, dict)  # 任务ID, 消息, 额外参数

    def __init__(
        self, task_id, url, save_path, ffmpeg_path, download_type, config_manager
    ):
        """
        初始化下载工作线程

        Args:
            task_id (str): 任务ID
            url (str): 下载URL
            save_path (str): 保存路径
            ffmpeg_path (str): FFmpeg路径
            download_type (str): 下载类型
            config_manager: 配置管理器
        """
        super().__init__()
        self.task_id = task_id
        self.url = url
        self.save_path = save_path
        self.ffmpeg_path = ffmpeg_path
        self.download_type = download_type
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.is_cancelled = False
        self.title = None  # 将在simulate_download_progress中设置

    def run(self):
        """
        执行下载任务
        """
        try:
            # 创建cache目录用于临时文件
            import os

            cache_dir = os.path.join(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                ),
                "cache",
            )
            os.makedirs(cache_dir, exist_ok=True)

            # 使用任务ID作为临时文件名
            temp_base_name = os.path.join(cache_dir, self.task_id)

            # 生成文件名：标题+时间戳
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

            # 使用传入的标题，如果没有则使用任务ID
            title = self.title if self.title else self.task_id
            file_name = f"{self._sanitize_filename(title)}_{timestamp}"

            # 创建最终保存目录 - 不再创建子目录
            final_path = os.path.join(self.save_path, file_name)

            # 记录详细信息
            self.logger.info(f"开始异步下载: {self.task_id}")
            self.logger.info(f"- URL: {self.url}")
            self.logger.info(f"- 临时文件路径: {temp_base_name}")
            self.logger.info(f"- 最终保存路径: {final_path}")
            self.logger.info(f"- 下载类型: {self.download_type}")

            # 发送日志消息
            self.log_message.emit(self.task_id, f"开始下载任务: {title}", {})
            self.log_message.emit(self.task_id, f"下载类型: {self.download_type}", {})
            self.log_message.emit(self.task_id, f"保存路径: {final_path}", {})

            # 创建下载器
            from src.core.downloader import BiliDownloader

            downloader = BiliDownloader(self.config_manager)

            # 重写下载器的日志方法，将进度更新发送到UI
            # TODO: 检查此处逻辑
            downloader._download_stream

            def download_stream_wrapper(url, save_path):
                """包装下载流方法，添加进度回调"""
                # 判断是视频还是音频
                is_video = ".video.tmp" in save_path
                is_audio = ".audio.tmp" in save_path

                try:
                    # 获取文件大小
                    response = downloader.session.head(
                        url,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",  # noqa: E501
                            "Referer": "https://www.bilibili.com",
                        },
                    )
                    total_size = int(response.headers.get("content-length", 0))

                    # 打开文件
                    with open(save_path, "wb") as f:
                        # 发送请求
                        response = downloader.session.get(
                            url,
                            stream=True,
                            headers={
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",  # noqa: E501
                                "Referer": "https://www.bilibili.com",
                            },
                        )
                        response.raise_for_status()

                        # 下载文件
                        downloaded = 0
                        for chunk in response.iter_content(chunk_size=8192):
                            if self.is_cancelled:
                                self.logger.info(f"下载任务已取消: {self.task_id}")
                                return False

                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)

                                # 计算进度
                                if total_size:
                                    progress = (downloaded / total_size) * 100

                                    # 根据类型发送不同的进度信号
                                    if is_video:
                                        self.video_progress_updated.emit(
                                            self.task_id, progress
                                        )
                                    elif is_audio:
                                        self.audio_progress_updated.emit(
                                            self.task_id, progress
                                        )

                                    # 发送总体进度
                                    if self.download_type == "full":
                                        # 完整视频下载: 视频占40%，音频占40%，合并占20%
                                        if is_video:
                                            overall_progress = progress * 0.4
                                        elif is_audio:
                                            overall_progress = 40 + progress * 0.4
                                    elif self.download_type == "video":
                                        # 仅视频: 视频占100%
                                        overall_progress = progress
                                    elif self.download_type == "audio":
                                        # 仅音频: 音频占100%
                                        overall_progress = progress

                                    self.progress_updated.emit(
                                        self.task_id,
                                        overall_progress,
                                        f"下载进度: {progress:.1f}% \
                                        ({downloader._format_size(downloaded)}/{downloader._format_size(total_size)})",
                                    )
                                    # TODO: 检查这里嵌套/缩进问题，是否可以抽出去

                    return True
                except Exception as e:
                    self.logger.error(f"下载失败: {e}")
                    return False

            # 替换下载方法
            downloader._download_stream = download_stream_wrapper

            # 执行下载
            success = downloader.download_video(
                self.url,
                temp_base_name,
                self.ffmpeg_path,
                self.download_type,
                final_path=final_path,
            )

            # 发送完成信号
            if success:
                self.download_finished.emit(
                    self.task_id, True, f"任务 {self.task_id} 下载完成"
                )
                self.logger.info(f"任务完成: {self.task_id}")
                self.logger.info(f"文件已保存到: {final_path}")
            else:
                self.download_finished.emit(
                    self.task_id, False, f"任务 {self.task_id} 下载失败"
                )
                self.logger.error(f"任务失败: {self.task_id}")

        except Exception as e:
            self.logger.error(f"下载过程中发生错误: {e}")
            self.download_finished.emit(self.task_id, False, f"下载错误: {str(e)}")

    def cancel(self):
        """取消下载任务"""
        self.is_cancelled = True

    def _sanitize_filename(self, filename):
        """
        清理文件名，移除不合法字符

        Args:
            filename (str): 原始文件名

        Returns:
            str: 清理后的文件名
        """
        # 替换Windows和Unix系统中不允许的文件名字符
        invalid_chars = r'[\\/*?:"<>|]'
        return re.sub(invalid_chars, "_", filename)


class MainWindow(QMainWindow):
    """
    Main application window for BiliDownload.

    Provides the primary user interface with a 7-shaped layout:
    - Top bar for selecting download types
    - Left sidebar for category navigation and actions
    - Right content area for downloads and file display
    """

    def __init__(self):
        """
        Initialize the main application window.

        Sets up the window properties, creates the UI components,
        and initializes the configuration manager.

        Returns:
            None
        """
        super().__init__()
        self.config_manager = ConfigManager()
        self.logger = Logger(__name__)  # 使用Logger类而不是直接使用logging
        self.file_manager = FileManager()
        self.task_manager = TaskManager(self.config_manager)

        # Set window properties
        self.setWindowTitle("BiliDownload - Bilibili Video Downloader")
        self.setMinimumSize(1000, 600)
        self.resize(1200, 700)

        # Set window resize policy
        try:
            self.setSizeGripEnabled(True)
        except AttributeError:
            pass

        # Set window resize event
        self.resizeEvent = self.on_resize_event

        # Initialize UI
        self.init_ui()

        # Load configuration
        self.load_config()

    def on_resize_event(self, event):
        """
        Handle window resize events.

        Args:
            event (QResizeEvent): Window resize event.

        Returns:
            None
        """
        super().resizeEvent(event)

        # Delay saving window size to avoid frequent saves
        QTimer.singleShot(500, self.save_window_size)

    def save_window_size(self):
        """
        Save current window dimensions to configuration.

        Silently records the new window size without logging.

        Returns:
            None
        """
        try:
            # Silently save, don't print logs
            pass
        except Exception:
            # Silent error handling, don't log
            pass

    def load_config(self):
        """
        Load application configuration.

        Loads window size and other basic settings from configuration.

        Returns:
            None
        """
        try:
            width = int(self.config_manager.get("UI", "window_width", "1200"))
            height = int(self.config_manager.get("UI", "window_height", "800"))
            self.resize(width, height)
        except Exception:
            pass

    def init_ui(self):
        """
        Initialize the user interface.

        Sets up the main window layout, creates all UI components,
        and establishes connections between them.

        Returns:
            None
        """
        # Set window properties
        self.setWindowTitle("BiliDownload - Bilibili Video Downloader")
        self.setMinimumSize(1000, 600)
        self.resize(1200, 700)

        # Apply theme
        self.apply_soft_theme()

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar for download type selection
        top_bar = self.create_download_type_bar()
        main_layout.addWidget(top_bar)

        # Middle section with sidebar and content
        middle_section = QSplitter(Qt.Orientation.Horizontal)
        middle_section.setObjectName("middleSplitter")
        middle_section.setHandleWidth(1)
        middle_section.setChildrenCollapsible(False)

        # Left sidebar
        left_sidebar = self.create_left_sidebar()
        left_sidebar.setMinimumWidth(200)
        left_sidebar.setMaximumWidth(300)

        # Right content area
        right_content = self.create_right_content()

        middle_section.addWidget(left_sidebar)
        middle_section.addWidget(right_content)

        # Set the split position (30% for sidebar, 70% for content)
        middle_section.setSizes([300, 900])

        main_layout.addWidget(middle_section, 1)  # Give it stretch

        # Set the main widget
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Load initial data
        self.load_config()
        self.refresh_download_paths_combo()

        # Refresh file display with default path
        default_path = self.config_manager.get_download_path()
        if os.path.isdir(default_path):
            self.populate_file_table_for_path(default_path)
            if hasattr(self, "current_path_label"):
                self.current_path_label.setText(default_path)

    def apply_soft_theme(self):
        """
        Apply a soft, Cloudreve-like theme across the main window widgets.

        Returns:
            None
        """
        self.setStyleSheet("""
            QWidget { background-color: #f8f9ff; color: #4a5bbf; }
            QLabel#appHeader { color: #4a5bbf; font-weight: bold; }
            QFrame#topBar {
                background: #ffffff;
                border-bottom: 1px solid #e1e8ff;
            }
            QFrame#functionBar {
                background: #ffffff;
                border: 1px solid #e1e8ff;
                border-radius: 6px;
            }
            QFrame#leftSidebar { background: #ffffff; border-right: 1px solid #e1e8ff; }
            QSplitter#middleSplitter::handle { background: #eef2ff; width: 6px; }
            QSplitter::handle:vertical { height: 6px; }
            QTreeWidget {
                border: 1px solid #e1e8ff;
                border-radius: 6px;
                background-color: white;
                font-family: 'Consolas', 'Menlo', 'Monaco', monospace;
                font-size: 13px;
            }
            QTreeWidget::item {
                height: 26px;
                padding-left: 5px;
                border-bottom: 1px solid #f0f4ff;
            }
            QTreeWidget::item:selected {
                background-color: #e8f0ff;
                color: #4a5bbf;
            }
            QTreeWidget::item:hover {
                background-color: #f0f4ff;
            }
            QTreeWidget::branch {
                background-color: white;
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                image: url(resources/collapsed.png);
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                image: url(resources/expanded.png);
            }
            QTableWidget {
                border: 1px solid #e1e8ff;
                border-radius: 6px;
                background: #ffffff;
            }
            QTableWidget::item {
                height: 36px;
                padding: 4px;
                border-bottom: 1px solid #f0f4ff;
            }
            QHeaderView::section {
                background-color: #f0f4ff;
                color: #5a6acf;
                padding: 8px;
                border: none;
                border-right: 1px solid #e1e8ff;
                height: 36px;
            }
            QLineEdit, QSpinBox, QComboBox {
                border: 1px solid #e1e8ff;
                border-radius: 6px;
                padding: 6px;
                background: #ffffff;
            }
            QPushButton {
                background: #e8f0ff;
                color: #5a6acf;
                border: 1px solid #d1d8ff;
                border-radius: 6px;
                padding: 4px 10px;
                min-height: 24px;
                max-height: 30px;
            }
            QPushButton:hover {
                background: #d8e8ff;
            }
            QToolButton {
                background: #e8f0ff;
                color: #5a6acf;
                border: 1px solid #d1d8ff;
                border-radius: 6px;
                padding: 4px 8px;
                min-width: 60px;
                min-height: 24px;
                max-height: 30px;
            }
            QToolButton:hover {
                background: #d8e8ff;
            }
            QToolButton:checked {
                background: #4a5bbf;
                color: white;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #d1d8ff;
                border-radius: 3px;
                background: white;
            }
            QCheckBox::indicator:checked {
                background-color: #4a5bbf;
                border-color: #4a5bbf;
            }
            QToolTip {
                background-color: #ffffff;
                color: #4a5bbf;
                border: 1px solid #e1e8ff;
                padding: 5px;
            }
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #e1e8ff;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f4ff;
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #d1d8ff;
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #b1b8ff;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                border: none;
                background: #f0f4ff;
                height: 10px;
                margin: 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background: #d1d8ff;
                min-width: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #b1b8ff;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
            QSpinBox {
                padding-right: 15px;
                background-color: white;
            }
            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 16px;
                height: 12px;
                border-left: 1px solid #d1d8ff;
                border-bottom: 1px solid #d1d8ff;
                border-top-right-radius: 6px;
                background: #f0f4ff;
            }
            QSpinBox::up-button:hover {
                background: #d8e8ff;
            }
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 16px;
                height: 12px;
                border-left: 1px solid #d1d8ff;
                border-bottom-right-radius: 6px;
                background: #f0f4ff;
            }
            QSpinBox::down-button:hover {
                background: #d8e8ff;
            }
        """)

    def create_title_bar(self):
        """
        Create the application title bar.

        Returns:
            QWidget: Title bar widget with logo, title, and quick action buttons.
        """
        title_bar = QFrame()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(80)

        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(20, 10, 20, 10)

        # Left: Title and icon
        left_layout = QHBoxLayout()

        # Icon (using emoji as temporary icon)
        icon_label = QLabel("🎬")
        icon_label.setFont(QFont("Arial", 24))
        left_layout.addWidget(icon_label)

        # Main title
        title_layout = QVBoxLayout()
        main_title = QLabel("BiliDownload")
        main_title.setObjectName("mainTitle")
        main_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title_layout.addWidget(main_title)

        subtitle = QLabel("Professional Bilibili Video Downloader")
        subtitle.setObjectName("subtitle")
        subtitle.setFont(QFont("Arial", 10))
        title_layout.addWidget(subtitle)

        left_layout.addLayout(title_layout)
        left_layout.addStretch()
        layout.addLayout(left_layout)

        # Right: Quick action buttons
        right_layout = QHBoxLayout()

        # Quick download button
        quick_download_btn = QPushButton("Quick Download")
        quick_download_btn.setObjectName("quickDownloadBtn")
        quick_download_btn.clicked.connect(self.show_quick_download)
        right_layout.addWidget(quick_download_btn)

        # Settings button
        settings_btn = QPushButton("Settings")
        settings_btn.setObjectName("settingsBtn")
        settings_btn.clicked.connect(self.show_settings)
        right_layout.addWidget(settings_btn)

        layout.addLayout(right_layout)

        return title_bar

    def create_function_tabs(self):
        """
        Create the left-side function tab panel.

        Returns:
            QTabWidget: Tab widget containing all functional tabs.
        """
        # Function tabs title
        tabs_title = QLabel("Function Tabs")
        tabs_title.setObjectName("tabsTitle")
        tabs_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        tabs_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tabs_title.setFixedHeight(40)

        # Create function tabs
        tab_widget = QTabWidget()
        tab_widget.setObjectName("functionTabs")
        tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        tab_widget.setTabShape(QTabWidget.TabShape.Rounded)

        # Add various function tabs
        download_tab = DownloadTab(self.config_manager)
        file_manager_tab = FileManagerTab(self.config_manager)
        category_tab = CategoryTab(self.config_manager)
        settings_tab = SettingsTab(self.config_manager)

        tab_widget.addTab(download_tab, "Download Management")
        tab_widget.addTab(file_manager_tab, "File Manager")
        tab_widget.addTab(category_tab, "Category Management")
        tab_widget.addTab(settings_tab, "Settings")

        # Create layout for tabs
        tabs_layout = QVBoxLayout()
        tabs_layout.addWidget(tabs_title)
        tabs_layout.addWidget(tab_widget)

        # Create container widget
        tabs_container = QWidget()
        tabs_container.setLayout(tabs_layout)

        return tabs_container

    def create_download_type_bar(self):
        """
        Create the top bar with navigation buttons.

        Returns:
            QFrame: The top bar frame containing navigation buttons
        """
        # Create top bar frame
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setMinimumHeight(60)
        top_bar.setMaximumHeight(60)

        # Create layout
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(20, 0, 20, 0)

        # Add BiliDownload title and make it clickable to return to main page
        title_label = QLabel("BiliDownload")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #4a5bbf;")
        title_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        title_label.mousePressEvent = lambda event: self.show_main_content()
        layout.addWidget(title_label)

        layout.addStretch()

        # Add home button to return to main content
        self.home_btn = QPushButton("下载管理")
        self.home_btn.setMinimumSize(100, 40)
        self.home_btn.clicked.connect(self.show_main_content)
        layout.addWidget(self.home_btn)

        # Add task list button
        self.task_list_btn = QPushButton("任务列表")
        self.task_list_btn.setMinimumSize(100, 40)
        self.task_list_btn.clicked.connect(self.show_task_list)
        layout.addWidget(self.task_list_btn)

        # Add settings button
        settings_btn = QPushButton("设置")
        settings_btn.setMinimumSize(100, 40)
        settings_btn.clicked.connect(self.show_settings)
        layout.addWidget(settings_btn)

        return top_bar

    def create_left_sidebar(self) -> QFrame:
        """
        Create the left sidebar with category tree and action buttons.

        Returns:
            QWidget: Left sidebar widget
        """
        left_sidebar = QWidget()
        layout = QVBoxLayout(left_sidebar)
        layout.setContentsMargins(0, 0, 0, 0)  # 移除边距，使内容铺满
        layout.setSpacing(5)  # 减少间距

        # 顶部分类标题区域
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(10, 10, 10, 5)

        # 分类标题 - 放大字体
        category_label = QLabel("分类")
        category_label.setStyleSheet(
            "font-weight: bold; font-size: 18px; color: #4a5bbf;"
        )
        title_layout.addWidget(category_label)
        layout.addWidget(title_container)

        # 分类树 - 铺满整个区域
        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderHidden(True)
        self.category_tree.setIndentation(15)
        self.category_tree.setIconSize(QSize(20, 20))  # 增大图标尺寸
        self.category_tree.setStyleSheet("""
            QTreeWidget {
                border: none;
                background-color: #f5f7fa;
                outline: none;
                padding: 5px;
            }
            QTreeWidget::item {
                height: 30px;
                border-radius: 4px;
                padding-left: 4px;
                color: #333333;
                margin: 2px 0px;
            }
            QTreeWidget::item:selected {
                background-color: #e8f0ff;
                color: #4a5bbf;
                font-weight: bold;
            }
            QTreeWidget::item:hover {
                background-color: #f0f5ff;
            }
            QTreeWidget::branch {
                background-color: transparent;
            }
        """)
        self.category_tree.itemClicked.connect(self.on_category_selected)
        # 设置尺寸策略，使树形控件可以扩展填充空间
        self.category_tree.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.category_tree)

        # 底部按钮容器
        bottom_container = QWidget()
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(10, 5, 10, 10)
        bottom_layout.setSpacing(5)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #e0e0e0;")
        bottom_layout.addWidget(separator)

        # 定义按钮样式
        button_style = """
            QPushButton {
                background-color: #e8f0ff;
                border: 1px solid #d0d8ff;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
                font-weight: bold;
                color: #4a5bbf;
                text-align: center;
                margin: 2px 0px;
            }
            QPushButton:hover {
                background-color: #d0e0ff;
                border-color: #b0c0ff;
            }
            QPushButton:pressed {
                background-color: #c0d0ff;
            }
        """

        # 新建文件夹按钮
        new_folder_btn = QPushButton("新建文件夹")
        new_folder_btn.setStyleSheet(button_style)
        new_folder_btn.clicked.connect(self.create_category_folder)
        bottom_layout.addWidget(new_folder_btn)

        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet(button_style)
        refresh_btn.clicked.connect(self.refresh_category_tree)
        bottom_layout.addWidget(refresh_btn)

        # 底部固定按钮
        info_btn = QPushButton("说明")
        info_btn.setStyleSheet(button_style)
        info_btn.clicked.connect(self.show_info)
        bottom_layout.addWidget(info_btn)

        config_btn = QPushButton("配置")
        config_btn.setStyleSheet(button_style)
        config_btn.clicked.connect(self.show_settings)
        bottom_layout.addWidget(config_btn)

        version_btn = QPushButton("版本")
        version_btn.setStyleSheet(button_style)
        version_btn.clicked.connect(self.show_version)
        bottom_layout.addWidget(version_btn)

        layout.addWidget(bottom_container)

        return left_sidebar

    def create_right_content(self):
        """
        Create the right content area with stacked pages.

        Returns:
            QStackedWidget: The stacked widget containing content pages
        """
        # Create stacked widget for content pages
        self.content_stack = QStackedWidget()

        # Create main content page (download + file display)
        main_content = self.create_main_content()
        self.content_stack.addWidget(main_content)

        # Create settings page
        settings_page = self.create_settings_page()
        self.content_stack.addWidget(settings_page)

        # Create task list page
        self.task_list_page = self.create_task_list_page()
        self.content_stack.addWidget(self.task_list_page)

        return self.content_stack

    def create_main_content(self):
        """
        Create the main content with download area and file display.

        Returns:
            QWidget: The main content widget
        """
        # Create main content container
        main_content = QWidget()
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create splitter for download area and file display
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Create download area
        download_area = QScrollArea()
        download_area.setWidgetResizable(True)
        download_area.setFrameShape(QFrame.Shape.NoFrame)

        # Create download tab
        self.download_tab = DownloadTab(
            self.config_manager, self.file_manager, self.logger
        )
        download_area.setWidget(self.download_tab)

        # Connect download tab signals
        self.download_tab.task_created.connect(self.on_task_created)
        self.download_tab.show_task_list_requested.connect(self.show_task_list)

        # Create separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setLineWidth(1)

        # Create file display
        file_display = QScrollArea()
        file_display.setWidgetResizable(True)
        file_display.setFrameShape(QFrame.Shape.NoFrame)
        file_display.setWidget(self.create_file_display())

        # Add widgets to splitter
        splitter.addWidget(download_area)
        splitter.addWidget(separator)
        splitter.addWidget(file_display)

        # Set initial sizes (2/3 for download, 10px for separator, 1/3 for files)
        splitter.setSizes(
            [int(splitter.height() * 0.66), 10, int(splitter.height() * 0.33)]
        )

        main_layout.addWidget(splitter)

        return main_content

    def create_file_display(self):
        """
        Create the file display area.

        Returns:
            QWidget: File display widget
        """
        file_display = QWidget()
        layout = QVBoxLayout(file_display)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # 创建滚动内容
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        # 顶部控制区域 - 包含当前路径、搜索、类型选择、刷新和打开文件夹按钮
        top_control = QWidget()
        top_layout = QHBoxLayout(top_control)
        top_layout.setContentsMargins(0, 0, 0, 10)
        top_layout.setSpacing(10)

        # 当前路径显示 - 使用QLineEdit替代QLabel以便完整显示路径
        path_widget = QWidget()
        path_layout = QHBoxLayout(path_widget)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(5)

        path_layout.addWidget(QLabel("当前路径:"))
        self.current_path_label = QLineEdit()
        self.current_path_label.setReadOnly(True)
        self.current_path_label.setStyleSheet("""
            QLineEdit {
                font-weight: bold;
                background-color: transparent;
                border: none;
                padding: 2px;
            }
        """)
        path_layout.addWidget(self.current_path_label, 1)  # 路径显示占据大部分空间

        # 文件计数
        self.file_count_label = QLabel("0 个文件")
        path_layout.addWidget(self.file_count_label)

        top_layout.addWidget(path_widget, 1)  # 路径区域占据大部分空间

        # 搜索框
        search_label = QLabel("搜索:")
        top_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入文件名搜索...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                min-width: 150px;
            }
            QLineEdit:focus {
                border-color: #409eff;
            }
        """)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        top_layout.addWidget(self.search_input)

        # 类型选择
        type_label = QLabel("类型:")
        top_layout.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.addItem("全部")
        self.type_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 5px 10px 5px 10px;
                background-color: white;
                min-width: 100px;
                font-size: 13px;
            }
            QComboBox:focus {
                border-color: #409eff;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border-left: none;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #409eff;
                background-color: white;
                selection-background-color: #e8f0ff;
                selection-color: #4a5bbf;
            }
            QComboBox QAbstractItemView::item {
                height: 25px;
                padding: 5px;
            }
        """)
        self.type_combo.currentIndexChanged.connect(self.on_file_type_changed)
        top_layout.addWidget(self.type_combo)

        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_file_display)
        top_layout.addWidget(refresh_btn)

        # 打开文件夹按钮
        open_folder_btn = QPushButton("打开文件夹")
        open_folder_btn.clicked.connect(
            lambda: self.open_folder(self.current_path_label.text())
        )
        top_layout.addWidget(open_folder_btn)

        scroll_layout.addWidget(top_control)

        # 文件表格
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(5)
        self.file_table.setHorizontalHeaderLabels(
            ["名称", "类型", "大小", "修改时间", "操作"]
        )
        self.file_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.file_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.file_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.file_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.file_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Fixed
        )
        self.file_table.horizontalHeader().setFixedHeight(40)  # 增大表头高度
        self.file_table.setColumnWidth(4, 180)  # 设置操作列宽度
        self.file_table.verticalHeader().setVisible(False)
        self.file_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.file_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setShowGrid(False)
        self.file_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e1e8ff;
                border-radius: 6px;
                background-color: white;
                gridline-color: transparent;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f4ff;
                height: 40px;  /* 增大行高 */
            }
            QTableWidget::item:selected {
                background-color: #e8f0ff;
                color: #4a5bbf;
            }
            QHeaderView::section {
                background-color: #f5f7fa;
                border: none;
                border-bottom: 1px solid #e1e8ff;
                padding: 8px;
                font-weight: bold;
                height: 40px;  /* 增大表头高度 */
            }
        """)
        # 设置行高为55像素
        self.file_table.verticalHeader().setDefaultSectionSize(55)

        scroll_layout.addWidget(self.file_table)

        # 设置滚动区域的内容
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        return file_display

    def filter_files(self, path, search_text="", file_type="全部"):
        """
        Filter files by search text and file type.

        Args:
            path (str): Directory path to filter files from
            search_text (str, optional): Search text to filter by
            file_type (str, optional): File type to filter by

        Returns:
            list: Filtered file list
        """
        try:
            if not path or not os.path.isdir(path):
                return []

            # 获取目录中的所有文件
            files = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path):
                    # 获取文件信息
                    try:
                        file_info = self.file_manager.get_file_info(item_path)
                    except ValueError:
                        # 如果获取文件信息失败，使用基本信息
                        file_info = {
                            "name": item,
                            "path": item_path,
                            "size": os.path.getsize(item_path)
                            if os.path.exists(item_path)
                            else 0,
                            "modified": datetime.fromtimestamp(
                                os.path.getmtime(item_path)
                            )
                            if os.path.exists(item_path)
                            else datetime.now(),
                            "type": os.path.splitext(item)[1].lstrip(".").upper()
                            or "文件",
                        }

                    # 应用过滤条件
                    if (
                        search_text
                        and search_text.lower() not in file_info["name"].lower()
                    ):
                        continue

                    if file_type != "全部" and file_type.lower() != (
                        "." + file_info["type"].lower()
                    ):
                        continue

                    files.append(file_info)

            return files

        except Exception as e:
            QMessageBox.warning(self, "错误", f"过滤文件失败：{e}")
            return []

    def update_file_type_combo(self, path=None):
        """
        Update file type combo box based on files in current directory.

        Args:
            path (str, optional): Directory path to scan for file types

        Returns:
            None
        """
        # 如果没有提供路径，使用当前路径
        if not path and hasattr(self, "current_path_label"):
            path = self.current_path_label.text()

        if not path or not os.path.exists(path):
            return

        # 获取目录中的所有文件
        try:
            files = os.listdir(path)
            extensions = set()

            # 收集所有文件扩展名
            for file in files:
                file_path = os.path.join(path, file)
                if os.path.isfile(file_path):
                    _, ext = os.path.splitext(file)
                    if ext:
                        extensions.add(ext.lower())

            # 保存当前选择的类型
            current_type = (
                self.type_combo.currentText() if self.type_combo.count() > 0 else "全部"
            )

            # 清空并重新填充类型下拉框
            self.type_combo.clear()
            self.type_combo.addItem("全部")

            # 添加找到的扩展名
            for ext in sorted(extensions):
                self.type_combo.addItem(ext)

            # 尝试恢复之前的选择
            index = self.type_combo.findText(current_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)
            else:
                self.type_combo.setCurrentIndex(0)  # 默认选择"全部"

        except Exception as e:
            self.logger.error(f"更新文件类型下拉框失败: {e}")

    def populate_file_table_for_path(self, path: str):
        """
        Populate the file table with files from the specified path.

        Args:
            path (str): Directory path to display files from.

        Returns:
            None
        """
        if not path or not os.path.isdir(path):
            self.file_table.setRowCount(0)
            self.file_count_label.setText("0 个文件")
            return

        try:
            # 获取并显示文件
            self.populate_file_table(path)

            # 更新文件类型下拉框
            self.update_file_type_combo(path)

        except Exception as e:
            self.logger.error(f"Failed to populate file table: {e}")
            QMessageBox.warning(self, "错误", f"加载文件列表失败：{e}")

    def populate_file_table(self, path, search_text="", file_type="全部"):
        """
        Populate the file table with filtered files.

        Args:
            path (str): Directory path to display files from
            search_text (str, optional): Search text to filter by
            file_type (str, optional): File type to filter by

        Returns:
            None
        """
        # 如果没有提供搜索文本和文件类型，使用当前值
        if search_text == "" and hasattr(self, "search_input"):
            search_text = self.search_input.text().lower()

        if file_type == "全部" and hasattr(self, "type_combo"):
            file_type = self.type_combo.currentText()

        # 获取过滤后的文件列表
        files = self.filter_files(path, search_text, file_type)

        # 更新文件计数
        self.file_count_label.setText(f"{len(files)} 个文件")

        # 清空表格
        self.file_table.setRowCount(0)

        # 添加文件到表格
        for i, file_info in enumerate(files):
            self.file_table.insertRow(i)

            # 文件名（长名称添加工具提示）
            name = file_info["name"]
            name_item = QTableWidgetItem(name)
            if len(name) > 30:
                name_item.setToolTip(name)
            self.file_table.setItem(i, 0, name_item)

            # 文件类型
            file_type = file_info["type"]
            type_item = QTableWidgetItem(file_type)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.file_table.setItem(i, 1, type_item)

            # 文件大小
            size = (
                self.format_size(file_info["size"])
                if isinstance(file_info["size"], (int, float))
                else str(file_info["size"])
            )
            size_item = QTableWidgetItem(size)
            size_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.file_table.setItem(i, 2, size_item)

            # 修改时间
            if isinstance(file_info["modified"], datetime):
                mod_time = file_info["modified"].strftime("%Y-%m-%d %H:%M")
            else:
                mod_time = str(file_info["modified"])
            time_item = QTableWidgetItem(mod_time)
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.file_table.setItem(i, 3, time_item)

            # 操作按钮
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 4, 4, 4)
            action_layout.setSpacing(8)

            open_btn = QPushButton("打开")
            open_btn.setFixedSize(70, 36)
            open_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e8f0ff;
                    border: 1px solid #d1d8ff;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #d8e8ff;
                }
            """)
            open_btn.clicked.connect(lambda _, fp=file_info["path"]: self.open_file(fp))

            delete_btn = QPushButton("删除")
            delete_btn.setFixedSize(70, 36)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffe8e8;
                    border: 1px solid #ffd1d1;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 13px;
                    font-weight: bold;
                    color: #bf4a4a;
                }
                QPushButton:hover {
                    background-color: #ffd8d8;
                }
            """)
            delete_btn.clicked.connect(
                lambda _, fp=file_info["path"]: self.delete_file(fp)
            )

            action_layout.addWidget(open_btn)
            action_layout.addWidget(delete_btn)
            action_layout.addStretch()

            self.file_table.setCellWidget(i, 4, action_widget)

    def on_search_text_changed(self):
        """
        Handle search text change event.

        Updates the file table based on the search text.

        Returns:
            None
        """
        search_text = self.search_input.text().lower()
        file_type = self.type_combo.currentText()
        path = self.current_path_label.text()

        # 更新文件表格
        self.populate_file_table(path, search_text, file_type)

    def on_file_type_changed(self, index):
        """
        Handle file type change event.

        Updates the file table based on the selected file type.

        Args:
            index (int): Selected index in the combo box

        Returns:
            None
        """
        file_type = self.type_combo.currentText()
        search_text = self.search_input.text().lower()
        path = self.current_path_label.text()

        # 更新文件表格
        self.populate_file_table(path, search_text, file_type)

    def format_size(self, size_bytes: int) -> str:
        """
        Format file size in bytes to human-readable format.

        Args:
            size_bytes (int): File size in bytes.

        Returns:
            str: Formatted file size string.
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    def refresh_download_paths_combo(self):
        """
        Refresh the download paths combo box and category tree.

        Returns:
            None
        """
        # Refresh category tree
        self.refresh_category_tree()

    def refresh_category_tree(self):
        """
        Refresh the category tree with folders from the download path.

        Returns:
            None
        """
        if not hasattr(self, "category_tree"):
            return

        self.category_tree.clear()

        # 获取下载根路径
        download_path = self.config_manager.get_download_path()
        if not os.path.isdir(download_path):
            self.logger.warning(f"Download path does not exist: {download_path}")
            try:
                os.makedirs(download_path, exist_ok=True)
                self.logger.info(f"Created download directory: {download_path}")
            except Exception as e:
                self.logger.error(f"Failed to create download directory: {e}")
                return

        # 获取下载路径的文件夹名称
        folder_name = os.path.basename(download_path)

        # 创建根节点，使用文件夹本身的名称
        root_item = QTreeWidgetItem(self.category_tree)
        root_item.setText(0, folder_name)
        root_item.setIcon(
            0, self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        )
        root_item.setForeground(0, QBrush(QColor("#4a5bbf")))
        root_item.setData(0, Qt.ItemDataRole.UserRole, download_path)

        # 递归添加子目录
        self._add_directory_to_tree(root_item, download_path)

        # 默认展开根节点
        root_item.setExpanded(True)

    def _add_directory_to_tree(self, parent_item: QTreeWidgetItem, directory_path: str):
        """
        Add subdirectories to the category tree recursively.

        Args:
            parent_item (QTreeWidgetItem): Parent tree item.
            directory_path (str): Directory path to add.

        Returns:
            None
        """
        try:
            # 检查路径是否为目录
            if not os.path.isdir(directory_path):
                self.logger.warning(f"Not a directory: {directory_path}")
                return

            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                if os.path.isdir(item_path) and not item.startswith("."):
                    child_item = QTreeWidgetItem(parent_item)
                    child_item.setText(0, item)  # 显示文件夹名称

                    # 设置工具提示显示完整路径
                    child_item.setToolTip(0, item_path)

                    # 使用系统标准图标，确保可见性
                    child_item.setIcon(
                        0, self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
                    )

                    # 设置文本颜色，确保与图标区分
                    child_item.setForeground(0, QBrush(QColor("#4a5bbf")))

                    child_item.setData(0, Qt.ItemDataRole.UserRole, item_path)

                    # Recursively add subdirectories
                    self._add_directory_to_tree(child_item, item_path)
        except Exception as e:
            self.logger.error(f"Error adding directory to tree: {e}")

    def on_category_selected(self, item: QTreeWidgetItem):
        """
        Handle category selection event.

        Updates the file display and download tab path when a category is selected.

        Args:
            item (QTreeWidgetItem): Selected category item

        Returns:
            None
        """
        try:
            if not item:
                return

            # 获取分类路径
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if not path or not os.path.isdir(path):
                self.logger.warning(f"Invalid category path: {path}")
                return

            # 更新文件显示
            self.populate_file_table_for_path(path)
            self.current_path_label.setText(path)

            # 更新搜索和类型过滤器
            self.search_input.clear()
            self.update_file_type_combo(path)

            # 总是切换到主页面
            if hasattr(self, "content_stack") and self.content_stack:
                self.content_stack.setCurrentIndex(0)
                self.update_nav_button_styles(self.home_btn)

            # 更新下载标签页的路径
            if hasattr(self, "download_tab") and self.download_tab:
                # 更新单个视频的保存路径
                if hasattr(self.download_tab, "single_save_path"):
                    self.download_tab.single_save_path.setText(path)

                # 更新系列视频的保存路径
                if hasattr(self.download_tab, "series_save_path"):
                    self.download_tab.series_save_path.setText(path)

                # 如果download_tab有on_category_changed方法，调用它
                if hasattr(self.download_tab, "on_category_changed"):
                    self.download_tab.on_category_changed(path)
        except Exception as e:
            self.logger.error(f"Failed to select category: {e}")

    def create_category_folder(self):
        """
        Create a new category folder.

        Returns:
            None
        """
        folder_name, ok = QInputDialog.getText(self, "新建文件夹", "请输入文件夹名称:")
        if ok and folder_name:
            # Get current selected path or default to root
            current_item = self.category_tree.currentItem()
            if current_item:
                parent_path = current_item.data(0, Qt.ItemDataRole.UserRole)
            else:
                parent_path = self.config_manager.get_download_path()

            # Create new folder
            new_folder_path = os.path.join(parent_path, folder_name)
            try:
                if not os.path.exists(new_folder_path):
                    os.makedirs(new_folder_path)
                    QMessageBox.information(
                        self, "成功", f"已创建文件夹: {folder_name}"
                    )

                    # 直接更新树形视图，无需重新加载整个树
                    if current_item:
                        # 添加到当前选中项
                        child_item = QTreeWidgetItem(current_item)
                        child_item.setText(0, folder_name)

                        # 使用更加明显的文件夹图标
                        folder_icon = QIcon.fromTheme("folder")
                        if not folder_icon.isNull():
                            child_item.setIcon(0, folder_icon)
                        else:
                            # 使用系统内置图标，确保可见性
                            child_item.setIcon(
                                0,
                                self.style().standardIcon(
                                    QStyle.StandardPixmap.SP_DirIcon
                                ),
                            )

                        # 设置文本颜色，确保与图标区分
                        child_item.setForeground(0, QBrush(QColor("#4a5bbf")))

                        child_item.setData(0, Qt.ItemDataRole.UserRole, new_folder_path)
                        current_item.setExpanded(True)
                    else:
                        # 如果没有选中项，刷新整个树
                        self.refresh_category_tree()
                else:
                    QMessageBox.warning(self, "错误", f"文件夹已存在: {folder_name}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建文件夹失败: {str(e)}")

    def refresh_file_display(self):
        """
        Refresh the file display with the current path.

        Returns:
            None
        """
        if hasattr(self, "current_path_label") and self.current_path_label:
            current_path = self.current_path_label.text()
            if current_path and os.path.isdir(current_path):
                self.populate_file_table_for_path(current_path)

    def show_settings(self):
        """
        Show settings panel.

        Returns:
            None
        """
        try:
            if hasattr(self, "content_stack") and self.content_stack:
                # Load current settings into form and switch
                self.load_settings_into_form()
                self.content_stack.setCurrentIndex(1)

                # Update button styles to show active state
                self.update_nav_button_styles(
                    self.findChild(QPushButton, "settingsBtn")
                )
            elif hasattr(self, "tab_widget") and self.tab_widget:
                self.tab_widget.setCurrentIndex(3)
            else:
                QMessageBox.information(self, "配置", "侧边栏配置页即将上线")
        except Exception:
            pass

    def show_info(self):
        """
        Show placeholder info panel.

        Returns:
            None
        """
        QMessageBox.information(self, "说明", "这里将展示使用说明与项目信息（预留）")

    def show_version(self):
        """
        Show application version.

        Returns:
            None
        """
        QMessageBox.information(self, "版本", "BiliDownload v1.0.0")

    def load_settings_into_form(self):
        """
        Load current configuration values into the settings form widgets.

        Returns:
            None
        """
        try:
            # 获取下载路径
            download_path = self.config_manager.get_download_path()
            if download_path:
                self.edit_download_path.setText(download_path)

            # 获取FFmpeg路径
            ffmpeg_path = self.config_manager.get_ffmpeg_path()
            if ffmpeg_path:
                self.edit_ffmpeg_path.setText(ffmpeg_path)

            # 获取最大并发下载数
            try:
                max_concurrent = self.config_manager.get_max_concurrent_downloads()
                if max_concurrent > 0:
                    self.spin_max_concurrent.setValue(max_concurrent)
            except (ValueError, TypeError) as e:
                self.logger.warning(f"加载最大并发下载数失败: {e}")
                self.spin_max_concurrent.setValue(3)  # 默认值

            # 获取断点续传块大小
            try:
                resume_chunk_size = self.config_manager.get_resume_chunk_size()
                if resume_chunk_size > 0:
                    self.spin_resume_chunk.setValue(resume_chunk_size)
            except (ValueError, TypeError) as e:
                self.logger.warning(f"加载断点续传块大小失败: {e}")
                self.spin_resume_chunk.setValue(10)  # 默认值

            # 获取详细日志设置
            try:
                verbose_logging = self.config_manager.get_advanced_setting(
                    "verbose_logging", "false"
                )
                self.chk_verbose.setChecked(verbose_logging.lower() == "true")
            except Exception as e:
                self.logger.warning(f"加载详细日志设置失败: {e}")
                self.chk_verbose.setChecked(False)  # 默认值

            self.logger.info("设置加载成功")
        except Exception as e:
            self.logger.error(f"加载设置失败: {e}")
            QMessageBox.warning(self, "加载设置", f"加载设置失败: {e}")

    def save_settings_from_form(self):
        """
        Persist settings from form widgets back to the configuration and refresh UI.

        Returns:
            None
        """
        try:
            self.config_manager.set_download_path(
                self.edit_download_path.text().strip()
            )
            self.config_manager.set_ffmpeg_path(self.edit_ffmpeg_path.text().strip())
            self.config_manager.set_max_concurrent_downloads(
                self.spin_max_concurrent.value()
            )
            self.config_manager.set_resume_chunk_size(self.spin_resume_chunk.value())

            # Ensure ADVANCED section exists before writing
            try:
                if not self.config_manager.config.has_section("ADVANCED"):
                    self.config_manager.config.add_section("ADVANCED")
                self.config_manager.set(
                    "ADVANCED",
                    "verbose_logging",
                    "true" if self.chk_verbose.isChecked() else "false",
                )
            except Exception as e:
                self.logger.error(f"Error setting ADVANCED section: {e}")

            # Save config to file
            self.config_manager.save_config()

            # Refresh sidebar and file view
            self.refresh_download_paths_combo()
            self.refresh_category_tree()
            self.refresh_file_display()

            # Switch back to main page
            self.content_stack.setCurrentIndex(0)
            QMessageBox.information(self, "配置", "保存成功。")
        except Exception as e:
            QMessageBox.warning(self, "配置", f"保存失败：{e}")

    def validate_ffmpeg_path(self):
        """
        验证 FFmpeg 路径是否可用。
        """
        path = self.edit_ffmpeg_path.text().strip()
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "FFmpeg 验证", "路径不存在或为空")
            return
        try:
            result = subprocess.run(
                [path, "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
            )
            if result.returncode == 0:
                QMessageBox.information(self, "FFmpeg 验证", "FFmpeg 可用")
            else:
                QMessageBox.warning(self, "FFmpeg 验证", "FFmpeg 返回非零状态")
        except Exception as e:
            QMessageBox.warning(self, "FFmpeg 验证", f"验证失败：{e}")

    def create_settings_page(self):
        """
        创建设置页面界面。

        Returns:
            QWidget: 设置页面的容器控件
        """
        # 创建设置页面容器
        settings_container = QWidget()
        settings_layout = QVBoxLayout(settings_container)
        settings_layout.setContentsMargins(15, 15, 15, 15)
        settings_layout.setSpacing(15)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # 创建滚动内容
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        scroll_layout.setSpacing(15)

        # 标题
        title_label = QLabel("应用设置")
        title_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; margin-bottom: 10px;"
        )
        scroll_layout.addWidget(title_label)

        # 基本设置组
        basic_group = QGroupBox("基本设置")
        basic_layout = QGridLayout(basic_group)
        basic_layout.setContentsMargins(15, 20, 15, 15)
        basic_layout.setSpacing(10)

        # 下载路径设置
        basic_layout.addWidget(QLabel("下载路径:"), 0, 0)
        self.edit_download_path = QLineEdit()
        basic_layout.addWidget(self.edit_download_path, 0, 1)
        browse_btn = QPushButton("浏览")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self.browse_download_path)
        basic_layout.addWidget(browse_btn, 0, 2)

        # FFmpeg路径设置
        basic_layout.addWidget(QLabel("FFmpeg 路径:"), 1, 0)
        self.edit_ffmpeg_path = QLineEdit()
        basic_layout.addWidget(self.edit_ffmpeg_path, 1, 1)
        ffmpeg_browse_btn = QPushButton("浏览")
        ffmpeg_browse_btn.setFixedWidth(80)
        ffmpeg_browse_btn.clicked.connect(self.browse_ffmpeg_path)
        basic_layout.addWidget(ffmpeg_browse_btn, 1, 2)

        # FFmpeg验证按钮
        ffmpeg_validate_btn = QPushButton("验证")
        ffmpeg_validate_btn.setFixedWidth(80)
        ffmpeg_validate_btn.clicked.connect(self.validate_ffmpeg_path)
        basic_layout.addWidget(ffmpeg_validate_btn, 1, 3)

        scroll_layout.addWidget(basic_group)

        # 高级设置组
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QGridLayout(advanced_group)
        advanced_layout.setContentsMargins(15, 20, 15, 15)
        advanced_layout.setSpacing(10)

        # 最大并发下载数
        advanced_layout.addWidget(QLabel("最大并发下载数:"), 0, 0)
        self.spin_max_concurrent = QSpinBox()
        self.spin_max_concurrent.setMinimum(1)
        self.spin_max_concurrent.setMaximum(10)
        self.spin_max_concurrent.setValue(3)
        self.spin_max_concurrent.setFixedWidth(80)
        self.spin_max_concurrent.setStyleSheet("""
            QSpinBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                font-size: 13px;
            }
            QSpinBox:focus {
                border-color: #409eff;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 12px;   /* 确保宽度足够显示箭头 */
                height: 12px;  /* 增加高度 */
                background-color: #f5f7fa;
                border-left: 1px solid #dcdfe6;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #e6f2ff;
            }
            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                border-top-right-radius: 3px;
            }
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                border-bottom-right-radius: 3px;
                border-top: 1px solid #dcdfe6;
            }
        """)
        advanced_layout.addWidget(self.spin_max_concurrent, 0, 1)

        # 提示按钮
        help_btn = QPushButton("?")
        help_btn.setFixedSize(30, 30)  # 增大按钮尺寸
        help_btn.setStyleSheet("""
            QPushButton {
                border-radius: 15px;
                background-color: #e0e0ff;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d0d0ff;
            }
        """)
        help_btn.clicked.connect(
            lambda: QMessageBox.information(
                self, "并发下载", "设置同时下载的视频数量，建议不超过5个。"
            )
        )
        advanced_layout.addWidget(help_btn, 0, 2)
        advanced_layout.setColumnStretch(3, 1)  # 添加拉伸以确保按钮不会占据过多空间

        # 断点续传块大小设置
        advanced_layout.addWidget(QLabel("断点续传块大小 (MB):"), 1, 0)
        self.spin_resume_chunk = QSpinBox()
        self.spin_resume_chunk.setMinimum(1)
        self.spin_resume_chunk.setMaximum(100)
        self.spin_resume_chunk.setValue(10)
        self.spin_resume_chunk.setFixedWidth(80)
        self.spin_resume_chunk.setStyleSheet("""
            QSpinBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                font-size: 13px;
            }
            QSpinBox:focus {
                border-color: #409eff;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 12px;
                height: 12px;
                background-color: #f5f7fa;
                border-left: 1px solid #dcdfe6;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #e6f2ff;
            }
            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                border-top-right-radius: 3px;
            }
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                border-bottom-right-radius: 3px;
                border-top: 1px solid #dcdfe6;
            }
        """)
        advanced_layout.addWidget(self.spin_resume_chunk, 1, 1)

        # 断点续传块大小提示按钮
        help_btn2 = QPushButton("?")
        help_btn2.setFixedSize(30, 30)
        help_btn2.setStyleSheet("""
            QPushButton {
                border-radius: 15px;
                background-color: #e0e0ff;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d0d0ff;
            }
        """)
        help_btn2.clicked.connect(
            lambda: QMessageBox.information(
                self,
                "断点续传块大小",
                "设置断点续传时每次下载的数据块大小，单位为MB。\n"
                "较大的值可能提高下载速度，但在网络不稳定时可能导致频繁重试。\n"
                "较小的值在网络不稳定时更可靠，但可能降低下载速度。",
            )
        )
        advanced_layout.addWidget(help_btn2, 1, 2)

        # 详细日志选项
        self.chk_verbose = QCheckBox("启用详细日志")
        advanced_layout.addWidget(self.chk_verbose, 2, 0, 1, 2)

        # 详细日志提示按钮
        help_btn3 = QPushButton("?")
        help_btn3.setFixedSize(30, 30)  # 增大按钮尺寸
        help_btn3.setStyleSheet("""
            QPushButton {
                border-radius: 15px;
                background-color: #e0e0ff;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d0d0ff;
            }
        """)
        help_btn3.clicked.connect(
            lambda: QMessageBox.information(
                self, "详细日志", "启用后将记录更详细的日志信息，有助于排查问题。"
            )
        )
        advanced_layout.addWidget(help_btn3, 2, 2)

        scroll_layout.addWidget(advanced_group)

        # 按钮区域
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 10, 0, 0)
        buttons_layout.setSpacing(10)

        save_btn = QPushButton("保存")
        save_btn.setMinimumWidth(120)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a5bbf;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #3a4baf;
            }
        """)
        save_btn.clicked.connect(self.save_settings_from_form)

        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumWidth(120)
        cancel_btn.clicked.connect(lambda: self.content_stack.setCurrentIndex(0))

        buttons_layout.addStretch()
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)

        scroll_layout.addLayout(buttons_layout)
        scroll_layout.addStretch()

        # 设置滚动区域
        scroll_area.setWidget(scroll_content)
        settings_layout.addWidget(scroll_area)

        return settings_container

    def browse_download_path(self):
        """
        打开文件夹选择对话框，用于选择下载路径。

        Returns:
            None
        """
        path = QFileDialog.getExistingDirectory(
            self,
            "选择下载路径",
            self.edit_download_path.text() or os.path.expanduser("~"),
        )
        if path:
            self.edit_download_path.setText(path)

    def browse_ffmpeg_path(self):
        """
        打开文件选择对话框，用于选择FFmpeg可执行文件路径。

        Returns:
            None
        """
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择FFmpeg可执行文件",
            self.edit_ffmpeg_path.text() or os.path.expanduser("~"),
        )
        if path:
            self.edit_ffmpeg_path.setText(path)

    def open_file(self, file_path: str):
        """
        Open a file with the default application.

        Args:
            file_path (str): Path to the file to open.

        Returns:
            None
        """
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "错误", "文件不存在")
            return

        try:
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", file_path])
            else:  # Linux
                subprocess.run(["xdg-open", file_path])
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开文件：{e}")

    def delete_file(self, file_path: str):
        """
        Delete a file after confirmation.

        Args:
            file_path (str): Path to the file to delete.

        Returns:
            None
        """
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "错误", "文件不存在")
            return

        file_name = os.path.basename(file_path)
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除文件 '{file_name}' 吗？\n此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(file_path)
                self.refresh_file_display()
            except Exception as e:
                QMessageBox.warning(self, "错误", f"删除文件失败：{e}")

    def open_folder(self, folder_path: str):
        """
        Open a folder in the system file explorer.

        Args:
            folder_path (str): Path to the folder to open.

        Returns:
            None
        """
        if not os.path.isdir(folder_path):
            QMessageBox.warning(self, "错误", "文件夹不存在")
            return

        try:
            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开文件夹：{e}")

    def create_task_list_page(self):
        """
        Create the task list page.

        Returns:
            QWidget: The task list page widget
        """
        # Create task list tab
        self.task_list_tab = TaskListTab(
            self.task_manager, self.config_manager, self.file_manager
        )

        # Connect task action signals
        self.task_list_tab.task_action_requested.connect(self.on_task_action)

        return self.task_list_tab

    def show_task_list(self):
        """
        Show the task list page.

        Returns:
            None
        """
        if hasattr(self, "content_stack") and self.content_stack:
            self.content_stack.setCurrentIndex(2)  # Task list is at index 2

            # Update button styles to show active state
            self.update_nav_button_styles(self.task_list_btn)

    def show_main_content(self):
        """
        Show the main content page.

        Returns:
            None
        """
        if hasattr(self, "content_stack") and self.content_stack:
            self.content_stack.setCurrentIndex(0)  # Main content is at index 0

            # Update button styles to show active state
            self.update_nav_button_styles(self.home_btn)

    def on_task_created(self, task_id, url, title, save_path, download_type):
        """
        处理任务创建事件

        Args:
            task_id (str): 任务ID
            url (str): 下载URL
            title (str): 视频标题
            save_path (str): 保存路径
            download_type (str): 下载类型
        """
        # 创建任务
        task = self.task_manager.create_task(url, title, save_path, download_type)
        self.logger.info(f"任务已创建: {task_id} - {title}")

        # 显示任务列表
        self.show_task_list()

        # 启动任务
        self.on_task_action(task.id, "start")

    def on_task_action(self, task_id, action):
        """
        处理任务操作请求

        Args:
            task_id (str): 任务ID
            action (str): 操作类型 (start/pause/cancel/delete/retry)
        """
        task = self.task_manager.get_task(task_id)
        if not task:
            return

        if action == "start":
            self.logger.info(f"开始任务: {task_id}")
            task.update_status(task.STATUS_ACTIVE)
            self.simulate_download_progress(task_id)
        elif action == "pause":
            self.logger.info(f"暂停任务: {task_id}")
            task.update_status(task.STATUS_PAUSED)

            # 如果有工作线程在运行，取消它
            if hasattr(self, "download_workers") and task_id in self.download_workers:
                self.download_workers[task_id].cancel()

        elif action == "cancel":
            self.logger.info(f"取消任务: {task_id}")
            task.update_status(task.STATUS_FAILED)

            # 如果有工作线程在运行，取消它
            if hasattr(self, "download_workers") and task_id in self.download_workers:
                self.download_workers[task_id].cancel()

        elif action == "delete":
            # 删除任务
            self.logger.info(f"删除任务: {task_id}")

            # 确认对话框
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除任务 '{task.title}' 吗？此操作不可恢复。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                # 如果有工作线程在运行，先取消它
                if (
                    hasattr(self, "download_workers")
                    and task_id in self.download_workers
                ):
                    self.download_workers[task_id].cancel()
                    self.download_workers[task_id].deleteLater()
                    del self.download_workers[task_id]

                # 从任务管理器中删除任务
                success = self.task_manager.remove_task(task_id)

                if success:
                    self.logger.info(f"任务已删除: {task_id}")

                    # 刷新任务列表
                    if hasattr(self, "task_list_tab") and self.task_list_tab:
                        self.task_list_tab.refresh_task_list()
                else:
                    self.logger.error(f"删除任务失败: {task_id}")
                    QMessageBox.warning(self, "删除失败", "删除任务失败，请稍后重试。")

        elif action == "retry":
            # 重试任务
            self.logger.info(f"重试任务: {task_id}")

            # 重置任务状态为等待中
            task.update_status(task.STATUS_PENDING)
            task.update_progress(0.0)  # 重置进度
            task.error = ""  # 清除错误信息

            # 刷新任务列表
            if hasattr(self, "task_list_tab") and self.task_list_tab:
                self.task_list_tab.refresh_task_list()

            # 立即开始任务
            self.on_task_action(task_id, "start")

    def simulate_download_progress(self, task_id):
        """
        实际执行下载任务，使用异步工作线程处理。

        Args:
            task_id (str): 任务ID

        Returns:
            None
        """
        task = self.task_manager.get_task(task_id)
        if not task or task.status != task.STATUS_ACTIVE:
            return

        try:
            # 获取任务信息
            url = task.url
            save_path = task.save_path
            download_type = task.download_type
            title = task.title

            # 创建下载工作线程
            self.download_workers = getattr(self, "download_workers", {})

            # 生成文件名：标题+时间戳
            # TODO: 这里是否需要？
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            f"{self._sanitize_filename(title)}_{timestamp}"

            worker = DownloadWorker(
                task_id,
                url,
                save_path,
                self.config_manager.get_ffmpeg_path(),
                download_type,
                self.config_manager,
            )

            # 传递标题给worker
            worker.title = title

            # 连接信号
            worker.progress_updated.connect(self.on_download_progress_updated)
            worker.video_progress_updated.connect(self.on_video_progress_updated)
            worker.audio_progress_updated.connect(self.on_audio_progress_updated)
            worker.merge_progress_updated.connect(self.on_merge_progress_updated)
            worker.download_finished.connect(self.on_download_finished)
            worker.log_message.connect(self.on_download_log_message)

            # 保存工作线程引用
            self.download_workers[task_id] = worker

            # 记录开始下载的日志
            self.logger.info(
                f"开始下载任务: {title}", task_id=task_id, task_title=title
            )

            # 启动工作线程
            worker.start()

        except Exception as e:
            # 处理异常
            task.update_status(task.STATUS_FAILED)
            self.logger.error(
                f"启动下载任务时发生错误: {e}", task_id=task_id, task_title=task.title
            )
            QMessageBox.critical(self, "下载错误", f"启动下载任务时发生错误: {e}")

            # 将错误信息显示到下载标签页
            if hasattr(self, "download_tab") and self.download_tab:
                self.download_tab.add_log_message(
                    f"下载错误: {str(e)}", task_id=task_id, task_title=task.title
                )

    def on_download_progress_updated(self, task_id, progress, message):
        """处理下载进度更新"""
        task = self.task_manager.get_task(task_id)
        if task:
            task.update_progress(progress)
            self.logger.info(message, task_id=task_id, task_title=task.title)

            # 将日志消息显示到下载标签页
            if hasattr(self, "download_tab") and self.download_tab:
                self.download_tab.add_log_message(
                    message, task_id=task_id, task_title=task.title
                )

            # 更新任务列表进度
            if hasattr(self, "task_list_tab") and self.task_list_tab:
                self.task_list_tab.update_task_progress(task_id, progress, message)

    def on_video_progress_updated(self, task_id, progress):
        """处理视频下载进度更新"""
        # 更新任务列表中的视频进度
        if hasattr(self, "task_list_tab") and self.task_list_tab:
            self.task_list_tab.update_task_video_progress(task_id, progress)

    def on_audio_progress_updated(self, task_id, progress):
        """处理音频下载进度更新"""
        # 更新任务列表中的音频进度
        if hasattr(self, "task_list_tab") and self.task_list_tab:
            self.task_list_tab.update_task_audio_progress(task_id, progress)

    def on_merge_progress_updated(self, task_id, progress):
        """处理合并进度更新"""
        # 更新任务列表中的合并进度
        if hasattr(self, "task_list_tab") and self.task_list_tab:
            self.task_list_tab.update_task_merge_progress(task_id, progress)

    def on_download_finished(self, task_id, success, message):
        """处理下载完成"""
        task = self.task_manager.get_task(task_id)
        if not task:
            return

        # 清理工作线程
        if hasattr(self, "download_workers") and task_id in self.download_workers:
            self.download_workers[task_id].deleteLater()
            del self.download_workers[task_id]

        if success:
            # 更新任务状态为完成
            task.update_status(task.STATUS_COMPLETED)
            task.update_progress(100.0)
            self.logger.info(
                f"任务完成: {task_id}", task_id=task_id, task_title=task.title
            )

            # 显示通知
            QMessageBox.information(
                self, "下载完成", f"任务 '{task.title}' 已完成下载。"
            )

            # 将完成信息显示到下载标签页
            if hasattr(self, "download_tab") and self.download_tab:
                self.download_tab.add_log_message(
                    f"任务完成: {task.title}", task_id=task_id, task_title=task.title
                )
        else:
            # 更新任务状态为失败
            task.update_status(task.STATUS_FAILED)
            self.logger.error(
                f"任务失败: {task_id}", task_id=task_id, task_title=task.title
            )

            # 显示通知
            QMessageBox.warning(
                self,
                "下载失败",
                f"任务 '{task.title}' 下载失败。请检查日志获取详细信息。",
            )

            # 将失败信息显示到下载标签页
            if hasattr(self, "download_tab") and self.download_tab:
                self.download_tab.add_log_message(
                    f"任务失败: {task.title}", task_id=task_id, task_title=task.title
                )

    def on_download_log_message(self, task_id, message, kwargs):
        """处理下载日志消息"""
        # 获取任务信息以添加标识
        task = self.task_manager.get_task(task_id)
        task_title = task.title if task else None

        # 将日志消息显示到下载标签页
        if hasattr(self, "download_tab") and self.download_tab:
            # 添加任务ID和标题到kwargs
            kwargs["task_id"] = task_id
            kwargs["task_title"] = task_title
            self.download_tab.add_log_message(message, **kwargs)

    def _sanitize_filename(self, filename):
        """
        清理文件名，移除不合法字符

        Args:
            filename (str): 原始文件名

        Returns:
            str: 清理后的文件名
        """
        # 替换Windows和Unix系统中不允许的文件名字符
        invalid_chars = r'[\\/*?:"<>|]'
        return re.sub(invalid_chars, "_", filename)

    def update_nav_button_styles(self, active_button=None):
        """
        Update navigation button styles to show active state.

        Args:
            active_button: The currently active button

        Returns:
            None
        """
        # Define button style templates
        active_style = """
            QPushButton {
                background-color: #4a5bbf;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a4baf;
            }
        """

        inactive_style = """
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
        """

        # Update styles
        for btn in [self.home_btn, self.task_list_btn]:
            if btn == active_button:
                btn.setStyleSheet(active_style)
            else:
                btn.setStyleSheet(inactive_style)

        settings_btn = self.findChild(QPushButton, "设置")
        if settings_btn:
            if settings_btn == active_button:
                settings_btn.setStyleSheet(active_style)
            else:
                settings_btn.setStyleSheet(inactive_style)


def main():
    """
    Main function for launching the application.

    Creates and displays the main application window.

    Returns:
        None
    """
    # Set application properties
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    # Create and display main window
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
