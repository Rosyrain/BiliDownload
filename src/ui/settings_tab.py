"""
设置标签页
"""

import os
import re
import subprocess

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    ComboBox,
    ExpandLayout,
    ExpandSettingCard,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    SettingCard,
    SettingCardGroup,
    SpinBox,
    SubtitleLabel,
    SwitchButton,
)

from src.core.managers.logger import get_logger


class SettingsTab(QWidget):
    """
    设置标签页，用于管理应用程序设置

    Attributes:
        config_manager (ConfigManager): 配置管理器
        logger: 日志记录器
    """

    # 定义信号
    settings_changed = pyqtSignal(str, str, str)  # 区域, 键, 值

    def __init__(self, config_manager, parent=None):
        """
        初始化设置标签页

        Args:
            config_manager: 配置管理器实例
            parent: 父组件
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = get_logger(__name__)

        # 初始化UI
        self._init_ui()

        # 加载设置
        self.load_settings()

    def _init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 标题
        title_label = SubtitleLabel("设置", self)
        title_label.setObjectName("SettingsTitle")
        main_layout.addWidget(title_label)

        # 创建滚动区域
        scroll_area = ScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget(scroll_area)
        scroll_layout = ExpandLayout(scroll_widget)
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        # 创建设置组
        self._create_general_settings(scroll_layout)
        self._create_download_settings(scroll_layout)
        self._create_ui_settings(scroll_layout)

        # 创建按钮区域
        self._create_button_area(main_layout)

    def _create_general_settings(self, parent_layout):
        """创建常规设置"""
        general_group = SettingCardGroup("常规设置", self)

        # 下载路径
        self.download_path_card = ExpandSettingCard(
            FluentIcon.DOWNLOAD, "下载路径", "设置视频下载的默认保存位置", self
        )
        
        # 创建内容布局
        content_layout = QHBoxLayout()
        self.download_path_input = LineEdit(self)
        self.download_path_input.setReadOnly(True)
        content_layout.addWidget(self.download_path_input, 1)
        
        browse_button = PushButton("浏览", self)
        browse_button.clicked.connect(self.browse_download_path)
        content_layout.addWidget(browse_button, 0)
        
        # 添加内容布局到卡片
        self.download_path_card.addWidget(self.download_path_input)
        self.download_path_card.addWidget(browse_button)
        
        general_group.addSettingCard(self.download_path_card)

        # FFmpeg路径
        self.ffmpeg_path_card = SettingCard(
            FluentIcon.MOVIE, "FFmpeg路径", "设置FFmpeg可执行文件的路径，用于视频处理", self
        )

        ffmpeg_layout = QHBoxLayout()
        ffmpeg_layout.setContentsMargins(0, 0, 0, 0)
        ffmpeg_layout.setSpacing(10)

        self.ffmpeg_path_input = LineEdit(self)
        self.ffmpeg_path_input.setReadOnly(True)
        ffmpeg_layout.addWidget(self.ffmpeg_path_input, 1)

        self.browse_ffmpeg_button = PushButton("浏览", self)
        self.browse_ffmpeg_button.clicked.connect(self.browse_ffmpeg_path)
        ffmpeg_layout.addWidget(self.browse_ffmpeg_button)

        self.ffmpeg_status_label = QLabel(self)
        ffmpeg_layout.addWidget(self.ffmpeg_status_label)

        self.ffmpeg_path_card.setLayout(ffmpeg_layout)
        general_group.addSettingCard(self.ffmpeg_path_card)

        # 添加到父布局
        parent_layout.addWidget(general_group)

    def _create_download_settings(self, parent_layout):
        """创建下载设置"""
        # 下载设置组
        download_group = SettingCardGroup("下载设置", self)

        # 最大并发下载数
        self.max_concurrent_card = SettingCard(
            FluentIcon.DOWNLOAD, "最大并发下载数", "同时进行的最大下载任务数", self
        )

        max_concurrent_layout = QHBoxLayout()
        max_concurrent_layout.setContentsMargins(0, 0, 0, 0)
        max_concurrent_layout.setSpacing(10)

        self.max_concurrent_spin = SpinBox(self)
        self.max_concurrent_spin.setRange(1, 10)
        self.max_concurrent_spin.setValue(3)
        max_concurrent_layout.addWidget(self.max_concurrent_spin)

        max_concurrent_layout.addStretch(1)

        self.max_concurrent_card.setLayout(max_concurrent_layout)
        download_group.addSettingCard(self.max_concurrent_card)

        # 默认下载类型
        self.default_download_type_card = SettingCard(
            FluentIcon.VIDEO, "默认下载类型", "设置默认的视频下载类型", self
        )

        download_type_layout = QHBoxLayout()
        download_type_layout.setContentsMargins(0, 0, 0, 0)
        download_type_layout.setSpacing(10)

        self.default_download_type_combo = ComboBox(self)
        self.default_download_type_combo.addItem("完整视频 (视频+音频)", "full")
        self.default_download_type_combo.addItem("仅视频 (无音频)", "video")
        self.default_download_type_combo.addItem("仅音频 (MP3)", "audio")
        download_type_layout.addWidget(self.default_download_type_combo)

        download_type_layout.addStretch(1)

        self.default_download_type_card.setLayout(download_type_layout)
        download_group.addSettingCard(self.default_download_type_card)

        # 自动开始下载
        self.auto_start_card = SettingCard(
            FluentIcon.PLAY, "自动开始下载", "添加任务后自动开始下载", self
        )

        auto_start_layout = QHBoxLayout()
        auto_start_layout.setContentsMargins(0, 0, 0, 0)
        auto_start_layout.setSpacing(10)

        self.auto_start_switch = SwitchButton(self)
        auto_start_layout.addWidget(self.auto_start_switch)

        auto_start_layout.addStretch(1)

        self.auto_start_card.setLayout(auto_start_layout)
        download_group.addSettingCard(self.auto_start_card)

        # 添加到父布局
        parent_layout.addWidget(download_group)

    def _create_ui_settings(self, parent_layout):
        """创建界面设置"""
        # 界面设置组
        ui_group = SettingCardGroup("界面设置", self)

        # 主题
        self.theme_card = SettingCard(
            FluentIcon.BRUSH, "主题", "设置应用程序的显示主题", self
        )

        theme_layout = QHBoxLayout()
        theme_layout.setContentsMargins(0, 0, 0, 0)
        theme_layout.setSpacing(10)

        self.theme_combo = ComboBox(self)
        self.theme_combo.addItem("跟随系统", "auto")
        self.theme_combo.addItem("亮色", "light")
        self.theme_combo.addItem("暗色", "dark")
        theme_layout.addWidget(self.theme_combo)

        theme_layout.addStretch(1)

        self.theme_card.setLayout(theme_layout)
        ui_group.addSettingCard(self.theme_card)

        # 显示通知
        self.show_notification_card = SettingCard(
            FluentIcon.CHAT, "显示通知", "显示下载完成等操作的通知", self
        )

        notification_layout = QHBoxLayout()
        notification_layout.setContentsMargins(0, 0, 0, 0)
        notification_layout.setSpacing(10)

        self.show_notification_switch = SwitchButton(self)
        notification_layout.addWidget(self.show_notification_switch)

        notification_layout.addStretch(1)

        self.show_notification_card.setLayout(notification_layout)
        ui_group.addSettingCard(self.show_notification_card)

        # 添加到父布局
        parent_layout.addWidget(ui_group)

    def _create_button_area(self, parent_layout):
        """创建按钮区域"""
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(10)

        button_layout.addStretch(1)

        # 保存按钮
        self.save_button = PrimaryPushButton("保存设置", self)
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)

        # 重置按钮
        self.reset_button = PushButton("重置为默认", self)
        self.reset_button.clicked.connect(self.reset_to_default)
        button_layout.addWidget(self.reset_button)

        parent_layout.addLayout(button_layout)

    def load_settings(self):
        """加载设置"""
        try:
            # 常规设置
            download_path = self.config_manager.get_download_path()
            self.download_path_input.setText(download_path)

            ffmpeg_path = self.config_manager.get_ffmpeg_path()
            self.ffmpeg_path_input.setText(ffmpeg_path)
            self.check_ffmpeg_status()

            # 下载设置
            max_concurrent = self.config_manager.get("DOWNLOAD", "max_concurrent", "3")
            self.max_concurrent_spin.setValue(int(max_concurrent))

            default_download_type = self.config_manager.get(
                "DOWNLOAD", "default_type", "full"
            )
            index = self.default_download_type_combo.findData(default_download_type)
            if index >= 0:
                self.default_download_type_combo.setCurrentIndex(index)

            auto_start = (
                self.config_manager.get("DOWNLOAD", "auto_start", "false").lower()
                == "true"
            )
            self.auto_start_switch.setChecked(auto_start)

            # 界面设置
            theme = self.config_manager.get("UI", "theme", "auto")
            index = self.theme_combo.findData(theme)
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)

            show_notification = (
                self.config_manager.get("UI", "show_notification", "true").lower()
                == "true"
            )
            self.show_notification_switch.setChecked(show_notification)

        except Exception as e:
            self.logger.error(f"加载设置失败: {e}")
            InfoBar.error(
                title="错误",
                content=f"加载设置失败: {e}",
                orient=InfoBarPosition.TOP,
                parent=self,
            )

    def save_settings(self):
        """保存设置"""
        try:
            # 常规设置
            download_path = self.download_path_input.text()
            self.config_manager.set("GENERAL", "download_path", download_path)

            ffmpeg_path = self.ffmpeg_path_input.text()
            self.config_manager.set("GENERAL", "ffmpeg_path", ffmpeg_path)

            # 下载设置
            max_concurrent = str(self.max_concurrent_spin.value())
            self.config_manager.set("DOWNLOAD", "max_concurrent", max_concurrent)

            default_download_type = self.default_download_type_combo.currentData()
            self.config_manager.set("DOWNLOAD", "default_download_type", default_download_type)

            auto_start = "1" if self.auto_start_switch.isChecked() else "0"
            self.config_manager.set("DOWNLOAD", "auto_start", auto_start)

            # 界面设置
            theme = self.theme_combo.currentData()
            self.config_manager.set("UI", "theme", theme)

            show_notification = "1" if self.show_notification_switch.isChecked() else "0"
            self.config_manager.set("UI", "show_notification", show_notification)

            # 保存配置
            self.config_manager.save()

            # 显示成功消息
            InfoBar.success(
                "保存成功",
                "设置已保存",
                duration=3000,
                parent=self,
                position=InfoBarPosition.TOP,
            )

            # 发送设置变更信号
            self.settings_changed.emit("ALL", "ALL", "ALL")

        except Exception as e:
            self.logger.error(f"保存设置失败: {e}")
            InfoBar.error(
                "保存失败",
                f"保存设置时发生错误: {e}",
                duration=3000,
                parent=self,
                position=InfoBarPosition.TOP,
            )

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
        current_path = self.download_path_input.text()
        directory = QFileDialog.getExistingDirectory(self, "选择下载目录", current_path)
        if directory:
            self.download_path_input.setText(directory)

    def browse_ffmpeg_path(self):
        """浏览FFmpeg路径"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择FFmpeg", "", "可执行文件 (*.exe);;所有文件 (*)"
        )
        if file_path:
            self.ffmpeg_path_input.setText(file_path)
            # 更新UI状态但不立即保存到配置文件
            self.check_ffmpeg_status()
            self.status_label.setText(
                f"FFmpeg路径已选择: {file_path}，点击保存按钮生效"
            )

    def check_ffmpeg_status(self):
        """检查FFmpeg状态"""
        ffmpeg_path = self.ffmpeg_path_input.text()
        if not ffmpeg_path:
            self.ffmpeg_status_label.setText("❌ 未设置")
            self.ffmpeg_status_label.setStyleSheet("color: red;")
            return False

        try:
            self.logger.info(f"验证FFmpeg路径: {ffmpeg_path}")
            # 检查文件是否存在
            if not os.path.exists(ffmpeg_path):
                self.ffmpeg_status_label.setText("❌ 文件不存在")
                self.ffmpeg_status_label.setStyleSheet("color: red;")
                return False

            # 检查文件是否可执行
            if not os.access(ffmpeg_path, os.X_OK):
                self.ffmpeg_status_label.setText("❌ 文件不可执行")
                self.ffmpeg_status_label.setStyleSheet("color: red;")
                return False

            # 尝试运行FFmpeg命令
            result = subprocess.run(
                [ffmpeg_path, "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                # 提取版本信息
                version_info = result.stdout.split("\n")[0]
                self.ffmpeg_status_label.setText(f"✅ 可用")
                self.ffmpeg_status_label.setStyleSheet("color: green;")
                return True
            else:
                self.ffmpeg_status_label.setText("❌ 验证失败")
                self.ffmpeg_status_label.setStyleSheet("color: red;")
                return False

        except Exception as e:
            self.logger.error(f"验证FFmpeg失败: {e}")
            self.ffmpeg_status_label.setText(f"❌ 错误: {str(e)[:20]}...")
            self.ffmpeg_status_label.setStyleSheet("color: red;")
            return False
