"""模块四：排序算法可视化。"""

import math
import random
import tkinter as tk
from tkinter import ttk

from core import sorting
from . import theme
from .base_view import ModuleView
from .theme import s
from .widgets import ActionButton, Card, Segmented, StatChip, hint, scroll_text


ALGORITHM_OPTIONS = [
    ("bubble", "冒泡"),
    ("selection", "选择"),
    ("insertion", "插入"),
    ("quick", "快速"),
]

ALGORITHM_TITLES = {
    "bubble": "冒泡排序",
    "selection": "选择排序",
    "insertion": "插入排序",
    "quick": "快速排序",
}

ALGORITHM_HINTS = {
    "bubble": "冒泡排序：反复比较相邻元素，较大者逐步移向末尾；某一轮没有交换即可提前结束。",
    "selection": "选择排序：每轮从未排序区间挑出最小值，与区间首元素交换。",
    "insertion": "插入排序：维护有序前缀，把新元素逐次向前交换到正确位置。",
    "quick": "快速排序：取区间末尾元素为基准，把较小值移到左侧，基准归位后递归处理两侧。",
}

GENERATORS = {
    "bubble": sorting.bubble_steps,
    "selection": sorting.selection_steps,
    "insertion": sorting.insertion_steps,
    "quick": sorting.quick_steps,
}

BAR_COLOR = "#2b6f8f"
MIN_SIZE = 8
MAX_SIZE = 44
DEFAULT_SIZE = 18
DEFAULT_DELAY = 0.12


class SortingView(ModuleView):
    title = "排序算法可视化"
    subtitle = "比较 · 交换 · 动画回放"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.algorithm = "bubble"
        self.size = DEFAULT_SIZE
        self.delay = DEFAULT_DELAY
        self.data = []
        self.steps = []
        self.index = 0
        self.playing = False
        self._after_id = None
        self._destroyed = False

        self._build_controls()
        self._build_body()
        self.bind("<Destroy>", self._on_destroy, add="+")
        self._new_data()

    # ---- 顶部控制区 -------------------------------------------------------
    def _build_controls(self):
        card = Card(self, title="① 算法与数据")
        card.pack(fill="x", pady=(0, s(10)))

        row1 = tk.Frame(card.body, bg=theme.SURFACE)
        row1.pack(fill="x")
        tk.Label(row1, text="算法", font=theme.BODY, bg=theme.SURFACE,
                 fg=theme.MUTED).pack(side="left", padx=(0, s(8)))

        self.algo_seg = Segmented(row1, ALGORITHM_OPTIONS, value=self.algorithm,
                                  command=self._on_algorithm_change)
        self.algo_seg.pack(side="left")

        ActionButton(row1, "随机数据", command=self._randomize, kind="ghost").pack(
            side="left", padx=(s(16), 0))

        tk.Label(row1, text="数据规模", font=theme.BODY, bg=theme.SURFACE,
                 fg=theme.MUTED).pack(side="left", padx=(s(20), s(8)))
        spin_wrap = tk.Frame(row1, bg=theme.BORDER)
        spin_wrap.pack(side="left")
        self.size_var = tk.StringVar(value=str(self.size))
        self.size_spin = tk.Spinbox(
            spin_wrap, from_=MIN_SIZE, to=MAX_SIZE, textvariable=self.size_var,
            width=4, font=theme.MONO, bg=theme.SURFACE_ALT, fg=theme.TEXT,
            buttonbackground=theme.SURFACE_ALT, insertbackground=theme.ACCENT,
            relief="flat", bd=0, highlightthickness=0, justify="center",
            command=self._on_size_change,
        )
        self.size_spin.pack(padx=s(1), pady=s(1), ipady=s(2))
        self.size_spin.bind("<Return>", self._on_size_change)
        self.size_spin.bind("<FocusOut>", self._on_size_change)

        row2 = tk.Frame(card.body, bg=theme.SURFACE)
        row2.pack(fill="x", pady=(s(8), 0))
        self.play_btn = ActionButton(row2, "播放", command=self._toggle_play)
        self.play_btn.pack(side="left")
        ActionButton(row2, "单步", command=self._step, kind="ghost").pack(
            side="left", padx=(s(8), 0))
        ActionButton(row2, "重置", command=self._reset, kind="ghost").pack(
            side="left", padx=(s(8), 0))

        tk.Label(row2, text="速度", font=theme.BODY, bg=theme.SURFACE,
                 fg=theme.MUTED).pack(side="left", padx=(s(22), s(6)))
        self.speed_scale = ttk.Scale(row2, from_=0.03, to=0.5, value=self.delay,
                                     orient="horizontal", length=s(150),
                                     command=self._on_speed_change)
        self.speed_scale.pack(side="left", pady=(s(2), 0))
        self.speed_label = tk.Label(row2, text=f"{self.delay:.2f} 秒/步",
                                    font=theme.SMALL, bg=theme.SURFACE,
                                    fg=theme.MUTED, width=10, anchor="w")
        self.speed_label.pack(side="left", padx=(s(8), 0))

        self.algo_hint = hint(card.body, ALGORITHM_HINTS[self.algorithm], wrap=880)
        self.algo_hint.pack(fill="x", pady=(s(6), 0))

    # ---- 主体：动画 + 统计 / 伪代码 ---------------------------------------
    def _build_body(self):
        body = tk.Frame(self, bg=theme.BG)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=0, minsize=s(330))
        body.grid_rowconfigure(0, weight=1)

        left = Card(body, title="② 动画区", subtitle="柱高 = 数值大小")
        left.grid(row=0, column=0, sticky="nsew")

        self.message_label = tk.Label(
            left.body, text="", font=theme.TITLE, bg=theme.SURFACE, fg=theme.TEXT,
            anchor="w", justify="left", wraplength=s(500),
        )
        self.message_label.pack(fill="x")

        legend = tk.Frame(left.body, bg=theme.SURFACE)
        legend.pack(fill="x", pady=(s(2), s(8)))
        for name, color in (("普通", BAR_COLOR), ("比较", theme.WARN),
                            ("交换", theme.DANGER), ("已就位", theme.OK),
                            ("基准", theme.PURPLE)):
            tk.Label(legend, text=f"■ {name}", font=theme.SMALL, bg=theme.SURFACE,
                     fg=color).pack(side="left", padx=(0, s(12)))

        self.canvas = tk.Canvas(
            left.body, width=1, height=1, bg=theme.BG,
            highlightthickness=s(1), highlightbackground=theme.BORDER, bd=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        right = tk.Frame(body, bg=theme.BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(s(10), 0))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        stats = Card(right, title="③ 运行统计")
        stats.grid(row=0, column=0, sticky="ew", pady=(0, s(10)))
        chips = tk.Frame(stats.body, bg=theme.SURFACE)
        chips.pack(fill="x")
        self.compare_chip = StatChip(chips, "比较次数", "0", theme.WARN)
        self.compare_chip.pack(side="left", padx=(0, s(6)))
        self.swap_chip = StatChip(chips, "交换次数", "0", theme.DANGER)
        self.swap_chip.pack(side="left", padx=(0, s(6)))
        self.step_chip = StatChip(chips, "当前步 / 总步数", "0 / 0", theme.ACCENT)
        self.step_chip.pack(side="left")

        code_card = Card(right, title="④ 伪代码", subtitle="高亮当前执行行")
        code_card.grid(row=1, column=0, sticky="nsew")
        code_frame, self.code_text = scroll_text(code_card.body, height=14, width=34)
        code_frame.pack(fill="both", expand=True)
        self.code_text.tag_configure("ln", foreground=theme.FAINT)
        self.code_text.tag_configure("current", background=theme.SURFACE_HOVER,
                                     foreground=theme.ACCENT)

    # ---- 数据与状态 -------------------------------------------------------
    def _new_data(self):
        self.data = [random.randint(5, 99) for _ in range(self.size)]
        self._rebuild()

    def _rebuild(self):
        self._pause()
        self.steps = list(GENERATORS[self.algorithm](self.data))
        self.index = 0
        self._load_pseudocode()
        self._render()

    def _load_pseudocode(self):
        self.code_text.configure(state="normal")
        self.code_text.delete("1.0", "end")
        for number, line in enumerate(sorting.PSEUDOCODE[self.algorithm], start=1):
            self.code_text.insert("end", f"{number:>2}  ", "ln")
            self.code_text.insert("end", f"{line}\n")
        self.code_text.configure(state="disabled")

    def _highlight_line(self, line):
        lines = len(sorting.PSEUDOCODE[self.algorithm])
        line = max(1, min(lines, line))
        self.code_text.configure(state="normal")
        self.code_text.tag_remove("current", "1.0", "end")
        self.code_text.tag_add("current", f"{line}.0", f"{line}.end")
        self.code_text.see(f"{line}.0")
        self.code_text.configure(state="disabled")

    def _render(self):
        if not self.steps:
            return
        frame = self.steps[self.index]
        self.message_label.configure(text=frame["message"])
        self.compare_chip.set(frame["comparisons"])
        self.swap_chip.set(frame["swaps"])
        self.step_chip.set(f"{self.index + 1} / {len(self.steps)}")
        self._highlight_line(frame["line"])
        self._draw()
        self._update_status()

    def _update_status(self):
        if not self.steps:
            return
        frame = self.steps[self.index]
        self.app.set_status(
            f"排序可视化：{ALGORITHM_TITLES[self.algorithm]} · "
            f"{self.index + 1}/{len(self.steps)} 步 · "
            f"比较 {frame['comparisons']} · 交换 {frame['swaps']}"
        )

    # ---- 播放控制 ---------------------------------------------------------
    def _on_algorithm_change(self, key):
        if key == self.algorithm:
            return
        self.algorithm = key
        self.algo_seg.set(key)
        self.algo_hint.configure(text=ALGORITHM_HINTS[key])
        self._rebuild()

    def _on_size_change(self, _event=None):
        try:
            value = int(self.size_var.get())
        except ValueError:
            value = self.size
        value = max(MIN_SIZE, min(MAX_SIZE, value))
        self.size_var.set(str(value))
        if value == self.size:
            return
        self.size = value
        self._new_data()

    def _on_speed_change(self, value):
        try:
            self.delay = max(0.03, min(0.5, float(value)))
        except (TypeError, ValueError):
            return
        if hasattr(self, "speed_label"):
            self.speed_label.configure(text=f"{self.delay:.2f} 秒/步")

    def _randomize(self):
        self._new_data()

    def _reset(self):
        self._pause()
        self.index = 0
        self._render()

    def _step(self):
        if self.playing:
            self._pause()
        if not self.steps:
            return
        if self.index < len(self.steps) - 1:
            self.index += 1
            self._render()

    def _toggle_play(self):
        if self.playing:
            self._pause()
            return
        if not self.steps:
            return
        if self.index >= len(self.steps) - 1:
            self.index = 0
            self._render()
        self.playing = True
        self.play_btn.configure(text="暂停")
        self._schedule_tick()

    def _schedule_tick(self):
        self._cancel_tick()
        self._after_id = self.after(int(self.delay * 1000), self._tick)

    def _tick(self):
        self._after_id = None
        if not self.playing or self._destroyed:
            return
        if self.index >= len(self.steps) - 1:
            self._pause()
            return
        self.index += 1
        self._render()
        if self.index >= len(self.steps) - 1:
            self._pause()
        else:
            self._schedule_tick()

    def _pause(self):
        self.playing = False
        self._cancel_tick()
        if hasattr(self, "play_btn"):
            self.play_btn.configure(text="播放")

    def _cancel_tick(self):
        if self._after_id is None:
            return
        try:
            self.after_cancel(self._after_id)
        except tk.TclError:
            pass
        self._after_id = None

    def _on_destroy(self, event):
        if event.widget is not self:
            return
        self._destroyed = True
        self.playing = False
        self._cancel_tick()

    # ---- 绘制 -------------------------------------------------------------
    def _on_canvas_resize(self, _event):
        self._draw()

    def _draw(self):
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        self.canvas.delete("all")
        if not self.steps or width < s(40) or height < s(80):
            return

        frame = self.steps[self.index]
        values = frame["array"]
        if not values:
            return

        left = s(16)
        right = width - s(16)
        top = s(34)
        base = height - s(26)
        if right <= left or base <= top:
            return

        plot_h = base - top
        max_value = max(values) or 1
        slot = (right - left) / len(values)
        gap = min(s(4), slot * 0.22)
        bar_w = max(s(2), slot - gap)

        compare = frame["compare"] or []
        swap = frame["swap"] or []
        pivot = frame["pivot"]
        placed = frame["sorted"]

        for fraction in (0.25, 0.5, 0.75):
            y = base - plot_h * fraction
            self.canvas.create_line(left, y, right, y, fill=theme.BORDER,
                                    dash=(s(2), s(4)))
        self.canvas.create_line(left, base, right, base, fill=theme.BORDER)

        show_values = bar_w >= s(18)
        index_step = max(1, math.ceil(s(13) / slot))
        for i, value in enumerate(values):
            bar_h = max(s(2), plot_h * value / max_value)
            x0 = left + i * slot + (slot - bar_w) / 2
            x1 = x0 + bar_w
            y0 = base - bar_h

            if i in swap:
                color = theme.DANGER
            elif pivot == i:
                color = theme.PURPLE
            elif i in compare:
                color = theme.WARN
            elif i in placed:
                color = theme.OK
            else:
                color = BAR_COLOR
            self.canvas.create_rectangle(x0, y0, x1, base, fill=color, outline="")

            cx = (x0 + x1) / 2
            if show_values and bar_h >= s(24):
                self.canvas.create_text(cx, y0 - s(6), text=str(value),
                                        fill=theme.TEXT, font=theme.MONO, anchor="s")
            if i % index_step == 0:
                self.canvas.create_text(cx, height - s(13), text=str(i),
                                        fill=color if color != BAR_COLOR else theme.FAINT,
                                        font=theme.MONO_SMALL, anchor="center")

    # ---- 模块入口 ---------------------------------------------------------
    def on_show(self):
        self._update_status()
