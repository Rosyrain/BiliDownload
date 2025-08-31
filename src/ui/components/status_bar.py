"""
状态栏组件，用于显示应用状态信息
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget


class StatusBar(QWidget):
    """状态栏组件，用于显示应用状态信息"""

    def __init__(self, parent=None):
        """
        初始化状态栏组件

        Args:
            parent: 父组件
        """
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 3, 10, 3)
        main_layout.setSpacing(10)

        # 状态标签
        self.status_label = QLabel("就绪", self)
        self.status_label.setObjectName("StatusLabel")
        main_layout.addWidget(self.status_label)

        # 添加弹性空间
        main_layout.addStretch(1)

        # 下载计数
        self.download_count_label = QLabel("下载: 0", self)
        self.download_count_label.setObjectName("CountLabel")
        main_layout.addWidget(self.download_count_label)

        # 文件计数
        self.file_count_label = QLabel("文件: 0", self)
        self.file_count_label.setObjectName("CountLabel")
        main_layout.addWidget(self.file_count_label)

        # FFmpeg状态
        self.ffmpeg_status_label = QLabel("FFmpeg: 检查中...", self)
        self.ffmpeg_status_label.setObjectName("FFmpegLabel")
        main_layout.addWidget(self.ffmpeg_status_label)

        # 设置固定高度
        self.setFixedHeight(28)

    def update_status(self, text):
        """
        更新状态文本

        Args:
            text: 状态文本
        """
        self.status_label.setText(text)

    def update_download_count(self, count):
        """
        更新下载任务数

        Args:
            count: 任务数
        """
        self.download_count_label.setText(f"下载: {count}")

    def update_file_count(self, count):
        """
        更新文件数

        Args:
            count: 文件数
        """
        self.file_count_label.setText(f"文件: {count}")

    def update_ffmpeg_status(self, available):
        """
        更新FFmpeg状态

        Args:
            available: 是否可用
        """
        if available:
            self.ffmpeg_status_label.setText("FFmpeg: ✅ 可用")
            self.ffmpeg_status_label.setStyleSheet("color: green;")
        else:
            self.ffmpeg_status_label.setText("FFmpeg: ❌ 未配置")
            self.ffmpeg_status_label.setStyleSheet("color: red;")
