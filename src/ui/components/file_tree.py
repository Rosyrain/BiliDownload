"""
文件树组件，用于显示文件列表
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import QTreeView
from qfluentwidgets import (
    Action,
    FluentIcon,
    RoundMenu,
)


class FileTree(QTreeView):
    """文件树组件，用于显示文件列表"""

    # 文件操作信号
    fileOpen = pyqtSignal(str)  # 参数为文件路径
    fileDelete = pyqtSignal(str)  # 参数为文件路径
    fileRename = pyqtSignal(str, str)  # 参数为旧路径和新路径
    fileCopy = pyqtSignal(str)  # 参数为文件路径
    filePaste = pyqtSignal(str)  # 参数为目标目录
    folderCreate = pyqtSignal(str)  # 参数为父目录

    def __init__(self, parent=None):
        """
        初始化文件树组件

        Args:
            parent: 父组件
        """
        super().__init__(parent)
        self._init_ui()
        self._setup_model()
        self._setup_context_menu()

    def _init_ui(self):
        """初始化UI"""
        # 设置模型
        self.model = QFileSystemModel()
        self.model.setRootPath("")

        # 设置视图属性
        self.setModel(self.model)
        self.setAnimated(True)
        self.setIndentation(20)
        self.setSortingEnabled(True)
        self.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        self.setDragDropMode(QTreeView.DragDropMode.NoDragDrop)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # 设置列宽
        self.setColumnWidth(0, 250)  # 名称列
        self.setColumnWidth(1, 100)  # 大小列
        self.setColumnWidth(2, 150)  # 类型列
        self.setColumnWidth(3, 150)  # 修改日期列

        # 连接信号
        self.doubleClicked.connect(self._on_item_double_clicked)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _setup_model(self):
        """设置模型"""
        self.model = QFileSystemModel()
        self.model.setReadOnly(False)
        self.model.setNameFilterDisables(False)
        self.setModel(self.model)

    def _setup_context_menu(self):
        """设置上下文菜单"""
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _on_item_double_clicked(self, index):
        """
        处理双击事件
        
        Args:
            index: 被双击的项的索引
        """
        if index.isValid():
            file_path = self.model.filePath(index)
            self.fileOpen.emit(file_path)

    def _show_context_menu(self, pos):
        """
        显示上下文菜单

        Args:
            pos: 菜单位置
        """
        # 获取选中的索引
        indexes = self.selectedIndexes()
        if not indexes:
            return

        # 只取每行的第一个索引（文件名列）
        unique_rows = set()
        filtered_indexes = []
        for index in indexes:
            if index.row() not in unique_rows and index.column() == 0:
                unique_rows.add(index.row())
                filtered_indexes.append(index)

        # 创建菜单
        menu = RoundMenu(parent=self)

        # 单个文件的菜单
        if len(filtered_indexes) == 1:
            index = filtered_indexes[0]
            file_path = self.model.filePath(index)
            is_dir = self.model.isDir(index)

            # 打开操作
            open_action = Action(FluentIcon.DOCUMENT, "打开" if not is_dir else "浏览")
            open_action.triggered.connect(lambda: self.fileOpen.emit(file_path))
            menu.addAction(open_action)

            menu.addSeparator()

            # 重命名操作
            rename_action = Action(FluentIcon.EDIT, "重命名")
            rename_action.triggered.connect(lambda: self.edit(index))
            menu.addAction(rename_action)

            # 删除操作
            delete_action = Action(FluentIcon.DELETE, "删除")
            delete_action.triggered.connect(lambda: self.fileDelete.emit(file_path))
            menu.addAction(delete_action)

            menu.addSeparator()

            # 复制操作
            copy_action = Action(FluentIcon.COPY, "复制")
            copy_action.triggered.connect(lambda: self.fileCopy.emit(file_path))
            menu.addAction(copy_action)

            # 粘贴操作（仅目录）
            if is_dir:
                paste_action = Action(FluentIcon.PASTE, "粘贴")
                paste_action.triggered.connect(lambda: self.filePaste.emit(file_path))
                menu.addAction(paste_action)

            # 新建文件夹（仅目录）
            if is_dir:
                menu.addSeparator()
                new_folder_action = Action(FluentIcon.FOLDER_ADD, "新建文件夹")
                new_folder_action.triggered.connect(
                    lambda: self.folderCreate.emit(file_path)
                )
                menu.addAction(new_folder_action)

        # 多个文件的菜单
        else:
            # 删除操作
            delete_action = Action(FluentIcon.DELETE, "删除选中项")
            delete_action.triggered.connect(
                lambda: self._delete_multiple(filtered_indexes)
            )
            menu.addAction(delete_action)

        # 显示菜单
        menu.exec(self.mapToGlobal(pos))

    def _delete_multiple(self, indexes):
        """
        删除多个文件

        Args:
            indexes: 索引列表
        """
        for index in indexes:
            file_path = self.model.filePath(index)
            self.fileDelete.emit(file_path)

    def set_root_path(self, path):
        """
        设置根路径

        Args:
            path: 根路径
        """
        index = self.model.setRootPath(path)
        self.setRootIndex(index)

    def get_selected_paths(self):
        """
        获取选中的文件路径

        Returns:
            选中的文件路径列表
        """
        indexes = self.selectedIndexes()

        # 只取每行的第一个索引（文件名列）
        unique_rows = set()
        paths = []
        for index in indexes:
            if index.row() not in unique_rows and index.column() == 0:
                unique_rows.add(index.row())
                paths.append(self.model.filePath(index))

        return paths
