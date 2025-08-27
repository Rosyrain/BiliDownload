#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BiliDownload 启动脚本
"""

import sys
import os

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    """主函数"""
    try:
        # 导入日志管理器
        from src.core.logger import get_logger
        
        # 获取日志管理器
        logger = get_logger("RunScript")
        logger.info("BiliDownload 启动脚本执行")
        
        # 导入并启动主窗口
        from src.ui.main_window import main as main_window_main
        logger.info("启动主窗口")
        main_window_main()
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main() 