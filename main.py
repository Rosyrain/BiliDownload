#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BiliDownload 主程序入口
B站资源下载器 - 支持视频、音频等多种资源类型
"""

import sys
import os
import traceback
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def main():
    """主函数"""
    try:
        # 导入日志管理器
        from src.core.logger import get_logger
        
        # 获取日志管理器
        logger = get_logger("Main")
        logger.info("BiliDownload 程序启动")
        
        # 导入主窗口
        from ui.main_window import main as main_window_main
        
        # 启动应用程序
        logger.info("启动主窗口")
        main_window_main()
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保已安装所有依赖包: pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"程序启动失败: {e}")
        print("详细错误信息:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 