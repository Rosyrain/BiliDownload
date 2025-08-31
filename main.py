"""
Main entry point for BiliDownload application.

This module initializes the application and launches the main window.
It sets up logging and handles the application lifecycle.
"""

import sys

from PyQt6.QtWidgets import QApplication

from src.core.managers import ConfigManager, FileManager, get_logger
from src.core.services import CategoryService, DownloadService, FileService
from src.ui.main_window import MainWindow

# Get logger instance
logger = get_logger("BiliDownload")


def main():
    """
    Main application entry point.

    Initializes the PyQt application, creates the main window,
    and starts the event loop.
    """
    try:
        # Create PyQt application
        app = QApplication(sys.argv)
        app.setApplicationName("BiliDownload")
        app.setApplicationVersion("1.0.0")

        # 初始化管理器
        config_manager = ConfigManager()
        file_manager = FileManager()

        # 初始化服务
        download_service = DownloadService(config_manager)
        file_service = FileService(config_manager, file_manager)
        category_service = CategoryService(config_manager)

        # Create and show main window
        window = MainWindow(
            config_manager,
            file_manager,
            download_service,
            file_service,
            category_service,
        )
        window.show()

        # Start application event loop
        sys.exit(app.exec())

    except Exception as e:
        import traceback
        logger.error(f"Application startup failed: {e}")
        logger.error(f"Error details: {traceback.format_exc()}")
        print(f"Exception type: {type(e)}")
        print(f"Exception args: {e.args}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
