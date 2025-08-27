#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试日志系统
"""

import sys
import os

def test_logger():
    """测试日志系统"""
    try:
        # 添加当前目录到Python路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        # 导入日志管理器
        from src.core.logger import get_logger, app_logger
        
        print("开始测试日志系统...")
        
        # 获取日志管理器
        logger = get_logger("TestLogger")
        
        # 测试各种日志级别
        logger.info("这是一条信息日志")
        logger.warning("这是一条警告日志")
        logger.error("这是一条错误日志")
        logger.debug("这是一条调试日志")
        
        # 测试下载日志
        logger.download_info("开始下载测试视频")
        logger.log_download_progress(50, "下载进度50%")
        logger.log_download_complete("https://example.com", True, "下载成功")
        
        # 测试配置变更日志
        logger.log_config_change("DEFAULT", "download_path", "/test/path")
        
        # 测试分类操作日志
        logger.log_category_operation("创建", "测试分类", "用于测试")
        
        # 测试文件操作日志
        logger.log_file_operation("删除", "/test/file.txt", True)
        
        # 测试异常日志
        try:
            raise ValueError("测试异常")
        except Exception as e:
            logger.log_exception("捕获到异常", e)
        
        print("✅ 日志系统测试完成！")
        print("请检查 logs/ 目录下的日志文件:")
        print("  - app.log: 普通应用日志")
        print("  - error.log: 错误日志")
        print("  - download.log: 下载日志")
        
        return True
        
    except Exception as e:
        print(f"❌ 日志系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_logger()
    
    if not success:
        print("\n请检查以下问题:")
        print("1. 项目结构是否正确")
        print("2. Python版本是否为3.8+")
        print("3. 是否有写入权限")
    
    input("\n按回车键退出...") 