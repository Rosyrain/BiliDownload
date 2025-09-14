import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (
    FluentTranslator,
    FluentWindow,
    MessageBox,
    NavigationAvatarWidget,
    NavigationItemPosition,
)

from src.ui.category_tab import CategoryTab
from src.ui.download_tab import DownloadTab
from src.ui.file_manager_tab import FileManagerTab
from src.ui.settings_tab import SettingsTab
from src.ui.task_list_tab import TaskListTab


class Main_Interface(FluentWindow):
    def __init__(self):
        super().__init__()
        # 实例化各个 tab
        self.setObjectName("MainInterface")
        self.taskListTab = TaskListTab(self)
        self.settingsTab = SettingsTab(self)
        self.downloadTab = DownloadTab(self)
        self.fileManagerTab = FileManagerTab(self)
        self.categoryTab = CategoryTab(self)

        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        # 添加各个 tab 到导航栏
        self.addSubInterface(self.taskListTab, FIF.CAR, "任务列表")
        self.addSubInterface(self.downloadTab, FIF.DOWNLOAD, "下载")
        self.addSubInterface(self.fileManagerTab, FIF.FOLDER, "文件管理")
        self.addSubInterface(self.categoryTab, FIF.TAG, "分类")

        self.addSubInterface(
            self.settingsTab,
            FIF.SETTING,
            "设置",
            position=NavigationItemPosition.BOTTOM,
        )

        self.navigationInterface.addWidget(
            routeKey="avatar",
            widget=NavigationAvatarWidget("用户名", "resource/images/avatar.png"),
            onClick=self.showMessageBox,
            position=NavigationItemPosition.BOTTOM,
        )

        self.navigationInterface.setExpandWidth(280)

    def initWindow(self):
        self.resize(900, 700)
        self.setWindowIcon(QIcon(":/qfluentwidgets/images/logo.png"))
        self.setWindowTitle("BiliDownload")

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def showMessageBox(self):
        MessageBox("提示", "这是一个头像点击事件", self).exec()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    translator = FluentTranslator()
    app.installTranslator(translator)
    w = Main_Interface()
    w.show()
    sys.exit(app.exec())
