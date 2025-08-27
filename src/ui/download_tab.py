"""
下载管理标签页
"""
import os
import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QProgressBar,
    QTextEdit, QComboBox, QCheckBox, QGroupBox,
    QFileDialog, QMessageBox, QFrame, QSplitter, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from src.core.downloader import BiliDownloader
from src.core.config_manager import ConfigManager
from src.core.logger import get_logger


class DownloadWorker(QThread):
    """下载工作线程"""
    
    progress_updated = pyqtSignal(int, str)
    download_finished = pyqtSignal(bool, str)
    
    def __init__(self, downloader, video_url, save_path, ffmpeg_path, 
                 cookie="", download_series=False):
        super().__init__()
        self.downloader = downloader
        self.video_url = video_url
        self.save_path = save_path
        self.ffmpeg_path = ffmpeg_path
        self.cookie = cookie
        self.download_series = download_series
        self.logger = get_logger("DownloadWorker")
    
    def run(self):
        """运行下载任务"""
        try:
            self.logger.info(f"开始下载任务: {self.video_url}")
            
            if self.download_series:
                self.logger.info("下载模式: 系列视频")
                success = self.downloader.download_series(
                    self.video_url, self.save_path, self.ffmpeg_path,
                    self.cookie, self.progress_updated.emit
                )
            else:
                self.logger.info("下载模式: 单个视频")
                video_info = self.downloader.get_video_info(self.video_url, self.cookie)
                if video_info:
                    success = self.downloader.download_video(
                        video_info, self.save_path, self.ffmpeg_path,
                        self.progress_updated.emit
                    )
                else:
                    self.logger.warning("无法获取视频信息")
                    success = False
            
            if success:
                self.logger.info("下载任务完成")
                self.download_finished.emit(True, "下载完成！")
            else:
                self.logger.warning("下载任务失败")
                self.download_finished.emit(False, "下载失败！")
                
        except Exception as e:
            self.logger.error(f"下载任务异常: {e}")
            self.download_finished.emit(False, f"下载出错: {str(e)}")


class DownloadTab(QWidget):
    """下载管理标签页"""
    
    def __init__(self, downloader: BiliDownloader, config_manager: ConfigManager):
        super().__init__()
        self.downloader = downloader
        self.config_manager = config_manager
        self.download_worker = None
        self.logger = get_logger("DownloadTab")
        
        self.init_ui()
        self.load_config()
    
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
            QPushButton:disabled {
                background-color: #f0f4ff;
                color: #a0a8cf;
                border-color: #e1e8ff;
            }
            QProgressBar {
                border: 1px solid #e1e8ff;
                border-radius: 6px;
                text-align: center;
                background: #f8f9ff;
                color: #4a5bbf;
                font-weight: 500;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #4a5bbf, stop:1 #5a6acf);
                border-radius: 5px;
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
            QCheckBox {
                color: #5a6acf;
                font-weight: 500;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #d1d8ff;
                border-radius: 3px;
                background: white;
            }
            QCheckBox::indicator:checked {
                background: #4a5bbf;
                border-color: #4a5bbf;
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
        
        # 左侧：下载控制面板
        left_panel = self.create_download_panel()
        splitter.addWidget(left_panel)
        
        # 右侧：下载日志
        right_panel = self.create_log_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setSizes([600, 400])
        
        # 底部：进度条
        bottom_panel = self.create_progress_panel()
        layout.addWidget(bottom_panel)
    
    def create_download_panel(self) -> QWidget:
        """创建下载控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("下载控制")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #4a5bbf;
            margin-bottom: 10px;
        """)
        layout.addWidget(title_label)
        
        # 视频URL输入
        url_group = QGroupBox("视频信息")
        url_layout = QVBoxLayout(url_group)
        
        url_input_layout = QHBoxLayout()
        url_label = QLabel("视频URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("请输入B站视频链接")
        url_input_layout.addWidget(url_label)
        url_input_layout.addWidget(self.url_input)
        url_layout.addLayout(url_input_layout)
        
        # 视频标题输入
        title_input_layout = QHBoxLayout()
        title_label = QLabel("视频标题:")
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("视频标题将自动获取，也可手动编辑")
        self.title_input.setReadOnly(False)  # 允许用户编辑
        title_input_layout.addWidget(title_label)
        title_input_layout.addWidget(self.title_input)
        
        self.get_title_btn = QPushButton("🔍 获取标题")
        self.get_title_btn.clicked.connect(self.get_video_title)
        title_input_layout.addWidget(self.get_title_btn)
        
        # 添加清空标题按钮
        self.clear_title_btn = QPushButton("🗑️ 清空")
        self.clear_title_btn.clicked.connect(self.clear_title)
        title_input_layout.addWidget(self.clear_title_btn)
        
        url_layout.addLayout(title_input_layout)
        
        # 快速操作按钮
        quick_actions = QHBoxLayout()
        quick_actions.setSpacing(10)
        
        self.paste_btn = QPushButton("📋 粘贴")
        self.paste_btn.clicked.connect(self.paste_url)
        quick_actions.addWidget(self.paste_btn)
        
        # 连接URL输入框的文本变化信号，自动获取标题
        self.url_input.textChanged.connect(self.on_url_changed)
        
        # 创建定时器，定期检查FFmpeg状态变化
        self.ffmpeg_check_timer = QTimer()
        self.ffmpeg_check_timer.timeout.connect(self.update_ffmpeg_status)
        self.ffmpeg_check_timer.start(5000)  # 每5秒检查一次
        
        self.clear_btn = QPushButton("🗑️ 清空")
        self.clear_btn.clicked.connect(self.clear_url)
        quick_actions.addWidget(self.clear_btn)
        
        quick_actions.addStretch()
        url_layout.addLayout(quick_actions)
        
        layout.addWidget(url_group)
        
        # 保存路径设置
        path_group = QGroupBox("保存设置")
        path_layout = QVBoxLayout(path_group)
        
        # 保存路径选择
        path_input_layout = QHBoxLayout()
        path_label = QLabel("保存路径:")
        self.save_path_input = QLineEdit()
        self.save_path_input.setPlaceholderText("选择保存路径")
        self.browse_path_btn = QPushButton("浏览")
        self.browse_path_btn.clicked.connect(self.browse_save_path)
        path_input_layout.addWidget(path_label)
        path_input_layout.addWidget(self.save_path_input)
        path_input_layout.addWidget(self.browse_path_btn)
        path_layout.addLayout(path_input_layout)
        
        # 快速路径选择
        quick_path_layout = QHBoxLayout()
        quick_path_layout.setSpacing(10)
        
        self.default_path_btn = QPushButton("📁 默认路径")
        self.default_path_btn.clicked.connect(self.set_default_path)
        quick_path_layout.addWidget(self.default_path_btn)
        
        self.video_path_btn = QPushButton("🎬 视频分类")
        self.video_path_btn.clicked.connect(self.set_video_path)
        quick_path_layout.addWidget(self.video_path_btn)
        
        self.music_path_btn = QPushButton("🎵 音乐分类")
        self.music_path_btn.clicked.connect(self.set_music_path)
        quick_path_layout.addWidget(self.music_path_btn)
        
        self.document_path_btn = QPushButton("📄 文档分类")
        self.document_path_btn.clicked.connect(self.set_document_path)
        quick_path_layout.addWidget(self.document_path_btn)
        
        quick_path_layout.addStretch()
        path_layout.addLayout(quick_path_layout)
        
        layout.addWidget(path_group)
        
        # 下载选项
        options_group = QGroupBox("下载选项")
        options_layout = QVBoxLayout(options_group)
        
        # 系列下载选项
        series_layout = QHBoxLayout()
        self.download_series_cb = QCheckBox("下载系列视频")
        self.download_series_cb.setToolTip("勾选后将下载整个系列的所有分P")
        series_layout.addWidget(self.download_series_cb)
        series_layout.addStretch()
        options_layout.addLayout(series_layout)
        
        # FFmpeg路径设置（从配置中自动获取，无需用户输入）
        ffmpeg_info_layout = QHBoxLayout()
        ffmpeg_info_label = QLabel("FFmpeg状态:")
        self.ffmpeg_status_label = QLabel("未设置")
        self.ffmpeg_status_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        ffmpeg_info_layout.addWidget(ffmpeg_info_label)
        ffmpeg_info_layout.addWidget(self.ffmpeg_status_label)
        ffmpeg_info_layout.addStretch()
        options_layout.addLayout(ffmpeg_info_layout)
        
        # 高级选项
        advanced_layout = QHBoxLayout()
        self.use_cookie_cb = QCheckBox("使用Cookie")
        self.use_cookie_cb.setToolTip("勾选后可以使用Cookie获取高清视频")
        advanced_layout.addWidget(self.use_cookie_cb)
        
        self.cookie_input = QLineEdit()
        self.cookie_input.setPlaceholderText("输入Cookie字符串（可选）")
        self.cookie_input.setVisible(False)
        advanced_layout.addWidget(self.cookie_input)
        
        self.use_cookie_cb.toggled.connect(self.cookie_input.setVisible)
        advanced_layout.addStretch()
        options_layout.addLayout(advanced_layout)
        
        layout.addWidget(options_group)
        
        # 下载按钮
        button_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("🚀 开始下载")
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a5bbf;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3a4baf;
            }
            QPushButton:disabled {
                background-color: #a0a8cf;
            }
        """)
        self.download_btn.clicked.connect(self.start_download)
        button_layout.addWidget(self.download_btn)
        
        self.stop_btn = QPushButton("⏹️ 停止下载")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_download)
        button_layout.addWidget(self.stop_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        return panel
    
    def create_log_panel(self) -> QWidget:
        """创建日志面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 标题
        title_label = QLabel("下载日志")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #0078d4;
            margin-bottom: 10px;
        """)
        layout.addWidget(title_label)
        
        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: "Consolas", "Monaco", monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.log_text)
        
        # 清空日志按钮
        clear_log_btn = QPushButton("清空日志")
        clear_log_btn.clicked.connect(self.clear_log)
        layout.addWidget(clear_log_btn)
        
        return panel
    
    def create_progress_panel(self) -> QWidget:
        """创建进度面板"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        layout.addWidget(QLabel("下载进度:"))
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)
        
        layout.addStretch()
        
        return panel
    
    def load_config(self):
        """加载配置"""
        # 设置保存路径
        save_path = self.config_manager.get_download_path()
        self.save_path_input.setText(save_path)
        
        # 更新FFmpeg状态显示
        self.update_ffmpeg_status()
        
        # 加载分类
        self.refresh_categories()
    
    def update_ffmpeg_status(self):
        """更新FFmpeg状态显示"""
        ffmpeg_path = self.config_manager.get_ffmpeg_path()
        if ffmpeg_path and os.path.exists(ffmpeg_path):
            self.ffmpeg_status_label.setText("已设置 ✓")
            self.ffmpeg_status_label.setStyleSheet("color: #51cf66; font-weight: bold;")
        else:
            self.ffmpeg_status_label.setText("未设置 ✗")
            self.ffmpeg_status_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
    
    def refresh_categories(self):
        """刷新分类列表"""
        # 这个方法现在用于更新快速路径选择按钮的状态
        # 分类选择已经改为路径选择，不再需要刷新分类下拉框
        pass
    
    def browse_save_path(self):
        """浏览保存路径"""
        path = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if path:
            self.save_path_input.setText(path)
            self.config_manager.set_download_path(path)
    
    # FFmpeg路径现在从配置中自动获取，无需用户手动设置
    
    def get_video_title(self):
        """获取视频标题（强制获取，覆盖用户编辑的内容）"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "警告", "请输入视频URL")
            return
        
        if not re.match(r'https?://.*bilibili\.com.*', url):
            QMessageBox.warning(self, "警告", "请输入有效的B站视频链接")
            return
        
        # 如果用户已经编辑了标题，询问是否覆盖
        current_title = self.title_input.text().strip()
        if current_title and current_title != "":
            reply = QMessageBox.question(
                self, "确认覆盖", 
                f"当前标题: {current_title}\n\n是否要获取新的标题覆盖当前内容？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        self.get_title_btn.setEnabled(False)
        self.get_title_btn.setText("获取中...")
        
        try:
            video_info = self.downloader.get_video_info(url)
            if video_info:
                self.title_input.setText(video_info['title'])
                self.log_message(f"成功获取视频标题: {video_info['title']}")
                self.get_title_btn.setText("重新获取")
            else:
                QMessageBox.warning(self, "错误", "无法获取视频标题")
                self.log_message("获取视频标题失败")
                self.get_title_btn.setText("获取标题")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取视频标题时出错: {str(e)}")
            self.log_message(f"获取视频标题出错: {str(e)}")
            self.get_title_btn.setText("获取标题")
        finally:
            self.get_title_btn.setEnabled(True)
    
    def start_download(self):
        """开始下载"""
        # 验证输入
        if not self.validate_inputs():
            return
        
        # 获取下载参数
        url = self.url_input.text().strip()
        save_path = self.save_path_input.text()
        cookie = self.cookie_input.text().strip()
        download_series = self.download_series_cb.isChecked()
        
        # 保存路径已经在save_path_input中设置，无需额外调整
        # 用户可以直接选择或输入保存路径
        
        # 创建下载工作线程（FFmpeg路径从配置中自动获取）
        self.download_worker = DownloadWorker(
            self.downloader, url, save_path, None, cookie, download_series
        )
        
        # 连接信号
        self.download_worker.progress_updated.connect(self.update_progress)
        self.download_worker.download_finished.connect(self.download_finished)
        
        # 开始下载
        self.download_worker.start()
        
        # 更新UI状态
        self.download_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        
        self.log_message("开始下载...")
    
    def stop_download(self):
        """停止下载"""
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.terminate()
            self.download_worker.wait()
            self.download_finished(False, "下载已停止")
    
    def validate_inputs(self) -> bool:
        """验证输入"""
        if not self.url_input.text().strip():
            QMessageBox.warning(self, "警告", "请输入视频URL")
            return False
        
        if not self.save_path_input.text():
            QMessageBox.warning(self, "警告", "请选择保存路径")
            return False
        
        # FFmpeg路径是可选的，不强制要求
        # if not self.ffmpeg_input.text():
        #     QMessageBox.warning(self, "警告", "请选择FFmpeg路径")
        #     return False
        
        return True
    
    def update_progress(self, value: int, message: str):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
        self.log_message(message)
    
    def download_finished(self, success: bool, message: str):
        """下载完成"""
        # 更新UI状态
        self.download_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # 显示结果
        if success:
            QMessageBox.information(self, "完成", message)
        else:
            QMessageBox.warning(self, "失败", message)
        
        self.log_message(message)
    
    def log_message(self, message: str):
        """添加日志消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
    
    def show_quick_download_dialog(self):
        """显示快速下载对话框"""
        # 这里可以实现一个简化的快速下载对话框
        self.url_input.setFocus() 
    
    def set_default_path(self):
        """设置默认路径"""
        try:
            default_path = self.config_manager.get_download_path()
            self.save_path_input.setText(default_path)
            self.logger.info(f"设置默认路径: {default_path}")
        except Exception as e:
            self.logger.error(f"设置默认路径失败: {e}")
    
    def set_video_path(self):
        """设置视频分类路径"""
        try:
            video_path = self.config_manager.get_category_path("video")
            self.save_path_input.setText(video_path)
            self.logger.info(f"设置视频分类路径: {video_path}")
        except Exception as e:
            self.logger.error(f"设置视频分类路径失败: {e}")
    
    def set_music_path(self):
        """设置音乐分类路径"""
        try:
            music_path = self.config_manager.get_category_path("music")
            self.save_path_input.setText(music_path)
            self.logger.info(f"设置音乐分类路径: {music_path}")
        except Exception as e:
            self.logger.error(f"设置音乐分类路径失败: {e}")
    
    def set_document_path(self):
        """设置文档分类路径"""
        try:
            document_path = self.config_manager.get_category_path("document")
            self.save_path_input.setText(document_path)
            self.logger.info(f"设置文档分类路径: {document_path}")
        except Exception as e:
            self.logger.error(f"设置文档分类路径失败: {e}")
    
    def paste_url(self):
        """粘贴URL"""
        try:
            clipboard = QApplication.clipboard()
            url = clipboard.text()
            if url:
                self.url_input.setText(url)
                self.logger.info("已粘贴URL")
                # 粘贴后自动获取标题
                self.auto_get_title(url)
            else:
                self.logger.info("剪贴板为空")
        except Exception as e:
            self.logger.error(f"粘贴URL失败: {e}")
    
    def on_url_changed(self, text):
        """URL文本变化时的处理"""
        # 当用户手动输入或修改URL时，延迟自动获取标题
        if text.strip() and text.startswith('http'):
            # 使用定时器延迟执行，避免用户输入过程中频繁请求
            QTimer.singleShot(1000, lambda: self.auto_get_title(text.strip()))
    
    def auto_get_title(self, url):
        """自动获取标题"""
        if not url or not url.strip():
            return
        
        # 检查是否是有效的B站链接
        if not re.match(r'https?://.*bilibili\.com.*', url):
            return
        
        # 如果用户已经手动编辑了标题，不自动覆盖
        current_title = self.title_input.text().strip()
        if current_title and current_title != "":
            self.log_message("用户已手动编辑标题，跳过自动获取")
            return
        
        # 自动获取标题
        self.get_title_btn.setEnabled(False)
        self.get_title_btn.setText("获取中...")
        
        try:
            video_info = self.downloader.get_video_info(url)
            if video_info:
                self.title_input.setText(video_info['title'])
                self.log_message(f"自动获取视频标题: {video_info['title']}")
                self.get_title_btn.setText("重新获取")
            else:
                self.log_message("自动获取视频标题失败")
                self.get_title_btn.setText("获取标题")
        except Exception as e:
            self.log_message(f"自动获取视频标题出错: {str(e)}")
            self.get_title_btn.setText("获取标题")
        finally:
            self.get_title_btn.setEnabled(True)
    
    def clear_url(self):
        """清空URL"""
        self.url_input.clear()
        self.logger.info("已清空URL")
    
    def clear_title(self):
        """清空标题"""
        self.title_input.clear()
        self.logger.info("已清空标题") 