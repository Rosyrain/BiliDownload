"""
Main application window for BiliDownload.

This module provides the primary application interface including:
- Main window layout and styling
- Top download-type bar and left sidebar (7-shaped structure)
- File management display linked with category tree
- Configuration panel entry points
"""

import os
import re
import sys

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
)
from qfluentwidgets import (
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    MessageBox,
    MSFluentWindow,
    NavigationItemPosition,
    Theme,
    isDarkTheme,
)

from src.core.managers.logger import Logger, get_logger
from src.ui.components import StatusBar
from src.ui.styles import style_manager

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
            from src.core.managers.downloader import BiliDownloader

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


class MainWindow(MSFluentWindow):
    """
    主窗口类

    使用QFluentWidgets的MSFluentWindow作为基类，实现现代化的UI界面
    """

    def __init__(
        self,
        config_manager,
        file_manager,
        download_service,
        file_service,
        category_service,
    ):
        """
        初始化主窗口

        Args:
            config_manager: 配置管理器
            file_manager: 文件管理器
            download_service: 下载服务
            file_service: 文件服务
            category_service: 分类服务
        """
        super().__init__()

        # 保存服务和管理器实例
        self.config_manager = config_manager
        self.logger = Logger(__name__)
        self.file_manager = file_manager
        self.download_service = download_service
        self.file_service = file_service
        self.category_service = category_service
        self.task_manager = TaskManager(self.config_manager)

        # 设置窗口属性
        self.setWindowTitle("BiliDownload - 哔哩哔哩下载工具")
        self.resize(1200, 800)

        # 初始化UI
        self._init_ui()

        # 连接信号
        self._connect_signals()

        # 应用样式
        self._apply_style()

    def _init_ui(self):
        """初始化UI"""
        # 创建状态栏
        self.status_bar = StatusBar(self)
        
        # 将状态栏添加到窗口底部
        # MSFluentWindow没有setStatusBar方法，所以我们使用其他方式添加状态栏
        # 这里我们可以将状态栏添加到主窗口的布局中
        # 获取窗口的布局
        layout = self.layout()
        if layout:
            layout.addWidget(self.status_bar)
        
        # 创建各个页面
        self.download_tab = DownloadTab(self.config_manager, self.task_manager, self)
        self.download_tab.setObjectName("downloadTab")
        
        self.task_list_tab = TaskListTab(
            self.task_manager, self.config_manager, self.file_manager, self
        )
        self.task_list_tab.setObjectName("taskListTab")
        
        self.file_manager_tab = FileManagerTab(
            self.config_manager, self.file_manager, self
        )
        self.file_manager_tab.setObjectName("fileManagerTab")
        
        self.settings_tab = SettingsTab(self.config_manager, self)
        self.settings_tab.setObjectName("settingsTab")

        # 添加导航项
        self.addSubInterface(self.download_tab, FluentIcon.DOWNLOAD, "下载")
        self.addSubInterface(self.task_list_tab, FluentIcon.VIEW, "任务列表")
        self.addSubInterface(self.file_manager_tab, FluentIcon.FOLDER, "文件管理")
        self.addSubInterface(
            self.settings_tab, FluentIcon.SETTING, "设置", position=1
        )

        # 设置初始界面
        self.navigationInterface.setCurrentItem(self.download_tab.objectName())

    def _connect_signals(self):
        """连接信号"""
        # 下载相关信号
        self.download_tab.download_requested.connect(self._handle_download_request)

        # 任务相关信号
        self.task_list_tab.task_action_requested.connect(self._handle_task_action)

        # 文件相关信号
        self.file_manager_tab.file_action_requested.connect(self._handle_file_action)

        # 设置相关信号
        self.settings_tab.settings_changed.connect(self._handle_settings_change)

        # 主题变更信号
        style_manager.themeChanged.connect(self._on_theme_changed)

    def _apply_style(self):
        """应用样式"""
        # 应用主题
        style_manager.set_theme(Theme.AUTO)

        # 设置字体
        font = style_manager.get_default_font()
        self.setFont(font)

    def _on_theme_changed(self, theme):
        """
        主题变更处理

        Args:
            theme: 新主题
        """
        # 更新状态栏
        self.status_bar.update_status(
            f"主题已切换: {'暗色' if isDarkTheme() else '亮色'}"
        )

    def _handle_download_request(self, url, title, save_path, download_type):
        """
        处理下载请求

        Args:
            url: 下载URL
            title: 视频标题
            save_path: 保存路径
            download_type: 下载类型
        """
        # 创建下载任务
        task = self.download_service.create_task(url, title, save_path, download_type)

        # 启动任务
        success = self.download_service.start_task(task.id)

        # 显示通知
        if success:
            InfoBar.success(
                title="下载任务已创建",
                content=f"开始下载: {title}",
                orient=InfoBarPosition.TOP_RIGHT,
                parent=self,
            )
        else:
            InfoBar.warning(
                title="下载任务已加入队列",
                content=f"任务将在其他下载完成后开始: {title}",
                orient=InfoBarPosition.TOP_RIGHT,
                parent=self,
            )

        # 更新任务列表
        self.task_list_tab.refresh_task_list()

    def _handle_task_action(self, task_id, action):
        """
        处理任务操作

        Args:
            task_id: 任务ID
            action: 操作类型
        """
        # 根据操作类型处理
        if action == "start":
            self.download_service.start_task(task_id)
        elif action == "pause":
            self.download_service.pause_task(task_id)
        elif action == "resume":
            self.download_service.resume_task(task_id)
        elif action == "cancel":
            self.download_service.cancel_task(task_id)
        elif action == "remove":
            self.download_service.remove_task(task_id)

        # 更新任务列表
        self.task_list_tab.refresh_task_list()

    def _handle_file_action(self, action, path):
        """
        处理文件操作
        
        Args:
            action: 操作类型
            path: 文件路径
        """
        # 根据操作类型处理
        if action == "delete":
            # 确认删除
            confirm = MessageBox(
                "确认删除",
                f"确定要删除 {os.path.basename(path)} 吗？\n此操作不可恢复！",
                self,
            )
            if confirm.exec():
                self.file_service.delete_file(path)

        # 更新文件列表
        self.file_manager_tab.refresh_file_list()

    def _handle_settings_change(self, section, key, value):
        """
        处理设置变更

        Args:
            section: 设置区域
            key: 设置键
            value: 设置值
        """
        # 保存设置
        self.config_manager.set(section, key, value)

        # 更新状态
        if section == "GENERAL" and key == "ffmpeg_path":
            ffmpeg_available = os.path.exists(value) and os.access(value, os.X_OK)
            self.status_bar.update_ffmpeg_status(ffmpeg_available)

        # 显示通知
        InfoBar.success(
            title="设置已保存",
            content=f"{section}.{key} 已更新",
            orient=InfoBarPosition.TOP_RIGHT,
            parent=self,
        )

    def closeEvent(self, event):
        """
        窗口关闭事件

        Args:
            event: 关闭事件
        """
        # 检查是否有活动任务
        active_tasks = self.download_service.get_active_tasks()
        if active_tasks:
            # 询问用户是否确认退出
            confirm = MessageBox(
                "确认退出",
                f"有 {len(active_tasks)} 个下载任务正在进行中，确定要退出吗?",
                self,
            )
            if not confirm.exec():
                event.ignore()
                return

        # 保存配置
        self.config_manager.save()

        # 接受关闭事件
        event.accept()


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
