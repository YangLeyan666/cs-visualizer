"""全局视觉主题：配色、字体与 ttk 样式。

所有界面模块只从本文件取颜色和字体，保证各模块视觉一致。
"""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# ---- 配色 ----------------------------------------------------------------
BG = "#0b1220"
SIDEBAR = "#0f1a2e"
SURFACE = "#142238"
SURFACE_ALT = "#1b2d49"
SURFACE_HOVER = "#22375a"
BORDER = "#283d5c"
TEXT = "#e8eefb"
MUTED = "#93a6c4"
FAINT = "#5f7391"
ACCENT = "#4cc2ff"
ACCENT_DARK = "#1b6f96"
OK = "#3ddc97"
WARN = "#ffc857"
DANGER = "#ff6b6b"
PURPLE = "#b388ff"
ORANGE = "#ff9f68"

# ---- 字体（由 init_fonts 在 Tk 启动后填充）---------------------------------
TITLE = ("Microsoft YaHei UI", 17, "bold")
SUBTITLE = ("Microsoft YaHei UI", 9)
H2 = ("Microsoft YaHei UI", 10, "bold")
BODY = ("Microsoft YaHei UI", 9)
BODY_BOLD = ("Microsoft YaHei UI", 9, "bold")
SMALL = ("Microsoft YaHei UI", 8)
MONO = ("Cascadia Mono", 9)
MONO_BOLD = ("Cascadia Mono", 9, "bold")
MONO_SMALL = ("Cascadia Mono", 8)


SCALE = 1.0


def init_scale(root: tk.Misc) -> None:
    """根据系统 DPI 计算像素缩放因子（192 DPI -> 2.0）。"""
    global SCALE
    SCALE = max(1.0, round(root.winfo_fpixels("1i") / 96.0, 2))


def s(value: float) -> int:
    """把设计稿像素值换算为当前 DPI 下的实际像素。"""
    return int(round(value * SCALE))


def init_fonts(root: tk.Misc) -> None:
    """根据系统可用字体修正字体族，避免中文显示为方块。"""
    global TITLE, SUBTITLE, H2, BODY, BODY_BOLD, SMALL
    global MONO, MONO_BOLD, MONO_SMALL

    families = set(tkfont.families(root))
    ui_family = next(
        (f for f in ("Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC")
         if f in families),
        "TkDefaultFont",
    )
    mono_family = next(
        (f for f in ("Cascadia Mono", "Consolas", "JetBrains Mono", "Courier New")
         if f in families),
        "TkFixedFont",
    )

    TITLE = (ui_family, 17, "bold")
    SUBTITLE = (ui_family, 9)
    H2 = (ui_family, 10, "bold")
    BODY = (ui_family, 9)
    BODY_BOLD = (ui_family, 9, "bold")
    SMALL = (ui_family, 8)
    MONO = (mono_family, 9)
    MONO_BOLD = (mono_family, 9, "bold")
    MONO_SMALL = (mono_family, 8)


def apply_ttk_style(root: tk.Misc) -> None:
    """统一 ttk 控件（Scale / Scrollbar / Spinbox）的暗色外观。"""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(
        "Horizontal.TScale",
        background=SURFACE,
        troughcolor=SURFACE_ALT,
        bordercolor=BORDER,
        lightcolor=ACCENT,
        darkcolor=ACCENT,
        sliderrelief="flat",
    )
    style.configure(
        "Vertical.TScrollbar",
        background=SURFACE_ALT,
        troughcolor=BG,
        bordercolor=BG,
        arrowcolor=MUTED,
    )
    style.configure(
        "TSpinbox",
        fieldbackground=SURFACE_ALT,
        background=SURFACE_ALT,
        foreground=TEXT,
        arrowcolor=MUTED,
        bordercolor=BORDER,
        insertcolor=TEXT,
    )
