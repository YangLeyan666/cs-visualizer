"""所有功能模块界面的基类。"""

import tkinter as tk

from . import theme


class ModuleView(tk.Frame):
    title = "模块"
    subtitle = ""

    def __init__(self, master, app):
        super().__init__(master, bg=theme.BG)
        self.app = app

    def on_show(self):
        """切换到该模块时调用，子类可覆盖以延迟初始化。"""
