"""CS 基础概念可视化实验室 —— 程序入口。

运行：python main.py
"""

import sys
import tkinter as tk

if sys.platform == "win32":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

from ui import theme
from ui.number_base_view import NumberBaseView
from ui.twos_complement_view import TwosComplementView
from ui.parity_view import ParityView
from ui.scheduling_view import SchedulingView

APP_NAME = "CS 可视化实验室"
APP_VERSION = "v1.0.0"

MODULES = [
    ("number_base", "01", "进制转换", "除基取余 / 乘基取整", NumberBaseView),
    ("twos_complement", "02", "补码加减法", "8 位补码 · 进位与溢出", TwosComplementView),
    ("parity", "03", "ASCII 与奇偶校验", "7 位 ASCII · 1 位校验", ParityView),
    ("scheduling", "05", "进程调度模拟", "FCFS / SJF / 时间片轮转", SchedulingView),
]


class NavItem(tk.Frame):
    """侧边栏导航项。"""

    def __init__(self, master, number: str, title: str, command):
        super().__init__(master, bg=theme.SIDEBAR, cursor="hand2")
        self._command = command
        self._active = False

        self.bar = tk.Frame(self, bg=theme.SIDEBAR, width=theme.s(3))
        self.bar.pack(side="left", fill="y")
        self.badge = tk.Label(self, text=number, font=(theme.MONO[0], 9, "bold"),
                              bg=theme.SIDEBAR, fg=theme.FAINT, width=3)
        self.badge.pack(side="left", padx=(theme.s(6), theme.s(6)), pady=theme.s(11))
        self.label = tk.Label(self, text=title, font=theme.BODY, bg=theme.SIDEBAR,
                              fg=theme.MUTED, anchor="w")
        self.label.pack(side="left", fill="x", expand=True, pady=theme.s(11))

        for widget in (self, self.bar, self.badge, self.label):
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

    def _on_click(self, _event):
        self._command()

    def _on_enter(self, _event):
        if not self._active:
            for widget in (self, self.bar, self.badge, self.label):
                widget.configure(bg=theme.SURFACE)

    def _on_leave(self, _event):
        if not self._active:
            for widget in (self, self.bar, self.badge, self.label):
                widget.configure(bg=theme.SIDEBAR)

    def set_active(self, active: bool):
        self._active = active
        bg = theme.SURFACE if active else theme.SIDEBAR
        for widget in (self, self.bar, self.badge, self.label):
            widget.configure(bg=bg)
        self.bar.configure(bg=theme.ACCENT if active else bg)
        self.badge.configure(fg=theme.ACCENT if active else theme.FAINT)
        self.label.configure(fg=theme.TEXT if active else theme.MUTED,
                             font=theme.BODY_BOLD if active else theme.BODY)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        theme.init_scale(self)
        theme.init_fonts(self)
        theme.apply_ttk_style(self)

        self.title(f"{APP_NAME} · 计算机科学基础概念可视化")
        self.configure(bg=theme.BG)
        self._views = {}
        self._nav_items = {}
        self._current = None

        self._build_layout()
        self._place_window()
        self.show(MODULES[0][0])

        for index in range(len(MODULES)):
            self.bind(f"<Control-Key-{index + 1}>",
                      lambda _e, key=MODULES[index][0]: self.show(key))

    def _place_window(self):
        width, height = theme.s(1210), theme.s(700)
        self.minsize(theme.s(1140), theme.s(650))
        screen_w, screen_h = self.winfo_screenwidth(), self.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2 - theme.s(20))
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_layout(self):
        shell = tk.Frame(self, bg=theme.BG)
        shell.pack(fill="both", expand=True)

        self._build_sidebar(shell)

        main = tk.Frame(shell, bg=theme.BG)
        main.pack(side="left", fill="both", expand=True)

        header = tk.Frame(main, bg=theme.BG)
        header.pack(fill="x", padx=theme.s(24), pady=(theme.s(16), theme.s(8)))
        text_box = tk.Frame(header, bg=theme.BG)
        text_box.pack(side="left", fill="x", expand=True)
        self.header_title = tk.Label(text_box, text="", font=theme.TITLE, bg=theme.BG,
                                     fg=theme.TEXT, anchor="w")
        self.header_title.pack(fill="x")
        self.header_subtitle = tk.Label(text_box, text="", font=theme.SUBTITLE, bg=theme.BG,
                                        fg=theme.MUTED, anchor="w")
        self.header_subtitle.pack(fill="x", pady=(theme.s(2), 0))

        self.header_chip = tk.Label(
            header, text="Python · Tkinter", font=theme.SMALL, bg=theme.SURFACE_ALT,
            fg=theme.MUTED, padx=theme.s(12), pady=theme.s(6),
        )
        self.header_chip.pack(side="right", pady=(theme.s(4), 0))

        tk.Frame(main, bg=theme.BORDER, height=1).pack(fill="x", padx=theme.s(24))

        self.content = tk.Frame(main, bg=theme.BG)
        self.content.pack(fill="both", expand=True, padx=theme.s(24), pady=theme.s(14))

        status = tk.Frame(main, bg=theme.SIDEBAR, height=theme.s(28))
        status.pack(fill="x", side="bottom")
        status.pack_propagate(False)
        self.status_label = tk.Label(status, text="就绪", font=theme.SMALL,
                                     bg=theme.SIDEBAR, fg=theme.MUTED, anchor="w")
        self.status_label.pack(side="left", padx=theme.s(14), pady=theme.s(4))
        tk.Label(status, text=f"{APP_NAME} {APP_VERSION} · MIT License", font=theme.SMALL,
                 bg=theme.SIDEBAR, fg=theme.FAINT).pack(side="right", padx=theme.s(14), pady=theme.s(4))

    def _build_sidebar(self, shell):
        sidebar = tk.Frame(shell, bg=theme.SIDEBAR, width=theme.s(220))
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg=theme.SIDEBAR)
        brand.pack(fill="x", padx=theme.s(16), pady=(theme.s(18), theme.s(16)))
        tk.Label(brand, text="</>", font=(theme.MONO[0], 12, "bold"),
                 bg=theme.ACCENT, fg=theme.BG, width=4, height=2).pack(side="left")
        brand_text = tk.Frame(brand, bg=theme.SIDEBAR)
        brand_text.pack(side="left", padx=(theme.s(10), 0))
        tk.Label(brand_text, text="CS 可视化", font=theme.H2, bg=theme.SIDEBAR,
                 fg=theme.TEXT, anchor="w").pack(fill="x")
        tk.Label(brand_text, text="基础概念实验室", font=theme.SMALL, bg=theme.SIDEBAR,
                 fg=theme.FAINT, anchor="w").pack(fill="x")

        tk.Frame(sidebar, bg=theme.BORDER, height=1).pack(fill="x", padx=theme.s(16))
        tk.Label(sidebar, text="实验模块", font=theme.SMALL, bg=theme.SIDEBAR,
                 fg=theme.FAINT, anchor="w").pack(fill="x", padx=theme.s(20),
                                                  pady=(theme.s(14), theme.s(6)))

        for key, number, title, _desc, _cls in MODULES:
            item = NavItem(sidebar, number, title, lambda k=key: self.show(k))
            item.pack(fill="x", padx=theme.s(10), pady=1)
            self._nav_items[key] = item

        footer = tk.Frame(sidebar, bg=theme.SIDEBAR)
        footer.pack(side="bottom", fill="x", padx=theme.s(16), pady=theme.s(14))
        tk.Frame(footer, bg=theme.BORDER, height=1).pack(fill="x", pady=(0, theme.s(10)))
        tk.Label(footer, text="Markdown · Git · Vibe Coding", font=theme.SMALL,
                 bg=theme.SIDEBAR, fg=theme.FAINT, anchor="w").pack(fill="x")
        tk.Label(footer, text="计算机科学基础 · 综合实验", font=theme.SMALL,
                 bg=theme.SIDEBAR, fg=theme.FAINT, anchor="w").pack(fill="x", pady=(theme.s(2), 0))

    def show(self, key: str):
        module = next((m for m in MODULES if m[0] == key), None)
        if module is None:
            return

        if key not in self._views:
            view = module[4](self.content, self)
            view.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._views[key] = view

        view = self._views[key]
        view.tkraise()
        view.on_show()

        self.header_title.configure(text=module[2])
        self.header_subtitle.configure(text=module[3])
        self.header_chip.configure(text=f"模块 {module[1]} / 06")

        for nav_key, item in self._nav_items.items():
            item.set_active(nav_key == key)
        self._current = key

    def set_status(self, text: str):
        self.status_label.configure(text=text)


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
