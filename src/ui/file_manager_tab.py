"""
文件管理器标签页
"""
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMenu, QGroupBox,
    QMessageBox, QComboBox, QFrame, QSplitter,
    QFileDialog, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QCursor, QAction

from src.core.file_manager import FileManager
from src.core.config_manager import ConfigManager


class FileManagerTab(QWidget):
    """文件管理器标签页"""
    
    def __init__(self, file_manager: FileManager, config_manager: ConfigManager):
        super().__init__()
        self.file_manager = file_manager
        self.config_manager = config_manager
        self.current_directory = self.config_manager.get_download_path()
        
        self.init_ui()
        self.refresh_files()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 应用柔和主题样式
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #5a6acf;
                border: 2px solid #e1e8ff;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background: #fafbff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: #fafbff;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #d1d8ff;
                border-radius: 6px;
                background: white;
                color: #4a5bbf;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #4a5bbf;
                background: #fefeff;
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
            QTableWidget {
                border: 1px solid #e1e8ff;
                border-radius: 6px;
                background: white;
                gridline-color: #f0f4ff;
                selection-background-color: #e8f0ff;
                selection-color: #4a5bbf;
            }
            QHeaderView::section {
                background-color: #f0f4ff;
                color: #5a6acf;
                padding: 8px;
                border: none;
                border-right: 1px solid #e1e8ff;
                border-bottom: 1px solid #e1e8ff;
                font-weight: bold;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f8f9ff;
                color: #4a5bbf;
            }
            QTableWidget::item:selected {
                background-color: #e8f0ff;
                color: #4a5bbf;
            }
            QTableWidget::item:hover {
                background-color: #f8f9ff;
            }
            QLabel {
                color: #4a5bbf;
                font-weight: 500;
            }
            QComboBox {
                padding: 6px;
                border: 1px solid #d1d8ff;
                border-radius: 6px;
                background: white;
                color: #4a5bbf;
                font-size: 12px;
            }
            QComboBox:focus {
                border-color: #4a5bbf;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #5a6acf;
                margin-right: 5px;
            }
            QTreeWidget {
                border: 1px solid #e1e8ff;
                border-radius: 6px;
                background: white;
                color: #4a5bbf;
            }
            QTreeWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f8f9ff;
            }
            QTreeWidget::item:selected {
                background-color: #e8f0ff;
                color: #4a5bbf;
            }
            QTreeWidget::item:hover {
                background-color: #f8f9ff;
            }
        """)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # 左侧：目录树和搜索
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右侧：文件列表
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setSizes([300, 700])
        
        # 底部：状态栏
        bottom_panel = self.create_bottom_panel()
        layout.addWidget(bottom_panel)
    
    def create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 标题
        title_label = QLabel("目录导航")
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #0078d4;
            margin-bottom: 10px;
        """)
        layout.addWidget(title_label)
        
        # 当前路径显示
        path_group = QGroupBox("当前路径")
        path_layout = QVBoxLayout(path_group)
        
        self.path_label = QLabel(self.current_directory)
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-family: "Consolas", "Monaco", monospace;
                font-size: 11px;
            }
        """)
        path_layout.addWidget(self.path_label)
        
        # 路径操作按钮
        path_buttons_layout = QHBoxLayout()
        
        self.browse_btn = QPushButton("浏览")
        self.browse_btn.clicked.connect(self.browse_directory)
        path_buttons_layout.addWidget(self.browse_btn)
        
        self.parent_btn = QPushButton("上级目录")
        self.parent_btn.clicked.connect(self.go_parent_directory)
        path_buttons_layout.addWidget(self.parent_btn)
        
        self.home_btn = QPushButton("下载目录")
        self.home_btn.clicked.connect(self.go_home_directory)
        path_buttons_layout.addWidget(self.home_btn)
        
        path_layout.addLayout(path_buttons_layout)
        layout.addWidget(path_group)
        
        # 分类选择
        category_group = QGroupBox("分类筛选")
        category_layout = QVBoxLayout(category_group)
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("全部")
        self.refresh_categories()
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        category_layout.addWidget(self.category_combo)
        
        layout.addWidget(category_group)
        
        # 搜索功能
        search_group = QGroupBox("搜索文件")
        search_layout = QVBoxLayout(search_group)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入文件名进行搜索...")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_input)
        
        self.search_btn = QPushButton("搜索")
        self.search_btn.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_btn)
        
        layout.addWidget(search_group)
        
        layout.addStretch()
        return panel
    
    def create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 标题和操作按钮
        header_layout = QHBoxLayout()
        
        title_label = QLabel("文件列表")
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #0078d4;
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 操作按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh_files)
        header_layout.addWidget(self.refresh_btn)
        
        self.new_folder_btn = QPushButton("新建文件夹")
        self.new_folder_btn.clicked.connect(self.create_new_folder)
        header_layout.addWidget(self.new_folder_btn)
        
        layout.addLayout(header_layout)
        
        # 文件表格
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(5)
        self.file_table.setHorizontalHeaderLabels([
            "名称", "大小", "类型", "修改时间", "操作"
        ])
        
        # 设置表格属性
        self.file_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_table.customContextMenuRequested.connect(self.show_context_menu)
        self.file_table.doubleClicked.connect(self.on_file_double_clicked)
        
        # 设置列宽
        header = self.file_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 名称列自适应
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 大小列
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 类型列
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 时间列
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 操作列
        
        layout.addWidget(self.file_table)
        
        return panel
    
    def create_bottom_panel(self) -> QWidget:
        """创建底部状态栏"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # 文件统计
        self.file_count_label = QLabel("文件: 0")
        layout.addWidget(self.file_count_label)
        
        self.folder_count_label = QLabel("文件夹: 0")
        layout.addWidget(self.folder_count_label)
        
        self.total_size_label = QLabel("总大小: 0 B")
        layout.addWidget(self.total_size_label)
        
        return panel
    
    def refresh_files(self):
        """刷新文件列表"""
        try:
            files = self.file_manager.get_files_in_directory(self.current_directory)
            self.update_file_table(files)
            self.update_status()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新文件列表失败: {str(e)}")
    
    def update_file_table(self, files):
        """更新文件表格"""
        self.file_table.setRowCount(len(files))
        
        for row, file_info in enumerate(files):
            # 文件名
            name_item = QTableWidgetItem(file_info['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.file_table.setItem(row, 0, name_item)
            
            # 文件大小
            if file_info['is_dir']:
                size_text = "文件夹"
            else:
                size_text = self.file_manager.format_file_size(file_info['size'])
            size_item = QTableWidgetItem(size_text)
            size_item.setFlags(size_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.file_table.setItem(row, 1, size_item)
            
            # 文件类型
            if file_info['is_dir']:
                type_text = "文件夹"
            else:
                type_text = file_info['extension'] or "文件"
            type_item = QTableWidgetItem(type_text)
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.file_table.setItem(row, 2, type_item)
            
            # 修改时间
            time_text = datetime.fromtimestamp(file_info['modified']).strftime("%Y-%m-%d %H:%M")
            time_item = QTableWidgetItem(time_text)
            time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.file_table.setItem(row, 3, time_item)
            
            # 操作按钮
            if file_info['is_dir']:
                open_btn = QPushButton("打开")
                open_btn.clicked.connect(lambda checked, path=file_info['path']: self.open_directory(path))
            else:
                open_btn = QPushButton("打开")
                open_btn.clicked.connect(lambda checked, path=file_info['path']: self.open_file(path))
            
            open_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
            """)
            
            self.file_table.setCellWidget(row, 4, open_btn)
    
    def update_status(self):
        """更新状态信息"""
        try:
            files = self.file_manager.get_files_in_directory(self.current_directory)
            
            file_count = len([f for f in files if not f['is_dir']])
            folder_count = len([f for f in files if f['is_dir']])
            total_size = sum(f['size'] for f in files if not f['is_dir'])
            
            self.file_count_label.setText(f"文件: {file_count}")
            self.folder_count_label.setText(f"文件夹: {folder_count}")
            self.total_size_label.setText(f"总大小: {self.file_manager.format_file_size(total_size)}")
            
            self.status_label.setText(f"当前目录: {self.current_directory}")
            
        except Exception as e:
            self.status_label.setText(f"状态更新失败: {str(e)}")
    
    def refresh_categories(self):
        """刷新分类列表"""
        self.category_combo.clear()
        self.category_combo.addItem("全部")
        categories = self.config_manager.get_all_categories()
        self.category_combo.addItems(categories)
    
    def browse_directory(self):
        """浏览目录"""
        path = QFileDialog.getExistingDirectory(self, "选择目录", self.current_directory)
        if path:
            self.current_directory = path
            self.path_label.setText(path)
            self.refresh_files()
    
    def go_parent_directory(self):
        """进入上级目录"""
        parent_path = os.path.dirname(self.current_directory)
        if parent_path != self.current_directory:
            self.current_directory = parent_path
            self.path_label.setText(parent_path)
            self.refresh_files()
    
    def go_home_directory(self):
        """进入下载目录"""
        home_path = self.config_manager.get_download_path()
        self.current_directory = home_path
        self.path_label.setText(home_path)
        self.refresh_files()
    
    def on_category_changed(self, category):
        """分类选择改变"""
        if category == "全部":
            self.current_directory = self.config_manager.get_download_path()
        else:
            category_path = self.config_manager.get_category_path(category)
            if category_path:
                self.current_directory = category_path
        
        self.path_label.setText(self.current_directory)
        self.refresh_files()
    
    def on_search_text_changed(self, text):
        """搜索文本改变"""
        if not text:
            self.refresh_files()
    
    def perform_search(self):
        """执行搜索"""
        query = self.search_input.text().strip()
        if not query:
            return
        
        try:
            results = self.file_manager.search_files(query, self.current_directory)
            self.update_file_table(results)
            self.status_label.setText(f"搜索 '{query}' 的结果: {len(results)} 个文件")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"搜索失败: {str(e)}")
    
    def create_new_folder(self):
        """创建新文件夹"""
        name, ok = QInputDialog.getText(self, "新建文件夹", "请输入文件夹名称:")
        if ok and name:
            try:
                if self.file_manager.create_folder(name, self.current_directory):
                    self.refresh_files()
                    QMessageBox.information(self, "成功", f"文件夹 '{name}' 创建成功")
                else:
                    QMessageBox.warning(self, "失败", f"文件夹 '{name}' 创建失败")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建文件夹时出错: {str(e)}")
    
    def open_file(self, file_path):
        """打开文件"""
        try:
            if self.file_manager.open_file(file_path):
                self.status_label.setText(f"正在打开文件: {os.path.basename(file_path)}")
            else:
                QMessageBox.warning(self, "警告", "无法打开文件")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开文件失败: {str(e)}")
    
    def open_directory(self, dir_path):
        """打开目录"""
        try:
            self.current_directory = dir_path
            self.path_label.setText(dir_path)
            self.refresh_files()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开目录失败: {str(e)}")
    
    def on_file_double_clicked(self, index):
        """文件双击事件"""
        row = index.row()
        file_name = self.file_table.item(row, 0).text()
        file_path = os.path.join(self.current_directory, file_name)
        
        if os.path.isdir(file_path):
            self.open_directory(file_path)
        else:
            self.open_file(file_path)
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        context_menu = QMenu()
        
        # 获取选中的行
        row = self.file_table.rowAt(position.y())
        if row >= 0:
            file_name = self.file_table.item(row, 0).text()
            file_path = os.path.join(self.current_directory, file_name)
            
            # 添加菜单项
            if os.path.isdir(file_path):
                open_action = QAction("打开文件夹", self)
                open_action.triggered.connect(lambda: self.open_directory(file_path))
                context_menu.addAction(open_action)
                
                open_explorer_action = QAction("在资源管理器中显示", self)
                open_explorer_action.triggered.connect(lambda: self.file_manager.open_folder(file_path))
                context_menu.addAction(open_explorer_action)
            else:
                open_action = QAction("打开文件", self)
                open_action.triggered.connect(lambda: self.open_file(file_path))
                context_menu.addAction(open_action)
                
                open_folder_action = QAction("在文件夹中显示", self)
                open_folder_action.triggered.connect(lambda: self.file_manager.open_folder(os.path.dirname(file_path)))
                context_menu.addAction(open_folder_action)
            
            context_menu.addSeparator()
            
            # 复制路径
            copy_path_action = QAction("复制路径", self)
            copy_path_action.triggered.connect(lambda: self.copy_path_to_clipboard(file_path))
            context_menu.addAction(copy_path_action)
            
            # 删除文件
            delete_action = QAction("删除", self)
            delete_action.triggered.connect(lambda: self.delete_file(file_path, file_name))
            context_menu.addAction(delete_action)
        
        # 显示菜单
        if context_menu.actions():
            context_menu.exec(self.file_table.mapToGlobal(position))
    
    def copy_path_to_clipboard(self, file_path):
        """复制文件路径到剪贴板"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(file_path)
        self.status_label.setText("路径已复制到剪贴板")
    
    def delete_file(self, file_path, file_name):
        """删除文件"""
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除 '{file_name}' 吗？\n此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.file_manager.delete_file(file_path):
                    self.refresh_files()
                    QMessageBox.information(self, "成功", f"'{file_name}' 删除成功")
                else:
                    QMessageBox.warning(self, "失败", f"'{file_name}' 删除失败")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除文件时出错: {str(e)}") 