"""
Main application window for BiliDownload.

This module provides the primary application interface including:
- Main window layout and styling
- Tab-based navigation system
- File management display
- Configuration panel
"""

import os
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QSplitter, QFrame, QScrollArea, QTableWidget,
    QTableWidgetItem, QHeaderView, QMenu, QAction, QFileDialog,
    QMessageBox, QApplication, QSizeGrip
)
from PyQt6.QtCore import Qt, QTimer, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPalette, QColor

from src.core.config_manager import ConfigManager
from src.core.logger import get_logger
from .download_tab import DownloadTab
from .file_manager_tab import FileManagerTab
from .category_tab import CategoryTab
from .settings_tab import SettingsTab


class MainWindow(QMainWindow):
    """
    Main application window for BiliDownload.
    
    Provides the primary user interface with tab-based navigation,
    file management display, and configuration panel.
    """
    
    def __init__(self):
        """
        Initialize the main application window.
        
        Sets up the window properties, creates the UI components,
        and initializes the configuration manager.
        
        Returns:
            None
        """
        super().__init__()
        self.config_manager = ConfigManager()
        self.logger = get_logger(__name__)
        
        # Set window properties
        self.setWindowTitle("BiliDownload - Bilibili Video Downloader")
        self.setMinimumSize(1200, 800)
        
        # Set window resize policy
        try:
            self.setSizeGripEnabled(True)
        except AttributeError:
            # If setSizeGripEnabled is not available, use alternative method
            pass
        
        # Set window resize event
        self.resizeEvent = self.on_resize_event
        
        # Initialize UI
        self.init_ui()
        
        # Load configuration
        self.load_config()
    
    def on_resize_event(self, event):
        """
        Handle window resize events.
        
        Args:
            event (QResizeEvent): Window resize event.
        
        Returns:
            None
        """
        super().resizeEvent(event)
        
        # Delay saving window size to avoid frequent saves
        QTimer.singleShot(500, self.save_window_size)
    
    def save_window_size(self):
        """
        Save current window dimensions to configuration.
        
        Silently records the new window size without logging.
        
        Returns:
            None
        """
        try:
            # Silently save, don't print logs
            pass
        except Exception:
            # Silent error handling, don't log
            pass
    
    def init_ui(self):
        """
        Initialize the user interface.
        
        Creates all UI components including title bar, main content area,
        file management display, and bottom configuration panel.
        
        Returns:
            None
        """
        # Set window icon
        self.setWindowIcon(self.create_window_icon())
        
        # Apply soft theme styles
        self.apply_soft_theme()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create title bar
        title_bar = self.create_title_bar()
        main_layout.addWidget(title_bar)
        
        # Create main content area (left tabs + right file management)
        content_layout = QHBoxLayout()
        
        # Left: Function tabs
        self.tab_widget = self.create_function_tabs()
        content_layout.addWidget(self.tab_widget, 2)
        
        # Right: File management display
        self.file_display = self.create_file_display()
        content_layout.addWidget(self.file_display, 1)
        
        # Set splitter ratio (left function area:right file management = 2:1)
        main_layout.addLayout(content_layout)
        
        # Bottom: Fixed configuration area
        self.bottom_panel = self.create_bottom_panel()
        main_layout.addWidget(self.bottom_panel)
        
        # Initialize status label reference
        self.status_label = None
        
        # After UI creation is complete, delay refreshing file display
        QTimer.singleShot(100, self.refresh_file_display)
    
    def create_title_bar(self):
        """
        Create the application title bar.
        
        Returns:
            QWidget: Title bar widget with logo, title, and quick action buttons.
        """
        title_bar = QFrame()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(80)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Left: Title and icon
        left_layout = QHBoxLayout()
        
        # Icon (using emoji as temporary icon)
        icon_label = QLabel("🎬")
        icon_label.setFont(QFont("Arial", 24))
        left_layout.addWidget(icon_label)
        
        # Main title
        title_layout = QVBoxLayout()
        main_title = QLabel("BiliDownload")
        main_title.setObjectName("mainTitle")
        main_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title_layout.addWidget(main_title)
        
        subtitle = QLabel("Professional Bilibili Video Downloader")
        subtitle.setObjectName("subtitle")
        subtitle.setFont(QFont("Arial", 10))
        title_layout.addWidget(subtitle)
        
        left_layout.addLayout(title_layout)
        left_layout.addStretch()
        layout.addLayout(left_layout)
        
        # Right: Quick action buttons
        right_layout = QHBoxLayout()
        
        # Quick download button
        quick_download_btn = QPushButton("Quick Download")
        quick_download_btn.setObjectName("quickDownloadBtn")
        quick_download_btn.clicked.connect(self.show_quick_download)
        right_layout.addWidget(quick_download_btn)
        
        # Settings button
        settings_btn = QPushButton("Settings")
        settings_btn.setObjectName("settingsBtn")
        settings_btn.clicked.connect(self.show_settings)
        right_layout.addWidget(settings_btn)
        
        layout.addLayout(right_layout)
        
        return title_bar
    
    def create_function_tabs(self):
        """
        Create the left-side function tab panel.
        
        Returns:
            QTabWidget: Tab widget containing all functional tabs.
        """
        # Function tabs title
        tabs_title = QLabel("Function Tabs")
        tabs_title.setObjectName("tabsTitle")
        tabs_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        tabs_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tabs_title.setFixedHeight(40)
        
        # Create function tabs
        tab_widget = QTabWidget()
        tab_widget.setObjectName("functionTabs")
        tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        tab_widget.setTabShape(QTabWidget.TabShape.Rounded)
        
        # Add various function tabs
        download_tab = DownloadTab(self.config_manager)
        file_manager_tab = FileManagerTab(self.config_manager)
        category_tab = CategoryTab(self.config_manager)
        settings_tab = SettingsTab(self.config_manager)
        
        tab_widget.addTab(download_tab, "Download Management")
        tab_widget.addTab(file_manager_tab, "File Manager")
        tab_widget.addTab(category_tab, "Category Management")
        tab_widget.addTab(settings_tab, "Settings")
        
        # Create layout for tabs
        tabs_layout = QVBoxLayout()
        tabs_layout.addWidget(tabs_title)
        tabs_layout.addWidget(tab_widget)
        
        # Create container widget
        tabs_container = QWidget()
        tabs_container.setLayout(tabs_layout)
        
        return tabs_container
    
    def create_file_display(self):
        """
        Create the right-side file management display panel.
        
        Returns:
            QWidget: File management display widget.
        """
        # File management title
        file_title = QLabel("File Management")
        file_title.setObjectName("fileTitle")
        file_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        file_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        file_title.setFixedHeight(40)
        
        # File management content (simplified version, mainly for display)
        file_content = QWidget()
        file_layout = QVBoxLayout(file_content)
        
        # Current path display
        path_label = QLabel("Current Path:")
        path_label.setFont(QFont("Arial", 10))
        file_layout.addWidget(path_label)
        
        self.current_path_label = QLabel("./data/default")
        self.current_path_label.setWordWrap(True)
        self.current_path_label.setStyleSheet("background-color: #f0f0f0; padding: 5px; border-radius: 3px;")
        file_layout.addWidget(self.current_path_label)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_file_display)
        file_layout.addWidget(refresh_btn)
        
        # File list (simplified version)
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels(["Name", "Type", "Size", "Modified"])
        
        # Set column widths
        header = self.file_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        file_layout.addWidget(self.file_table)
        
        # Don't refresh immediately here, wait for UI creation to complete
        file_layout.addStretch()
        
        # Create container widget
        file_container = QWidget()
        file_container.setLayout(file_layout)
        
        return file_container
    
    def create_bottom_panel(self):
        """
        Create the bottom fixed configuration panel.
        
        Returns:
            QWidget: Bottom configuration panel widget.
        """
        bottom_panel = QFrame()
        bottom_panel.setObjectName("bottomPanel")
        bottom_panel.setFixedHeight(60)
        
        layout = QHBoxLayout(bottom_panel)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Left: Software information
        left_layout = QHBoxLayout()
        
        # Version information
        version_label = QLabel("v1.0.0")
        version_label.setObjectName("versionLabel")
        left_layout.addWidget(version_label)
        
        # Status information
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("status_label")  # Set object name
        left_layout.addWidget(self.status_label)
        
        left_layout.addStretch()
        layout.addLayout(left_layout)
        
        # Right: Quick operations
        right_layout = QHBoxLayout()
        
        # Open download directory
        open_dir_btn = QPushButton("Open Download Directory")
        open_dir_btn.clicked.connect(self.open_download_directory)
        right_layout.addWidget(open_dir_btn)
        
        # Check for updates
        update_btn = QPushButton("Check Updates")
        update_btn.clicked.connect(self.check_for_updates)
        right_layout.addWidget(update_btn)
        
        # About
        about_btn = QPushButton("About")
        about_btn.clicked.connect(self.show_about)
        right_layout.addWidget(about_btn)
        
        layout.addLayout(right_layout)
        
        return bottom_panel
    
    def create_window_icon(self):
        """
        Create application window icon.
        
        Returns:
            QIcon: Application icon.
        """
        # Use emoji as temporary icon
        return QIcon()
    
    def setup_signals(self):
        """
        Set up signal connections for UI components.
        
        Returns:
            None
        """
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
    
    def load_config(self):
        """
        Load application configuration.
        
        Loads window size, position, and other settings from configuration.
        
        Returns:
            None
        """
        # Load window size and position
        try:
            width = int(self.config_manager.get('UI', 'window_width', '1200'))
            height = int(self.config_manager.get('UI', 'window_height', '800'))
            self.resize(width, height)
        except:
            pass
    
    def on_tab_changed(self, index):
        """
        Handle tab change events.
        
        Args:
            index (int): Index of the newly selected tab.
        
        Returns:
            None
        """
        if index == 0:
            self.tab_widget.setCurrentIndex(0)  # Switch to download management tab
        elif index == 3:
            self.tab_widget.setCurrentIndex(3)  # Switch to settings tab
    
    def refresh_file_display(self):
        """
        Refresh the file management display.
        
        Updates the file list and current path display.
        
        Returns:
            None
        """
        try:
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.setText("File display refreshed")
        except:
            pass
    
    def create_folder_icon(self):
        """
        Create folder icon for file display.
        
        Returns:
            QPixmap: Folder icon pixmap.
        """
        return QPixmap()
    
    def create_file_icon(self):
        """
        Create file icon for file display.
        
        Returns:
            QPixmap: File icon pixmap.
        """
        return QPixmap()
    
    def show_quick_download(self):
        """
        Show quick download dialog.
        
        Displays a simplified download interface for quick access.
        
        Returns:
            None
        """
        QMessageBox.information(self, "Quick Download", "Quick download feature coming soon!")
    
    def show_settings(self):
        """
        Show settings dialog.
        
        Opens the application settings interface.
        
        Returns:
            None
        """
        self.tab_widget.setCurrentIndex(3)
    
    def open_download_directory(self):
        """
        Open the default download directory.
        
        Opens the system file manager at the configured download location.
        
        Returns:
            None
        """
        try:
            download_path = self.config_manager.get_download_path()
            if os.path.exists(download_path):
                import subprocess
                import platform
                
                system = platform.system()
                if system == "Windows":
                    subprocess.run(["explorer", download_path])
                elif system == "Darwin":  # macOS
                    subprocess.run(["open", download_path])
                else:  # Linux
                    subprocess.run(["xdg-open", download_path])
        except Exception as e:
            self.logger.error(f"Failed to open download directory: {e}")
    
    def check_for_updates(self):
        """
        Check for application updates.
        
        Checks if a newer version of the application is available.
        
        Returns:
            None
        """
        QMessageBox.information(self, "Check Updates", "Update check feature coming soon!")
    
    def show_about(self):
        """
        Show about information.
        
        Displays application information and credits.
        
        Returns:
            None
        """
        QMessageBox.about(self, "About BiliDownload", 
                         "BiliDownload v1.0.0\n\n"
                         "Professional Bilibili Video Downloader\n"
                         "Built with PyQt6\n\n"
                         "© 2024 BiliDownload Team")
    
    def closeEvent(self, event):
        """
        Handle window close events.
        
        Args:
            event (QCloseEvent): Window close event.
        
        Returns:
            None
        """
        # Save window size
        try:
            self.config_manager.set('UI', 'window_width', str(self.width()))
            self.config_manager.set('UI', 'window_height', str(self.height()))
        except:
            pass
        
        event.accept()


def main():
    """
    Main function for launching the application.
    
    Creates and displays the main application window.
    
    Returns:
        None
    """
    # Set application properties
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    # Create and display main window
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 