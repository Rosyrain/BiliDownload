"""
样式管理器模块，负责管理应用的主题和样式
"""

from enum import Enum

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QFont
from qfluentwidgets import (
    Theme,
    isDarkTheme,
    setStyleSheet,
    setTheme,
)


class StyleManager(QObject):
    """样式管理器，负责管理应用的主题和样式"""

    # 主题变更信号
    themeChanged = pyqtSignal(Theme)

    class Themes(Enum):
        """主题枚举"""

        LIGHT = "light"
        DARK = "dark"

    def __init__(self):
        super().__init__()
        self._current_theme = Theme.AUTO
        self._init_theme()

    def _init_theme(self):
        """初始化主题"""
        setTheme(self._current_theme)

    def toggle_theme(self):
        """切换主题"""
        if isDarkTheme():
            self.set_theme(Theme.LIGHT)
        else:
            self.set_theme(Theme.DARK)

    def set_theme(self, theme):
        """设置主题"""
        if theme == self._current_theme:
            return

        self._current_theme = theme
        setTheme(theme)
        self.themeChanged.emit(theme)

    @staticmethod
    def get_default_font():
        """获取默认字体"""
        font = QFont("Microsoft YaHei UI", 10)
        return font

    @staticmethod
    def apply_stylesheet(widget, stylesheet_path):
        """应用样式表"""
        setStyleSheet(widget, stylesheet_path)


# 全局样式管理器实例
style_manager = StyleManager()
