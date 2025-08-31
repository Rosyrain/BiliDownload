"""
File Manager tab for browsing, searching, and managing downloaded files.

This module defines the FileManagerTab widget used by the UI layer to
navigate directories, filter by categories, search files, and perform
basic file operations.
"""

import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QInputDialog,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CardWidget,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    MessageBox,
    PushButton,
    SearchLineEdit,
    SubtitleLabel,
    TreeWidget,
)

from src.core.managers.logger import get_logger
from src.ui.components import FileTree


class FileManagerTab(QWidget):
    """
    文件管理标签页，用于浏览和管理下载的文件

    Attributes:
        config_manager (ConfigManager): 配置管理器
        file_manager (FileManager): 文件管理器
        logger: 日志记录器
    """

    # 定义信号
    file_action_requested = pyqtSignal(str, str)  # 操作类型, 文件路径

    def __init__(self, config_manager, file_manager, parent=None):
        """
        初始化文件管理标签页

        Args:
            config_manager: 配置管理器实例
            file_manager: 文件管理器实例
            parent: 父组件
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.file_manager = file_manager
        self.logger = get_logger(__name__)

        # 当前路径
        self.current_path = self.config_manager.get_download_path()

        # 初始化UI
        self._init_ui()

        # 加载初始目录
        self.navigate_to(self.current_path)

    def _init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 标题
        title_label = SubtitleLabel("文件管理", self)
        title_label.setObjectName("FileManagerTitle")
        main_layout.addWidget(title_label)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # 左侧分类树
        self._create_category_tree(splitter)

        # 右侧文件列表
        self._create_file_list(splitter)

        # 设置分割比例 - 增大左侧空间
        splitter.setSizes([300, 500])

        # 添加分割器到主布局
        main_layout.addWidget(splitter)

    def _create_category_tree(self, parent):
        """
        创建分类树
        
        Args:
            parent: 父组件
        """
        # 分类面板
        category_card = CardWidget(parent)
        category_layout = QVBoxLayout(category_card)
        category_layout.setContentsMargins(10, 10, 10, 10)
        category_layout.setSpacing(10)

        # 分类树
        self.category_tree = QTreeWidget(category_card)
        self.category_tree.setHeaderHidden(True)
        self.category_tree.setColumnCount(1)
        self.category_tree.setIndentation(20)
        self.category_tree.setAnimated(True)
        self.category_tree.setObjectName("CategoryTree")
        self.category_tree.itemClicked.connect(self._on_category_clicked)
        category_layout.addWidget(self.category_tree)

        # 加载分类
        self._load_categories()
        
        # 添加到父组件
        parent.addWidget(category_card)

    def _create_file_list(self, parent):
        """
        创建文件列表
        
        Args:
            parent: 父组件
        """
        # 文件列表面板
        file_card = CardWidget(parent)
        file_layout = QVBoxLayout(file_card)
        file_layout.setContentsMargins(10, 10, 10, 10)
        file_layout.setSpacing(10)

        # 工具栏
        self._create_toolbar(file_layout)

        # 文件树
        self.file_tree = FileTree(file_card)
        self.file_tree.fileOpen.connect(self._on_file_open)
        self.file_tree.fileDelete.connect(self._on_file_delete)
        self.file_tree.fileRename.connect(self._on_file_rename)
        self.file_tree.fileCopy.connect(self._on_file_copy)
        self.file_tree.filePaste.connect(self._on_file_paste)
        self.file_tree.folderCreate.connect(self._on_folder_create)
        file_layout.addWidget(self.file_tree)
        
        # 添加到父组件
        parent.addWidget(file_card)

    def _create_toolbar(self, parent_layout):
        """
        创建工具栏
        
        Args:
            parent_layout: 父布局
        """
        # 工具栏布局
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(10)

        # 路径输入框
        self.path_input = LineEdit(self)
        self.path_input.setReadOnly(True)
        self.path_input.setPlaceholderText("当前路径")
        toolbar_layout.addWidget(self.path_input, 1)

        # 上级目录按钮
        self.up_button = PushButton(FluentIcon.UP, "", self)
        self.up_button.setToolTip("上级目录")
        self.up_button.clicked.connect(self._navigate_up)
        toolbar_layout.addWidget(self.up_button)

        # 刷新按钮
        self.refresh_button = PushButton(FluentIcon.SYNC, "", self)
        self.refresh_button.setToolTip("刷新")
        self.refresh_button.clicked.connect(self._refresh)
        toolbar_layout.addWidget(self.refresh_button)

        # 主目录按钮
        self.home_button = PushButton(FluentIcon.HOME, "", self)
        self.home_button.setToolTip("下载目录")
        self.home_button.clicked.connect(self._navigate_home)
        toolbar_layout.addWidget(self.home_button)

        parent_layout.addLayout(toolbar_layout)

    def _load_categories(self):
        """加载分类"""
        # 清空分类树
        self.category_tree.clear()

        # 添加根节点 - 所有文件
        root_item = QTreeWidgetItem(self.category_tree)
        root_item.setText(0, "所有文件")
        root_item.setIcon(0, FluentIcon.FOLDER.icon())
        root_item.setData(0, Qt.ItemDataRole.UserRole, self.config_manager.get_download_path())
        
        # 添加数据文件夹
        data_item = QTreeWidgetItem(root_item)
        data_item.setText(0, "数据文件夹")
        data_item.setIcon(0, FluentIcon.FOLDER.icon())
        data_path = os.path.join(os.getcwd(), "data")
        data_item.setData(0, Qt.ItemDataRole.UserRole, data_path)

        # 展开根节点
        self.category_tree.expandAll()
        
        # 选择根节点
        self.category_tree.setCurrentItem(root_item)

    def navigate_to(self, path):
        """
        导航到指定路径

        Args:
            path: 目标路径
        """
        if not os.path.exists(path):
            InfoBar.error(
                title="错误",
                content=f"路径不存在: {path}",
                orient=InfoBarPosition.TOP,
                parent=self,
            )
            return

        # 更新当前路径
        self.current_path = path
        self.path_input.setText(path)

        # 设置文件树根路径
        self.file_tree.set_root_path(path)

    def _navigate_up(self):
        """导航到上级目录"""
        parent_path = os.path.dirname(self.current_path)
        if parent_path and parent_path != self.current_path:
            self.navigate_to(parent_path)

    def _refresh(self):
        """刷新当前目录"""
        self.navigate_to(self.current_path)
        
    def refresh_file_list(self):
        """刷新文件列表（_refresh方法的别名）"""
        self._refresh()

    def _navigate_home(self):
        """导航到下载目录"""
        home_path = self.config_manager.get_download_path()
        self.navigate_to(home_path)

    def _on_category_clicked(self, item, column):
        """
        处理分类点击事件

        Args:
            item: 点击的项
            column: 点击的列
        """
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path:
            self.navigate_to(path)

    def _on_search_changed(self, text):
        """
        处理搜索文本变化

        Args:
            text: 搜索文本
        """
        # 这里可以实现实时搜索功能
        # 由于FileTree组件使用QFileSystemModel，需要自定义搜索逻辑
        pass

    def _on_file_open(self, path):
        """
        处理文件打开事件

        Args:
            path: 文件路径
        """
        try:
            if os.path.isdir(path):
                self.navigate_to(path)
            else:
                if self.file_manager.open_file(path):
                    InfoBar.success(
                        title="打开文件",
                        content=f"已打开: {os.path.basename(path)}",
                        orient=InfoBarPosition.TOP,
                        parent=self,
                    )
                else:
                    InfoBar.warning(
                        title="打开文件",
                        content="无法打开文件",
                        orient=InfoBarPosition.TOP,
                        parent=self,
                    )
        except Exception as e:
            self.logger.error(f"打开文件失败: {e}")
            InfoBar.error(
                title="错误",
                content=f"打开文件失败: {e}",
                orient=InfoBarPosition.TOP,
                parent=self,
            )

    def _on_file_delete(self, path):
        """
        处理文件删除事件

        Args:
            path: 文件路径
        """
        try:
            # 确认删除
            confirm = MessageBox(
                "确认删除",
                f"确定要删除 {os.path.basename(path)} 吗？\n此操作不可恢复！",
                self,
            )

            if confirm.exec():
                if self.file_manager.delete_file(path):
                    InfoBar.success(
                        title="删除成功",
                        content=f"已删除: {os.path.basename(path)}",
                        orient=InfoBarPosition.TOP,
                        parent=self,
                    )
                    # 刷新文件列表
                    self._refresh()
                else:
                    InfoBar.error(
                        title="删除失败",
                        content="无法删除文件",
                        orient=InfoBarPosition.TOP,
                        parent=self,
                    )
        except Exception as e:
            self.logger.error(f"删除文件失败: {e}")
            InfoBar.error(
                title="错误",
                content=f"删除文件失败: {e}",
                orient=InfoBarPosition.TOP,
                parent=self,
            )

    def _on_file_rename(self, old_path, new_path):
        """
        处理文件重命名事件

        Args:
            old_path: 旧文件路径
            new_path: 新文件路径
        """
        try:
            if os.path.exists(new_path):
                InfoBar.warning(
                    title="重命名失败",
                    content="目标文件已存在",
                    orient=InfoBarPosition.TOP,
                    parent=self,
                )
                return

            os.rename(old_path, new_path)
            InfoBar.success(
                title="重命名成功",
                content=f"已重命名为: {os.path.basename(new_path)}",
                orient=InfoBarPosition.TOP,
                parent=self,
            )
            # 刷新文件列表
            self._refresh()
        except Exception as e:
            self.logger.error(f"重命名文件失败: {e}")
            InfoBar.error(
                title="错误",
                content=f"重命名文件失败: {e}",
                orient=InfoBarPosition.TOP,
                parent=self,
            )

    def _on_file_copy(self, path):
        """
        处理文件复制事件

        Args:
            path: 文件路径
        """
        # 将路径保存到剪贴板
        QApplication.clipboard().setText(path)
        InfoBar.success(
            title="复制成功",
            content="文件路径已复制到剪贴板",
            orient=InfoBarPosition.TOP,
            parent=self,
        )

    def _on_file_paste(self, target_dir):
        """
        处理文件粘贴事件

        Args:
            target_dir: 目标目录
        """
        # 从剪贴板获取路径
        path = QApplication.clipboard().text()

        if not os.path.exists(path):
            InfoBar.warning(
                title="粘贴失败",
                content="剪贴板中的路径不存在",
                orient=InfoBarPosition.TOP,
                parent=self,
            )
            return

        try:
            # 构建目标路径
            target_path = os.path.join(target_dir, os.path.basename(path))

            # 检查目标路径是否已存在
            if os.path.exists(target_path):
                InfoBar.warning(
                    title="粘贴失败",
                    content="目标位置已存在同名文件",
                    orient=InfoBarPosition.TOP,
                    parent=self,
                )
                return

            # 复制文件或目录
            if os.path.isdir(path):
                import shutil

                shutil.copytree(path, target_path)
            else:
                import shutil

                shutil.copy2(path, target_path)

            InfoBar.success(
                title="粘贴成功",
                content=f"已粘贴: {os.path.basename(path)}",
                orient=InfoBarPosition.TOP,
                parent=self,
            )
            # 刷新文件列表
            self._refresh()
        except Exception as e:
            self.logger.error(f"粘贴文件失败: {e}")
            InfoBar.error(
                title="错误",
                content=f"粘贴文件失败: {e}",
                orient=InfoBarPosition.TOP,
                parent=self,
            )

    def _on_folder_create(self, parent_dir):
        """
        处理创建文件夹事件

        Args:
            parent_dir: 父目录
        """
        # 弹出输入对话框
        name, ok = QInputDialog.getText(self, "新建文件夹", "请输入文件夹名称:")

        if ok and name:
            try:
                # 构建新文件夹路径
                new_folder_path = os.path.join(parent_dir, name)

                # 检查是否已存在
                if os.path.exists(new_folder_path):
                    InfoBar.warning(
                        title="创建失败",
                        content="文件夹已存在",
                        orient=InfoBarPosition.TOP,
                        parent=self,
                    )
                    return

                # 创建文件夹
                os.makedirs(new_folder_path)

                InfoBar.success(
                    title="创建成功",
                    content=f"已创建文件夹: {name}",
                    orient=InfoBarPosition.TOP,
                    parent=self,
                )
                # 刷新文件列表
                self._refresh()
            except Exception as e:
                self.logger.error(f"创建文件夹失败: {e}")
                InfoBar.error(
                    title="错误",
                    content=f"创建文件夹失败: {e}",
                    orient=InfoBarPosition.TOP,
                    parent=self,
                )
