#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试项目导入是否正常
"""

import os
import sys


def test_imports():
    """测试所有模块的导入"""
    print("开始测试项目导入...")

    try:
        # 导入日志管理器
        from src.core.managers.logger import get_logger

        logger = get_logger("TestImports")
        logger.info("开始测试项目导入")

        # 测试管理器模块
        print("✓ 测试管理器模块...")
        logger.info("测试管理器模块导入")
        from src.core.managers.config_manager import ConfigManager
        from src.core.managers.downloader import BiliDownloader
        from src.core.managers.file_manager import FileManager

        print("  - 管理器模块导入成功")
        logger.info("管理器模块导入成功")

        # 测试服务模块
        print("✓ 测试服务模块...")
        logger.info("测试服务模块导入")
        from src.core.services.category_service import CategoryService
        from src.core.services.download_service import DownloadService
        from src.core.services.file_service import FileService

        print("  - 服务模块导入成功")
        logger.info("服务模块导入成功")

        # 测试UI模块
        print("✓ 测试UI模块...")
        logger.info("测试UI模块导入")
        from src.ui.category_tab import CategoryTab  # noqa: F401
        from src.ui.download_tab import DownloadTab  # noqa: F401
        from src.ui.file_manager_tab import FileManagerTab  # noqa: F401
        from src.ui.main_window import MainWindow  # noqa: F401
        from src.ui.settings_tab import SettingsTab  # noqa: F401

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
        BiliDownloader(config)
        print("  - 下载器初始化成功")
        logger.info("下载器初始化成功")

        # 测试文件管理器
        print("✓ 测试文件管理器...")
        logger.info("测试文件管理器")
        FileManager()
        print("  - 文件管理器初始化成功")
        logger.info("文件管理器初始化成功")

        # 测试服务
        print("✓ 测试服务...")
        logger.info("测试服务")
        file_manager = FileManager()
        # 初始化服务但不使用变量
        DownloadService(config)
        FileService(config, file_manager)
        CategoryService(config)
        print("  - 服务初始化成功")
        logger.info("服务初始化成功")

        print("\n🎉 所有模块导入测试通过！项目结构正常。")
        logger.info("所有模块导入测试通过")
        return True

    except ImportError as e:
        print(f"\n❌ 导入错误: {e}")
        try:
            from src.core.managers.logger import get_logger

            logger = get_logger("TestImports")
            logger.error(f"导入错误: {e}")
        except Exception as log_error:
            print(f"无法初始化日志记录器: {log_error}")
        print("请检查项目结构和依赖安装。")
        return False

    except Exception as e:
        print(f"\n❌ 其他错误: {e}")
        try:
            from src.core.managers.logger import get_logger

            logger = get_logger("TestImports")
            logger.error(f"其他错误: {e}")
        except Exception as log_error:
            print(f"无法初始化日志记录器: {log_error}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 添加当前目录到Python路径
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, current_dir)

    success = test_imports()

    if not success:
        print("\n请检查以下问题:")
        print("1. 是否安装了所有依赖: pip install -r requirements.txt")
        print("2. 项目结构是否正确")
        print("3. Python版本是否为3.8+")

    input("\n按回车键退出...")
