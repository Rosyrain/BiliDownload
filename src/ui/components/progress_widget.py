"""
进度条组件，用于显示下载进度
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qfluentwidgets import InfoBadge, ProgressBar


class ProgressWidget(QWidget):
    """进度条组件，用于显示下载进度"""

    # 取消信号
    cancelClicked = pyqtSignal(str)  # 参数为任务ID

    # 状态枚举
    STATUS_ACTIVE = "active"
    STATUS_PAUSED = "paused"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_PENDING = "pending"

    def __init__(self, task_id, title, parent=None):
        """
        初始化进度条组件

        Args:
            task_id: 任务ID
            title: 任务标题
            parent: 父组件
        """
        super().__init__(parent)
        self.task_id = task_id
        self.title = title
        self.status = self.STATUS_PENDING
        self._progress = 0
        self._video_progress = 0
        self._audio_progress = 0
        self._merge_progress = 0

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        # 标题和状态
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        # 标题
        self.title_label = QLabel(self.title, self)
        self.title_label.setObjectName("ProgressTitle")
        header_layout.addWidget(self.title_label)

        # 状态
        header_layout.addStretch(1)

        self.status_badge = InfoBadge(self.status, self)
        header_layout.addWidget(self.status_badge)

        main_layout.addLayout(header_layout)

        # 进度条组
        progress_group = QGroupBox("下载进度", self)
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setContentsMargins(10, 15, 10, 10)
        progress_layout.setSpacing(10)

        # 总进度
        total_layout = QHBoxLayout()
        total_layout.setContentsMargins(0, 0, 0, 0)
        total_layout.setSpacing(10)

        total_label = QLabel("总进度:", self)
        total_layout.addWidget(total_label)

        self.total_progress_bar = ProgressBar(self)
        self.total_progress_bar.setRange(0, 100)
        self.total_progress_bar.setValue(0)
        total_layout.addWidget(self.total_progress_bar)

        self.total_percent_label = QLabel("0%", self)
        total_layout.addWidget(self.total_percent_label)

        progress_layout.addLayout(total_layout)

        # 视频进度
        video_layout = QHBoxLayout()
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.setSpacing(10)

        video_label = QLabel("视频:", self)
        video_layout.addWidget(video_label)

        self.video_progress_bar = ProgressBar(self)
        self.video_progress_bar.setRange(0, 100)
        self.video_progress_bar.setValue(0)
        video_layout.addWidget(self.video_progress_bar)

        self.video_percent_label = QLabel("0%", self)
        video_layout.addWidget(self.video_percent_label)

        progress_layout.addLayout(video_layout)

        # 音频进度
        audio_layout = QHBoxLayout()
        audio_layout.setContentsMargins(0, 0, 0, 0)
        audio_layout.setSpacing(10)

        audio_label = QLabel("音频:", self)
        audio_layout.addWidget(audio_label)

        self.audio_progress_bar = ProgressBar(self)
        self.audio_progress_bar.setRange(0, 100)
        self.audio_progress_bar.setValue(0)
        audio_layout.addWidget(self.audio_progress_bar)

        self.audio_percent_label = QLabel("0%", self)
        audio_layout.addWidget(self.audio_percent_label)

        progress_layout.addLayout(audio_layout)

        # 合并进度
        merge_layout = QHBoxLayout()
        merge_layout.setContentsMargins(0, 0, 0, 0)
        merge_layout.setSpacing(10)

        merge_label = QLabel("合并:", self)
        merge_layout.addWidget(merge_label)

        self.merge_progress_bar = ProgressBar(self)
        self.merge_progress_bar.setRange(0, 100)
        self.merge_progress_bar.setValue(0)
        merge_layout.addWidget(self.merge_progress_bar)

        self.merge_percent_label = QLabel("0%", self)
        merge_layout.addWidget(self.merge_percent_label)

        progress_layout.addLayout(merge_layout)

        main_layout.addWidget(progress_group)

    def _on_cancel_clicked(self):
        """取消按钮点击事件"""
        self.cancelClicked.emit(self.task_id)

    def update_progress(self, progress):
        """
        更新总体进度

        Args:
            progress: 进度值(0-100)
        """
        self._progress = progress
        self.total_progress_bar.setValue(int(progress))
        self.total_percent_label.setText(f"{int(progress)}%")

    def update_video_progress(self, progress):
        """
        更新视频进度

        Args:
            progress: 进度值(0-100)
        """
        self._video_progress = progress
        self.video_progress_bar.setValue(int(progress))
        self.video_percent_label.setText(f"{int(progress)}%")

    def update_audio_progress(self, progress):
        """
        更新音频进度

        Args:
            progress: 进度值(0-100)
        """
        self._audio_progress = progress
        self.audio_progress_bar.setValue(int(progress))
        self.audio_percent_label.setText(f"{int(progress)}%")

    def update_merge_progress(self, progress):
        """
        更新合并进度

        Args:
            progress: 进度值(0-100)
        """
        self._merge_progress = progress
        self.merge_progress_bar.setValue(int(progress))
        self.merge_percent_label.setText(f"{int(progress)}%")

    def update_status(self, status):
        """
        更新状态

        Args:
            status: 状态值
        """
        self.status = status

        # 更新状态徽章
        if status == self.STATUS_ACTIVE:
            self.status_badge.setText("下载中")
            self.status_badge.setCustomBackgroundColor("#0078D4")
        elif status == self.STATUS_PAUSED:
            self.status_badge.setText("已暂停")
            self.status_badge.setCustomBackgroundColor("#F7630C")
        elif status == self.STATUS_COMPLETED:
            self.status_badge.setText("已完成")
            self.status_badge.setCustomBackgroundColor("#107C10")
        elif status == self.STATUS_FAILED:
            self.status_badge.setText("已失败")
            self.status_badge.setCustomBackgroundColor("#E81123")
        elif status == self.STATUS_PENDING:
            self.status_badge.setText("等待中")
            self.status_badge.setCustomBackgroundColor("#767676")
