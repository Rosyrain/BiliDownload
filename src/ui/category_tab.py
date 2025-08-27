"""
分类管理标签页
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTreeWidget,
    QTreeWidgetItem, QHeaderView, QMenu, QComboBox,
    QMessageBox, QInputDialog, QGroupBox, QFrame,
    QSplitter, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QAction

from src.core.config_manager import ConfigManager


class CategoryTab(QWidget):
    """分类管理标签页"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        
        self.init_ui()
        self.refresh_categories()
    
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
            QTextEdit {
                border: 1px solid #e1e8ff;
                border-radius: 6px;
                background: white;
                color: #4a5bbf;
                font-family: 'Monaco', 'Consolas', monospace;
                font-size: 11px;
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
        """)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # 左侧：分类树
        left_panel = self.create_category_tree_panel()
        splitter.addWidget(left_panel)
        
        # 右侧：分类详情和操作
        right_panel = self.create_category_detail_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setSizes([400, 600])
    
    def create_category_tree_panel(self) -> QWidget:
        """创建分类树面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 标题
        title_label = QLabel("分类树")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #0078d4;
            margin-bottom: 10px;
        """)
        layout.addWidget(title_label)
        
        # 分类树
        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderLabel("分类名称")
        self.category_tree.setAlternatingRowColors(True)
        self.category_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.category_tree.customContextMenuRequested.connect(self.show_category_context_menu)
        self.category_tree.itemClicked.connect(self.on_category_selected)
        
        # 设置样式
        self.category_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
            QTreeWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f8f9fa;
            }
            QTreeWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QTreeWidget::item:hover {
                background-color: #f8f9fa;
            }
        """)
        
        layout.addWidget(self.category_tree)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.add_category_btn = QPushButton("添加分类")
        self.add_category_btn.clicked.connect(self.add_category)
        button_layout.addWidget(self.add_category_btn)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh_categories)
        button_layout.addWidget(self.refresh_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        return panel
    
    def create_category_detail_panel(self) -> QWidget:
        """创建分类详情面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 标题
        title_label = QLabel("分类详情")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #0078d4;
            margin-bottom: 10px;
        """)
        layout.addWidget(title_label)
        
        # 分类信息
        info_group = QGroupBox("基本信息")
        info_layout = QGridLayout(info_group)
        
        info_layout.addWidget(QLabel("分类名称:"), 0, 0)
        self.category_name_input = QLineEdit()
        self.category_name_input.setPlaceholderText("分类名称")
        info_layout.addWidget(self.category_name_input, 0, 1)
        
        info_layout.addWidget(QLabel("父分类:"), 1, 0)
        self.parent_category_combo = QComboBox()
        self.parent_category_combo.addItem("无")
        info_layout.addWidget(self.parent_category_combo, 1, 1)
        
        info_layout.addWidget(QLabel("描述:"), 2, 0)
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("分类描述（可选）")
        info_layout.addWidget(self.description_input, 2, 1)
        
        info_layout.addWidget(QLabel("路径:"), 3, 0)
        self.path_label = QLabel("")
        self.path_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px;
                font-family: "Consolas", "Monaco", monospace;
                font-size: 11px;
            }
        """)
        info_layout.addWidget(self.path_label, 3, 1)
        
        layout.addWidget(info_group)
        
        # 操作按钮
        operation_group = QGroupBox("操作")
        operation_layout = QHBoxLayout(operation_group)
        
        self.save_btn = QPushButton("保存修改")
        self.save_btn.clicked.connect(self.save_category)
        self.save_btn.setEnabled(False)
        operation_layout.addWidget(self.save_btn)
        
        self.delete_btn = QPushButton("删除分类")
        self.delete_btn.clicked.connect(self.delete_category)
        self.delete_btn.setEnabled(False)
        operation_layout.addWidget(self.delete_btn)
        
        self.open_folder_btn = QPushButton("打开文件夹")
        self.open_folder_btn.clicked.connect(self.open_category_folder)
        self.open_folder_btn.setEnabled(False)
        operation_layout.addWidget(self.open_folder_btn)
        
        operation_layout.addStretch()
        layout.addWidget(operation_group)
        
        # 分类统计
        stats_group = QGroupBox("统计信息")
        stats_layout = QGridLayout(stats_group)
        
        self.file_count_label = QLabel("文件数量: 0")
        stats_layout.addWidget(self.file_count_label, 0, 0)
        
        self.folder_count_label = QLabel("子文件夹: 0")
        stats_layout.addWidget(self.folder_count_label, 0, 1)
        
        self.total_size_label = QLabel("总大小: 0 B")
        stats_layout.addWidget(self.total_size_label, 1, 0)
        
        self.created_time_label = QLabel("创建时间: -")
        stats_layout.addWidget(self.created_time_label, 1, 1)
        
        layout.addWidget(stats_group)
        
        # 子分类列表
        children_group = QGroupBox("子分类")
        children_layout = QVBoxLayout(children_group)
        
        self.children_list = QTextEdit()
        self.children_list.setReadOnly(True)
        self.children_list.setMaximumHeight(100)
        self.children_list.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: "Consolas", "Monaco", monospace;
                font-size: 11px;
            }
        """)
        children_layout.addWidget(self.children_list)
        
        layout.addWidget(children_group)
        
        layout.addStretch()
        return panel
    
    def refresh_categories(self):
        """刷新分类列表"""
        try:
            # 清空分类树
            self.category_tree.clear()
            
            # 获取分类数据
            categories = self.config_manager.get_category_tree()
            
            # 构建分类树
            root_items = []
            for name, info in categories.items():
                if info['parent'] is None:
                    item = QTreeWidgetItem([name])
                    item.setData(0, Qt.ItemDataRole.UserRole, name)
                    self.add_children_to_tree(item, categories)
                    root_items.append(item)
            
            self.category_tree.addTopLevelItems(root_items)
            
            # 刷新父分类下拉框
            self.refresh_parent_category_combo()
            
            # 展开所有项目
            self.category_tree.expandAll()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新分类失败: {str(e)}")
    
    def add_children_to_tree(self, parent_item, categories):
        """递归添加子分类到树中"""
        parent_name = parent_item.data(0, Qt.ItemDataRole.UserRole)
        if parent_name in categories:
            for child_name in categories[parent_name]['children']:
                child_item = QTreeWidgetItem([child_name])
                child_item.setData(0, Qt.ItemDataRole.UserRole, child_name)
                parent_item.addChild(child_item)
                self.add_children_to_tree(child_item, categories)
    
    def refresh_parent_category_combo(self):
        """刷新父分类下拉框"""
        self.parent_category_combo.clear()
        self.parent_category_combo.addItem("无")
        
        categories = self.config_manager.get_all_categories()
        for category in categories:
            self.parent_category_combo.addItem(category)
    
    def on_category_selected(self, item, column):
        """分类选择事件"""
        category_name = item.data(0, Qt.ItemDataRole.UserRole)
        self.load_category_details(category_name)
    
    def load_category_details(self, category_name):
        """加载分类详情"""
        try:
            categories = self.config_manager.get_category_tree()
            if category_name not in categories:
                return
            
            category_info = categories[category_name]
            
            # 更新UI
            self.category_name_input.setText(category_name)
            self.category_name_input.setEnabled(False)  # 分类名称不可编辑
            
            # 设置父分类
            parent = category_info['parent']
            if parent:
                index = self.parent_category_combo.findText(parent)
                if index >= 0:
                    self.parent_category_combo.setCurrentIndex(index)
            else:
                self.parent_category_combo.setCurrentIndex(0)
            
            # 设置描述
            self.description_input.setText(category_info.get('description', ''))
            
            # 设置路径
            path = category_info.get('path', '')
            self.path_label.setText(path)
            
            # 设置统计信息
            self.update_category_stats(category_name)
            
            # 设置子分类
            children = category_info.get('children', [])
            if children:
                self.children_list.setText('\n'.join(children))
            else:
                self.children_list.setText("无子分类")
            
            # 启用操作按钮
            self.save_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            self.open_folder_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载分类详情失败: {str(e)}")
    
    def update_category_stats(self, category_name):
        """更新分类统计信息"""
        try:
            from ..core.file_manager import FileManager
            
            category_path = self.config_manager.get_category_path(category_name)
            if not category_path or not os.path.exists(category_path):
                self.file_count_label.setText("文件数量: 0")
                self.folder_count_label.setText("子文件夹: 0")
                self.total_size_label.setText("总大小: 0 B")
                return
            
            file_manager = FileManager(category_path)
            files = file_manager.get_files_in_directory()
            
            file_count = len([f for f in files if not f['is_dir']])
            folder_count = len([f for f in files if f['is_dir']])
            total_size = sum(f['size'] for f in files if not f['is_dir'])
            
            self.file_count_label.setText(f"文件数量: {file_count}")
            self.folder_count_label.setText(f"子文件夹: {folder_count}")
            self.total_size_label.setText(f"总大小: {file_manager.format_file_size(total_size)}")
            
            # 设置创建时间
            categories = self.config_manager.get_category_tree()
            if category_name in categories:
                created_time = categories[category_name].get('created_at', '')
                if created_time:
                    from datetime import datetime
                    try:
                        dt = datetime.fromisoformat(created_time)
                        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                        self.created_time_label.setText(f"创建时间: {time_str}")
                    except:
                        self.created_time_label.setText(f"创建时间: {created_time}")
                else:
                    self.created_time_label.setText("创建时间: -")
            
        except Exception as e:
            self.file_count_label.setText("文件数量: 错误")
            self.folder_count_label.setText("子文件夹: 错误")
            self.total_size_label.setText("总大小: 错误")
    
    def add_category(self):
        """添加分类"""
        name, ok = QInputDialog.getText(self, "添加分类", "请输入分类名称:")
        if ok and name:
            if not name.strip():
                QMessageBox.warning(self, "警告", "分类名称不能为空")
                return
            
            if name in self.config_manager.get_all_categories():
                QMessageBox.warning(self, "警告", f"分类 '{name}' 已存在")
                return
            
            # 选择父分类
            parent, ok = QInputDialog.getItem(
                self, "选择父分类", "请选择父分类（可选）:",
                ["无"] + self.config_manager.get_all_categories(), 0, False
            )
            
            if ok:
                parent = None if parent == "无" else parent
                
                # 输入描述
                description, ok = QInputDialog.getText(
                    self, "分类描述", "请输入分类描述（可选）:"
                )
                
                if ok:
                    try:
                        if self.config_manager.add_category(name, parent, description):
                            self.refresh_categories()
                            QMessageBox.information(self, "成功", f"分类 '{name}' 创建成功")
                        else:
                            QMessageBox.warning(self, "失败", f"分类 '{name}' 创建失败")
                    except Exception as e:
                        QMessageBox.critical(self, "错误", f"创建分类时出错: {str(e)}")
    
    def save_category(self):
        """保存分类修改"""
        try:
            # 获取当前选中的分类
            current_item = self.category_tree.currentItem()
            if not current_item:
                return
            
            category_name = current_item.data(0, Qt.ItemDataRole.UserRole)
            
            # 获取修改后的信息
            new_parent = self.parent_category_combo.currentText()
            if new_parent == "无":
                new_parent = None
            
            description = self.description_input.text().strip()
            
            # 更新分类信息
            # 注意：这里需要重新实现分类更新逻辑
            QMessageBox.information(self, "提示", "分类信息更新功能待实现")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存分类失败: {str(e)}")
    
    def delete_category(self):
        """删除分类"""
        current_item = self.category_tree.currentItem()
        if not current_item:
            return
        
        category_name = current_item.data(0, Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除分类 '{category_name}' 吗？\n此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.config_manager.remove_category(category_name):
                    self.refresh_categories()
                    self.clear_category_details()
                    QMessageBox.information(self, "成功", f"分类 '{category_name}' 删除成功")
                else:
                    QMessageBox.warning(self, "失败", f"分类 '{category_name}' 删除失败")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除分类时出错: {str(e)}")
    
    def open_category_folder(self):
        """打开分类文件夹"""
        current_item = self.category_tree.currentItem()
        if not current_item:
            return
        
        category_name = current_item.data(0, Qt.ItemDataRole.UserRole)
        category_path = self.config_manager.get_category_path(category_name)
        
        if category_path and os.path.exists(category_path):
            try:
                from ..core.file_manager import FileManager
                file_manager = FileManager(category_path)
                file_manager.open_folder(category_path)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"打开文件夹失败: {str(e)}")
        else:
            QMessageBox.warning(self, "警告", "分类文件夹不存在")
    
    def clear_category_details(self):
        """清空分类详情"""
        self.category_name_input.clear()
        self.category_name_input.setEnabled(True)
        self.parent_category_combo.setCurrentIndex(0)
        self.description_input.clear()
        self.path_label.clear()
        self.file_count_label.setText("文件数量: 0")
        self.folder_count_label.setText("子文件夹: 0")
        self.total_size_label.setText("总大小: 0 B")
        self.created_time_label.setText("创建时间: -")
        self.children_list.clear()
        
        # 禁用操作按钮
        self.save_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.open_folder_btn.setEnabled(False)
    
    def show_category_context_menu(self, position):
        """显示分类右键菜单"""
        context_menu = QMenu()
        
        # 获取选中的项目
        item = self.category_tree.itemAt(position)
        if item:
            category_name = item.data(0, Qt.ItemDataRole.UserRole)
            
            # 添加菜单项
            add_child_action = QAction("添加子分类", self)
            add_child_action.triggered.connect(lambda: self.add_child_category(category_name))
            context_menu.addAction(add_child_action)
            
            context_menu.addSeparator()
            
            delete_action = QAction("删除分类", self)
            delete_action.triggered.connect(lambda: self.delete_category())
            context_menu.addAction(delete_action)
        
        # 显示菜单
        if context_menu.actions():
            context_menu.exec(self.category_tree.mapToGlobal(position))
    
    def add_child_category(self, parent_name):
        """添加子分类"""
        name, ok = QInputDialog.getText(self, "添加子分类", f"请输入子分类名称（父分类: {parent_name}）:")
        if ok and name:
            if not name.strip():
                QMessageBox.warning(self, "警告", "分类名称不能为空")
                return
            
            if name in self.config_manager.get_all_categories():
                QMessageBox.warning(self, "警告", f"分类 '{name}' 已存在")
                return
            
            # 输入描述
            description, ok = QInputDialog.getText(
                self, "分类描述", "请输入分类描述（可选）:"
            )
            
            if ok:
                try:
                    if self.config_manager.add_category(name, parent_name, description):
                        self.refresh_categories()
                        QMessageBox.information(self, "成功", f"子分类 '{name}' 创建成功")
                    else:
                        QMessageBox.warning(self, "失败", f"子分类 '{name}' 创建失败")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"创建子分类时出错: {str(e)}") 