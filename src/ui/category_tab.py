"""
分类管理标签页
"""

import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QSplitter,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    Action,
    CardWidget,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    MessageBox,
    PushButton,
    RoundMenu,
    SubtitleLabel,
    TreeWidget,
)

from src.core.managers.logger import get_logger


class CategoryTab(QWidget):
    """
    分类管理标签页，用于管理视频分类

    Attributes:
        config_manager (ConfigManager): 配置管理器
        logger: 日志记录器
    """

    # 定义信号
    category_action_requested = pyqtSignal(str, str)  # 操作类型, 分类名称

    def __init__(self, config_manager, parent=None):
        """
        初始化分类管理标签页

        Args:
            config_manager: 配置管理器实例
            parent: 父组件
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = get_logger(__name__)

        # 初始化UI
        self._init_ui()

        # 加载分类
        self.refresh_category_list()

    def _init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 标题
        title_label = SubtitleLabel("分类管理", self)
        title_label.setObjectName("CategoryTitle")
        main_layout.addWidget(title_label)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # 左侧分类管理
        self._create_category_panel(splitter)

        # 右侧分类详情
        self._create_detail_panel(splitter)

        # 设置分割比例
        splitter.setSizes([300, 500])

        # 添加分割器到主布局
        main_layout.addWidget(splitter)

    def _create_category_panel(self, parent):
        """
        创建分类管理面板

        Args:
            parent: 父组件
        """
        # 分类面板
        category_card = CardWidget(parent)
        category_layout = QVBoxLayout(category_card)
        category_layout.setContentsMargins(10, 10, 10, 10)
        category_layout.setSpacing(10)

        # 分类列表标题和操作
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        header_label = SubtitleLabel("分类列表", category_card)
        header_layout.addWidget(header_label)

        header_layout.addStretch(1)

        add_button = PushButton("添加分类", category_card)
        add_button.setIcon(FluentIcon.ADD)
        add_button.clicked.connect(self._add_category)
        header_layout.addWidget(add_button)

        category_layout.addLayout(header_layout)

        # 分类树
        self.category_tree = TreeWidget(category_card)
        self.category_tree.setHeaderHidden(True)
        self.category_tree.setSelectionMode(TreeWidget.SelectionMode.SingleSelection)
        self.category_tree.itemClicked.connect(self._on_category_clicked)
        self.category_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.category_tree.customContextMenuRequested.connect(self._show_context_menu)
        category_layout.addWidget(self.category_tree)

        # 添加到父组件
        parent.addWidget(category_card)

    def _create_detail_panel(self, parent):
        """
        创建分类详情面板

        Args:
            parent: 父组件
        """
        # 详情面板
        detail_card = CardWidget(parent)
        detail_layout = QVBoxLayout(detail_card)
        detail_layout.setContentsMargins(10, 10, 10, 10)
        detail_layout.setSpacing(10)

        # 详情标题
        detail_title = SubtitleLabel("分类详情", detail_card)
        detail_layout.addWidget(detail_title)

        # 分类名称
        name_layout = QHBoxLayout()
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(10)

        name_label = QLabel("名称:", detail_card)
        name_layout.addWidget(name_label)

        self.name_input = LineEdit(detail_card)
        self.name_input.setPlaceholderText("分类名称")
        self.name_input.setReadOnly(True)
        name_layout.addWidget(self.name_input)

        detail_layout.addLayout(name_layout)

        # 分类路径
        path_layout = QHBoxLayout()
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(10)

        path_label = QLabel("路径:", detail_card)
        path_layout.addWidget(path_label)

        self.path_input = LineEdit(detail_card)
        self.path_input.setPlaceholderText("分类路径")
        self.path_input.setReadOnly(True)
        path_layout.addWidget(self.path_input)

        detail_layout.addLayout(path_layout)

        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)

        button_layout.addStretch(1)

        self.edit_button = PushButton("编辑", detail_card)
        self.edit_button.setIcon(FluentIcon.EDIT)
        self.edit_button.clicked.connect(self._edit_category)
        self.edit_button.setEnabled(False)
        button_layout.addWidget(self.edit_button)

        self.delete_button = PushButton("删除", detail_card)
        self.delete_button.setIcon(FluentIcon.DELETE)
        self.delete_button.clicked.connect(self._delete_category)
        self.delete_button.setEnabled(False)
        button_layout.addWidget(self.delete_button)

        detail_layout.addLayout(button_layout)

        # 添加弹性空间
        detail_layout.addStretch(1)

        # 添加到父组件
        parent.addWidget(detail_card)

    def refresh_category_list(self):
        """刷新分类列表"""
        try:
            # 清空分类树
            self.category_tree.clear()

            # 获取分类数据
            categories = self.config_manager.get_category_tree()

            # 构建分类树
            root_items = []
            for name, info in categories.items():
                if info["parent"] is None:
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
            for child_name in categories[parent_name]["children"]:
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

    def _on_category_clicked(self, item, column):
        """分类选择事件"""
        category_name = item.data(0, Qt.ItemDataRole.UserRole)
        if category_name:
            # 获取分类信息
            category_path = self.config_manager.get_category_path(category_name)

            # 更新详情面板
            self.name_input.setText(category_name)
            self.path_input.setText(category_path if category_path else "")

            # 启用操作按钮
            self.edit_button.setEnabled(True)
            self.delete_button.setEnabled(True)

    def _show_context_menu(self, position):
        """显示右键菜单"""
        item = self.category_tree.itemAt(position)
        if not item:
            return

        category_name = item.data(0, Qt.ItemDataRole.UserRole)
        if not category_name:
            return

        # 创建菜单
        menu = RoundMenu(self)

        # 添加菜单项
        edit_action = Action(FluentIcon.EDIT, "编辑")
        edit_action.triggered.connect(lambda: self._edit_category())
        menu.addAction(edit_action)

        delete_action = Action(FluentIcon.DELETE, "删除")
        delete_action.triggered.connect(lambda: self._delete_category())
        menu.addAction(delete_action)

        menu.addSeparator()

        open_folder_action = Action(FluentIcon.FOLDER, "打开文件夹")
        open_folder_action.triggered.connect(
            lambda: self._open_category_folder(category_name)
        )
        menu.addAction(open_folder_action)

        # 显示菜单
        menu.exec(self.category_tree.mapToGlobal(position))

    def _add_category(self):
        """添加分类"""
        # 弹出输入对话框
        name, ok = QInputDialog.getText(self, "添加分类", "请输入分类名称:")

        if not ok or not name:
            return

        # 检查分类是否已存在
        categories = self.config_manager.get_all_categories()
        if name in categories:
            InfoBar.warning(
                title="添加失败",
                content=f"分类 '{name}' 已存在",
                orient=InfoBarPosition.TOP,
                parent=self,
            )
            return

        # 添加分类
        try:
            self.config_manager.add_category(name)

            # 刷新分类列表
            self.refresh_category_list()

            # 显示成功消息
            InfoBar.success(
                title="添加成功",
                content=f"分类 '{name}' 已添加",
                orient=InfoBarPosition.TOP,
                parent=self,
            )

            # 发送信号
            self.category_action_requested.emit("add", name)
        except Exception as e:
            self.logger.error(f"添加分类失败: {e}")
            InfoBar.error(
                title="错误",
                content=f"添加分类失败: {e}",
                orient=InfoBarPosition.TOP,
                parent=self,
            )

    def _edit_category(self):
        """编辑分类"""
        # 获取当前选中的分类
        current_name = self.name_input.text()
        if not current_name:
            return

        # 弹出输入对话框
        new_name, ok = QInputDialog.getText(
            self, "编辑分类", "请输入新的分类名称:", text=current_name
        )

        if not ok or not new_name or new_name == current_name:
            return

        # 检查新名称是否已存在
        categories = self.config_manager.get_all_categories()
        if new_name in categories and new_name != current_name:
            InfoBar.warning(
                title="编辑失败",
                content=f"分类 '{new_name}' 已存在",
                orient=InfoBarPosition.TOP,
                parent=self,
            )
            return

        # 更新分类
        try:
            # 更新配置
            self.config_manager.rename_category(current_name, new_name)

            # 刷新分类列表
            self.refresh_category_list()

            # 显示成功消息
            InfoBar.success(
                title="编辑成功",
                content=f"分类已从 '{current_name}' 更改为 '{new_name}'",
                orient=InfoBarPosition.TOP,
                parent=self,
            )

            # 发送信号
            self.category_action_requested.emit("rename", new_name)
        except Exception as e:
            self.logger.error(f"编辑分类失败: {e}")
            InfoBar.error(
                title="错误",
                content=f"编辑分类失败: {e}",
                orient=InfoBarPosition.TOP,
                parent=self,
            )

    def _delete_category(self):
        """删除分类"""
        # 获取当前选中的分类
        category_name = self.name_input.text()
        if not category_name:
            return

        # 确认删除
        confirm = MessageBox(
            "确认删除",
            f"确定要删除分类 '{category_name}' 吗？\n"
            f"注意：分类文件夹及其内容不会被删除。",
            self,
        )

        if not confirm.exec():
            return

        # 删除分类
        try:
            self.config_manager.remove_category(category_name)

            # 清空详情面板
            self.name_input.clear()
            self.path_input.clear()

            # 禁用操作按钮
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)

            # 刷新分类列表
            self.refresh_category_list()

            # 显示成功消息
            InfoBar.success(
                title="删除成功",
                content=f"分类 '{category_name}' 已删除",
                orient=InfoBarPosition.TOP,
                parent=self,
            )

            # 发送信号
            self.category_action_requested.emit("remove", category_name)
        except Exception as e:
            self.logger.error(f"删除分类失败: {e}")
            InfoBar.error(
                title="错误",
                content=f"删除分类失败: {e}",
                orient=InfoBarPosition.TOP,
                parent=self,
            )

    def _open_category_folder(self, category_name):
        """打开分类文件夹"""
        try:
            category_path = self.config_manager.get_category_path(category_name)
            if not category_path:
                InfoBar.warning(
                    title="打开失败",
                    content=f"分类 '{category_name}' 没有关联的文件夹",
                    orient=InfoBarPosition.TOP,
                    parent=self,
                )
                return

            # 检查路径是否存在
            if not os.path.exists(category_path):
                # 创建文件夹
                os.makedirs(category_path, exist_ok=True)

            # 打开文件夹
            if os.path.exists(category_path):
                import platform
                import subprocess

                if platform.system() == "Windows":
                    subprocess.run(["explorer", category_path])
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", category_path])
                else:  # Linux
                    subprocess.run(["xdg-open", category_path])
            else:
                InfoBar.error(
                    title="打开失败",
                    content=f"无法打开文件夹: {category_path}",
                    orient=InfoBarPosition.TOP,
                    parent=self,
                )
        except Exception as e:
            self.logger.error(f"打开分类文件夹失败: {e}")
            InfoBar.error(
                title="错误",
                content=f"打开分类文件夹失败: {e}",
                orient=InfoBarPosition.TOP,
                parent=self,
            )
