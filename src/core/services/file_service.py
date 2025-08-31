"""
File service for BiliDownload application.

This service provides file-related functionality including:
- File listing and filtering
- File operations (open, delete)
- Directory management
- File search
"""

import os
import platform
import subprocess
from datetime import datetime
from typing import Callable, Dict, List

from src.core.managers.config_manager import ConfigManager
from src.core.managers.file_manager import FileManager
from src.core.managers.logger import get_logger


class FileService:
    """
    Service for managing files and directories.

    Provides high-level functionality for file operations,
    abstracting the underlying file system implementation.
    """

    def __init__(self, config_manager: ConfigManager, file_manager: FileManager):
        """
        Initialize the file service.

        Args:
            config_manager: Configuration manager instance
            file_manager: File manager instance
        """
        self.config_manager = config_manager
        self.file_manager = file_manager
        self.logger = get_logger(__name__)

        # 回调函数
        self.file_changed_callbacks: List[Callable[[str], None]] = []

    def register_file_changed_callback(self, callback: Callable[[str], None]):
        """
        注册文件变更回调函数

        Args:
            callback: 回调函数，接收参数(path)
        """
        self.file_changed_callbacks.append(callback)

    def get_files(
        self, path: str, search_text: str = "", file_type: str = "全部"
    ) -> List[Dict]:
        """
        获取指定路径下的文件列表，支持搜索和类型过滤

        Args:
            path: 目录路径
            search_text: 搜索文本
            file_type: 文件类型过滤

        Returns:
            文件信息列表
        """
        try:
            if not path or not os.path.isdir(path):
                return []

            # 获取目录中的所有文件
            files = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path):
                    # 获取文件信息
                    try:
                        file_info = self.file_manager.get_file_info(item_path)
                    except ValueError:
                        # 如果获取文件信息失败，使用基本信息
                        file_info = {
                            "name": item,
                            "path": item_path,
                            "size": os.path.getsize(item_path)
                            if os.path.exists(item_path)
                            else 0,
                            "modified": datetime.fromtimestamp(
                                os.path.getmtime(item_path)
                            )
                            if os.path.exists(item_path)
                            else datetime.now(),
                            "type": os.path.splitext(item)[1].lstrip(".").upper()
                            or "文件",
                        }

                    # 应用过滤条件
                    if (
                        search_text
                        and search_text.lower() not in file_info["name"].lower()
                    ):
                        continue

                    if file_type != "全部" and file_type.lower() != (
                        "." + file_info["type"].lower()
                    ):
                        continue

                    files.append(file_info)

            return files
        except Exception as e:
            self.logger.error(f"获取文件列表失败: {e}")
            return []

    def get_file_types(self, path: str) -> List[str]:
        """
        获取指定路径下的文件类型列表

        Args:
            path: 目录路径

        Returns:
            文件类型列表
        """
        try:
            if not path or not os.path.exists(path):
                return ["全部"]

            # 获取目录中的所有文件
            files = os.listdir(path)
            extensions = set()

            # 收集所有文件扩展名
            for file in files:
                file_path = os.path.join(path, file)
                if os.path.isfile(file_path):
                    _, ext = os.path.splitext(file)
                    if ext:
                        extensions.add(ext.lower())

            # 返回排序后的类型列表
            return ["全部"] + sorted(list(extensions))
        except Exception as e:
            self.logger.error(f"获取文件类型列表失败: {e}")
            return ["全部"]

    def open_file(self, file_path: str) -> bool:
        """
        使用系统默认应用打开文件

        Args:
            file_path: 文件路径

        Returns:
            是否成功打开
        """
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"文件不存在: {file_path}")
                return False

            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", file_path])
            else:  # Linux
                subprocess.run(["xdg-open", file_path])

            self.logger.info(f"打开文件: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"打开文件失败: {e}")
            return False

    def delete_file(self, file_path: str) -> bool:
        """
        删除文件

        Args:
            file_path: 文件路径

        Returns:
            是否成功删除
        """
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"文件不存在: {file_path}")
                return False

            os.remove(file_path)

            # 通知文件变更
            self._notify_file_changed(os.path.dirname(file_path))

            self.logger.info(f"删除文件: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"删除文件失败: {e}")
            return False

    def open_folder(self, folder_path: str) -> bool:
        """
        在系统文件浏览器中打开文件夹

        Args:
            folder_path: 文件夹路径

        Returns:
            是否成功打开
        """
        try:
            if not os.path.isdir(folder_path):
                self.logger.error(f"文件夹不存在: {folder_path}")
                return False

            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])

            self.logger.info(f"打开文件夹: {folder_path}")
            return True
        except Exception as e:
            self.logger.error(f"打开文件夹失败: {e}")
            return False

    def create_folder(self, parent_path: str, folder_name: str) -> bool:
        """
        创建文件夹

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

            # 通知文件变更
            self._notify_file_changed(parent_path)

            self.logger.info(f"创建文件夹: {new_folder_path}")
            return True
        except Exception as e:
            self.logger.error(f"创建文件夹失败: {e}")
            return False

    def get_category_tree(self) -> List[Dict]:
        """
        获取分类树结构

        Returns:
            分类树结构列表
        """
        try:
            # 获取下载根路径
            download_path = self.config_manager.get_download_path()
            if not os.path.isdir(download_path):
                self.logger.warning(f"下载路径不存在: {download_path}")
                try:
                    os.makedirs(download_path, exist_ok=True)
                    self.logger.info(f"创建下载目录: {download_path}")
                except Exception as e:
                    self.logger.error(f"创建下载目录失败: {e}")
                    return []

            # 获取下载路径的文件夹名称
            folder_name = os.path.basename(download_path)

            # 创建根节点
            root_item = {
                "text": folder_name,
                "path": download_path,
                "children": self._get_directory_tree(download_path),
            }

            return [root_item]
        except Exception as e:
            self.logger.error(f"获取分类树失败: {e}")
            return []

    def _get_directory_tree(self, directory_path: str) -> List[Dict]:
        """
        递归获取目录树结构

        Args:
            directory_path: 目录路径

        Returns:
            目录树结构列表
        """
        try:
            # 检查路径是否为目录
            if not os.path.isdir(directory_path):
                self.logger.warning(f"不是目录: {directory_path}")
                return []

            result = []
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                if os.path.isdir(item_path) and not item.startswith("."):
                    # 创建子节点
                    child_item = {
                        "text": item,
                        "path": item_path,
                        "children": self._get_directory_tree(item_path),
                    }
                    result.append(child_item)

            return result
        except Exception as e:
            self.logger.error(f"获取目录树失败: {e}")
            return []

    def format_file_size(self, size_bytes: int) -> str:
        """
        将字节大小格式化为人类可读的形式

        Args:
            size_bytes: 文件大小（字节）

        Returns:
            格式化后的文件大小字符串
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    def _notify_file_changed(self, path: str):
        """通知文件变更"""
        for callback in self.file_changed_callbacks:
            try:
                callback(path)
            except Exception as e:
                self.logger.error(f"文件变更回调异常: {e}")
