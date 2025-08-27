"""
配置管理器
"""
import os
import json
import configparser
from typing import Dict, List, Optional, Any
from pathlib import Path

from .logger import get_logger


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.logger = get_logger("ConfigManager")
        self.logger.info("配置管理器初始化")
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file, encoding='utf-8')
            self.logger.info(f"已加载配置文件: {self.config_file}")
        else:
            self.logger.info("配置文件不存在，创建默认配置")
            self.create_default_config()
    
    def create_default_config(self):
        """创建默认配置"""
        self.logger.info("创建默认配置")
        
        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent
        default_download_path = str(project_root / "data" / "default")
        
        self.config['DEFAULT'] = {
            'download_path': default_download_path,
            'ffmpeg_path': '',
            'max_concurrent_downloads': '3',
            'auto_create_categories': 'true',
            'default_category': 'default'
        }
        
        self.config['UI'] = {
            'theme': 'light',
            'window_width': '1600',
            'window_height': '1000',
            'language': 'zh_CN'
        }
        
        self.config['DOWNLOAD'] = {
            'chunk_size': '8192',
            'timeout': '30',
            'retry_count': '3',
            'delay_between_requests': '1',
            'enable_resume': 'true',
            'progress_update_interval': '500'
        }
        
        self.config['CATEGORIES'] = {
            'default': 'default',
            'video': 'video',
            'music': 'music',
            'document': 'document'
        }
        
        self.config['ADVANCED'] = {
            'verbose_logging': 'false',
            'max_log_size': '10',
            'log_retention_days': '30',
            'use_proxy': 'false',
            'proxy_host': '',
            'proxy_port': '',
            'debug_mode': 'false'
        }
        
        self.save_config()
        self.logger.info("默认配置创建完成")
        
        # 创建默认目录结构
        self._create_default_directories()
    
    def _create_default_directories(self):
        """创建默认目录结构"""
        try:
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / "data"
            
            # 创建data目录
            data_dir.mkdir(exist_ok=True)
            self.logger.info(f"创建目录: {data_dir}")
            
            # 创建所有分类目录
            categories = self.get_all_categories()
            for category_name, category_path in categories.items():
                category_dir = data_dir / category_path
                category_dir.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"创建分类目录: {category_dir}")
                
        except Exception as e:
            self.logger.error(f"创建默认目录失败: {e}")
    
    def save_config(self):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)
        self.logger.debug(f"配置文件已保存: {self.config_file}")
    
    def get(self, section: str, key: str, fallback: str = None) -> str:
        """获取配置值"""
        return self.config.get(section, key, fallback=fallback)
    
    def set(self, section: str, key: str, value: str):
        """设置配置值"""
        # DEFAULT 节是特殊节，不能手动添加
        if section == 'DEFAULT':
            # 直接设置值，不需要检查节是否存在
            old_value = self.config.get(section, key, fallback=None)
            self.config.set(section, key, value)
        else:
            # 其他节需要检查是否存在
            if not self.config.has_section(section):
                self.config.add_section(section)
                self.logger.debug(f"新增配置节: [{section}]")
            
            old_value = self.config.get(section, key, fallback=None)
            self.config.set(section, key, value)
        
        if old_value != value:
            self.logger.info(f"配置变更: [{section}] {key} = {value}")
            self.logger.log_config_change(section, key, value)
        
        self.save_config()
    
    def get_download_path(self) -> str:
        """获取下载路径"""
        path = self.get('DEFAULT', 'download_path')
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        return path
    
    def set_download_path(self, path: str):
        """设置下载路径"""
        self.set('DEFAULT', 'download_path', path)
    
    def get_ffmpeg_path(self) -> str:
        """获取FFmpeg路径"""
        return self.get('DEFAULT', 'ffmpeg_path')
    
    def set_ffmpeg_path(self, path: str):
        """设置FFmpeg路径"""
        self.set('DEFAULT', 'ffmpeg_path', path)
    
    def get_category_path(self, category_name: str) -> str:
        """获取分类对应的下载路径"""
        try:
            # 从配置中获取分类路径
            category_path = self.config.get('CATEGORIES', category_name, fallback=None)
            if category_path:
                # 构建完整路径
                project_root = Path(__file__).parent.parent.parent
                full_path = project_root / "data" / category_path
                full_path.mkdir(parents=True, exist_ok=True)
                return str(full_path)
            else:
                # 如果分类不存在，返回默认路径
                return self.get_download_path()
        except Exception as e:
            self.logger.error(f"获取分类路径失败: {e}")
            return self.get_download_path()
    
    def get_series_download_path(self, category_name: str, series_name: str) -> str:
        """获取系列视频的下载路径"""
        try:
            # 获取分类路径
            category_path = self.get_category_path(category_name)
            if category_path:
                # 在分类目录下创建系列文件夹
                series_path = Path(category_path) / series_name
                series_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"创建系列目录: {series_path}")
                return str(series_path)
            else:
                # 如果分类路径获取失败，在默认目录下创建
                default_path = self.get_download_path()
                series_path = Path(default_path) / series_name
                series_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"在默认目录创建系列目录: {series_path}")
                return str(series_path)
        except Exception as e:
            self.logger.error(f"获取系列下载路径失败: {e}")
            # 返回默认路径
            return self.get_download_path()
    
    def add_category(self, name: str, path: str = None) -> bool:
        """添加分类"""
        try:
            if not path:
                # 如果没有指定路径，使用分类名作为路径
                path = name
            
            # 添加到配置
            self.config.set('CATEGORIES', name, path)
            
            # 创建对应的目录
            project_root = Path(__file__).parent.parent.parent
            category_dir = project_root / "data" / path
            category_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"添加分类: {name} -> {path}")
            self.logger.log_category_operation("添加", name, f"路径: {path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"添加分类失败: {e}")
            return False
    
    def remove_category(self, name: str) -> bool:
        """删除分类"""
        try:
            if name == 'default':
                self.logger.warning("不能删除默认分类")
                return False
            
            # 从配置中移除
            if self.config.has_option('CATEGORIES', name):
                self.config.remove_option('CATEGORIES', name)
                self.save_config()
                
                self.logger.info(f"删除分类: {name}")
                self.logger.log_category_operation("删除", name)
                
                return True
            else:
                self.logger.warning(f"分类不存在: {name}")
                return False
                
        except Exception as e:
            self.logger.error(f"删除分类失败: {e}")
            return False
    
    def get_all_categories(self) -> Dict[str, str]:
        """获取所有分类"""
        try:
            categories = {}
            if self.config.has_section('CATEGORIES'):
                for key in self.config.options('CATEGORIES'):
                    value = self.config.get('CATEGORIES', key)
                    categories[key] = value
            return categories
        except Exception as e:
            self.logger.error(f"获取分类列表失败: {e}")
            return {}
    
    def get_category_tree(self) -> Dict[str, Any]:
        """获取分类树结构"""
        try:
            categories = self.get_all_categories()
            tree = {}
            
            for name, path in categories.items():
                # 解析路径层级
                path_parts = path.split('/')
                current_level = tree
                
                for i, part in enumerate(path_parts):
                    if part not in current_level:
                        current_level[part] = {
                            'name': part,
                            'full_path': '/'.join(path_parts[:i+1]),
                            'children': {},
                            'is_leaf': i == len(path_parts) - 1
                        }
                    current_level = current_level[part]['children']
            
            return tree
            
        except Exception as e:
            self.logger.error(f"获取分类树失败: {e}")
            return {}
    
    def get_advanced_setting(self, key: str, fallback: str = None) -> str:
        """获取高级设置"""
        return self.config.get('ADVANCED', key, fallback=fallback)
    
    def set_advanced_setting(self, key: str, value: str):
        """设置高级设置"""
        self.config.set('ADVANCED', key, value)
    
    def get_download_setting(self, key: str, fallback: str = None) -> str:
        """获取下载设置"""
        return self.config.get('DOWNLOAD', key, fallback=fallback)
    
    def set_download_setting(self, key: str, value: str):
        """设置下载设置"""
        self.config.set('DOWNLOAD', key, value) 