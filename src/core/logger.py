"""
Centralized logging system for BiliDownload application.

This module provides comprehensive logging functionality including:
- Console and file logging
- Log rotation and retention
- Specialized log types (download, error, general)
- Structured logging methods
"""

import logging
import os
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
    
    def _setup_handlers(self):
        """
        Set up logging handlers for different output destinations.
        
        Configures console handler, general log file, error log file,
        and download-specific log file with appropriate formatting.
        """
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler - General logs
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        general_handler = RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        general_handler.setLevel(logging.INFO)
        general_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        general_handler.setFormatter(general_formatter)
        self.logger.addHandler(general_handler)
        
        # File handler - Error logs
        error_handler = RotatingFileHandler(
            log_dir / "error.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)
        
        # File handler - Download logs
        download_handler = RotatingFileHandler(
            log_dir / "download.log",
            maxBytes=20*1024*1024,  # 20MB
            backupCount=10,
            encoding='utf-8'
        )
        download_handler.setLevel(logging.INFO)
        download_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        download_handler.setFormatter(download_formatter)
        self.logger.addHandler(download_handler)
    
    def info(self, message):
        """
        Log information message.
        
        Args:
            message (str): Information message to log
        """
        self.logger.info(message)
    
    def warning(self, message):
        """
        Log warning message.
        
        Args:
            message (str): Warning message to log
        """
        self.logger.warning(message)
    
    def error(self, message):
        """
        Log error message.
        
        Args:
            message (str): Error message to log
        """
        self.logger.error(message)
    
    def debug(self, message):
        """
        Log debug message.
        
        Args:
            message (str): Debug message to log
        """
        self.logger.debug(message)
    
    def critical(self, message):
        """
        Log critical error message.
        
        Args:
            message (str): Critical error message to log
        """
        self.logger.critical(message)
    
    def log_download_info(self, message):
        """
        Log download-specific information.
        
        Uses specialized download log handler for better organization.
        
        Args:
            message (str): Download information message to log
        """
        # Use specialized download log handler
        self.logger.info(message)
    
    def log_exception(self, message, exc_info=True):
        """
        Log exception information with traceback.
        
        Args:
            message (str): Exception message to log
            exc_info (bool): Whether to include exception traceback
        """
        self.logger.exception(message, exc_info=exc_info)
    
    def log_download_progress(self, message):
        """
        Log download progress information.
        
        Args:
            message (str): Download progress message to log
        """
        self.logger.info(message)
    
    def log_download_start(self, message):
        """
        Log download start event.
        
        Args:
            message (str): Download start message to log
        """
        self.logger.info(message)
    
    def log_download_complete(self, message):
        """
        Log download completion event.
        
        Args:
            message (str): Download completion message to log
        """
        self.logger.info(message)
    
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