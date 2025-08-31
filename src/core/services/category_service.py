"""
Category service for BiliDownload application.

This service provides category-related functionality including:
- Category management
- Category tree structure
- Category path operations
"""

import os
from typing import Callable, Dict, List

from src.core.managers.config_manager import ConfigManager
from src.core.managers.logger import get_logger


class CategoryService:
    """
    Service for managing categories.

    Provides high-level functionality for category operations,
    abstracting the underlying configuration and file system implementation.
    """

    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the category service.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = get_logger(__name__)

        # 回调函数
        self.category_changed_callbacks: List[Callable[[], None]] = []

    def register_category_changed_callback(self, callback: Callable[[], None]):
        """
        注册分类变更回调函数

        Args:
            callback: 回调函数
        """
        self.category_changed_callbacks.append(callback)

    def get_all_categories(self) -> Dict[str, str]:
        """
        获取所有分类

        Returns:
            分类字典，键为分类名称，值为分类路径
        """
        return self.config_manager.get_all_categories()

    def get_category_path(self, category_name: str) -> str:
        """
        获取分类路径

        Args:
            category_name: 分类名称

        Returns:
            分类路径
        """
        return self.config_manager.get_category_path(category_name)

    def add_category(self, name: str, path: str = None) -> bool:
        """
        添加分类

        Args:
            name: 分类名称
            path: 分类路径（可选）

        Returns:
            是否成功添加
        """
        result = self.config_manager.add_category(name, path)

        if result:
            # 通知分类变更
            self._notify_category_changed()

        return result

    def remove_category(self, name: str) -> bool:
        """
        删除分类

        Args:
            name: 分类名称

        Returns:
            是否成功删除
        """
        result = self.config_manager.remove_category(name)

        if result:
            # 通知分类变更
            self._notify_category_changed()

        return result

    def get_default_category(self) -> str:
        """
        获取默认分类

        Returns:
            默认分类名称
        """
        return self.config_manager.get_default_category()

    def set_default_category(self, category: str) -> bool:
        """
        设置默认分类

        Args:
            category: 分类名称

        Returns:
            是否成功设置
        """
        try:
            self.config_manager.set_default_category(category)

            # 通知分类变更
            self._notify_category_changed()

            return True
        except Exception as e:
            self.logger.error(f"设置默认分类失败: {e}")
            return False

    def get_category_tree(self) -> Dict[str, any]:
        """
        获取分类树结构

        Returns:
            分类树结构
        """
        return self.config_manager.get_category_tree()

    def get_series_download_path(self, category_name: str, series_name: str) -> str:
        """
        获取系列下载路径

        Args:
            category_name: 分类名称
            series_name: 系列名称

        Returns:
            系列下载路径
        """
        return self.config_manager.get_series_download_path(category_name, series_name)

    def create_category_folder(self, parent_path: str, folder_name: str) -> bool:
        """
        创建分类文件夹

        Args:
            parent_path: 父目录路径
            folder_name: 文件夹名称

        Returns:
            是否成功创建
        """
        try:
            if not os.path.isdir(parent_path):
                self.logger.error(f"父目录不存在: {parent_path}")
                return False

            # 创建文件夹
            new_folder_path = os.path.join(parent_path, folder_name)

            if os.path.exists(new_folder_path):
                self.logger.warning(f"文件夹已存在: {new_folder_path}")
                return False

            os.makedirs(new_folder_path, exist_ok=True)

            # 获取相对于下载根路径的路径
            download_path = self.config_manager.get_download_path()
            if new_folder_path.startswith(download_path):
                relative_path = os.path.relpath(
                    new_folder_path, os.path.dirname(download_path)
                )

                # 添加为分类
                self.add_category(folder_name, relative_path)

            self.logger.info(f"创建分类文件夹: {new_folder_path}")
            return True
        except Exception as e:
            self.logger.error(f"创建分类文件夹失败: {e}")
            return False

    def _notify_category_changed(self):
        """通知分类变更"""
        for callback in self.category_changed_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"分类变更回调异常: {e}")
