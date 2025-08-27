#!/usr/bin/env python3
"""
测试FFmpeg配置的读取和保存
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.config_manager import ConfigManager
from src.core.downloader import BiliDownloader

def test_ffmpeg_config():
    """测试FFmpeg配置功能"""
    print("=== 测试FFmpeg配置功能 ===")
    
    # 创建配置管理器
    config_manager = ConfigManager("test_config.ini")
    
    # 测试默认FFmpeg路径
    print(f"默认FFmpeg路径: '{config_manager.get_ffmpeg_path()}'")
    
    # 设置FFmpeg路径
    test_ffmpeg_path = "/opt/brew/bin/ffmpeg"
    print(f"设置FFmpeg路径: {test_ffmpeg_path}")
    config_manager.set_ffmpeg_path(test_ffmpeg_path)
    
    # 验证是否保存成功
    saved_path = config_manager.get_ffmpeg_path()
    print(f"保存后的FFmpeg路径: '{saved_path}'")
    
    if saved_path == test_ffmpeg_path:
        print("✅ FFmpeg路径保存成功")
    else:
        print("❌ FFmpeg路径保存失败")
    
    # 测试下载器是否能正确获取FFmpeg路径
    print("\n=== 测试下载器FFmpeg路径获取 ===")
    downloader = BiliDownloader(config_manager)
    
    # 检查下载器是否有配置管理器
    if hasattr(downloader, 'config_manager') and downloader.config_manager:
        print("✅ 下载器已关联配置管理器")
        
        # 测试从配置中获取FFmpeg路径
        ffmpeg_path = downloader.config_manager.get_ffmpeg_path()
        print(f"下载器获取的FFmpeg路径: '{ffmpeg_path}'")
        
        if ffmpeg_path == test_ffmpeg_path:
            print("✅ 下载器能正确获取FFmpeg路径")
        else:
            print("❌ 下载器获取FFmpeg路径失败")
    else:
        print("❌ 下载器未关联配置管理器")
    
    # 检查配置文件内容
    print("\n=== 检查配置文件内容 ===")
    if os.path.exists("test_config.ini"):
        with open("test_config.ini", "r", encoding="utf-8") as f:
            content = f.read()
            print("配置文件内容:")
            print(content)
    else:
        print("❌ 配置文件未创建")
    
    # 清理测试文件
    if os.path.exists("test_config.ini"):
        os.remove("test_config.ini")
        print("\n已清理测试配置文件")

if __name__ == "__main__":
    test_ffmpeg_config() 