"""
主窗口界面
"""
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QLineEdit, QFileDialog,
    QProgressBar, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu,
    QMessageBox, QComboBox, QSpinBox, QCheckBox, QGroupBox,
    QSplitter, QFrame, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QIcon, QFont, QPixmap, QCursor, QAction

from src.core.downloader import BiliDownloader
from src.core.config_manager import ConfigManager
from src.core.file_manager import FileManager
from src.ui.download_tab import DownloadTab
from src.ui.file_manager_tab import FileManagerTab
from src.ui.category_tab import CategoryTab
from src.ui.settings_tab import SettingsTab


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.downloader = BiliDownloader(self.config_manager)
        self.file_manager = FileManager(self.config_manager.get_download_path())
        
        # 设置窗口大小调整策略
        try:
            self.setSizeGripEnabled(True)
        except AttributeError:
            # 如果setSizeGripEnabled不可用，使用其他方式
            pass
        self.setMinimumSize(1200, 800)
        
        self.init_ui()
        self.setup_connections()
        self.load_config()
        
        # 设置窗口大小调整事件
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.save_window_size)
    
    def resizeEvent(self, event):
        """窗口大小调整事件"""
        super().resizeEvent(event)
        
        # 延迟保存窗口大小，避免频繁保存
        self.resize_timer.start(500)  # 500ms后保存
    
    def save_window_size(self):
        """保存窗口大小到配置文件"""
        try:
            # 默默记录，不打印日志
            self.config_manager.set('UI', 'window_width', str(self.width()))
            self.config_manager.set('UI', 'window_height', str(self.height()))
        except Exception:
            # 静默处理错误，不记录日志
            pass
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("BiliDownload - B站资源下载器")
        self.setGeometry(100, 100, 1600, 1000)
        
        # 设置窗口图标
        self.setWindowIcon(self.create_icon())
        
        # 应用柔和主题样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9ff;
            }
            QTabWidget::pane {
                border: 1px solid #e1e8ff;
                background: #ffffff;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #f0f4ff;
                color: #5a6acf;
                padding: 12px 20px;
                margin-right: 4px;
                border: 1px solid #e1e8ff;
                border-bottom: none;
                border-radius: 8px 8px 0 0;
                font-weight: 600;
                font-size: 13px;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom: 1px solid #ffffff;
                color: #4a5bbf;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #e8f0ff;
                color: #4a5bbf;
            }
            QPushButton {
                background-color: #e8f0ff;
                color: #5a6acf;
                border: 1px solid #d1d8ff;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #d8e8ff;
                border-color: #b8c8ff;
            }
            QPushButton:pressed {
                background-color: #c8d8ff;
            }
            QLabel {
                color: #4a5bbf;
            }
            QGroupBox {
                font-weight: bold;
                color: #5a6acf;
                border: 2px solid #e1e8ff;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: #f8f9ff;
            }
        """)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # 创建标题栏
        title_bar = self.create_title_bar()
        main_layout.addWidget(title_bar)
        
        # 创建主内容区域（左侧标签页 + 右侧文件管理）
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(content_splitter)
        
        # 左侧：功能标签页
        left_panel = self.create_left_panel()
        content_splitter.addWidget(left_panel)
        
        # 右侧：文件管理展示
        right_panel = self.create_right_panel()
        content_splitter.addWidget(right_panel)
        
        # 设置分割器比例 (左侧功能区域:右侧文件管理 = 2:1)
        content_splitter.setSizes([1000, 500])
        
        # 底部：固定配置区域
        bottom_panel = self.create_bottom_panel()
        main_layout.addWidget(bottom_panel)
        
        # 初始化状态标签引用
        self.status_label = bottom_panel.findChild(QLabel, "status_label")
        
        # 界面创建完成后，延迟刷新文件显示
        QTimer.singleShot(100, self.refresh_file_display)
    
    def create_title_bar(self) -> QWidget:
        """创建标题栏"""
        title_bar = QFrame()
        title_bar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #f0f4ff, stop:1 #e8f0ff);
                border: 1px solid #e1e8ff;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # 左侧：标题和图标
        title_layout = QHBoxLayout()
        
        # 图标（使用emoji作为临时图标）
        icon_label = QLabel("🎬")
        icon_label.setStyleSheet("font-size: 24px; margin-right: 10px;")
        title_layout.addWidget(icon_label)
        
        # 主标题
        title_label = QLabel("BiliDownload")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #4a5bbf;
            margin-right: 5px;
        """)
        title_layout.addWidget(title_label)
        
        # 副标题
        subtitle_label = QLabel("B站资源下载器")
        subtitle_label.setStyleSheet("""
            font-size: 14px;
            color: #8a9acf;
            font-style: italic;
        """)
        title_layout.addWidget(subtitle_label)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        # 右侧：快速操作按钮
        quick_actions = QHBoxLayout()
        quick_actions.setSpacing(10)
        
        # 快速下载按钮
        quick_download_btn = QPushButton("⚡ 快速下载")
        quick_download_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a5bbf;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3a4baf;
            }
        """)
        quick_download_btn.clicked.connect(self.show_quick_download)
        quick_actions.addWidget(quick_download_btn)
        
        # 设置按钮
        settings_btn = QPushButton("⚙️ 设置")
        settings_btn.clicked.connect(self.show_settings)
        quick_actions.addWidget(settings_btn)
        
        layout.addLayout(quick_actions)
        
        return title_bar
    
    def create_left_panel(self) -> QWidget:
        """创建左侧功能面板"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e1e8ff;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 功能标签页标题
        title_label = QLabel("功能导航")
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #4a5bbf;
            margin-bottom: 10px;
            padding: 10px;
            background: #f8f9ff;
            border-radius: 6px;
        """)
        layout.addWidget(title_label)
        
        # 创建功能标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: #f0f4ff;
                color: #5a6acf;
                padding: 15px 25px;
                margin-right: 6px;
                margin-bottom: 4px;
                border: 1px solid #e1e8ff;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                min-width: 140px;
                min-height: 20px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border: 2px solid #4a5bbf;
                color: #4a5bbf;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #e8f0ff;
                border-color: #b8c8ff;
            }
        """)
        
        # 添加各个功能标签页
        self.download_tab = DownloadTab(self.downloader, self.config_manager)
        self.file_manager_tab = FileManagerTab(self.file_manager, self.config_manager)
        self.category_tab = CategoryTab(self.config_manager)
        self.settings_tab = SettingsTab(self.config_manager)
        
        self.tab_widget.addTab(self.download_tab, "📥 下载管理")
        self.tab_widget.addTab(self.file_manager_tab, "📁 文件管理")
        self.tab_widget.addTab(self.category_tab, "🏷️ 分类管理")
        self.tab_widget.addTab(self.settings_tab, "⚙️ 设置")
        
        layout.addWidget(self.tab_widget)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """创建右侧文件管理展示面板"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e1e8ff;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 文件管理标题
        title_label = QLabel("📁 文件管理")
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #4a5bbf;
            margin-bottom: 10px;
            padding: 10px;
            background: #f8f9ff;
            border-radius: 6px;
        """)
        layout.addWidget(title_label)
        
        # 文件管理内容（简化版本，主要用于展示）
        self.file_display_widget = self.create_file_display()
        layout.addWidget(self.file_display_widget)
        
        return panel
    
    def create_file_display(self) -> QWidget:
        """创建文件展示组件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 当前路径显示
        path_frame = QFrame()
        path_frame.setStyleSheet("""
            QFrame {
                background: #f8f9ff;
                border: 1px solid #e1e8ff;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        path_layout = QHBoxLayout(path_frame)
        
        path_label = QLabel("当前路径:")
        path_label.setStyleSheet("font-weight: bold; color: #5a6acf;")
        path_layout.addWidget(path_label)
        
        self.current_path_label = QLabel(self.config_manager.get_download_path())
        self.current_path_label.setStyleSheet("""
            color: #4a5bbf;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 11px;
            padding: 4px 8px;
            background: white;
            border: 1px solid #e1e8ff;
            border-radius: 4px;
        """)
        path_layout.addWidget(self.current_path_label)
        path_layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a5bbf;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #3a4baf;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_file_display)
        path_layout.addWidget(refresh_btn)
        
        layout.addWidget(path_frame)
        
        # 文件列表（简化版本）
        self.file_list = QTableWidget()
        self.file_list.setColumnCount(4)
        self.file_list.setHorizontalHeaderLabels(["名称", "类型", "大小", "修改时间"])
        self.file_list.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e1e8ff;
                border-radius: 6px;
                background: white;
                gridline-color: #f0f4ff;
            }
            QHeaderView::section {
                background-color: #f0f4ff;
                color: #5a6acf;
                padding: 8px;
                border: none;
                border-right: 1px solid #e1e8ff;
                border-bottom: 1px solid #e1e8ff;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f8f9ff;
            }
            QTableWidget::item:selected {
                background-color: #e8f0ff;
                color: #4a5bbf;
            }
        """)
        
        # 设置列宽
        header = self.file_list.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.file_list)
        
        # 不在这里立即刷新，等界面创建完成后再刷新
        # self.refresh_file_display()
        
        return widget
    
    def create_bottom_panel(self) -> QWidget:
        """创建底部固定配置面板"""
        bottom_panel = QFrame()
        bottom_panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #f8f9ff, stop:1 #f0f4ff);
                border: 1px solid #e1e8ff;
                border-radius: 8px;
                padding: 5px;
            }
        """)
        
        layout = QHBoxLayout(bottom_panel)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # 左侧：软件信息
        info_layout = QHBoxLayout()
        
        # 版本信息
        version_label = QLabel("版本: 2.0.0")
        version_label.setStyleSheet("color: #8a9acf; font-size: 12px;")
        info_layout.addWidget(version_label)
        
        # 状态信息
        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("status_label")  # 设置对象名称
        self.status_label.setStyleSheet("color: #5a6acf; font-size: 12px; font-weight: 500;")
        info_layout.addWidget(QLabel(" | "))
        info_layout.addWidget(self.status_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # 右侧：快速操作
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(10)
        
        # 打开下载目录
        open_download_btn = QPushButton("📁 打开下载目录")
        open_download_btn.setStyleSheet("""
            QPushButton {
                background-color: #e8f0ff;
                color: #5a6acf;
                border: 1px solid #d1d8ff;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #d8e8ff;
            }
        """)
        open_download_btn.clicked.connect(self.open_download_directory)
        quick_layout.addWidget(open_download_btn)
        
        # 检查更新
        check_update_btn = QPushButton("🔄 检查更新")
        check_update_btn.setStyleSheet("""
            QPushButton {
                background-color: #e8f0ff;
                color: #5a6acf;
                border: 1px solid #d1d8ff;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #d8e8ff;
            }
        """)
        check_update_btn.clicked.connect(self.check_for_updates)
        quick_layout.addWidget(check_update_btn)
        
        # 关于
        about_btn = QPushButton("ℹ️ 关于")
        about_btn.setStyleSheet("""
            QPushButton {
                background-color: #e8f0ff;
                color: #5a6acf;
                border: 1px solid #d1d8ff;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #d8e8ff;
            }
        """)
        about_btn.clicked.connect(self.show_about)
        quick_layout.addWidget(about_btn)
        
        layout.addLayout(quick_layout)
        
        return bottom_panel
    
    def create_icon(self):
        """创建窗口图标"""
        # 使用emoji作为临时图标
        return QIcon()
    
    def setup_connections(self):
        """设置信号连接"""
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
    
    def load_config(self):
        """加载配置"""
        # 加载窗口大小和位置
        width = int(self.config_manager.get('UI', 'window_width', '1600'))
        height = int(self.config_manager.get('UI', 'window_height', '1000'))
        self.resize(width, height)
    
    def on_tab_changed(self, index):
        """标签页切换事件"""
        tab_names = ["下载管理", "文件管理", "分类管理", "设置"]
        if 0 <= index < len(tab_names):
            self.status_label.setText(f"当前功能: {tab_names[index]}")
    
    def refresh_file_display(self):
        """刷新文件显示"""
        try:
            files = self.file_manager.get_files_in_directory()
            
            self.file_list.setRowCount(len(files))
            
            for row, file_info in enumerate(files):
                # 名称
                name_item = QTableWidgetItem(file_info['name'])
                if file_info['is_dir']:
                    name_item.setIcon(self.create_folder_icon())
                else:
                    name_item.setIcon(self.create_file_icon())
                self.file_list.setItem(row, 0, name_item)
                
                # 类型
                type_text = "文件夹" if file_info['is_dir'] else file_info['extension']
                self.file_list.setItem(row, 1, QTableWidgetItem(type_text))
                
                # 大小
                if file_info['is_dir']:
                    size_text = "-"
                else:
                    size_text = self.file_manager.format_file_size(file_info['size'])
                self.file_list.setItem(row, 2, QTableWidgetItem(size_text))
                
                # 修改时间
                from datetime import datetime
                time_text = datetime.fromtimestamp(file_info['modified']).strftime("%Y-%m-%d %H:%M")
                self.file_list.setItem(row, 3, QTableWidgetItem(time_text))
            
            self.status_label.setText(f"文件数量: {len(files)}")
            
        except Exception as e:
            self.status_label.setText(f"刷新失败: {str(e)}")
    
    def create_folder_icon(self):
        """创建文件夹图标"""
        return QIcon()
    
    def create_file_icon(self):
        """创建文件图标"""
        return QIcon()
    
    def show_quick_download(self):
        """显示快速下载对话框"""
        self.tab_widget.setCurrentIndex(0)  # 切换到下载管理标签页
        self.status_label.setText("快速下载模式")
    
    def show_settings(self):
        """显示设置"""
        self.tab_widget.setCurrentIndex(3)  # 切换到设置标签页
        self.status_label.setText("设置")
    
    def open_download_directory(self):
        """打开下载目录"""
        try:
            self.file_manager.open_folder(self.config_manager.get_download_path())
            self.status_label.setText("已打开下载目录")
        except Exception as e:
            self.status_label.setText(f"打开目录失败: {str(e)}")
    
    def check_for_updates(self):
        """检查更新"""
        self.status_label.setText("检查更新功能待实现")
    
    def show_about(self):
        """显示关于信息"""
        QMessageBox.about(self, "关于 BiliDownload", 
                         "BiliDownload v2.0.0\n\n"
                         "B站资源下载器\n"
                         "支持视频、音频等多种资源类型\n\n"
                         "基于 PyQt6 构建\n"
                         "界面设计：柔和淡蓝色主题")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 保存窗口大小
        self.config_manager.set('UI', 'window_width', str(self.width()))
        self.config_manager.set('UI', 'window_height', str(self.height()))
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("BiliDownload")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("BiliDownload")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 