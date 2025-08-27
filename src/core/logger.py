"""
日志管理器
提供统一的日志输出功能，支持文件和控制台输出
"""
import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional


class Logger:
    """日志管理器"""
    
    def __init__(self, name: str = "BiliDownload", log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 创建日志记录器
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器 - 普通日志
        info_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "app.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        info_handler.setLevel(logging.INFO)
        info_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        info_handler.setFormatter(info_formatter)
        self.logger.addHandler(info_handler)
        
        # 文件处理器 - 错误日志
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "error.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)
        
        # 文件处理器 - 下载日志
        download_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "download.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        download_handler.setLevel(logging.INFO)
        download_formatter = logging.Formatter(
            '%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        download_handler.setFormatter(download_formatter)
        self.logger.addHandler(download_handler)
    
    def info(self, message: str):
        """信息日志"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """警告日志"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """错误日志"""
        self.logger.error(message)
    
    def debug(self, message: str):
        """调试日志"""
        self.logger.debug(message)
    
    def critical(self, message: str):
        """严重错误日志"""
        self.logger.critical(message)
    
    def download_info(self, message: str):
        """下载信息日志"""
        # 使用专门的下载日志处理器
        for handler in self.logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler) and "download.log" in handler.baseFilename:
                handler.emit(logging.LogRecord(
                    name=self.name,
                    level=logging.INFO,
                    pathname="",
                    lineno=0,
                    msg=message,
                    args=(),
                    exc_info=None
                ))
                break
    
    def log_exception(self, message: str, exc_info=None):
        """记录异常信息"""
        self.logger.exception(message, exc_info=exc_info)
    
    def log_download_progress(self, progress: int, message: str):
        """记录下载进度"""
        self.download_info(f"进度 {progress}%: {message}")
    
    def log_download_start(self, url: str, save_path: str):
        """记录下载开始"""
        self.download_info(f"开始下载: {url} -> {save_path}")
    
    def log_download_complete(self, url: str, success: bool, message: str):
        """记录下载完成"""
        status = "成功" if success else "失败"
        self.download_info(f"下载{status}: {url} - {message}")
    
    def log_config_change(self, section: str, key: str, value: str):
        """记录配置变更"""
        self.info(f"配置变更: [{section}] {key} = {value}")
    
    def log_category_operation(self, operation: str, category_name: str, details: str = ""):
        """记录分类操作"""
        message = f"分类操作: {operation} '{category_name}'"
        if details:
            message += f" - {details}"
        self.info(message)
    
    def log_file_operation(self, operation: str, file_path: str, success: bool):
        """记录文件操作"""
        status = "成功" if success else "失败"
        self.info(f"文件操作{status}: {operation} - {file_path}")
    
    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志文件"""
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            for log_file in self.log_dir.glob("*.log.*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    self.info(f"清理旧日志文件: {log_file}")
                    
        except Exception as e:
            self.error(f"清理日志文件失败: {e}")


# 全局日志管理器实例
app_logger = Logger()


def get_logger(name: str = None) -> Logger:
    """获取日志管理器"""
    if name:
        return Logger(name)
    return app_logger


def log_function_call(func):
    """装饰器：记录函数调用"""
    def wrapper(*args, **kwargs):
        logger = get_logger()
        logger.debug(f"调用函数: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"函数 {func.__name__} 执行成功")
            return result
        except Exception as e:
            logger.error(f"函数 {func.__name__} 执行失败: {e}")
            raise
    return wrapper 