"""
Main entry point for BiliDownload application.

This module initializes the application and launches the main window.
It sets up logging and handles the application lifecycle.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Import logger manager
from src.core.logger import get_logger

# Get logger instance
logger = get_logger("Main")

# Import main window
from src.ui.main_window import MainWindow


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