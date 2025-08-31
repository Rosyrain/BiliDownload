"""
Configuration management module for BiliDownload application.

This module provides centralized configuration management including:
- Application settings
- Download paths
- Category management
- Advanced options
"""

import configparser
import os
from typing import Any, Dict

from src.core.managers.logger import get_logger


class ConfigManager:
    """
    Configuration manager for BiliDownload application.

    Manages all application settings including download paths, categories,
    UI preferences, and advanced options. Provides methods for loading,
    saving, and accessing configuration values.
    """

    def __init__(self, config_file: str = "config.ini"):
        """
        Initialize the configuration manager.

        Args:
            config_file (str): Path to the configuration file
        """
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.logger = get_logger("ConfigManager")
        self.logger.info("Configuration manager initialized")
        self.load_config()

    def load_config(self):
        """
        Load configuration from file.

        Creates default configuration if file doesn't exist.
        """
        if os.path.exists(self.config_file):
            self.config.read(self.config_file, encoding="utf-8")
            self.logger.info(f"Configuration file loaded: {self.config_file}")
        else:
            self.logger.info(
                "Configuration file not found, creating default configuration"
            )
            self.create_default_config()

    def create_default_config(self):
        """
        Create default configuration with standard settings.

        Sets up default download paths, categories, and application preferences.
        """
        self.logger.info("Creating default configuration")

        # 使用当前目录下的data作为默认下载路径
        default_download_path = os.path.join(os.getcwd(), "data")

        # TODO: remove the hardcode, using template ini file directly.

        self.config["GENERAL"] = {
            "download_path": default_download_path,
            "ffmpeg_path": "",
            "max_concurrent_downloads": "3",
            "auto_create_categories": "true",
            "default_category": "default",
        }

        self.config["UI"] = {
            "theme": "light",
            "window_width": "1600",
            "window_height": "1000",
            "language": "zh_CN",
        }

        self.config["DOWNLOAD"] = {
            "chunk_size": "8192",
            "timeout": "30",
            "retry_count": "3",
            "delay_between_requests": "1",
            "enable_resume": "true",
            "progress_update_interval": "500",
        }

        self.config["CATEGORIES"] = {
            "default": "default",
            "video": "video",
            "music": "music",
            "document": "document",
        }

        self.config["ADVANCED"] = {
            "verbose_logging": "false",
            "max_log_size": "10",
            "log_retention_days": "30",
            "use_proxy": "false",
            "proxy_host": "",
            "proxy_port": "",
            "debug_mode": "false",
        }

        self.save_config()
        self.logger.info("Default configuration created successfully")

        # Create default directory structure
        self._create_default_directories()

    def _create_default_directories(self):
        """
        Create default directory structure for downloads and categories.

        Creates data/ directory and all category subdirectories as specified
        in the [CATEGORIES] section of the configuration.
        """
        try:
            data_dir = os.path.join(os.getcwd(), "data")

            # Create data directory
            os.makedirs(data_dir, exist_ok=True)
            self.logger.info(f"Directory created: {data_dir}")

            # Create all category directories
            categories = self.get_all_categories()
            for category_name, category_path in categories.items():
                category_dir = os.path.join(data_dir, category_path)
                os.makedirs(category_dir, exist_ok=True)
                self.logger.info(f"Category directory created: {category_dir}")

            # Create tasks.json
            tasks_file = os.path.join(data_dir, "tasks.json")
            if not os.path.exists(tasks_file):
                with open(tasks_file, "w", encoding="utf-8") as f:
                    f.write("{}")
                self.logger.info(f"Tasks file created: {tasks_file}")

        except Exception as e:
            self.logger.error(f"Failed to create default directories: {e}")

    def save_config(self):
        """
        Save current configuration to file.

        Writes all configuration changes to the config.ini file.
        """
        with open(self.config_file, "w", encoding="utf-8") as f:
            self.config.write(f)
        self.logger.debug(f"Configuration file saved: {self.config_file}")

    def get(self, section: str, key: str, fallback: str = None) -> str:
        """
        Get configuration value.

        Args:
            section (str): Configuration section name
            key (str): Configuration option name
            fallback (str, optional): Default value if option not found

        Returns:
            str: Configuration value or fallback
        """
        return self.config.get(section, key, fallback=fallback)

    def set(self, section: str, key: str, value: str):
        """
        Set configuration value.

        Args:
            section (str): Configuration section name
            key (str): Configuration option name
            value (str): Value to set
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
            self.logger.debug(f"New configuration section added: [{section}]")

        old_value = self.config.get(section, key, fallback=None)
        self.config.set(section, key, value)

        if old_value != value:
            self.logger.info(f"Configuration changed: [{section}] {key} = {value}")
            # Remove call to non-existent method
            # self.logger.log_config_change(section, key, value)

        self.save_config()

    def save(self):
        """
        保存配置到文件
        """
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                self.config.write(f)
            self.logger.info(f"配置已保存到: {self.config_file}")
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            raise

    def get_download_path(self) -> str:
        """
        Get the default download path.

        Returns:
            str: Default download path from configuration
        """
        path = self.get("GENERAL", "download_path", "")
        if path and not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
            except Exception as e:
                self.logger.error(f"Failed to create download path: {e}")

        # 如果路径为空或创建失败，返回当前目录下的data
        if not path or not os.path.exists(path):
            fallback_path = os.path.join(os.getcwd(), "data")
            os.makedirs(fallback_path, exist_ok=True)
            self.logger.warning(f"Using fallback download path: {fallback_path}")
            return fallback_path

        return path

    def set_download_path(self, path: str):
        """
        Set the default download path.

        Args:
            path (str): New download path to set
        """
        self.set("GENERAL", "download_path", path)

    def get_ffmpeg_path(self) -> str:
        """
        Get FFmpeg executable path.

        Returns:
            str: FFmpeg path from configuration
        """
        return self.get("GENERAL", "ffmpeg_path")

    def set_ffmpeg_path(self, path: str):
        """
        Set FFmpeg executable path.

        Args:
            path (str): New FFmpeg path to set
        """
        self.logger.info(f"设置FFmpeg路径: {path}")
        self.set("GENERAL", "ffmpeg_path", path)
        # 验证设置是否成功
        new_path = self.get_ffmpeg_path()
        self.logger.info(f"验证FFmpeg路径: {new_path}")

    def get_max_concurrent_downloads(self) -> int:
        """
        Get maximum concurrent downloads setting.

        Returns:
            int: Maximum number of concurrent downloads
        """
        try:
            return int(self.get("GENERAL", "max_concurrent_downloads", "3"))
        except ValueError:
            return 3

    def set_max_concurrent_downloads(self, count: int):
        """
        Set maximum concurrent downloads setting.

        Args:
            count (int): New maximum concurrent downloads value
        """
        self.set("GENERAL", "max_concurrent_downloads", str(count))

    def get_default_category(self) -> str:
        """
        Get the default category from DEFAULT section.

        Returns:
            str: Default category name
        """
        return self.get("GENERAL", "default_category", "default")

    def set_default_category(self, category: str):
        """
        Set the default category in DEFAULT section.

        Args:
            category (str): Default category name to set
        """
        self.set("GENERAL", "default_category", category)

    def get_download_settings(self) -> dict:
        """
        Get all download settings.

        Returns:
            dict: Dictionary containing download settings
        """
        settings = {
            "chunk_size": int(self.get("DOWNLOAD", "chunk_size", "8192")),
            "timeout": int(self.get("DOWNLOAD", "timeout", "30")),
            "retry_count": int(self.get("DOWNLOAD", "retry_count", "3")),
            "delay_between_requests": float(
                self.get("DOWNLOAD", "delay_between_requests", "1")
            ),
            "enable_resume": self.get("DOWNLOAD", "enable_resume", "true").lower()
            == "true",
            "resume_chunk_size": int(self.get("DOWNLOAD", "resume_chunk_size", "10")),
            "progress_update_interval": int(
                self.get("DOWNLOAD", "progress_update_interval", "500")
            ),
        }
        return settings

    def get_resume_chunk_size(self) -> int:
        """
        Get resume chunk size in MB.

        Returns:
            int: Resume chunk size in MB
        """
        try:
            return int(self.config.get("DOWNLOAD", "resume_chunk_size", fallback=10))
        except ValueError:
            return 10

    def set_resume_chunk_size(self, size: int):
        """
        Set resume chunk size in MB.

        Args:
            size (int): New resume chunk size in MB
        """
        if not self.config.has_section("DOWNLOAD"):
            self.config.add_section("DOWNLOAD")

        self.config.set("DOWNLOAD", "resume_chunk_size", str(size))
        self.save_config()

    def get_category_path(self, category_name):
        """
        获取分类路径
        
        Args:
            category_name: 分类名称
            
        Returns:
            str: 分类路径
        """
        try:
            if not self.config.has_section("CATEGORIES"):
                self.config.add_section("CATEGORIES")
                
            if not self.config.has_option("CATEGORIES", category_name):
                # 如果分类不存在，返回下载路径
                return self.get_download_path()
                
            return self.config.get("CATEGORIES", category_name)
        except Exception as e:
            self.logger.error(f"Failed to get category path: {e}")
            # 返回下载路径作为默认值
            return self.get_download_path()

    def get_series_download_path(self, category_name: str, series_name: str) -> str:
        """
        Get download path for series videos within a category.

        Args:
            category_name (str): Category name
            series_name (str): Series name for folder naming

        Returns:
            str: Full path for series downloads
        """
        try:
            # Get category path
            category_path = self.get_category_path(category_name)
            if category_path:
                # Create series folder within category directory
                series_path = os.path.join(category_path, series_name)
                os.makedirs(series_path, exist_ok=True)
                self.logger.info(f"Series directory created: {series_path}")
                return series_path
            else:
                # If category path retrieval failed, create in default directory
                default_path = self.get_download_path()
                series_path = os.path.join(default_path, series_name)
                os.makedirs(series_path, exist_ok=True)
                self.logger.info(
                    f"Series directory created in default directory: {series_path}"
                )
                return series_path
        except Exception as e:
            self.logger.error(f"Failed to get series download path: {e}")
            # Return default path
            return self.get_download_path()

    def add_category(self, name: str, path: str = None) -> bool:
        """
        Add a new download category.

        Args:
            name (str): Category name
            path (str, optional): Custom path for the category

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not path:
                # If no path specified, use category name as path
                path = name

            # Add to configuration
            self.config.set("CATEGORIES", name, path)

            # Create corresponding directory
            data_dir = os.path.join(os.getcwd(), "data")
            category_dir = os.path.join(data_dir, path)
            os.makedirs(category_dir, exist_ok=True)

            self.logger.info(f"Category added: {name} -> {path}")
            # 移除不存在的方法调用
            # self.logger.log_category_operation("add", name, f"path: {path}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to add category: {e}")
            return False

    def remove_category(self, name: str) -> bool:
        """
        Remove a download category.

        Args:
            name (str): Category name to remove

        Returns:
            bool: True if successful, False otherwise

        Note:
            This only removes the category from configuration.
            The actual directory and files are not deleted.
        """
        try:
            if name == "default":
                self.logger.warning("Cannot delete default category")
                return False

            # Remove from configuration
            if self.config.has_option("CATEGORIES", name):
                self.config.remove_option("CATEGORIES", name)
                self.save_config()

                self.logger.info(f"Category removed: {name}")
                self.logger.log_category_operation("remove", name)

                return True
            else:
                self.logger.warning(f"Category not found: {name}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to remove category: {e}")
            return False

    def get_all_categories(self) -> Dict[str, str]:
        """
        Get all available categories.

        Returns:
            Dict[str, str]: Dictionary mapping category names to their paths
        """
        try:
            if self.config.has_section("CATEGORIES"):
                return dict(self.config.items("CATEGORIES"))
            return {}
        except Exception as e:
            self.logger.error(f"Failed to get category list: {e}")
            return {}

    def get_category_tree(self) -> Dict[str, Any]:
        """
        Get hierarchical category structure.

        Returns:
            Dict[str, Any]: Tree structure of categories with nested paths
        """
        try:
            categories = self.get_all_categories()
            tree = {}

            for name, path in categories.items():
                # Parse path hierarchy
                path_parts = path.split("/")
                current_level = tree

                for i, part in enumerate(path_parts):
                    if part not in current_level:
                        current_level[part] = {
                            "name": part,
                            "full_path": "/".join(path_parts[: i + 1]),
                            "children": {},
                            "is_leaf": i == len(path_parts) - 1,
                        }
                    current_level = current_level[part]["children"]

            return tree

        except Exception as e:
            self.logger.error(f"Failed to get category tree: {e}")
            return {}

    def get_advanced_setting(self, key: str, fallback: str = None) -> str:
        """
        Get advanced configuration setting.

        Args:
            key (str): Setting option name
            fallback (str, optional): Default value if not found

        Returns:
            str: Setting value or fallback
        """
        return self.config.get("ADVANCED", key, fallback=fallback)

    def set_advanced_setting(self, key: str, value: str):
        """
        Set advanced configuration setting.

        Args:
            key (str): Setting option name
            value (str): Value to set
        """
        self.config.set("ADVANCED", key, value)

    def get_download_setting(self, key: str, fallback: str = None) -> str:
        """
        Get download configuration setting.

        Args:
            key (str): Setting option name
            fallback (str, optional): Default value if not found

        Returns:
            str: Setting value or fallback
        """
        return self.config.get("DOWNLOAD", key, fallback=fallback)

    def set_download_setting(self, key: str, value: str):
        """
        Set download configuration setting.

        Args:
            key (str): Setting option name
            value (str): Value to set
        """
        self.config.set("DOWNLOAD", key, value)
