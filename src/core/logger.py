"""
Centralized logging system for BiliDownload application.

This module provides comprehensive logging functionality including:
- Console and file logging
- Log rotation and retention
- Specialized log types (download, error, general)
- Structured logging methods
"""

import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path


class Logger:
    """
    Centralized logging manager for BiliDownload application.

    Provides multiple logging handlers for different purposes:
    - Console output for immediate feedback
    - Rotating file logs for persistence
    - Specialized handlers for different log types
    """

    def __init__(self, name="BiliDownload"):
        """
        Initialize the logger with multiple handlers.

        Args:
            name (str): Logger name identifier
        """
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Avoid adding handlers multiple times
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self, name="BiliDownload"):
        """
        Set up logging handlers for different output destinations.

        Configures console handler, general log file, error log file,
        and download-specific log file with appropriate formatting.
        """
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler - General logs
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        general_handler = RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        general_handler.setLevel(logging.INFO)
        general_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        general_handler.setFormatter(general_formatter)
        self.logger.addHandler(general_handler)

        # File handler - Error logs
        error_handler = RotatingFileHandler(
            log_dir / "error.log",
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"  # noqa: E501
        )
        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)

        # File handler - Download logs
        download_handler = RotatingFileHandler(
            log_dir / "download.log",
            maxBytes=20 * 1024 * 1024,  # 20MB
            backupCount=10,
            encoding="utf-8",
        )
        download_handler.setLevel(logging.INFO)
        download_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        download_handler.setFormatter(download_formatter)
        self.logger.addHandler(download_handler)

        # 新增：下载详细信息日志
        today = datetime.now().strftime("%Y%m%d")
        download_detail_handler = RotatingFileHandler(
            log_dir / f"download_detail_{today}.log",
            maxBytes=20 * 1024 * 1024,  # 20MB
            backupCount=10,
            encoding="utf-8",
        )
        download_detail_handler.setLevel(logging.INFO)
        download_detail_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        download_detail_handler.setFormatter(download_detail_formatter)

        # 创建专门的下载详细日志记录器
        self.download_detail_logger = logging.getLogger(f"{name}.download_detail")
        self.download_detail_logger.setLevel(logging.INFO)
        self.download_detail_logger.addHandler(download_detail_handler)
        self.download_detail_logger.propagate = False  # 不向父级记录器传播日志

    def info(self, message, task_id=None, task_title=None):
        """
        Log information message.

        Args:
            message (str): Information message to log
            task_id (str, optional): Task ID for identification
            task_title (str, optional): Task title for identification
        """
        # 构建任务前缀
        task_prefix = self._build_task_prefix(task_id, task_title)
        # 直接使用原始的logger方法，不传递额外参数
        if task_prefix:
            self.logger.info(f"{task_prefix}{message}")
        else:
            self.logger.info(message)

    def warning(self, message, task_id=None, task_title=None):
        """
        Log warning message.

        Args:
            message (str): Warning message to log
            task_id (str, optional): Task ID for identification
            task_title (str, optional): Task title for identification
        """
        # 构建任务前缀
        task_prefix = self._build_task_prefix(task_id, task_title)
        # 直接使用原始的logger方法，不传递额外参数
        if task_prefix:
            self.logger.warning(f"{task_prefix}{message}")
        else:
            self.logger.warning(message)

    def error(self, message, task_id=None, task_title=None):
        """
        Log error message.

        Args:
            message (str): Error message to log
            task_id (str, optional): Task ID for identification
            task_title (str, optional): Task title for identification
        """
        # 构建任务前缀
        task_prefix = self._build_task_prefix(task_id, task_title)
        # 直接使用原始的logger方法，不传递额外参数
        if task_prefix:
            self.logger.error(f"{task_prefix}{message}")
        else:
            self.logger.error(message)

    def debug(self, message, task_id=None, task_title=None):
        """
        Log debug message.

        Args:
            message (str): Debug message to log
            task_id (str, optional): Task ID for identification
            task_title (str, optional): Task title for identification
        """
        # 构建任务前缀
        task_prefix = self._build_task_prefix(task_id, task_title)
        # 直接使用原始的logger方法，不传递额外参数
        if task_prefix:
            self.logger.debug(f"{task_prefix}{message}")
        else:
            self.logger.debug(message)

    def critical(self, message, task_id=None, task_title=None):
        """
        Log critical error message.

        Args:
            message (str): Critical error message to log
            task_id (str, optional): Task ID for identification
            task_title (str, optional): Task title for identification
        """
        # 构建任务前缀
        task_prefix = self._build_task_prefix(task_id, task_title)
        # 直接使用原始的logger方法，不传递额外参数
        if task_prefix:
            self.logger.critical(f"{task_prefix}{message}")
        else:
            self.logger.critical(message)

    def _build_task_prefix(self, task_id=None, task_title=None):
        """
        构建任务前缀

        Args:
            task_id (str, optional): 任务ID
            task_title (str, optional): 任务标题

        Returns:
            str: 格式化的任务前缀
        """
        task_prefix = ""
        if task_title:
            # 如果标题太长，截断显示
            if len(task_title) > 20:
                task_prefix = f"[{task_title[:18]}..] "
            else:
                task_prefix = f"[{task_title}] "
        elif task_id:
            task_prefix = f"[{task_id}] "
        return task_prefix

    def log_download_info(self, message, task_id=None, task_title=None):
        """
        Log download-specific information.

        Uses specialized download log handler for better organization.

        Args:
            message (str): Download information message to log
            task_id (str, optional): Task ID for identification
            task_title (str, optional): Task title for identification
        """
        # 构建任务前缀
        task_prefix = self._build_task_prefix(task_id, task_title)
        # Use specialized download log handler
        self.logger.info(message, extra={"task_prefix": task_prefix})

    def log_exception(self, message, exc_info=True, task_id=None, task_title=None):
        """
        Log exception information with traceback.

        Args:
            message (str): Exception message to log
            exc_info (bool): Whether to include exception traceback
            task_id (str, optional): Task ID for identification
            task_title (str, optional): Task title for identification
        """
        # 构建任务前缀
        task_prefix = self._build_task_prefix(task_id, task_title)
        self.logger.exception(
            message, exc_info=exc_info, extra={"task_prefix": task_prefix}
        )

    def log_download_progress(self, message, task_id=None, task_title=None):
        """
        Log download progress information.

        Args:
            message (str): Download progress message to log
            task_id (str, optional): Task ID for identification
            task_title (str, optional): Task title for identification
        """
        # 构建任务前缀
        task_prefix = self._build_task_prefix(task_id, task_title)
        self.logger.info(message, extra={"task_prefix": task_prefix})

    def log_download_start(self, message, task_id=None, task_title=None):
        """
        Log download start event.

        Args:
            message (str): Download start message to log
            task_id (str, optional): Task ID for identification
            task_title (str, optional): Task title for identification
        """
        # 构建任务前缀
        task_prefix = self._build_task_prefix(task_id, task_title)
        self.logger.info(message, extra={"task_prefix": task_prefix})

    def log_download_complete(self, message, task_id=None, task_title=None):
        """
        Log download completion event.

        Args:
            message (str): Download completion message to log
            task_id (str, optional): Task ID for identification
            task_title (str, optional): Task title for identification
        """
        # 构建任务前缀
        task_prefix = self._build_task_prefix(task_id, task_title)
        self.logger.info(message, extra={"task_prefix": task_prefix})

    def log_download_detail(self, event_type, message="", **kwargs):
        """
        记录下载详细信息到专用日志文件。

        Args:
            event_type (str): 事件类型，如'title', 'video', 'audio', 'ffmpeg'
            message (str): 日志消息
            **kwargs: 附加信息，如URL、路径等

        Returns:
            str: 格式化后的日志消息，用于UI显示
        """
        # 提取任务标识信息
        task_id = kwargs.get("task_id", "")
        task_title = kwargs.get("task_title", "")

        # 构建任务前缀
        task_prefix = self._build_task_prefix(task_id, task_title)

        # 根据事件类型构建格式化的消息
        if event_type == "title":
            success = kwargs.get("success", False)
            title = kwargs.get("title", "未知")
            formatted_msg = f"标题获取{'成功' if success else '失败'} -- {title}"

        elif event_type == "video":
            success = kwargs.get("success", False)
            url = kwargs.get("url", "未知")
            # 添加视频标题信息
            title_info = ""
            if "title" in kwargs and kwargs["title"]:
                title = kwargs["title"]
                if len(title) > 20:
                    title_info = f" - {title[:18]}.."
                else:
                    title_info = f" - {title}"
            formatted_msg = (
                f"无声视频下载{'成功' if success else '失败'}{title_info} -- {url}"
            )

        elif event_type == "audio":
            success = kwargs.get("success", False)
            url = kwargs.get("url", "未知")
            # 添加视频标题信息
            title_info = ""
            if "title" in kwargs and kwargs["title"]:
                title = kwargs["title"]
                if len(title) > 20:
                    title_info = f" - {title[:18]}.."
                else:
                    title_info = f" - {title}"
            formatted_msg = (
                f"音频下载{'成功' if success else '失败'}{title_info} -- {url}"
            )

        elif event_type == "ffmpeg":
            success = kwargs.get("success", False)
            path = kwargs.get("path", "未知")
            ffmpeg_path = kwargs.get("ffmpeg_path", "")

            if success:
                formatted_msg = f"FFmpeg合并成功 -- {path}"
            else:
                formatted_msg = f"FFmpeg合并失败 -- {path} -- FFmpeg路径: {ffmpeg_path}"

        else:
            formatted_msg = message

        # 记录到专用日志
        if kwargs.get("success", False):
            if task_prefix:
                self.download_detail_logger.info(f"{task_prefix}{formatted_msg}")
            else:
                self.download_detail_logger.info(formatted_msg)
        else:
            if task_prefix:
                self.download_detail_logger.error(f"{task_prefix}{formatted_msg}")
            else:
                self.download_detail_logger.error(formatted_msg)

        # 同时记录到常规日志
        if task_prefix:
            self.logger.info(f"{task_prefix}{formatted_msg}")
        else:
            self.logger.info(formatted_msg)

        # 返回格式化后的消息，以便在UI中显示
        return formatted_msg

    def log_config_change(self, section, key, value):
        """
        Log configuration change event.

        Args:
            section (str): Configuration section name
            key (str): Configuration key name
            value (str): New configuration value
        """
        self.logger.info(f"Configuration changed: [{section}] {key} = {value}")

    def log_category_operation(self, operation, category_name, details=""):
        """
        Log category management operation.

        Args:
            operation (str): Operation type (add, remove, etc.)
            category_name (str): Name of the category
            details (str, optional): Additional operation details
        """
        message = f"Category {operation}: {category_name}"
        if details:
            message += f" - {details}"
        self.logger.info(message)

    def log_file_operation(self, operation, file_path, details=""):
        """
        Log file system operation.

        Args:
            operation (str): Operation type (create, delete, move, etc.)
            file_path (str): Path of the file or directory
            details (str, optional): Additional operation details
        """
        message = f"File {operation}: {file_path}"
        if details:
            message += f" - {details}"
        self.logger.info(message)

    def cleanup_old_logs(self, days_to_keep=30):
        """
        Clean up old log files.

        Removes log files older than specified number of days.

        Args:
            days_to_keep (int): Number of days to keep log files
        """
        # Implementation for log cleanup would go here
        pass


# Global logger instance
_logger_instance = None


def get_logger(name="BiliDownload"):
    """
    Get or create a logger instance.

    Creates a singleton logger instance if none exists,
    otherwise returns the existing instance.

    Args:
        name (str): Logger name identifier

    Returns:
        Logger: Configured logger instance
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger(name)
    return _logger_instance.logger


def log_download_detail(event_type, message="", **kwargs):
    """
    记录下载详细信息到专用日志文件，并返回格式化的消息用于UI显示。

    Args:
        event_type (str): 事件类型，如'title', 'video', 'audio', 'ffmpeg'
        message (str): 日志消息
        **kwargs: 附加信息，如URL、路径等，可包含task_id和task_title用于标识任务

    Returns:
        str: 格式化后的日志消息
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger("BiliDownload")

    return _logger_instance.log_download_detail(event_type, message, **kwargs)
