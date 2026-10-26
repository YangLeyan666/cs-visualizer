"""可复用的界面组件：卡片、分段选择器、表格、滚动容器等。"""

import tkinter as tk
from tkinter import ttk

from . import theme
from .theme import s


class Card(tk.Frame):
    """带标题的卡片（Tk 无真圆角，用细边框模拟）。"""

    def __init__(self, master, title: str = "", subtitle: str = "", pad: int = 14, **kw):
        super().__init__(master, bg=theme.SURFACE, highlightbackground=theme.BORDER,
                         highlightthickness=1, **kw)
        self.body = tk.Frame(self, bg=theme.SURFACE)
        self.body.pack(fill="both", expand=True, padx=s(pad), pady=s(pad))

        if title:
            head = tk.Frame(self.body, bg=theme.SURFACE)
            head.pack(fill="x", pady=(0, s(8)))
            tk.Label(head, text=title, font=theme.H2, bg=theme.SURFACE,
                     fg=theme.TEXT, anchor="w").pack(side="left")
            if subtitle:
                tk.Label(head, text=subtitle, font=theme.SMALL, bg=theme.SURFACE,
                         fg=theme.MUTED, anchor="w").pack(side="left", padx=(s(10), 0),
                                                          pady=(s(3), 0))


class Segmented(tk.Frame):
    """一排互斥按钮，替代 Combobox，避免原生下拉框的配色问题。"""

    def __init__(self, master, options, command=None, value=None, **kw):
        super().__init__(master, bg=theme.SURFACE_ALT, highlightbackground=theme.BORDER,
                         highlightthickness=1, **kw)
        self._choices = list(options)
        self._command = command
        self._value = value if value is not None else self._choices[0][0]
        self._buttons = {}
        for index, (key, text) in enumerate(self._choices):
            btn = tk.Button(
                self, text=text, font=theme.BODY, bd=0, relief="flat",
                padx=s(12), pady=s(5), cursor="hand2",
                command=lambda k=key: self.set(k, notify=True),
            )
            btn.pack(side="left", padx=(1 if index else 0, 0), pady=1)
            self._buttons[key] = btn
        self._paint()

    def _paint(self):
        for key, btn in self._buttons.items():
            active = key == self._value
            btn.configure(
                bg=theme.ACCENT if active else theme.SURFACE_ALT,
                fg=theme.BG if active else theme.MUTED,
                activebackground=theme.ACCENT if active else theme.SURFACE_HOVER,
                activeforeground=theme.BG if active else theme.TEXT,
            )

    def set(self, value, notify: bool = False):
        if value not in self._buttons:
            return
        self._value = value
        self._paint()
        if notify and self._command:
            self._command(value)

    def get(self):
        return self._value


class ActionButton(tk.Button):
    def __init__(self, master, text, command=None, kind: str = "primary", **kw):
        palette = {
            "primary": (theme.ACCENT, theme.BG, theme.ACCENT_DARK),
            "ghost": (theme.SURFACE_ALT, theme.TEXT, theme.SURFACE_HOVER),
            "danger": (theme.DANGER, theme.BG, "#d94f4f"),
            "ok": (theme.OK, theme.BG, "#2fb87c"),
        }[kind]
        bg, fg, hover = palette
        super().__init__(
            master, text=text, command=command, bg=bg, fg=fg,
            activebackground=hover, activeforeground=fg,
            font=theme.BODY_BOLD, bd=0, relief="flat", cursor="hand2",
            padx=s(14), pady=s(6), **kw,
        )


class StatChip(tk.Frame):
    """小型指标块：上方数值，下方说明。"""

    def __init__(self, master, label: str, value: str = "—", color: str = theme.ACCENT):
        super().__init__(master, bg=theme.SURFACE_ALT, highlightbackground=theme.BORDER,
                         highlightthickness=1)
        self._value = tk.Label(self, text=value, font=(theme.MONO[0], 13, "bold"),
                               bg=theme.SURFACE_ALT, fg=color)
        self._value.pack(padx=s(12), pady=(s(6), 0))
        tk.Label(self, text=label, font=theme.SMALL, bg=theme.SURFACE_ALT,
                 fg=theme.MUTED).pack(padx=s(12), pady=(0, s(5)))

    def set(self, value, color: str | None = None):
        self._value.configure(text=str(value))
        if color:
            self._value.configure(fg=color)


class DataTable(tk.Frame):
    """轻量表格：使用 grid 排布 Label，支持行底色交替与单元格着色。"""

    def __init__(self, master, columns, widths=None, anchors=None, header_bg=theme.SURFACE_ALT):
        super().__init__(master, bg=theme.BORDER)
        self.columns = list(columns)
        self.widths = list(widths or [10] * len(columns))
        self.anchors = list(anchors or ["center"] * len(columns))
        self._header_bg = header_bg
        self._rows = 0
        self._render_header()

    def _render_header(self):
        for col, name in enumerate(self.columns):
            cell = tk.Label(
                self, text=name, font=theme.SMALL, bg=self._header_bg, fg=theme.MUTED,
                width=self.widths[col], anchor="center", padx=s(6), pady=s(5),
            )
            cell.grid(row=0, column=col, sticky="nsew", padx=(0, 1), pady=(0, 1))

    def clear(self):
        for child in self.grid_slaves():
            info = child.grid_info()
            if int(info["row"]) > 0:
                child.destroy()
        self._rows = 0

    def set_rows(self, rows, cell_colors=None):
        """rows: list[list[str]]；cell_colors: {(row, col): (fg, bg)}"""
        self.clear()
        cell_colors = cell_colors or {}
        for r, row in enumerate(rows, start=1):
            bg = theme.SURFACE if r % 2 else "#17273f"
            for c, text in enumerate(row):
                fg, cell_bg = cell_colors.get((r - 1, c), (theme.TEXT, bg))
                tk.Label(
                    self, text=str(text), font=theme.MONO_SMALL, bg=cell_bg, fg=fg,
                    width=self.widths[c], anchor=self.anchors[c], padx=s(6), pady=s(4),
                ).grid(row=r, column=c, sticky="nsew", padx=(0, 1), pady=(0, 1))
        self._rows = len(rows)
        for c in range(len(self.columns)):
            self.grid_columnconfigure(c, weight=1)


class ScrollFrame(tk.Frame):
    """纵向滚动容器，内容放在 .inner 中。"""

    def __init__(self, master, bg=theme.BG):
        super().__init__(master, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.vbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.canvas.configure(yscrollcommand=self.vbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.vbar.pack(side="right", fill="y")

        self.inner.bind("<Configure>", self._on_inner)
        self.canvas.bind("<Configure>", self._on_canvas)
        self.canvas.bind("<Enter>", lambda _e: self._bind_wheel(True))
        self.canvas.bind("<Leave>", lambda _e: self._bind_wheel(False))

    def _on_inner(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas(self, event):
        self.canvas.itemconfigure(self._window, width=event.width)

    def _bind_wheel(self, active: bool):
        if active:
            self.canvas.bind_all("<MouseWheel>", self._on_wheel)
        else:
            self.canvas.unbind_all("<MouseWheel>")

    def _on_wheel(self, event):
        self.canvas.yview_scroll(int(-event.delta / 120), "units")


class BitStrip(tk.Canvas):
    """一排二进制位方块，可用于补码 / 校验位演示。"""

    def __init__(self, master, count: int = 8, cell: int = 34, gap: int = 5,
                 bg=theme.SURFACE, show_index: bool = True, group: int | None = None):
        self.count = count
        self.cell = s(cell)
        self.gap = s(gap)
        self.show_index = show_index
        height = self.cell + (s(20) if show_index else 0)
        super().__init__(master, bg=bg, width=1, height=height, highlightthickness=0, bd=0)
        self._bits = ["0"] * count
        self._group = group
        self._colors = {}
        self.bind("<Configure>", lambda _e: self.redraw())

    def set_bits(self, bits, group: int | None = None, colors: dict | None = None):
        """colors: {index: (bg, fg)}"""
        self._bits = list(bits)[: self.count]
        self._group = group if group is not None else self._group
        self._colors = colors or {}
        self.redraw()

    def redraw(self):
        self.delete("all")
        width = self.winfo_width()
        total = self.count * self.cell + (self.count - 1) * self.gap
        start = max(s(8), (width - total) / 2)
        for i, bit in enumerate(self._bits):
            x = start + i * (self.cell + self.gap)
            if self._group and i and i % self._group == 0:
                x += s(8)
            bg, fg = self._colors.get(i, (theme.SURFACE_ALT, theme.ACCENT))
            self.create_rectangle(x, 2, x + self.cell, 2 + self.cell, fill=bg,
                                  outline=theme.BORDER, width=1)
            self.create_text(x + self.cell / 2, 2 + self.cell / 2, text=bit,
                             fill=fg, font=(theme.MONO[0], 14, "bold"))
            if self.show_index:
                self.create_text(x + self.cell / 2, self.cell + s(10),
                                 text=str(self.count - 1 - i),
                                 fill=theme.FAINT, font=theme.MONO_SMALL)


def hline(master, color=theme.BORDER):
    tk.Frame(master, bg=color, height=1).pack(fill="x", pady=s(8))


def hint(master, text: str, bg=theme.SURFACE, wrap: int = 560):
    return tk.Label(master, text=text, font=theme.SMALL, bg=bg, fg=theme.FAINT,
                    anchor="w", justify="left", wraplength=s(wrap))


def scroll_text(master, height=8, **kw):
    """只读等宽文本区域（用于日志 / 伪代码）。"""
    frame = tk.Frame(master, bg=theme.BORDER)
    text = tk.Text(frame, height=height, bg=theme.SURFACE_ALT, fg=theme.TEXT,
                   insertbackground=theme.TEXT, font=theme.MONO_SMALL,
                   bd=0, relief="flat", padx=s(8), pady=s(6), wrap="none", **kw)
    bar = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
    text.configure(yscrollcommand=bar.set)
    text.pack(side="left", fill="both", expand=True)
    bar.pack(side="right", fill="y")
    return frame, text
