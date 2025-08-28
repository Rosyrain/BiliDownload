"""
Task List tab for managing download tasks.

This module defines the TaskListTab widget used by the UI layer to
display, filter, and control download tasks with different states
(pending, active, completed).
"""
import os
import json
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMenu, QGroupBox,
    QMessageBox, QComboBox, QFrame, QSplitter,
    QFileDialog, QInputDialog, QTabWidget, QProgressBar,
    QDateEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QCursor, QAction, QIcon, QBrush

from src.core.file_manager import FileManager
from src.core.config_manager import ConfigManager
from src.core.logger import get_logger


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
            self.STATUS_FAILED: "失败"
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
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
            'data', 
            'tasks.json'
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
            elif status == DownloadTask.STATUS_ACTIVE and old_status == DownloadTask.STATUS_PENDING:
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
            except:
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
                    'id': task.id,
                    'url': task.url,
                    'title': task.title,
                    'save_path': task.save_path,
                    'download_type': task.download_type,
                    'status': task.status,
                    'progress': task.progress,
                    'created_at': task.created_at.isoformat(),
                    'updated_at': task.updated_at.isoformat(),
                    'error': task.error
                }
            
            # 写入文件
            with open(self.tasks_file_path, 'w', encoding='utf-8') as f:
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
            
            with open(self.tasks_file_path, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
            
            # 清空当前任务
            self.tasks = {}
            self.active_tasks = set()
            
            # 重建任务对象
            for task_id, task_data in tasks_data.items():
                task = DownloadTask(
                    task_data['id'],
                    task_data['url'],
                    task_data['title'],
                    task_data['save_path'],
                    task_data['download_type']
                )
                task.status = task_data['status']
                task.progress = task_data['progress']
                task.created_at = datetime.fromisoformat(task_data['created_at'])
                task.updated_at = datetime.fromisoformat(task_data['updated_at'])
                task.error = task_data['error']
                
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
    
    def __init__(self, task_manager, config_manager=None, file_manager=None):
        """
        初始化任务列表标签页
        
        Args:
            task_manager: 任务管理器实例
            config_manager: 配置管理器实例
            file_manager: 文件管理器实例
        """
        super().__init__()
        self.task_manager = task_manager
        self.config_manager = config_manager
        self.file_manager = file_manager
        self.logger = get_logger(__name__)
        
        # 当前显示的任务状态过滤
        self.current_filter = "all"
        
        # 时间筛选
        self.start_date = None
        self.end_date = None
        
        # 存储任务的详细进度信息
        self.task_progress_details = {}  # {task_id: {'video': 0, 'audio': 0, 'merge': 0}}
        
        # 初始化UI
        self.init_ui()
        
        # 设置刷新定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_task_list)
        self.refresh_timer.start(1000)  # 每秒刷新一次
    
    def init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("下载任务管理")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 控制面板
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # 任务列表
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(7)
        
        # 设置列顺序 - 操作, 标题, 进度, 类型, 保存路径, 状态, 创建时间
        self.task_table.setHorizontalHeaderLabels(["操作", "标题", "进度", "类型", "保存路径", "状态", "创建时间"])
        
        # 设置列宽度策略
        self.task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 操作
        self.task_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 标题
        self.task_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # 进度
        self.task_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 类型
        self.task_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 保存路径
        self.task_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # 状态
        self.task_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # 创建时间
        
        # 设置进度列的固定宽度
        self.task_table.setColumnWidth(2, 200)
        
        # 设置行高
        self.task_table.verticalHeader().setDefaultSectionSize(60)
        
        self.task_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.task_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.task_table.setAlternatingRowColors(True)
        self.task_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                background-color: white;
            }
            QTableWidget::item:alternate {
                background-color: #f5f7fa;
            }
            QTableWidget::item:selected {
                background-color: #e6f2ff;
                color: #409eff;
            }
            QHeaderView::section {
                background-color: #f5f7fa;
                padding: 5px;
                border: 1px solid #dcdfe6;
                border-left: none;
                border-top: none;
                font-weight: bold;
            }
        """)
        main_layout.addWidget(self.task_table)
        
        # 状态栏
        status_layout = QHBoxLayout()
        self.status_label = QLabel("总计: 0 个任务")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        main_layout.addLayout(status_layout)
        
        # 初始加载任务
        self.refresh_task_list()
    
    def create_control_panel(self):
        """创建控制面板"""
        panel = QGroupBox("任务筛选")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 上层筛选控件
        top_filter_layout = QHBoxLayout()
        
        # 状态过滤下拉框
        top_filter_layout.addWidget(QLabel("状态:"))
        self.status_filter = QComboBox()
        self.status_filter.setMinimumWidth(120)  # 增加宽度确保内容完全显示
        self.status_filter.setMaximumHeight(30)  # 控制高度
        self.status_filter.addItem("全部", "all")
        self.status_filter.addItem("等待中", DownloadTask.STATUS_PENDING)
        self.status_filter.addItem("下载中", DownloadTask.STATUS_ACTIVE)
        self.status_filter.addItem("已暂停", DownloadTask.STATUS_PAUSED)
        self.status_filter.addItem("已完成", DownloadTask.STATUS_COMPLETED)
        self.status_filter.addItem("失败", DownloadTask.STATUS_FAILED)
        self.status_filter.setStyleSheet("""
            QComboBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border-left: none;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #e6f2ff;
                selection-color: #409eff;
                padding: 4px;
            }
        """)
        self.status_filter.currentIndexChanged.connect(self.on_filter_changed)
        top_filter_layout.addWidget(self.status_filter)
        
        # 搜索框
        top_filter_layout.addWidget(QLabel("搜索:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词搜索...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #409eff;
            }
        """)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        top_filter_layout.addWidget(self.search_input)
        
        # 时间筛选范围
        top_filter_layout.addWidget(QLabel("时间范围:"))
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItem("全部", "all")
        self.time_range_combo.addItem("今天", "today")
        self.time_range_combo.addItem("昨天", "yesterday")
        self.time_range_combo.addItem("本周", "this_week")
        self.time_range_combo.addItem("上周", "last_week")
        self.time_range_combo.addItem("本月", "this_month")
        self.time_range_combo.addItem("上月", "last_month")
        self.time_range_combo.addItem("自定义", "custom")
        self.time_range_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border-left: none;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #e6f2ff;
                selection-color: #409eff;
                padding: 4px;
            }
        """)
        self.time_range_combo.currentIndexChanged.connect(self.on_time_range_changed)
        top_filter_layout.addWidget(self.time_range_combo)
        
        layout.addLayout(top_filter_layout)
        
        # 自定义时间范围控件（初始隐藏）
        self.custom_date_widget = QWidget()
        custom_date_layout = QHBoxLayout(self.custom_date_widget)
        custom_date_layout.setContentsMargins(0, 0, 0, 0)
        
        # 开始日期
        custom_date_layout.addWidget(QLabel("开始日期:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(datetime.now().date())
        self.start_date_edit.setStyleSheet("""
            QDateEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
            }
        """)
        self.start_date_edit.dateChanged.connect(self.on_custom_date_changed)
        custom_date_layout.addWidget(self.start_date_edit)
        
        # 结束日期
        custom_date_layout.addWidget(QLabel("结束日期:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(datetime.now().date())
        self.end_date_edit.setStyleSheet("""
            QDateEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
            }
        """)
        self.end_date_edit.dateChanged.connect(self.on_custom_date_changed)
        custom_date_layout.addWidget(self.end_date_edit)
        
        # 应用按钮
        apply_date_btn = QPushButton("应用")
        apply_date_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
        """)
        apply_date_btn.clicked.connect(self.on_custom_date_applied)
        custom_date_layout.addWidget(apply_date_btn)
        
        layout.addWidget(self.custom_date_widget)
        self.custom_date_widget.setVisible(False)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f7fa;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 4px 12px;
                color: #606266;
            }
            QPushButton:hover {
                background-color: #e6f2ff;
                color: #409eff;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_task_list)
        button_layout.addWidget(refresh_btn)
        
        # 清理已完成按钮
        clear_completed_btn = QPushButton("清理已完成")
        clear_completed_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f7fa;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 4px 12px;
                color: #606266;
            }
            QPushButton:hover {
                background-color: #ffe6e6;
                color: #f56c6c;
            }
        """)
        clear_completed_btn.clicked.connect(self.clear_completed_tasks)
        button_layout.addWidget(clear_completed_btn)
        
        layout.addLayout(button_layout)
        
        return panel
    
    def on_filter_changed(self):
        """处理过滤条件变化"""
        self.current_filter = self.status_filter.currentData()
        self.refresh_task_list()
    
    def on_search_text_changed(self):
        """处理搜索文本变化"""
        self.refresh_task_list()
    
    def on_time_range_changed(self):
        """处理时间范围变化"""
        range_type = self.time_range_combo.currentData()
        
        # 重置日期范围
        self.start_date = None
        self.end_date = None
        
        # 显示/隐藏自定义日期控件
        self.custom_date_widget.setVisible(range_type == "custom")
        
        # 设置预定义的时间范围
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if range_type == "today":
            self.start_date = today
            self.end_date = today + timedelta(days=1) - timedelta(microseconds=1)
        
        elif range_type == "yesterday":
            self.start_date = today - timedelta(days=1)
            self.end_date = today - timedelta(microseconds=1)
        
        elif range_type == "this_week":
            # 获取本周一
            self.start_date = today - timedelta(days=today.weekday())
            self.end_date = self.start_date + timedelta(days=7) - timedelta(microseconds=1)
        
        elif range_type == "last_week":
            # 获取上周一
            last_week_start = today - timedelta(days=today.weekday() + 7)
            self.start_date = last_week_start
            self.end_date = last_week_start + timedelta(days=7) - timedelta(microseconds=1)
        
        elif range_type == "this_month":
            # 获取本月第一天
            self.start_date = today.replace(day=1)
            # 获取下月第一天
            if today.month == 12:
                next_month = today.replace(year=today.year + 1, month=1, day=1)
            else:
                next_month = today.replace(month=today.month + 1, day=1)
            self.end_date = next_month - timedelta(microseconds=1)
        
        elif range_type == "last_month":
            # 获取上月第一天
            if today.month == 1:
                last_month_start = today.replace(year=today.year - 1, month=12, day=1)
            else:
                last_month_start = today.replace(month=today.month - 1, day=1)
            self.start_date = last_month_start
            # 获取本月第一天
            this_month_start = today.replace(day=1)
            self.end_date = this_month_start - timedelta(microseconds=1)
        
        # 刷新任务列表
        if range_type != "custom":
            self.refresh_task_list()
    
    def on_custom_date_changed(self):
        """处理自定义日期变化"""
        # 不立即刷新，等待用户点击应用按钮
        pass
    
    def on_custom_date_applied(self):
        """应用自定义日期范围"""
        start_date = self.start_date_edit.date().toPyDate()
        end_date = self.end_date_edit.date().toPyDate()
        
        # 转换为datetime对象
        self.start_date = datetime.combine(start_date, datetime.min.time())
        self.end_date = datetime.combine(end_date, datetime.max.time())
        
        # 刷新任务列表
        self.refresh_task_list()
    
    def refresh_task_list(self):
        """刷新任务列表"""
        # 获取所有任务
        all_tasks = self.task_manager.get_all_tasks()
        
        # 应用过滤
        search_text = self.search_input.text().lower()
        filtered_tasks = []
        
        for task in all_tasks:
            # 状态过滤
            if self.current_filter != "all" and task.status != self.current_filter:
                continue
            
            # 时间范围过滤
            if self.start_date and task.created_at < self.start_date:
                continue
            if self.end_date and task.created_at > self.end_date:
                continue
            
            # 搜索过滤 - 增强搜索范围，包括标题、URL、保存路径和任务ID
            if search_text:
                if (search_text not in task.title.lower() and 
                    search_text not in task.url.lower() and 
                    search_text not in task.save_path.lower() and
                    search_text not in task.id.lower()):
                    continue
            
            filtered_tasks.append(task)
        
        # 更新表格
        self.task_table.setRowCount(0)  # 清空表格
        
        for task in filtered_tasks:
            row = self.task_table.rowCount()
            self.task_table.insertRow(row)
            
            # 操作按钮 (列0)
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(5)
            
            # 根据任务状态显示不同的按钮
            if task.status == DownloadTask.STATUS_ACTIVE:
                # 暂停按钮
                pause_btn = QPushButton("暂停")
                pause_btn.setProperty("task_id", task.id)
                pause_btn.setMinimumHeight(30)
                pause_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f5f7fa;
                        border: 1px solid #dcdfe6;
                        border-radius: 4px;
                        padding: 2px 8px;
                        color: #606266;
                        min-height: 30px;
                    }
                    QPushButton:hover {
                        background-color: #e6f2ff;
                        color: #409eff;
                    }
                """)
                pause_btn.clicked.connect(lambda checked, tid=task.id: self.task_action_requested.emit(tid, "pause"))
                action_layout.addWidget(pause_btn)
            elif task.status == DownloadTask.STATUS_PAUSED or task.status == DownloadTask.STATUS_PENDING:
                # 开始按钮
                start_btn = QPushButton("开始")
                start_btn.setProperty("task_id", task.id)
                start_btn.setMinimumHeight(30)
                start_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f0f9eb;
                        border: 1px solid #c2e7b0;
                        border-radius: 4px;
                        padding: 2px 8px;
                        color: #67c23a;
                        min-height: 30px;
                    }
                    QPushButton:hover {
                        background-color: #e1f3d8;
                    }
                """)
                start_btn.clicked.connect(lambda checked, tid=task.id: self.task_action_requested.emit(tid, "start"))
                action_layout.addWidget(start_btn)
            
            # 根据任务状态显示不同的操作按钮
            if task.status == DownloadTask.STATUS_FAILED:
                # 对于失败的任务，显示"重试"和"删除"按钮
                
                # 重试按钮
                retry_btn = QPushButton("重试")
                retry_btn.setProperty("task_id", task.id)
                retry_btn.setMinimumHeight(30)
                retry_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f0f9eb;
                        border: 1px solid #c2e7b0;
                        border-radius: 4px;
                        padding: 2px 8px;
                        color: #67c23a;
                        min-height: 30px;
                    }
                    QPushButton:hover {
                        background-color: #e1f3d8;
                    }
                """)
                retry_btn.clicked.connect(lambda checked, tid=task.id: self.task_action_requested.emit(tid, "retry"))
                action_layout.addWidget(retry_btn)
                
                # 删除按钮
                delete_btn = QPushButton("删除")
                delete_btn.setProperty("task_id", task.id)
                delete_btn.setMinimumHeight(30)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #fef0f0;
                        border: 1px solid #fbc4c4;
                        border-radius: 4px;
                        padding: 2px 8px;
                        color: #f56c6c;
                        min-height: 30px;
                    }
                    QPushButton:hover {
                        background-color: #fde2e2;
                    }
                """)
                delete_btn.clicked.connect(lambda checked, tid=task.id: self.task_action_requested.emit(tid, "delete"))
                action_layout.addWidget(delete_btn)
            else:
                # 其他状态的任务显示取消按钮
                cancel_btn = QPushButton("取消")
                cancel_btn.setProperty("task_id", task.id)
                cancel_btn.setMinimumHeight(30)
                cancel_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #fef0f0;
                        border: 1px solid #fbc4c4;
                        border-radius: 4px;
                        padding: 2px 8px;
                        color: #f56c6c;
                        min-height: 30px;
                    }
                    QPushButton:hover {
                        background-color: #fde2e2;
                    }
                """)
                cancel_btn.clicked.connect(lambda checked, tid=task.id: self.task_action_requested.emit(tid, "cancel"))
                action_layout.addWidget(cancel_btn)
            
            # 如果是已完成状态，添加打开文件夹按钮
            if task.status == DownloadTask.STATUS_COMPLETED:
                open_folder_btn = QPushButton("打开文件夹")
                open_folder_btn.setProperty("task_id", task.id)
                open_folder_btn.setMinimumHeight(30)
                open_folder_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ecf5ff;
                        border: 1px solid #b3d8ff;
                        border-radius: 4px;
                        padding: 2px 8px;
                        color: #409eff;
                        min-height: 30px;
                    }
                    QPushButton:hover {
                        background-color: #d9ecff;
                    }
                """)
                open_folder_btn.clicked.connect(lambda checked, tid=task.id: self.open_task_folder(tid))
                action_layout.addWidget(open_folder_btn)
            
            self.task_table.setCellWidget(row, 0, action_widget)
            
            # 标题 (列1)
            title_item = QTableWidgetItem(task.title)
            title_item.setData(Qt.ItemDataRole.UserRole, task.id)  # 存储任务ID
            self.task_table.setItem(row, 1, title_item)
            
            # 进度 (列2)
            progress_widget = self.create_progress_widget(task)
            self.task_table.setCellWidget(row, 2, progress_widget)
            
            # 类型 (列3)
            self.task_table.setItem(row, 3, QTableWidgetItem(task.get_display_type()))
            
            # 保存路径 (列4)
            self.task_table.setItem(row, 4, QTableWidgetItem(task.save_path))
            
            # 状态 (列5)
            status_item = QTableWidgetItem(task.get_display_status())
            if task.status == DownloadTask.STATUS_FAILED:
                status_item.setForeground(QBrush(Qt.GlobalColor.red))
            elif task.status == DownloadTask.STATUS_COMPLETED:
                status_item.setForeground(QBrush(Qt.GlobalColor.green))
            self.task_table.setItem(row, 5, status_item)
            
            # 创建时间 (列6)
            time_str = task.created_at.strftime("%Y-%m-%d %H:%M:%S")
            self.task_table.setItem(row, 6, QTableWidgetItem(time_str))
        
        # 更新状态栏
        self.status_label.setText(f"总计: {len(filtered_tasks)} 个任务")
    
    def create_progress_widget(self, task):
        """
        创建进度显示组件
        
        Args:
            task: 任务对象
            
        Returns:
            QWidget: 包含进度条的组件
        """
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(4, 2, 4, 2)
        progress_layout.setSpacing(2)
        
        # 根据下载类型和状态创建不同的进度条
        if task.download_type == "full" and task.status == task.STATUS_ACTIVE:
            # 完整视频下载需要三个进度条：视频、音频、合并
            
            # 主进度条
            main_progress = QProgressBar()
            main_progress.setRange(0, 100)
            main_progress.setValue(int(task.progress))
            main_progress.setFormat(f"总进度: %p% ({task.progress:.1f}%)")
            main_progress.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #dcdfe6;
                    border-radius: 3px;
                    text-align: center;
                    background-color: #f5f7fa;
                    min-height: 15px;
                }
                QProgressBar::chunk {
                    background-color: #409eff;
                    border-radius: 2px;
                }
            """)
            progress_layout.addWidget(main_progress)
            
            # 获取详细进度
            progress_details = self.task_progress_details.get(task.id, {'video': 0, 'audio': 0, 'merge': 0})
            
            # 视频进度条
            video_progress = QProgressBar()
            video_progress.setRange(0, 100)
            video_progress.setValue(int(progress_details.get('video', 0)))
            video_progress.setFormat(f"视频: %p%")
            video_progress.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #dcdfe6;
                    border-radius: 2px;
                    text-align: center;
                    background-color: #f5f7fa;
                    min-height: 10px;
                }
                QProgressBar::chunk {
                    background-color: #67c23a;
                    border-radius: 1px;
                }
            """)
            progress_layout.addWidget(video_progress)
            
            # 音频进度条
            audio_progress = QProgressBar()
            audio_progress.setRange(0, 100)
            audio_progress.setValue(int(progress_details.get('audio', 0)))
            audio_progress.setFormat(f"音频: %p%")
            audio_progress.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #dcdfe6;
                    border-radius: 2px;
                    text-align: center;
                    background-color: #f5f7fa;
                    min-height: 10px;
                }
                QProgressBar::chunk {
                    background-color: #e6a23c;
                    border-radius: 1px;
                }
            """)
            progress_layout.addWidget(audio_progress)
            
        else:
            # 单一类型下载只需要一个进度条
            progress_widget = QProgressBar()
            progress_widget.setMinimum(0)
            progress_widget.setMaximum(100)
            progress_widget.setValue(int(task.progress))
            progress_widget.setTextVisible(True)
            progress_widget.setFormat("%.1f%%" % task.progress)
            
            # 根据状态设置不同样式
            if task.status == task.STATUS_COMPLETED:
                progress_widget.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid #dcdfe6;
                        border-radius: 3px;
                        text-align: center;
                        background-color: #f5f7fa;
                        min-height: 20px;
                    }
                    QProgressBar::chunk {
                        background-color: #67c23a;
                        border-radius: 2px;
                    }
                """)
            elif task.status == task.STATUS_FAILED:
                progress_widget.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid #dcdfe6;
                        border-radius: 3px;
                        text-align: center;
                        background-color: #f5f7fa;
                        min-height: 20px;
                    }
                    QProgressBar::chunk {
                        background-color: #f56c6c;
                        border-radius: 2px;
                    }
                """)
            else:
                progress_widget.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid #dcdfe6;
                        border-radius: 3px;
                        text-align: center;
                        background-color: #f5f7fa;
                        min-height: 20px;
                    }
                    QProgressBar::chunk {
                        background-color: #409eff;
                        border-radius: 2px;
                    }
                """)
            progress_layout.addWidget(progress_widget)
        
        return progress_container
    
    def update_task_progress(self, task_id, progress, message=""):
        """
        更新任务进度
        
        Args:
            task_id (str): 任务ID
            progress (float): 进度百分比
            message (str): 进度消息
        """
        # 更新任务管理器中的进度
        self.task_manager.update_task_progress(task_id, progress)
    
    def update_task_video_progress(self, task_id, progress):
        """
        更新任务的视频下载进度
        
        Args:
            task_id (str): 任务ID
            progress (float): 视频下载进度百分比
        """
        # 确保任务进度详情字典存在
        if task_id not in self.task_progress_details:
            self.task_progress_details[task_id] = {'video': 0, 'audio': 0, 'merge': 0}
        
        # 更新视频进度
        self.task_progress_details[task_id]['video'] = progress
    
    def update_task_audio_progress(self, task_id, progress):
        """
        更新任务的音频下载进度
        
        Args:
            task_id (str): 任务ID
            progress (float): 音频下载进度百分比
        """
        # 确保任务进度详情字典存在
        if task_id not in self.task_progress_details:
            self.task_progress_details[task_id] = {'video': 0, 'audio': 0, 'merge': 0}
        
        # 更新音频进度
        self.task_progress_details[task_id]['audio'] = progress
    
    def update_task_merge_progress(self, task_id, progress):
        """
        更新任务的合并进度
        
        Args:
            task_id (str): 任务ID
            progress (float): 合并进度百分比
        """
        # 确保任务进度详情字典存在
        if task_id not in self.task_progress_details:
            self.task_progress_details[task_id] = {'video': 0, 'audio': 0, 'merge': 0}
        
        # 更新合并进度
        self.task_progress_details[task_id]['merge'] = progress
    
    def open_task_folder(self, task_id):
        """打开任务保存文件夹"""
        task = self.task_manager.get_task(task_id)
        if task and self.file_manager:
            folder_path = os.path.dirname(task.save_path)
            self.file_manager.open_folder(folder_path)
    
    def clear_completed_tasks(self):
        """清理已完成的任务"""
        completed_tasks = self.task_manager.get_tasks_by_status(DownloadTask.STATUS_COMPLETED)
        if not completed_tasks:
            QMessageBox.information(self, "提示", "没有已完成的任务可清理")
            return
        
        reply = QMessageBox.question(
            self,
            "确认清理", 
            f"确定要清理 {len(completed_tasks)} 个已完成的任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for task in completed_tasks:
                self.task_manager.remove_task(task.id)
                
                # 清理进度详情
                if task.id in self.task_progress_details:
                    del self.task_progress_details[task.id]
                    
            self.refresh_task_list()
            QMessageBox.information(self, "提示", "清理完成") 