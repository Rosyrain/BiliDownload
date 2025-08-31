"""
Task List tab for managing download tasks.

This module defines the TaskListTab widget used by the UI layer to
display, filter, and control download tasks with different states
(pending, active, completed).
"""

import json
import os
from datetime import datetime, timedelta

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    ComboBox,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    MessageBox,
    ProgressBar,
    PushButton,
    SearchLineEdit,
    SubtitleLabel,
    TableWidget,
    TransparentPushButton,
)

from src.core.managers.logger import get_logger


class DownloadTask:
    """
    表示一个下载任务的数据模型

    Attributes:
        id (str): 任务唯一标识符
        url (str): 下载URL
        title (str): 视频标题
        save_path (str): 保存路径
        download_type (str): 下载类型 (full/audio/video)
        status (str): 任务状态 (pending/active/paused/completed/failed)
        progress (float): 下载进度 (0-100)
        created_at (datetime): 创建时间
        updated_at (datetime): 最后更新时间
        error (str): 错误信息 (如果有)
    """

    STATUS_PENDING = "pending"
    STATUS_ACTIVE = "active"
    STATUS_PAUSED = "paused"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"

    def __init__(self, task_id, url, title, save_path, download_type="full"):
        """
        初始化下载任务

        Args:
            task_id (str): 任务唯一标识符
            url (str): 下载URL
            title (str): 视频标题
            save_path (str): 保存路径
            download_type (str): 下载类型 (full/audio/video)
        """
        self.id = task_id
        self.url = url
        self.title = title
        self.save_path = save_path
        self.download_type = download_type
        self.status = self.STATUS_PENDING
        self.progress = 0.0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.error = ""

    def update_progress(self, progress):
        """更新下载进度"""
        self.progress = progress
        self.updated_at = datetime.now()

    def update_status(self, status):
        """更新任务状态"""
        self.status = status
        self.updated_at = datetime.now()

    def set_error(self, error_message):
        """设置错误信息"""
        self.error = error_message
        self.status = self.STATUS_FAILED
        self.updated_at = datetime.now()

    def get_display_type(self):
        """获取显示用的下载类型文本"""
        if self.download_type == "full":
            return "完整视频"
        elif self.download_type == "audio":
            return "仅音频"
        elif self.download_type == "video":
            return "无声视频"
        return self.download_type

    def get_display_status(self):
        """获取显示用的状态文本"""
        status_map = {
            self.STATUS_PENDING: "等待中",
            self.STATUS_ACTIVE: "下载中",
            self.STATUS_PAUSED: "已暂停",
            self.STATUS_COMPLETED: "已完成",
            self.STATUS_FAILED: "失败",
        }
        return status_map.get(self.status, self.status)


class TaskManager:
    """
    任务管理器，负责任务的创建、存储和状态管理

    Attributes:
        tasks (dict): 任务字典，键为任务ID
        config_manager (ConfigManager): 配置管理器
        logger: 日志记录器
        active_tasks (set): 当前活动的任务ID集合
        tasks_file_path (str): 任务数据持久化存储文件路径
    """

    def __init__(self, config_manager=None):
        """
        初始化任务管理器

        Args:
            config_manager: 配置管理器实例
        """
        self.tasks = {}
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.active_tasks = set()  # 跟踪当前活动的任务

        # 设置任务数据文件路径
        self.tasks_file_path = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "data",
            "tasks.json",
        )

        # 确保data目录存在
        os.makedirs(os.path.dirname(self.tasks_file_path), exist_ok=True)

        # 加载已保存的任务
        self.load_tasks()

    def create_task(self, url, title, save_path, download_type="full"):
        """
        创建新任务

        Args:
            url (str): 下载URL
            title (str): 视频标题
            save_path (str): 保存路径
            download_type (str): 下载类型

        Returns:
            DownloadTask: 创建的任务对象
        """
        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.tasks)}"
        task = DownloadTask(task_id, url, title, save_path, download_type)
        self.tasks[task_id] = task
        self.logger.info(f"创建任务: {task_id} - {title}")

        # 保存任务到文件
        self.save_tasks()

        # 检查是否可以立即开始任务
        self.check_and_start_pending_tasks()

        return task

    def get_task(self, task_id):
        """获取指定ID的任务"""
        return self.tasks.get(task_id)

    def get_all_tasks(self):
        """获取所有任务"""
        return list(self.tasks.values())

    def get_tasks_by_status(self, status):
        """获取指定状态的任务"""
        return [task for task in self.tasks.values() if task.status == status]

    def get_tasks_by_date_range(self, start_date=None, end_date=None):
        """
        获取指定日期范围内的任务

        Args:
            start_date (datetime): 开始日期
            end_date (datetime): 结束日期

        Returns:
            list: 符合条件的任务列表
        """
        tasks = self.get_all_tasks()

        if start_date:
            tasks = [task for task in tasks if task.created_at >= start_date]

        if end_date:
            tasks = [task for task in tasks if task.created_at <= end_date]

        return tasks

    def update_task_progress(self, task_id, progress):
        """更新任务进度"""
        task = self.get_task(task_id)
        if task:
            task.update_progress(progress)
            # 只有当进度变化较大或达到100%时才保存
            if progress % 10 == 0 or progress >= 100:
                self.save_tasks()

    def update_task_status(self, task_id, status):
        """更新任务状态"""
        task = self.get_task(task_id)
        if task:
            old_status = task.status
            task.update_status(status)

            # 如果任务完成或失败，从活动任务中移除
            if status in [DownloadTask.STATUS_COMPLETED, DownloadTask.STATUS_FAILED]:
                if task_id in self.active_tasks:
                    self.active_tasks.remove(task_id)
                # 检查是否有等待中的任务可以开始
                self.check_and_start_pending_tasks()
            # 如果任务从等待变为活动，添加到活动任务集合
            elif (
                status == DownloadTask.STATUS_ACTIVE
                and old_status == DownloadTask.STATUS_PENDING
            ):
                self.active_tasks.add(task_id)

            # 保存任务状态变更
            self.save_tasks()

    def remove_task(self, task_id):
        """移除任务"""
        if task_id in self.tasks:
            # 如果是活动任务，从活动集合中移除
            if task_id in self.active_tasks:
                self.active_tasks.remove(task_id)

            # 从任务字典中删除
            del self.tasks[task_id]
            self.logger.info(f"移除任务: {task_id}")

            # 保存变更
            self.save_tasks()

            # 检查是否有等待中的任务可以开始
            self.check_and_start_pending_tasks()
            return True
        return False

    def get_max_concurrent_downloads(self):
        """获取最大并发下载数"""
        if self.config_manager:
            try:
                return self.config_manager.get_max_concurrent_downloads()
            except ValueError:
                pass
        return 3  # 默认值

    def check_and_start_pending_tasks(self):
        """检查并启动等待中的任务"""
        # 获取最大并发下载数
        max_concurrent = self.get_max_concurrent_downloads()

        # 如果当前活动任务数小于最大并发数
        if len(self.active_tasks) < max_concurrent:
            # 获取所有等待中的任务
            pending_tasks = self.get_tasks_by_status(DownloadTask.STATUS_PENDING)

            # 按创建时间排序
            pending_tasks.sort(key=lambda t: t.created_at)

            # 计算可以启动的任务数
            available_slots = max_concurrent - len(self.active_tasks)

            # 启动等待中的任务
            for task in pending_tasks[:available_slots]:
                self.logger.info(f"自动启动任务: {task.id}")
                task.update_status(DownloadTask.STATUS_ACTIVE)
                self.active_tasks.add(task.id)

            # 保存变更
            if pending_tasks[:available_slots]:
                self.save_tasks()

    def save_tasks(self):
        """
        将任务数据保存到JSON文件
        """
        try:
            # 将任务对象转换为可序列化的字典
            tasks_data = {}
            for task_id, task in self.tasks.items():
                tasks_data[task_id] = {
                    "id": task.id,
                    "url": task.url,
                    "title": task.title,
                    "save_path": task.save_path,
                    "download_type": task.download_type,
                    "status": task.status,
                    "progress": task.progress,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                    "error": task.error,
                }

            # 写入文件
            with open(self.tasks_file_path, "w", encoding="utf-8") as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=2)

            self.logger.debug(f"任务数据已保存到 {self.tasks_file_path}")
        except Exception as e:
            self.logger.error(f"保存任务数据失败: {e}")

    def load_tasks(self):
        """
        从JSON文件加载任务数据
        """
        try:
            if not os.path.exists(self.tasks_file_path):
                self.logger.info(f"任务数据文件不存在: {self.tasks_file_path}")
                return

            with open(self.tasks_file_path, "r", encoding="utf-8") as f:
                tasks_data = json.load(f)

            # 清空当前任务
            self.tasks = {}
            self.active_tasks = set()

            # 重建任务对象
            for task_id, task_data in tasks_data.items():
                task = DownloadTask(
                    task_data["id"],
                    task_data["url"],
                    task_data["title"],
                    task_data["save_path"],
                    task_data["download_type"],
                )
                task.status = task_data["status"]
                task.progress = task_data["progress"]
                task.created_at = datetime.fromisoformat(task_data["created_at"])
                task.updated_at = datetime.fromisoformat(task_data["updated_at"])
                task.error = task_data["error"]

                # 添加到任务字典
                self.tasks[task_id] = task

                # 如果是活动任务，添加到活动集合
                if task.status == DownloadTask.STATUS_ACTIVE:
                    self.active_tasks.add(task_id)

            self.logger.info(f"已加载 {len(self.tasks)} 个任务")
        except Exception as e:
            self.logger.error(f"加载任务数据失败: {e}")


class TaskListTab(QWidget):
    """
    任务列表标签页，用于显示和管理下载任务

    Attributes:
        task_manager (TaskManager): 任务管理器
        config_manager (ConfigManager): 配置管理器
        file_manager (FileManager): 文件管理器
        logger: 日志记录器
    """

    # 定义信号
    task_action_requested = pyqtSignal(str, str)  # 任务ID, 动作

    def __init__(
        self, task_manager, config_manager=None, file_manager=None, parent=None
    ):
        """
        初始化任务列表标签页

        Args:
            task_manager: 任务管理器实例
            config_manager: 配置管理器实例
            file_manager: 文件管理器实例
            parent: 父组件
        """
        super().__init__(parent)
        self.task_manager = task_manager
        self.config_manager = config_manager
        self.file_manager = file_manager
        self.logger = get_logger(__name__)

        # 初始化变量
        self.current_filter = "all"  # 当前过滤条件
        self.current_search = ""  # 当前搜索文本
        self.start_date = None  # 开始日期
        self.end_date = None  # 结束日期

        # 初始化UI
        self._init_ui()

        # 启动定时器，定期刷新任务列表
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_task_list)
        self.refresh_timer.start(2000)  # 每2秒刷新一次

        # 初始加载任务列表
        self.refresh_task_list()

    def _init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 标题
        title_label = SubtitleLabel("任务列表", self)
        title_label.setObjectName("TaskListTitle")
        main_layout.addWidget(title_label)

        # 工具栏
        self._create_toolbar(main_layout)

        # 任务表格
        self._create_task_table(main_layout)

        # 操作按钮
        self._create_action_buttons(main_layout)

    def _create_toolbar(self, layout):
        """
        创建工具栏

        Args:
            layout: 父布局
        """
        # 工具栏布局
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(10)

        # 搜索框
        self.search_input = SearchLineEdit(self)
        self.search_input.setPlaceholderText("搜索任务...")
        self.search_input.textChanged.connect(self._on_search_changed)
        toolbar_layout.addWidget(self.search_input, 1)

        # 状态过滤器
        status_label = QLabel("状态:", self)
        toolbar_layout.addWidget(status_label)

        self.status_filter = ComboBox(self)
        self.status_filter.addItem("全部", "all")
        self.status_filter.addItem("等待中", "pending")
        self.status_filter.addItem("下载中", "active")
        self.status_filter.addItem("已完成", "completed")
        self.status_filter.addItem("已失败", "failed")
        self.status_filter.currentIndexChanged.connect(self._on_filter_changed)
        toolbar_layout.addWidget(self.status_filter)

        # 日期过滤器
        date_label = QLabel("日期:", self)
        toolbar_layout.addWidget(date_label)

        self.date_filter = ComboBox(self)
        self.date_filter.addItem("全部", "all")
        self.date_filter.addItem("今天", "today")
        self.date_filter.addItem("昨天", "yesterday")
        self.date_filter.addItem("本周", "this_week")
        self.date_filter.addItem("上周", "last_week")
        self.date_filter.addItem("本月", "this_month")
        self.date_filter.addItem("上月", "last_month")
        # 移除自定义选项
        # self.date_filter.addItem("自定义...", "custom")
        self.date_filter.currentIndexChanged.connect(self._on_date_filter_changed)
        toolbar_layout.addWidget(self.date_filter)

        # 刷新按钮
        self.refresh_button = PushButton(FluentIcon.SYNC, "", self)
        self.refresh_button.setToolTip("刷新")
        self.refresh_button.clicked.connect(self.refresh_task_list)
        toolbar_layout.addWidget(self.refresh_button)

        # 添加到主布局
        layout.addLayout(toolbar_layout)

    def _create_task_table(self, layout):
        """
        创建任务表格

        Args:
            layout: 父布局
        """
        # 任务表格
        self.task_table = TableWidget(self)
        self.task_table.setColumnCount(6)
        self.task_table.setHorizontalHeaderLabels(
            ["ID", "标题", "状态", "进度", "创建时间", "操作"]
        )
        self.task_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.task_table.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.task_table.setSelectionMode(TableWidget.SelectionMode.SingleSelection)
        self.task_table.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.task_table.setAlternatingRowColors(True)

        # 设置列宽
        self.task_table.setColumnWidth(0, 80)  # ID
        self.task_table.setColumnWidth(2, 100)  # 状态
        self.task_table.setColumnWidth(3, 100)  # 进度
        self.task_table.setColumnWidth(4, 150)  # 创建时间
        self.task_table.setColumnWidth(5, 150)  # 操作

        # 添加到主布局
        layout.addWidget(self.task_table)

    def _create_action_buttons(self, layout):
        """
        创建操作按钮

        Args:
            layout: 父布局
        """
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)

        # 添加弹性空间
        button_layout.addStretch(1)

        # 批量操作按钮
        self.batch_pause_button = PushButton("批量暂停", self)
        self.batch_pause_button.setIcon(FluentIcon.PAUSE)
        self.batch_pause_button.clicked.connect(self._batch_pause)
        button_layout.addWidget(self.batch_pause_button)

        self.batch_resume_button = PushButton("批量恢复", self)
        self.batch_resume_button.setIcon(FluentIcon.PLAY)
        self.batch_resume_button.clicked.connect(self._batch_resume)
        button_layout.addWidget(self.batch_resume_button)

        self.batch_remove_button = PushButton("批量删除", self)
        self.batch_remove_button.setIcon(FluentIcon.DELETE)
        self.batch_remove_button.clicked.connect(self._batch_remove)
        button_layout.addWidget(self.batch_remove_button)

        # 添加到主布局
        layout.addLayout(button_layout)

    def _on_search_changed(self, text):
        """处理搜索文本变化"""
        self.current_search = text
        self.refresh_task_list()

    def _on_filter_changed(self, index):
        """处理状态过滤器变化"""
        self.current_filter = self.status_filter.currentData()
        self.refresh_task_list()

    def _on_date_filter_changed(self, index):
        """处理日期过滤器变化"""
        range_type = self.date_filter.currentData()

        # 重置日期范围
        self.start_date = None
        self.end_date = None

        # 设置预定义的时间范围
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if range_type == "today":
            self.start_date = today
            self.end_date = today + timedelta(days=1) - timedelta(microseconds=1)
        elif range_type == "yesterday":
            self.start_date = today - timedelta(days=1)
            self.end_date = today - timedelta(microseconds=1)
        elif range_type == "this_week":
            # 本周一到现在
            days_since_monday = today.weekday()
            self.start_date = today - timedelta(days=days_since_monday)
            self.end_date = today + timedelta(days=1) - timedelta(microseconds=1)
        elif range_type == "last_week":
            # 上周一到上周日
            days_since_monday = today.weekday()
            self.start_date = today - timedelta(days=days_since_monday + 7)
            self.end_date = (
                today
                - timedelta(days=days_since_monday + 1)
                - timedelta(microseconds=1)
            )
        elif range_type == "this_month":
            # 本月1号到现在
            self.start_date = today.replace(day=1)
            self.end_date = today + timedelta(days=1) - timedelta(microseconds=1)
        elif range_type == "last_month":
            # 上月1号到上月最后一天
            last_month = today.replace(day=1) - timedelta(days=1)
            self.start_date = last_month.replace(day=1)
            self.end_date = today.replace(day=1) - timedelta(microseconds=1)
        # 移除对自定义日期范围的支持
        # elif range_type == "custom":
        #     # 打开日期范围选择对话框
        #     self._show_date_range_dialog()
        #     return

        # 刷新任务列表
        self.refresh_task_list()

    def _batch_pause(self):
        """批量暂停任务"""
        active_tasks = self._get_selected_tasks_by_status(DownloadTask.STATUS_ACTIVE)
        if not active_tasks:
            InfoBar.warning(
                title="无可暂停任务",
                content="没有选中的活动任务可以暂停",
                orient=InfoBarPosition.TOP,
                parent=self,
            )
            return

        for task_id in active_tasks:
            self.task_action_requested.emit(task_id, "pause")

        InfoBar.success(
            title="批量操作",
            content=f"已暂停 {len(active_tasks)} 个任务",
            orient=InfoBarPosition.TOP,
            parent=self,
        )

    def _batch_resume(self):
        """批量恢复任务"""
        paused_tasks = self._get_selected_tasks_by_status(DownloadTask.STATUS_PAUSED)
        if not paused_tasks:
            InfoBar.warning(
                title="无可恢复任务",
                content="没有选中的暂停任务可以恢复",
                orient=InfoBarPosition.TOP,
                parent=self,
            )
            return

        for task_id in paused_tasks:
            self.task_action_requested.emit(task_id, "resume")

        InfoBar.success(
            title="批量操作",
            content=f"已恢复 {len(paused_tasks)} 个任务",
            orient=InfoBarPosition.TOP,
            parent=self,
        )

    def _batch_remove(self):
        """批量删除任务"""
        selected_tasks = self._get_selected_tasks()
        if not selected_tasks:
            InfoBar.warning(
                title="无选中任务",
                content="没有选中的任务可以删除",
                orient=InfoBarPosition.TOP,
                parent=self,
            )
            return

        # 确认删除
        confirm = MessageBox(
            "确认删除", f"确定要删除选中的 {len(selected_tasks)} 个任务吗？", self
        )

        if confirm.exec():
            for task_id in selected_tasks:
                self.task_action_requested.emit(task_id, "remove")

            InfoBar.success(
                title="批量操作",
                content=f"已删除 {len(selected_tasks)} 个任务",
                orient=InfoBarPosition.TOP,
                parent=self,
            )

    def _get_selected_tasks(self):
        """获取选中的任务ID列表"""
        selected_rows = set(item.row() for item in self.task_table.selectedItems())
        selected_tasks = []

        for row in selected_rows:
            task_id = self.task_table.item(row, 0).text()
            selected_tasks.append(task_id)

        return selected_tasks

    def _get_selected_tasks_by_status(self, status):
        """获取选中的指定状态的任务ID列表"""
        selected_rows = set(item.row() for item in self.task_table.selectedItems())
        selected_tasks = []

        for row in selected_rows:
            task_id = self.task_table.item(row, 0).text()
            task_status = self.task_table.item(row, 2).data(Qt.ItemDataRole.UserRole)
            if task_status == status:
                selected_tasks.append(task_id)

        return selected_tasks

    def refresh_task_list(self):
        """刷新任务列表"""
        # 清空表格
        self.task_table.setRowCount(0)

        # 获取任务列表
        tasks = self.task_manager.get_all_tasks()

        # 应用过滤条件
        if self.current_filter != "all":
            tasks = [task for task in tasks if task.status == self.current_filter]

        # 应用时间过滤
        if self.start_date and self.end_date:
            tasks = [
                task
                for task in tasks
                if self.start_date <= task.created_at <= self.end_date
            ]

        # 应用搜索过滤
        if self.current_search:
            search_text = self.current_search.lower()
            tasks = [
                task
                for task in tasks
                if (
                    search_text in task.id.lower()
                    or search_text in task.title.lower()
                    or search_text in task.save_path.lower()
                    or search_text in task.status.lower()
                )
            ]

        # 填充表格
        for row, task in enumerate(tasks):
            self.task_table.insertRow(row)

            # ID列
            id_item = QTableWidgetItem(task.id)
            self.task_table.setItem(row, 0, id_item)

            # 标题列
            title_item = QTableWidgetItem(task.title)
            self.task_table.setItem(row, 1, title_item)

            # 状态列
            status_text = self._get_status_display(task.status)
            status_item = QTableWidgetItem(status_text)
            status_item.setData(Qt.ItemDataRole.UserRole, task.status)
            status_item.setForeground(self._get_status_color(task.status))
            self.task_table.setItem(row, 2, status_item)

            # 进度列
            progress_bar = ProgressBar(self)
            progress_bar.setValue(int(task.progress))
            self.task_table.setCellWidget(row, 3, progress_bar)

            # 创建时间列
            time_item = QTableWidgetItem(task.created_at.strftime("%Y-%m-%d %H:%M:%S"))
            self.task_table.setItem(row, 4, time_item)

            # 操作列
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(5)

            # 根据状态显示不同的操作按钮
            if task.status == DownloadTask.STATUS_PENDING:
                # 开始按钮
                start_btn = TransparentPushButton(FluentIcon.PLAY, "", action_widget)
                start_btn.setToolTip("开始")
                start_btn.clicked.connect(
                    lambda checked, tid=task.id: self.task_action_requested.emit(
                        tid, "start"
                    )
                )
                action_layout.addWidget(start_btn)

                # 取消按钮
                cancel_btn = TransparentPushButton(FluentIcon.CLOSE, "", action_widget)
                cancel_btn.setToolTip("取消")
                cancel_btn.clicked.connect(
                    lambda checked, tid=task.id: self.task_action_requested.emit(
                        tid, "cancel"
                    )
                )
                action_layout.addWidget(cancel_btn)

            elif task.status == DownloadTask.STATUS_ACTIVE:
                # 暂停按钮
                pause_btn = TransparentPushButton(FluentIcon.PAUSE, "", action_widget)
                pause_btn.setToolTip("暂停")
                pause_btn.clicked.connect(
                    lambda checked, tid=task.id: self.task_action_requested.emit(
                        tid, "pause"
                    )
                )
                action_layout.addWidget(pause_btn)

                # 取消按钮
                cancel_btn = TransparentPushButton(FluentIcon.CLOSE, "", action_widget)
                cancel_btn.setToolTip("取消")
                cancel_btn.clicked.connect(
                    lambda checked, tid=task.id: self.task_action_requested.emit(
                        tid, "cancel"
                    )
                )
                action_layout.addWidget(cancel_btn)

            elif task.status == DownloadTask.STATUS_PAUSED:
                # 恢复按钮
                resume_btn = TransparentPushButton(FluentIcon.PLAY, "", action_widget)
                resume_btn.setToolTip("恢复")
                resume_btn.clicked.connect(
                    lambda checked, tid=task.id: self.task_action_requested.emit(
                        tid, "resume"
                    )
                )
                action_layout.addWidget(resume_btn)

                # 取消按钮
                cancel_btn = TransparentPushButton(FluentIcon.CLOSE, "", action_widget)
                cancel_btn.setToolTip("取消")
                cancel_btn.clicked.connect(
                    lambda checked, tid=task.id: self.task_action_requested.emit(
                        tid, "cancel"
                    )
                )
                action_layout.addWidget(cancel_btn)

            elif task.status == DownloadTask.STATUS_COMPLETED:
                # 打开文件夹按钮
                open_folder_btn = TransparentPushButton(
                    FluentIcon.FOLDER, "", action_widget
                )
                open_folder_btn.setToolTip("打开文件夹")
                open_folder_btn.clicked.connect(
                    lambda checked, path=task.save_path: self._open_folder(path)
                )
                action_layout.addWidget(open_folder_btn)

                # 删除按钮
                delete_btn = TransparentPushButton(FluentIcon.DELETE, "", action_widget)
                delete_btn.setToolTip("删除任务")
                delete_btn.clicked.connect(
                    lambda checked, tid=task.id: self.task_action_requested.emit(
                        tid, "remove"
                    )
                )
                action_layout.addWidget(delete_btn)

            elif task.status == DownloadTask.STATUS_FAILED:
                # 重试按钮
                retry_btn = TransparentPushButton(FluentIcon.RETRY, "", action_widget)
                retry_btn.setToolTip("重试")
                retry_btn.clicked.connect(
                    lambda checked, tid=task.id: self.task_action_requested.emit(
                        tid, "retry"
                    )
                )
                action_layout.addWidget(retry_btn)

                # 删除按钮
                delete_btn = TransparentPushButton(FluentIcon.DELETE, "", action_widget)
                delete_btn.setToolTip("删除任务")
                delete_btn.clicked.connect(
                    lambda checked, tid=task.id: self.task_action_requested.emit(
                        tid, "remove"
                    )
                )
                action_layout.addWidget(delete_btn)

            self.task_table.setCellWidget(row, 5, action_widget)

        # 更新状态栏
        # self.status_label.setText(f"总计: {len(tasks)} 个任务")

    def _get_status_display(self, status):
        """获取状态显示文本"""
        status_map = {
            DownloadTask.STATUS_PENDING: "等待中",
            DownloadTask.STATUS_ACTIVE: "下载中",
            DownloadTask.STATUS_PAUSED: "已暂停",
            DownloadTask.STATUS_COMPLETED: "已完成",
            DownloadTask.STATUS_FAILED: "已失败",
            DownloadTask.STATUS_CANCELLED: "已取消",
        }
        return status_map.get(status, status)

    def _get_status_color(self, status):
        """获取状态颜色"""
        status_color_map = {
            DownloadTask.STATUS_PENDING: QBrush(QColor("#909399")),  # 灰色
            DownloadTask.STATUS_ACTIVE: QBrush(QColor("#409EFF")),  # 蓝色
            DownloadTask.STATUS_PAUSED: QBrush(QColor("#E6A23C")),  # 黄色
            DownloadTask.STATUS_COMPLETED: QBrush(QColor("#67C23A")),  # 绿色
            DownloadTask.STATUS_FAILED: QBrush(QColor("#F56C6C")),  # 红色
            DownloadTask.STATUS_CANCELLED: QBrush(QColor("#909399")),  # 灰色
        }
        return status_color_map.get(status, QBrush(QColor("#000000")))

    def _open_folder(self, path):
        """打开文件夹"""
        if self.file_manager:
            self.file_manager.open_folder(path)
        else:
            # 使用系统默认方式打开文件夹
            try:
                import platform
                import subprocess

                if platform.system() == "Windows":
                    subprocess.run(["explorer", path])
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", path])
                else:  # Linux
                    subprocess.run(["xdg-open", path])
            except Exception as e:
                self.logger.error(f"打开文件夹失败: {e}")
                InfoBar.error(
                    title="错误",
                    content=f"打开文件夹失败: {e}",
                    orient=InfoBarPosition.TOP,
                    parent=self,
                )
