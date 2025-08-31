"""
测试新的UI界面 - 简化版
"""

import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from qfluentwidgets import (
    MSFluentWindow, SubtitleLabel, setTheme, Theme, 
    FluentIcon, InfoBar, InfoBarPosition, PushButton
)


class TestWindow(MSFluentWindow):
    """测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UI测试 - 简化版")
        self.resize(1200, 800)
        
        # 创建测试页面
        self._create_test_pages()
        
        # 应用主题
        setTheme(Theme.AUTO)
    
    def _create_test_pages(self):
        """创建测试页面"""
        # 页面1
        page1 = self.create_page("页面1")
        page1.setObjectName("homePage")
        self.addSubInterface(page1, FluentIcon.HOME, "首页")
        
        # 页面2
        page2 = self.create_page("页面2")
        page2.setObjectName("downloadPage")
        self.addSubInterface(page2, FluentIcon.DOWNLOAD, "下载")
        
        # 页面3
        page3 = self.create_page("页面3")
        page3.setObjectName("filePage")
        self.addSubInterface(page3, FluentIcon.FOLDER, "文件")
        
        # 设置页面
        settings_page = self.create_page("设置页面")
        settings_page.setObjectName("settingsPage")
        # 使用位置参数而不是NavigationItemPosition.BOTTOM
        self.addSubInterface(settings_page, FluentIcon.SETTING, "设置", position=1)
    
    def create_page(self, title):
        """创建测试页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # 添加标题
        title_label = SubtitleLabel(title, page)
        layout.addWidget(title_label)
        
        # 添加按钮
        button = PushButton("显示通知", page)
        button.clicked.connect(lambda: self.show_notification(title))
        layout.addWidget(button)
        
        # 添加弹性空间
        layout.addStretch(1)
        
        return page
    
    def show_notification(self, title):
        """显示通知"""
        InfoBar.success(
            title="通知",
            content=f"这是来自 {title} 的通知",
            orient=InfoBarPosition.TOP_RIGHT,
            parent=self
        )


if __name__ == "__main__":
    # 创建应用
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec()) 