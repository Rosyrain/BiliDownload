"""
设置标签页
"""

import os
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QGroupBox,
    QFrame,
    QFileDialog,
    QMessageBox,
    QTabWidget,
    QFormLayout,
)

from src.core.config_manager import ConfigManager


class SettingsTab(QWidget):
    """设置标签页"""

    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 应用柔和主题样式
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e1e8ff;
                background: white;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #f0f4ff;
                padding: 12px 20px;
                margin-right: 4px;
                border: 1px solid #e1e8ff;
                border-bottom: none;
                border-radius: 8px 8px 0 0;
                font-weight: bold;
                color: #5a6acf;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 1px solid white;
                color: #4a5bbf;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #e8f0ff;
                color: #4a5bbf;
            }
            QGroupBox {
                font-weight: bold;
                color: #5a6acf;
                border: 2px solid #e1e8ff;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background: #fafbff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: #fafbff;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #d1d8ff;
                border-radius: 6px;
                background: white;
                color: #4a5bbf;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #4a5bbf;
                background: #fefeff;
            }
            QPushButton {
                background-color: #e8f0ff;
                color: #5a6acf;
                border: 1px solid #d1d8ff;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #d8e8ff;
                border-color: #b8c8ff;
            }
            QPushButton:pressed {
                background-color: #c8d8ff;
            }
            QLabel {
                color: #4a5bbf;
                font-weight: 500;
            }
            QCheckBox {
                color: #5a6acf;
                font-weight: 500;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #d1d8ff;
                border-radius: 3px;
                background: white;
            }
            QCheckBox::indicator:checked {
                background: #4a5bbf;
                border-color: #4a5bbf;
            }
            QComboBox {
                padding: 6px;
                border: 1px solid #d1d8ff;
                border-radius: 6px;
                background: white;
                color: #4a5bbf;
                font-size: 12px;
            }
            QComboBox:focus {
                border-color: #4a5bbf;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #5a6acf;
                margin-right: 5px;
            }
            QSpinBox {
                padding: 6px;
                border: 1px solid #d1d8ff;
                border-radius: 6px;
                background: white;
                color: #4a5bbf;
                font-size: 12px;
            }
            QSpinBox:focus {
                border-color: #4a5bbf;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 16px;
                border: none;
                background: #f0f4ff;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #e8f0ff;
            }
            QSpinBox::up-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 4px solid #5a6acf;
                margin: 2px;
            }
            QSpinBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #5a6acf;
                margin: 2px;
            }
        """)

        # 创建标签页
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # 添加各个设置标签页
        self.tab_widget.addTab(self.create_general_tab(), "📁 常规设置")
        self.tab_widget.addTab(self.create_download_tab(), "⬇️ 下载设置")
        self.tab_widget.addTab(self.create_ui_tab(), "🎨 界面设置")
        self.tab_widget.addTab(self.create_advanced_tab(), "⚙️ 高级设置")

        # 底部按钮
        bottom_panel = QFrame()
        bottom_panel.setStyleSheet("""
            QFrame {
                background-color: #f8f9ff;
                border: 1px solid #e1e8ff;
                border-radius: 8px;
                padding: 15px;
                margin-top: 15px;
            }
        """)
        bottom_layout = QHBoxLayout(bottom_panel)

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet(
            "color: #5a6acf; font-style: italic; font-weight: 500;"
        )
        bottom_layout.addWidget(self.status_label)

        bottom_layout.addStretch()

        self.reset_btn = QPushButton("🔄 重置为默认")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_to_default)
        bottom_layout.addWidget(self.reset_btn)

        self.save_btn = QPushButton("💾 保存设置")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a5bbf;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3a4baf;
            }
        """)
        self.save_btn.clicked.connect(self.save_settings)
        bottom_layout.addWidget(self.save_btn)

        layout.addWidget(bottom_panel)

    def create_general_tab(self) -> QWidget:
        """创建常规设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)

        # 下载路径设置
        path_group = QGroupBox("📁 下载路径设置")
        path_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #495057;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        path_layout = QFormLayout(path_group)
        path_layout.setSpacing(15)

        # 路径输入框和按钮的容器
        path_container = QWidget()
        path_container_layout = QHBoxLayout(path_container)
        path_container_layout.setContentsMargins(0, 0, 0, 0)

        self.download_path_input = QLineEdit()
        self.download_path_input.setPlaceholderText("选择默认下载目录")
        self.download_path_input.setReadOnly(True)
        self.download_path_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #dee2e6;
                border-radius: 4px;
                background: white;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
        """)

        browse_path_btn = QPushButton("📂 浏览")
        browse_path_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        browse_path_btn.clicked.connect(self.browse_download_path)

        path_container_layout.addWidget(self.download_path_input)
        path_container_layout.addWidget(browse_path_btn)

        path_layout.addRow("默认下载路径:", path_container)

        # 快速路径按钮
        quick_path_layout = QHBoxLayout()
        quick_path_layout.setSpacing(10)

        desktop_btn = QPushButton("🖥️ 桌面")
        desktop_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        desktop_btn.clicked.connect(lambda: self.set_quick_path("desktop"))

        downloads_btn = QPushButton("📥 下载文件夹")
        downloads_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        downloads_btn.clicked.connect(lambda: self.set_quick_path("downloads"))

        custom_btn = QPushButton("📁 自定义")
        custom_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        custom_btn.clicked.connect(self.browse_download_path)

        quick_path_layout.addWidget(desktop_btn)
        quick_path_layout.addWidget(downloads_btn)
        quick_path_layout.addWidget(custom_btn)
        quick_path_layout.addStretch()

        path_layout.addRow("快速选择:", quick_path_layout)

        layout.addWidget(path_group)

        # FFmpeg设置
        ffmpeg_group = QGroupBox("🎬 FFmpeg设置")
        ffmpeg_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #495057;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        ffmpeg_layout = QFormLayout(ffmpeg_group)
        ffmpeg_layout.setSpacing(15)

        # FFmpeg路径输入框和按钮的容器
        ffmpeg_container = QWidget()
        ffmpeg_container_layout = QHBoxLayout(ffmpeg_container)
        ffmpeg_container_layout.setContentsMargins(0, 0, 0, 0)

        self.ffmpeg_path_input = QLineEdit()
        self.ffmpeg_path_input.setPlaceholderText("选择FFmpeg可执行文件路径")
        self.ffmpeg_path_input.setReadOnly(True)
        self.ffmpeg_path_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #dee2e6;
                border-radius: 4px;
                background: white;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
        """)

        browse_ffmpeg_btn = QPushButton("📂 浏览")
        browse_ffmpeg_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        browse_ffmpeg_btn.clicked.connect(self.browse_ffmpeg_path)

        ffmpeg_container_layout.addWidget(self.ffmpeg_path_input)
        ffmpeg_container_layout.addWidget(browse_ffmpeg_btn)

        ffmpeg_layout.addRow("FFmpeg路径:", ffmpeg_container)

        # FFmpeg检测状态
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)

        self.ffmpeg_status_label = QLabel("未检测")
        self.ffmpeg_status_label.setStyleSheet("color: #666666; font-weight: bold;")

        self.ffmpeg_test_btn = QPushButton("🧪 测试")
        self.ffmpeg_test_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        self.ffmpeg_test_btn.clicked.connect(self.test_ffmpeg)

        status_layout.addWidget(self.ffmpeg_status_label)
        status_layout.addWidget(self.ffmpeg_test_btn)
        status_layout.addStretch()

        ffmpeg_layout.addRow("状态:", status_container)

        layout.addWidget(ffmpeg_group)

        # 分类设置
        category_group = QGroupBox("🏷️ 分类设置")
        category_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #495057;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        category_layout = QFormLayout(category_group)
        category_layout.setSpacing(15)

        self.auto_create_categories_cb = QCheckBox("自动创建分类文件夹")
        self.auto_create_categories_cb.setStyleSheet("""
            QCheckBox {
                font-size: 13px;
                color: #495057;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        category_layout.addRow("", self.auto_create_categories_cb)

        self.default_category_combo = QComboBox()
        self.default_category_combo.addItem("未分类")
        self.default_category_combo.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 2px solid #dee2e6;
                border-radius: 4px;
                background: white;
                min-width: 150px;
            }
            QComboBox:focus {
                border-color: #0078d4;
            }
        """)
        category_layout.addRow("默认分类:", self.default_category_combo)

        layout.addWidget(category_group)

        layout.addStretch()
        return tab

    def create_download_tab(self) -> QWidget:
        """创建下载设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 下载参数设置
        download_group = QGroupBox("下载参数")
        download_layout = QFormLayout(download_group)

        self.chunk_size_spin = QSpinBox()
        self.chunk_size_spin.setRange(1024, 65536)
        self.chunk_size_spin.setSuffix(" bytes")
        self.chunk_size_spin.setToolTip("下载时的数据块大小，影响内存使用和下载速度")
        download_layout.addRow("数据块大小:", self.chunk_size_spin)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setSuffix(" 秒")
        self.timeout_spin.setToolTip("网络请求超时时间")
        download_layout.addRow("超时时间:", self.timeout_spin)

        self.retry_count_spin = QSpinBox()
        self.retry_count_spin.setRange(1, 10)
        self.retry_count_spin.setToolTip("下载失败时的重试次数")
        download_layout.addRow("重试次数:", self.retry_count_spin)

        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 10)
        self.delay_spin.setSuffix(" 秒")
        self.delay_spin.setToolTip("请求之间的延迟时间，避免被限制")
        download_layout.addRow("请求延迟:", self.delay_spin)

        layout.addWidget(download_group)

        # 并发设置
        concurrent_group = QGroupBox("并发设置")
        concurrent_layout = QFormLayout(concurrent_group)

        self.max_concurrent_spin = QSpinBox()
        self.max_concurrent_spin.setRange(1, 10)
        self.max_concurrent_spin.setToolTip("同时进行的最大下载任务数")
        concurrent_layout.addRow("最大并发数:", self.max_concurrent_spin)

        layout.addWidget(concurrent_group)

        # 断点续传设置
        resume_group = QGroupBox("断点续传")
        resume_layout = QFormLayout(resume_group)

        self.enable_resume_cb = QCheckBox("启用断点续传")
        self.enable_resume_cb.setToolTip("支持下载中断后继续下载")
        resume_layout.addRow("", self.enable_resume_cb)

        self.resume_threshold_spin = QSpinBox()
        self.resume_threshold_spin.setRange(1024, 1048576)
        self.resume_threshold_spin.setSuffix(" bytes")
        self.resume_threshold_spin.setToolTip("启用断点续传的最小文件大小")
        resume_layout.addRow("最小文件大小:", self.resume_threshold_spin)

        layout.addWidget(resume_group)

        layout.addStretch()
        return tab

    def create_ui_tab(self) -> QWidget:
        """创建界面设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 主题设置
        theme_group = QGroupBox("主题设置")
        theme_layout = QFormLayout(theme_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色", "深色", "自动"])
        self.theme_combo.setToolTip("选择界面主题")
        theme_layout.addRow("主题:", self.theme_combo)

        layout.addWidget(theme_group)

        # 语言设置
        language_group = QGroupBox("语言设置")
        language_layout = QFormLayout(language_group)

        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English"])
        self.language_combo.setToolTip("选择界面语言")
        language_layout.addRow("语言:", self.language_combo)

        layout.addWidget(language_group)

        # 窗口设置
        window_group = QGroupBox("窗口设置")
        window_layout = QFormLayout(window_group)

        self.remember_window_size_cb = QCheckBox("记住窗口大小")
        self.remember_window_size_cb.setToolTip("下次启动时恢复上次的窗口大小")
        window_layout.addRow("", self.remember_window_size_cb)

        self.remember_window_position_cb = QCheckBox("记住窗口位置")
        self.remember_window_position_cb.setToolTip("下次启动时恢复上次的窗口位置")
        window_layout.addRow("", self.remember_window_position_cb)

        self.start_minimized_cb = QCheckBox("启动时最小化")
        self.start_minimized_cb.setToolTip("程序启动时自动最小化到系统托盘")
        window_layout.addRow("", self.start_minimized_cb)

        layout.addWidget(window_group)

        # 通知设置
        notification_group = QGroupBox("通知设置")
        notification_layout = QFormLayout(notification_group)

        self.show_download_notification_cb = QCheckBox("显示下载完成通知")
        self.show_download_notification_cb.setToolTip("下载完成后显示系统通知")
        notification_layout.addRow("", self.show_download_notification_cb)

        self.play_sound_cb = QCheckBox("播放提示音")
        self.play_sound_cb.setToolTip("下载完成后播放提示音")
        notification_layout.addRow("", self.play_sound_cb)

        layout.addWidget(notification_group)

        layout.addStretch()
        return tab

    def create_advanced_tab(self) -> QWidget:
        """创建高级设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 网络设置
        network_group = QGroupBox("网络设置")
        network_layout = QFormLayout(network_group)

        self.use_proxy_cb = QCheckBox("使用代理")
        self.use_proxy_cb.setToolTip("启用代理服务器")
        network_layout.addRow("", self.use_proxy_cb)

        self.proxy_host_input = QLineEdit()
        self.proxy_host_input.setPlaceholderText("代理服务器地址")
        self.proxy_host_input.setEnabled(False)
        network_layout.addRow("代理地址:", self.proxy_host_input)

        self.proxy_port_input = QLineEdit()
        self.proxy_port_input.setPlaceholderText("端口")
        self.proxy_port_input.setEnabled(False)
        network_layout.addRow("代理端口:", self.proxy_port_input)

        # 连接代理设置和复选框
        self.use_proxy_cb.toggled.connect(self.toggle_proxy_settings)

        layout.addWidget(network_group)

        # 日志设置
        log_group = QGroupBox("日志设置")
        log_layout = QFormLayout(log_group)

        self.enable_logging_cb = QCheckBox("启用日志记录")
        self.enable_logging_cb.setToolTip("记录程序运行日志")
        log_layout.addRow("", self.enable_logging_cb)

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["调试", "信息", "警告", "错误"])
        self.log_level_combo.setToolTip("日志记录级别")
        log_layout.addRow("日志级别:", self.log_level_combo)

        self.max_log_size_spin = QSpinBox()
        self.max_log_size_spin.setRange(1, 100)
        self.max_log_size_spin.setSuffix(" MB")
        self.max_log_size_spin.setToolTip("单个日志文件的最大大小")
        log_layout.addRow("最大日志大小:", self.max_log_size_spin)

        layout.addWidget(log_group)

        # 性能设置
        performance_group = QGroupBox("性能设置")
        performance_layout = QFormLayout(performance_group)

        self.enable_cache_cb = QCheckBox("启用缓存")
        self.enable_cache_cb.setToolTip("缓存视频信息以提高性能")
        performance_layout.addRow("", self.enable_cache_cb)

        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(10, 1000)
        self.cache_size_spin.setSuffix(" MB")
        self.cache_size_spin.setToolTip("缓存的最大大小")
        performance_layout.addRow("缓存大小:", self.cache_size_spin)

        # 高级设置组
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QFormLayout(advanced_group)
        advanced_layout.setContentsMargins(15, 15, 15, 15)
        advanced_layout.setSpacing(15)

        # 断点续传块大小设置
        self.resume_chunk_size = QSpinBox()
        self.resume_chunk_size.setMinimum(1)
        self.resume_chunk_size.setMaximum(100)
        self.resume_chunk_size.setValue(10)  # 默认值
        self.resume_chunk_size.setSuffix(" MB")
        self.resume_chunk_size.setToolTip(
            "设置断点续传时的块大小，较小的值可以提高断点续传的精度，但可能增加网络请求次数"
        )
        advanced_layout.addRow("断点续传块大小:", self.resume_chunk_size)

        # 最大并发下载数设置
        self.max_concurrent_downloads = QSpinBox()
        self.max_concurrent_downloads.setMinimum(1)
        self.max_concurrent_downloads.setMaximum(10)
        self.max_concurrent_downloads.setValue(3)  # 默认值
        self.max_concurrent_downloads.setToolTip(
            "设置最大同时下载任务数，过多的并发下载可能导致网络拥塞"
        )
        advanced_layout.addRow("最大并发下载数:", self.max_concurrent_downloads)

        # 添加到主布局
        layout.addWidget(advanced_group)

        layout.addStretch()
        return tab

    def load_settings(self):
        """加载设置"""
        try:
            # 常规设置
            download_path = self.config_manager.get_download_path()
            self.download_path_input.setText(download_path)

            ffmpeg_path = self.config_manager.get_ffmpeg_path()
            if ffmpeg_path:
                self.ffmpeg_path_input.setText(ffmpeg_path)
                self.check_ffmpeg_status()

            auto_create = self.config_manager.get(
                "GENERAL", "auto_create_categories", "true"
            )
            self.auto_create_categories_cb.setChecked(auto_create.lower() == "true")

            default_category = self.config_manager.get(
                "GENERAL", "default_category", "未分类"
            )
            self.default_category_combo.setCurrentText(default_category)

            # 下载设置
            chunk_size = int(self.config_manager.get("DOWNLOAD", "chunk_size", "8192"))
            self.chunk_size_spin.setValue(chunk_size)

            timeout = int(self.config_manager.get("DOWNLOAD", "timeout", "30"))
            self.timeout_spin.setValue(timeout)

            retry_count = int(self.config_manager.get("DOWNLOAD", "retry_count", "3"))
            self.retry_count_spin.setValue(retry_count)

            delay = int(
                self.config_manager.get("DOWNLOAD", "delay_between_requests", "1")
            )
            self.delay_spin.setValue(delay)

            max_concurrent = int(
                self.config_manager.get("GENERAL", "max_concurrent_downloads", "3")
            )
            self.max_concurrent_spin.setValue(max_concurrent)

            # 界面设置
            theme = self.config_manager.get("UI", "theme", "light")
            theme_map = {"light": "浅色", "dark": "深色", "auto": "自动"}
            self.theme_combo.setCurrentText(theme_map.get(theme, "浅色"))

            language = self.config_manager.get("UI", "language", "zh_CN")
            lang_map = {"zh_CN": "简体中文", "en_US": "English"}
            self.language_combo.setCurrentText(lang_map.get(language, "简体中文"))

            # 高级设置
            self.enable_logging_cb.setChecked(True)
            self.log_level_combo.setCurrentText("信息")
            self.max_log_size_spin.setValue(50)
            self.enable_cache_cb.setChecked(True)
            self.cache_size_spin.setValue(100)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载设置失败: {str(e)}")

    def save_settings(self):
        """保存设置"""
        try:
            # 常规设置
            self.config_manager.set_download_path(self.download_path_input.text())
            self.config_manager.set_ffmpeg_path(self.ffmpeg_path_input.text())

            self.config_manager.set(
                "GENERAL",
                "auto_create_categories",
                str(self.auto_create_categories_cb.isChecked()).lower(),
            )
            self.config_manager.set(
                "GENERAL", "default_category", self.default_category_combo.currentText()
            )

            # 下载设置
            self.config_manager.set(
                "DOWNLOAD", "chunk_size", str(self.chunk_size_spin.value())
            )
            self.config_manager.set(
                "DOWNLOAD", "timeout", str(self.timeout_spin.value())
            )
            self.config_manager.set(
                "DOWNLOAD", "retry_count", str(self.retry_count_spin.value())
            )
            self.config_manager.set(
                "DOWNLOAD", "delay_between_requests", str(self.delay_spin.value())
            )
            self.config_manager.set(
                "GENERAL",
                "max_concurrent_downloads",
                str(self.max_concurrent_spin.value()),
            )

            # 界面设置
            theme_map = {"浅色": "light", "深色": "dark", "自动": "auto"}
            theme = theme_map.get(self.theme_combo.currentText(), "light")
            self.config_manager.set("UI", "theme", theme)

            lang_map = {"简体中文": "zh_CN", "English": "en_US"}
            language = lang_map.get(self.language_combo.currentText(), "zh_CN")
            self.config_manager.set("UI", "language", language)

            # 保存配置
            self.config_manager.save_config()

            QMessageBox.information(self, "成功", "设置保存成功！")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置失败: {str(e)}")

    def reset_to_default(self):
        """重置为默认设置"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要重置所有设置为默认值吗？\n此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 删除配置文件，重新创建默认配置
                if os.path.exists(self.config_manager.config_file):
                    os.remove(self.config_manager.config_file)

                # 重新加载配置管理器
                self.config_manager.load_config()

                # 重新加载设置
                self.load_settings()

                QMessageBox.information(self, "成功", "设置已重置为默认值！")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"重置设置失败: {str(e)}")

    def browse_download_path(self):
        """浏览下载路径"""
        path = QFileDialog.getExistingDirectory(
            self, "选择下载目录", self.download_path_input.text()
        )
        if path:
            self.download_path_input.setText(path)

    def browse_ffmpeg_path(self):
        """浏览FFmpeg路径"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择FFmpeg", "", "可执行文件 (*.exe);;所有文件 (*)"
        )
        if file_path:
            self.ffmpeg_path_input.setText(file_path)
            # 立即保存到配置文件
            self.config_manager.set_ffmpeg_path(file_path)
            self.check_ffmpeg_status()
            self.status_label.setText(f"FFmpeg路径已保存: {file_path}")

    def check_ffmpeg_status(self):
        """检查FFmpeg状态"""
        ffmpeg_path = self.ffmpeg_path_input.text()
        if not ffmpeg_path:
            self.ffmpeg_status_label.setText("未设置")
            self.ffmpeg_status_label.setStyleSheet("color: #666666;")
            return

        if os.path.exists(ffmpeg_path):
            self.ffmpeg_status_label.setText("已找到")
            self.ffmpeg_status_label.setStyleSheet("color: #28a745;")
        else:
            self.ffmpeg_status_label.setText("文件不存在")
            self.ffmpeg_status_label.setStyleSheet("color: #dc3545;")

    def toggle_proxy_settings(self, enabled):
        """切换代理设置启用状态"""
        self.proxy_host_input.setEnabled(enabled)
        self.proxy_port_input.setEnabled(enabled)

    def refresh_settings(self):
        """刷新设置"""
        self.load_settings()

    def set_quick_path(self, path_type: str):
        """设置快速路径"""
        import os
        from pathlib import Path

        if path_type == "desktop":
            path = str(Path.home() / "Desktop")
        elif path_type == "downloads":
            path = str(Path.home() / "Downloads")
        else:
            path = ""

        if path and os.path.exists(path):
            self.download_path_input.setText(path)
            self.status_label.setText(f"已设置路径: {path}")
        else:
            self.status_label.setText("路径不存在")

    def test_ffmpeg(self):
        """测试FFmpeg"""
        ffmpeg_path = self.ffmpeg_path_input.text()
        if not ffmpeg_path:
            self.status_label.setText("请先设置FFmpeg路径")
            return

        try:
            import subprocess

            result = subprocess.run(
                [ffmpeg_path, "-version"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                self.ffmpeg_status_label.setText("✅ 正常")
                self.ffmpeg_status_label.setStyleSheet(
                    "color: #28a745; font-weight: bold;"
                )
                self.status_label.setText("FFmpeg测试成功")
            else:
                self.ffmpeg_status_label.setText("❌ 异常")
                self.ffmpeg_status_label.setStyleSheet(
                    "color: #dc3545; font-weight: bold;"
                )
                self.status_label.setText("FFmpeg测试失败")
        except Exception as e:
            self.ffmpeg_status_label.setText("❌ 错误")
            self.ffmpeg_status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
            self.status_label.setText(f"FFmpeg测试出错: {str(e)}")
