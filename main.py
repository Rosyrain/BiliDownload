"""
Main entry point for BiliDownload application.

This module initializes the application and launches the main window.
It sets up logging and handles the application lifecycle.
"""

import sys

from PyQt6.QtWidgets import QApplication

from src.core.logger import get_logger
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

        # Create and show main window
        window = MainWindow()
        window.show()

        # Start application event loop
        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
