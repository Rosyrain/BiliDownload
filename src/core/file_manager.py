"""
文件管理器
"""
import os
import platform
import subprocess
from typing import List, Dict, Optional
from pathlib import Path

from .logger import get_logger


class FileManager:
    """文件管理器"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.system = platform.system()
        self.logger = get_logger("FileManager")
        self.logger.info(f"文件管理器初始化，基础路径: {base_path}")
        self.logger.info(f"操作系统: {self.system}")
    
    def get_files_in_directory(self, directory: str = None) -> List[Dict]:
        """获取目录中的文件列表"""
        if directory is None:
            directory = self.base_path
        else:
            directory = Path(directory)
        
        if not directory.exists():
            return []
        
        files = []
        try:
            for item in directory.iterdir():
                file_info = {
                    'name': item.name,
                    'path': str(item),
                    'is_dir': item.is_dir(),
                    'size': self._get_file_size(item) if item.is_file() else 0,
                    'modified': item.stat().st_mtime,
                    'extension': item.suffix if item.is_file() else ''
                }
                files.append(file_info)
            
            # 按类型和名称排序
            files.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
            
        except PermissionError:
            self.logger.warning(f"权限不足，无法访问目录: {directory}")
        except Exception as e:
            self.logger.error(f"获取目录文件列表失败: {e}")
        
        return files
    
    def _get_file_size(self, file_path: Path) -> int:
        """获取文件大小"""
        try:
            return file_path.stat().st_size
        except Exception as e:
            self.logger.debug(f"获取文件大小失败: {file_path} - {e}")
            return 0
    
    def format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小显示"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def open_file(self, file_path: str) -> bool:
        """打开文件（使用系统默认程序）"""
        try:
            if self.system == "Darwin":  # macOS
                subprocess.run(["open", file_path], check=True)
            elif self.system == "Windows":
                os.startfile(file_path)
            else:  # Linux
                subprocess.run(["xdg-open", file_path], check=True)
            return True
        except Exception as e:
            self.logger.error(f"打开文件失败: {file_path} - {e}")
            return False
    
    def open_folder(self, folder_path: str) -> bool:
        """打开文件夹"""
        try:
            if self.system == "Darwin":  # macOS
                subprocess.run(["open", folder_path], check=True)
            elif self.system == "Windows":
                subprocess.run(["explorer", folder_path], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", folder_path], check=True)
            return True
        except Exception as e:
            self.logger.error(f"打开文件夹失败: {folder_path} - {e}")
            return False
    
    def create_folder(self, folder_name: str, parent_path: str = None) -> bool:
        """创建文件夹"""
        try:
            if parent_path is None:
                parent_path = self.base_path
            else:
                parent_path = Path(parent_path)
            
            new_folder = parent_path / folder_name
            new_folder.mkdir(exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"创建文件夹失败: {folder_name} - {e}")
            return False
    
    def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        try:
            path = Path(file_path)
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
            return True
        except Exception as e:
            self.logger.error(f"删除文件失败: {file_path} - {e}")
            return False
    
    def move_file(self, source_path: str, destination_path: str) -> bool:
        """移动文件"""
        try:
            source = Path(source_path)
            destination = Path(destination_path)
            
            if source.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                source.rename(destination)
                return True
            return False
        except Exception as e:
            self.logger.error(f"移动文件失败: {source_path} -> {destination_path} - {e}")
            return False
    
    def copy_file(self, source_path: str, destination_path: str) -> bool:
        """复制文件"""
        try:
            source = Path(source_path)
            destination = Path(destination_path)
            
            if source.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                if source.is_file():
                    import shutil
                    shutil.copy2(source, destination)
                else:
                    import shutil
                    shutil.copytree(source, destination, dirs_exist_ok=True)
                return True
            return False
        except Exception as e:
            self.logger.error(f"复制文件失败: {source_path} -> {destination_path} - {e}")
            return False
    
    def search_files(self, query: str, directory: str = None, recursive: bool = True) -> List[Dict]:
        """搜索文件"""
        if directory is None:
            directory = self.base_path
        else:
            directory = Path(directory)
        
        results = []
        
        try:
            if recursive:
                for item in directory.rglob("*"):
                    if query.lower() in item.name.lower():
                        file_info = {
                            'name': item.name,
                            'path': str(item),
                            'is_dir': item.is_dir(),
                            'size': self._get_file_size(item) if item.is_file() else 0,
                            'modified': item.stat().st_mtime,
                            'extension': item.suffix if item.is_file() else ''
                        }
                        results.append(file_info)
            else:
                for item in directory.iterdir():
                    if query.lower() in item.name.lower():
                        file_info = {
                            'name': item.name,
                            'path': str(item),
                            'is_dir': item.is_dir(),
                            'size': self._get_file_size(item) if item.is_file() else 0,
                            'modified': item.stat().st_mtime,
                            'extension': item.suffix if item.is_file() else ''
                        }
                        results.append(file_info)
            
            # 按修改时间排序
            results.sort(key=lambda x: x['modified'], reverse=True)
            
        except PermissionError:
            self.logger.warning(f"权限不足，无法搜索目录: {directory}")
        except Exception as e:
            self.logger.error(f"搜索文件失败: {e}")
        
        return results
    
    def get_directory_size(self, directory: str) -> int:
        """获取目录总大小"""
        try:
            total_size = 0
            directory_path = Path(directory)
            
            for item in directory_path.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
            
            return total_size
        except Exception as e:
            self.logger.error(f"计算目录大小失败: {directory} - {e}")
            return 0 