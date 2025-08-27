#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试项目导入是否正常
"""

import sys
import os

def test_imports():
    """测试所有模块的导入"""
    print("开始测试项目导入...")
    
    try:
        # 导入日志管理器
        from src.core.logger import get_logger
        logger = get_logger("TestImports")
        logger.info("开始测试项目导入")
        
        # 测试核心模块
        print("✓ 测试核心模块...")
        logger.info("测试核心模块导入")
        from src.core.downloader import BiliDownloader
        from src.core.config_manager import ConfigManager
        from src.core.file_manager import FileManager
        print("  - 核心模块导入成功")
        logger.info("核心模块导入成功")
        
        # 测试UI模块
        print("✓ 测试UI模块...")
        logger.info("测试UI模块导入")
        from src.ui.main_window import MainWindow
        from src.ui.download_tab import DownloadTab
        from src.ui.file_manager_tab import FileManagerTab
        from src.ui.category_tab import CategoryTab
        from src.ui.settings_tab import SettingsTab
        print("  - UI模块导入成功")
        logger.info("UI模块导入成功")
        
        # 测试配置管理器
        print("✓ 测试配置管理器...")
        logger.info("测试配置管理器")
        config = ConfigManager()
        print(f"  - 下载路径: {config.get_download_path()}")
        print(f"  - 分类数量: {len(config.get_all_categories())}")
        logger.info(f"配置管理器测试完成，下载路径: {config.get_download_path()}")
        
        # 测试下载器
        print("✓ 测试下载器...")
        logger.info("测试下载器")
        downloader = BiliDownloader()
        print("  - 下载器初始化成功")
        logger.info("下载器初始化成功")
        
        # 测试文件管理器
        print("✓ 测试文件管理器...")
        logger.info("测试文件管理器")
        file_manager = FileManager(config.get_download_path())
        print("  - 文件管理器初始化成功")
        logger.info("文件管理器初始化成功")
        
        print("\n🎉 所有模块导入测试通过！项目结构正常。")
        logger.info("所有模块导入测试通过")
        return True
        
    except ImportError as e:
        print(f"\n❌ 导入错误: {e}")
        logger.error(f"导入错误: {e}")
        print("请检查项目结构和依赖安装。")
        return False
        
    except Exception as e:
        print(f"\n❌ 其他错误: {e}")
        logger.error(f"其他错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 添加当前目录到Python路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    success = test_imports()
    
    if not success:
        print("\n请检查以下问题:")
        print("1. 是否安装了所有依赖: pip install -r requirements.txt")
        print("2. 项目结构是否正确")
        print("3. Python版本是否为3.8+")
    
    input("\n按回车键退出...") 