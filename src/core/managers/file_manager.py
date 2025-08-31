"""
File system management module for BiliDownload application.

This module provides file and directory operations including:
- File listing and navigation
- File operations (copy, move, delete)
- File information retrieval
- Directory management
"""

import os
import platform
import shutil
import subprocess
from typing import Dict, List

from src.core.managers.logger import get_logger


class FileManager:
    """
    File system manager for BiliDownload application.

    Handles all file and directory operations including listing,
    navigation, file operations, and system integration.

    Attributes:
        logger: Module logger used for error and info messages.
    """

    def __init__(self):
        """
        Initialize the file manager with logging capability.

        Returns:
            None
        """
        self.logger = get_logger(__name__)

    def list_directory(self, path: str) -> List[Dict[str, any]]:
        """
        Get list of files and directories in specified path.

        Args:
            path (str): Absolute or relative directory path to list.

        Returns:
            List[Dict[str, any]]: List of file/directory information dictionaries. Each
                item contains at least the following keys:
                - name (str): Base name of the entry.
                - path (str): Absolute or provided path to the entry.
                - is_dir (bool): Whether the entry is a directory.
                - size (int): File size in bytes (0 for directories or on error).
                - modified (float): POSIX timestamp of last modification time.
                - created (float): POSIX timestamp of creation time.

                The list is sorted by type and name based on implementation details.
        """
        try:
            if not os.path.exists(path):
                self.logger.error(f"Directory not found: {path}")
                return []

            items = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                item_info = self._get_file_info(item_path)
                items.append(item_info)

            # Sort by type and name
            items.sort(key=lambda x: (x["is_dir"], x["name"].lower()))
            return items

        except Exception as e:
            self.logger.error(f"Failed to list directory {path}: {e}")
            return []

    def _get_file_info(self, file_path: str) -> Dict[str, any]:
        """
        Get detailed information about a file or directory.

        Args:
            file_path (str): Path to the file or directory.

        Returns:
            Dict[str, any]: File information dictionary with keys:
                - name (str): Base name of the file or directory.
                - path (str): Absolute or provided path to the entry.
                - is_dir (bool): Whether the entry is a directory.
                - size (int): File size in bytes (0 for directories or on error).
                - modified (float): POSIX timestamp of last modification time.
                - created (float): POSIX timestamp of creation time.
                - type (str): File extension without dot, or "FOLDER" for directories.

            On error, returns a best-effort structure with defaults.
        """
        try:
            stat = os.stat(file_path)
            is_dir = os.path.isdir(file_path)

            # 获取文件类型（扩展名）
            file_type = (
                "FOLDER"
                if is_dir
                else os.path.splitext(file_path)[1].lstrip(".").upper() or "FILE"
            )

            return {
                "name": os.path.basename(file_path),
                "path": file_path,
                "is_dir": is_dir,
                "size": stat.st_size if not is_dir else 0,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "type": file_type,
            }
        except Exception as e:
            self.logger.error(f"Failed to get file info for {file_path}: {e}")
            return {
                "name": os.path.basename(file_path),
                "path": file_path,
                "is_dir": False,
                "size": 0,
                "modified": 0,
                "created": 0,
                "type": "UNKNOWN",
            }

    def get_file_info(self, file_path: str) -> Dict[str, any]:
        """
        Get detailed information about a file or directory.
        Public wrapper for _get_file_info.

        Args:
            file_path (str): Path to the file or directory.

        Returns:
            Dict[str, any]: File information dictionary
        """
        return self._get_file_info(file_path)

    def get_file_size(self, file_path: str) -> int:
        """
        Get file size in bytes.

        Args:
            file_path (str): Path to the file.

        Returns:
            int: File size in bytes, or 0 if the file does not exist or is a directory,
            or on error.
        """
        try:
            if os.path.isfile(file_path):
                return os.path.getsize(file_path)
            return 0
        except Exception as e:
            self.logger.error(f"Failed to get file size for {file_path}: {e}")
            return 0

    def format_file_size(self, size_bytes: int) -> str:
        """
        Format file size for human-readable display.

        Args:
            size_bytes (int): File size in bytes.

        Returns:
            str: Formatted file size string using binary units (e.g., "1.5 MB").
        """
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.1f} {size_names[i]}"

    def open_file(self, file_path: str) -> bool:
        """
        Open file using system default application.

        Args:
            file_path (str): Path to the file to open.

        Returns:
            bool: True if the file launch command was executed successfully.

        Notes:
            Uses platform-specific mechanisms: os.startfile on Windows, "open" on macOS,
            and "xdg-open" on Linux.
        """
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"File not found: {file_path}")
                return False

            system = platform.system()
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", file_path], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", file_path], check=True)

            self.logger.info(f"File opened: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to open file {file_path}: {e}")
            return False

    def open_folder(self, folder_path: str) -> bool:
        """
        Open folder in system file manager.

        Args:
            folder_path (str): Path to the folder to open.

        Returns:
            bool: True if the folder launch command was executed successfully.

        Notes:
            Uses platform-specific mechanisms: explorer on Windows, "open" on macOS,
            and "xdg-open" on Linux.
        """
        try:
            if not os.path.exists(folder_path):
                self.logger.error(f"Folder not found: {folder_path}")
                return False

            system = platform.system()
            if system == "Windows":
                subprocess.run(["explorer", folder_path], check=True)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", folder_path], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", folder_path], check=True)

            self.logger.info(f"Folder opened: {folder_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to open folder {folder_path}: {e}")
            return False

    def create_folder(self, folder_path: str) -> bool:
        """
        Create a new folder.

        Args:
            folder_path (str): Path for the new folder.

        Returns:
            bool: True if the folder exists after the operation, False otherwise.

        Notes:
            This operation uses exist_ok=True, so it will not raise an error if the
            folder already exists.
        """
        try:
            os.makedirs(folder_path, exist_ok=True)
            self.logger.info(f"Folder created: {folder_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create folder {folder_path}: {e}")
            return False

    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file or directory.

        Args:
            file_path (str): Path to the file or directory to delete.

        Returns:
            bool: True if deletion succeeded, False otherwise.

        Notes:
            Directories are removed recursively.
            Nonexistent paths result in False and a warning log.
        """
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                self.logger.info(f"File deleted: {file_path}")
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                self.logger.info(f"Directory deleted: {file_path}")
            else:
                self.logger.warning(f"Path not found: {file_path}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to delete {file_path}: {e}")
            return False

    def move_file(self, source_path: str, destination_path: str) -> bool:
        """
        Move a file or directory to a new location.

        Args:
            source_path (str): Source file or directory path.
            destination_path (str): Destination path.

        Returns:
            bool: True if the move operation succeeded, False otherwise.
        """
        try:
            shutil.move(source_path, destination_path)
            self.logger.info(f"File moved: {source_path} -> {destination_path}")
            return True
        except Exception as e:
            self.logger.error(
                f"Failed to move {source_path} to {destination_path}: {e}"
            )
            return False

    def copy_file(self, source_path: str, destination_path: str) -> bool:
        """
        Copy a file or directory to a new location.

        Args:
            source_path (str): Source file or directory path.
            destination_path (str): Destination path.

        Returns:
            bool: True if the copy operation succeeded, False otherwise.

        Notes:
            Directories are copied recursively. Copying a directory to an existing
            destination may fail depending on the platform and Python version.
        """
        try:
            if os.path.isfile(source_path):
                shutil.copy2(source_path, destination_path)
            elif os.path.isdir(source_path):
                shutil.copytree(source_path, destination_path)
            else:
                self.logger.warning(f"Source path not found: {source_path}")
                return False

            self.logger.info(f"File copied: {source_path} -> {destination_path}")
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to copy {source_path} to {destination_path}: {e}"
            )
            return False

    def search_files(self, directory: str, pattern: str) -> List[str]:
        """
        Search for files matching a pattern in a directory.

        Args:
            directory (str): Directory to search in.
            pattern (str): Search pattern (substring of filename or extension).

        Returns:
            List[str]: List of matching file paths, sorted by modification time in
            descending order (newest first).
        """
        try:
            matching_files = []
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if pattern.lower() in file.lower():
                        matching_files.append(os.path.join(root, file))

            # Sort by modification time
            matching_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            return matching_files

        except Exception as e:
            self.logger.error(f"Failed to search in {directory}: {e}")
            return []

    def get_directory_size(self, directory: str) -> int:
        """
        Calculate total size of a directory and its contents.

        Args:
            directory (str): Directory path to calculate size for.

        Returns:
            int: Total size in bytes for all files found recursively.
        """
        try:
            total_size = 0
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
            return total_size
        except Exception as e:
            self.logger.error(
                f"Failed to calculate directory size for {directory}: {e}"
            )
            return 0
