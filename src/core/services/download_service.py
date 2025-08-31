"""
Download service for BiliDownload application.

This service provides download-related functionality including:
- Video information extraction
- Download task management
- Download progress tracking
- FFmpeg integration for media processing
"""

import os
from datetime import datetime
from typing import Callable, Dict, List, Optional

from src.core.managers.config_manager import ConfigManager
from src.core.managers.downloader import BiliDownloader
from src.core.managers.logger import get_logger


class DownloadTask:
    """
    Download task data model.

    Represents a download task with all its properties and state.
    """

    STATUS_PENDING = "pending"
    STATUS_ACTIVE = "active"
    STATUS_PAUSED = "paused"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    def __init__(
        self, task_id: str, url: str, title: str, save_path: str, download_type: str
    ):
        """
        Initialize a download task.

        Args:
            task_id (str): Unique task identifier
            url (str): Video URL to download
            title (str): Video title
            save_path (str): Path to save the downloaded file
            download_type (str): Type of download (full, video, audio)
        """
        self.id = task_id
        self.url = url
        self.title = title
        self.save_path = save_path
        self.download_type = download_type
        self.status = self.STATUS_PENDING
        self.progress = 0.0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.error = ""

        # 进度详情
        self.video_progress = 0.0
        self.audio_progress = 0.0
        self.merge_progress = 0.0

    def update_status(self, status: str):
        """更新任务状态"""
        self.status = status
        self.updated_at = datetime.now()

    def update_progress(self, progress: float):
        """更新任务进度"""
        self.progress = progress
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """转换为字典表示"""
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "save_path": self.save_path,
            "download_type": self.download_type,
            "status": self.status,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "error": self.error,
            "video_progress": self.video_progress,
            "audio_progress": self.audio_progress,
            "merge_progress": self.merge_progress,
        }


class DownloadService:
    """
    Service for managing video downloads.

    Provides high-level functionality for video downloads, abstracting
    the underlying downloader implementation and managing download tasks.
    """

    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the download service.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.downloader = BiliDownloader(config_manager)
        self.logger = get_logger(__name__)
        self.tasks: Dict[str, DownloadTask] = {}
        self.active_downloads = 0
        self.max_concurrent_downloads = config_manager.get_max_concurrent_downloads()

        # 回调函数
        self.progress_callbacks: List[Callable[[str, float, str], None]] = []
        self.video_progress_callbacks: List[Callable[[str, float], None]] = []
        self.audio_progress_callbacks: List[Callable[[str, float], None]] = []
        self.merge_progress_callbacks: List[Callable[[str, float], None]] = []
        self.status_callbacks: List[Callable[[str, str, str], None]] = []

    def register_progress_callback(self, callback: Callable[[str, float, str], None]):
        """
        注册进度回调函数

        Args:
            callback: 回调函数，接收参数(task_id, progress, message)
        """
        self.progress_callbacks.append(callback)

    def register_video_progress_callback(self, callback: Callable[[str, float], None]):
        """
        注册视频进度回调函数

        Args:
            callback: 回调函数，接收参数(task_id, progress)
        """
        self.video_progress_callbacks.append(callback)

    def register_audio_progress_callback(self, callback: Callable[[str, float], None]):
        """
        注册音频进度回调函数

        Args:
            callback: 回调函数，接收参数(task_id, progress)
        """
        self.audio_progress_callbacks.append(callback)

    def register_merge_progress_callback(self, callback: Callable[[str, float], None]):
        """
        注册合并进度回调函数

        Args:
            callback: 回调函数，接收参数(task_id, progress)
        """
        self.merge_progress_callbacks.append(callback)

    def register_status_callback(self, callback: Callable[[str, str, str], None]):
        """
        注册状态回调函数

        Args:
            callback: 回调函数，接收参数(task_id, status, message)
        """
        self.status_callbacks.append(callback)

    def create_task(
        self, url: str, title: str, save_path: str, download_type: str = "full"
    ) -> DownloadTask:
        """
        创建下载任务

        Args:
            url: 视频URL
            title: 视频标题
            save_path: 保存路径
            download_type: 下载类型（full, video, audio）

        Returns:
            创建的任务对象
        """
        # 生成任务ID
        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.tasks)}"

        # 创建任务
        task = DownloadTask(task_id, url, title, save_path, download_type)
        self.tasks[task_id] = task

        # 记录日志
        self.logger.info(f"创建任务: {task_id} - {title}")

        return task

    def start_task(self, task_id: str) -> bool:
        """
        启动下载任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功启动
        """
        if task_id not in self.tasks:
            self.logger.error(f"任务不存在: {task_id}")
            return False

        task = self.tasks[task_id]

        # 检查是否达到最大并发下载数
        if self.active_downloads >= self.max_concurrent_downloads:
            self.logger.warning(
                f"已达到最大并发下载数 ({self.max_concurrent_downloads})，"
                f"任务 {task_id} 将等待"
            )
            task.update_status(DownloadTask.STATUS_PENDING)
            self._notify_status(task_id, task.status, "等待下载槽位...")
            return False

        # 更新任务状态
        task.update_status(DownloadTask.STATUS_ACTIVE)
        self.active_downloads += 1

        # 通知状态变更
        self._notify_status(task_id, task.status, "开始下载...")

        # 启动下载线程
        self._download_task(task)

        return True

    def pause_task(self, task_id: str) -> bool:
        """
        暂停下载任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功暂停
        """
        if task_id not in self.tasks:
            self.logger.error(f"任务不存在: {task_id}")
            return False

        task = self.tasks[task_id]

        # 只有活动任务可以暂停
        if task.status != DownloadTask.STATUS_ACTIVE:
            self.logger.warning(f"任务 {task_id} 状态为 {task.status}，无法暂停")
            return False

        # 更新任务状态
        task.update_status(DownloadTask.STATUS_PAUSED)
        self.active_downloads -= 1

        # 通知状态变更
        self._notify_status(task_id, task.status, "已暂停")

        return True

    def cancel_task(self, task_id: str) -> bool:
        """
        取消下载任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        if task_id not in self.tasks:
            self.logger.error(f"任务不存在: {task_id}")
            return False

        task = self.tasks[task_id]

        # 如果任务正在下载，减少活动下载数
        if task.status == DownloadTask.STATUS_ACTIVE:
            self.active_downloads -= 1

        # 更新任务状态
        task.update_status(DownloadTask.STATUS_FAILED)
        task.error = "用户取消"

        # 通知状态变更
        self._notify_status(task_id, task.status, "已取消")

        return True

    def retry_task(self, task_id: str) -> bool:
        """
        重试下载任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功重试
        """
        if task_id not in self.tasks:
            self.logger.error(f"任务不存在: {task_id}")
            return False

        task = self.tasks[task_id]

        # 重置任务状态
        task.update_status(DownloadTask.STATUS_PENDING)
        task.progress = 0.0
        task.error = ""
        task.video_progress = 0.0
        task.audio_progress = 0.0
        task.merge_progress = 0.0

        # 通知状态变更
        self._notify_status(task_id, task.status, "准备重试...")

        # 启动任务
        return self.start_task(task_id)

    def remove_task(self, task_id: str) -> bool:
        """
        删除下载任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功删除
        """
        if task_id not in self.tasks:
            self.logger.error(f"任务不存在: {task_id}")
            return False

        task = self.tasks[task_id]

        # 如果任务正在下载，减少活动下载数
        if task.status == DownloadTask.STATUS_ACTIVE:
            self.active_downloads -= 1

        # 删除任务
        del self.tasks[task_id]

        # 记录日志
        self.logger.info(f"删除任务: {task_id}")

        return True

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """
        获取任务对象

        Args:
            task_id: 任务ID

        Returns:
            任务对象，如果不存在则返回None
        """
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[DownloadTask]:
        """
        获取所有任务

        Returns:
            任务列表
        """
        return list(self.tasks.values())

    def get_video_info(self, url: str) -> Dict[str, any]:
        """
        获取视频信息

        Args:
            url: 视频URL

        Returns:
            视频信息字典
        """
        return self.downloader.get_video_info(url)

    def get_tasks_by_status(self, status):
        """
        获取指定状态的任务
        
        Args:
            status: 任务状态
            
        Returns:
            dict: 符合条件的任务字典
        """
        return {k: v for k, v in self.tasks.items() if v.status == status}
        
    def get_active_tasks(self):
        """
        获取所有活动中的任务
        
        Returns:
            dict: 活动中的任务字典
        """
        return self.get_tasks_by_status(DownloadTask.STATUS_ACTIVE)

    def _download_task(self, task: DownloadTask):
        """
        执行下载任务

        Args:
            task: 下载任务对象
        """
        try:
            # 创建临时文件路径
            cache_dir = os.path.join(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                ),
                "cache",
            )
            os.makedirs(cache_dir, exist_ok=True)
            temp_base_name = os.path.join(cache_dir, task.id)

            # 创建最终保存目录
            final_path = os.path.join(
                task.save_path, self._sanitize_filename(task.title)
            )
            os.makedirs(os.path.dirname(final_path), exist_ok=True)

            # 记录日志
            self.logger.info(f"开始下载: {task.id}")
            self.logger.info(f"- URL: {task.url}")
            self.logger.info(f"- 临时文件路径: {temp_base_name}")
            self.logger.info(f"- 最终保存路径: {final_path}")
            self.logger.info(f"- 下载类型: {task.download_type}")

            # 设置进度回调
            def progress_callback(task_id, progress, message):
                task.update_progress(progress)
                self._notify_progress(task_id, progress, message)

            def video_progress_callback(task_id, progress):
                task.video_progress = progress
                self._notify_video_progress(task_id, progress)

            def audio_progress_callback(task_id, progress):
                task.audio_progress = progress
                self._notify_audio_progress(task_id, progress)

            def merge_progress_callback(task_id, progress):
                task.merge_progress = progress
                self._notify_merge_progress(task_id, progress)

            # 执行下载
            success = self.downloader.download_video(
                task.url,
                temp_base_name,
                self.config_manager.get_ffmpeg_path(),
                task.download_type,
                final_path=final_path,
            )

            # 清理临时文件
            video_temp = temp_base_name + ".video.tmp"
            audio_temp = temp_base_name + ".audio.tmp"
            for temp_file in [video_temp, audio_temp]:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                        self.logger.info(f"清理临时文件: {temp_file}")
                    except Exception as e:
                        self.logger.error(f"清理临时文件失败: {e}")

            # 更新任务状态
            if success:
                task.update_status(DownloadTask.STATUS_COMPLETED)
                task.update_progress(100.0)
                self._notify_status(task.id, task.status, "下载完成")
                self.logger.info(f"任务完成: {task.id}")
            else:
                task.update_status(DownloadTask.STATUS_FAILED)
                task.error = "下载失败"
                self._notify_status(task.id, task.status, "下载失败")
                self.logger.error(f"任务失败: {task.id}")

            # 减少活动下载数
            self.active_downloads -= 1

            # 检查是否有等待的任务可以启动
            self._check_pending_tasks()

        except Exception as e:
            # 处理异常
            task.update_status(DownloadTask.STATUS_FAILED)
            task.error = str(e)
            self._notify_status(task.id, task.status, f"错误: {str(e)}")
            self.logger.error(f"下载过程中发生错误: {e}")

            # 减少活动下载数
            self.active_downloads -= 1

            # 检查是否有等待的任务可以启动
            self._check_pending_tasks()

    def _check_pending_tasks(self):
        """检查是否有等待的任务可以启动"""
        if self.active_downloads >= self.max_concurrent_downloads:
            return

        # 查找等待中的任务
        for task_id, task in self.tasks.items():
            if task.status == DownloadTask.STATUS_PENDING:
                # 启动任务
                self.start_task(task_id)
                break

    def _notify_progress(self, task_id: str, progress: float, message: str):
        """通知进度更新"""
        for callback in self.progress_callbacks:
            try:
                callback(task_id, progress, message)
            except Exception as e:
                self.logger.error(f"进度回调异常: {e}")

    def _notify_video_progress(self, task_id: str, progress: float):
        """通知视频进度更新"""
        for callback in self.video_progress_callbacks:
            try:
                callback(task_id, progress)
            except Exception as e:
                self.logger.error(f"视频进度回调异常: {e}")

    def _notify_audio_progress(self, task_id: str, progress: float):
        """通知音频进度更新"""
        for callback in self.audio_progress_callbacks:
            try:
                callback(task_id, progress)
            except Exception as e:
                self.logger.error(f"音频进度回调异常: {e}")

    def _notify_merge_progress(self, task_id: str, progress: float):
        """通知合并进度更新"""
        for callback in self.merge_progress_callbacks:
            try:
                callback(task_id, progress)
            except Exception as e:
                self.logger.error(f"合并进度回调异常: {e}")

    def _notify_status(self, task_id: str, status: str, message: str):
        """通知状态更新"""
        for callback in self.status_callbacks:
            try:
                callback(task_id, status, message)
            except Exception as e:
                self.logger.error(f"状态回调异常: {e}")

    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除不合法字符

        Args:
            filename: 原始文件名

        Returns:
            清理后的文件名
        """
        import re

        # 替换Windows和Unix系统中不允许的文件名字符
        invalid_chars = r'[\\/*?:"<>|]'
        return re.sub(invalid_chars, "_", filename)
