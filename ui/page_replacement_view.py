"""模块六：页面置换模拟界面。"""

import tkinter as tk
from tkinter import ttk

from core import page_replacement as pr
from . import theme
from .base_view import ModuleView
from .theme import s
from .widgets import ActionButton, Card, Segmented, StatChip


ALGO_INFO = {
    "fifo": (
        "FIFO",
        "按页面装入物理块的先后顺序淘汰：最早进入的页最先离开。实现简单，但可能出现 Belady 异常。",
    ),
    "lru": (
        "LRU",
        "淘汰最长时间没有被访问的页：每次命中都会刷新该页的最近使用时间，不需要预知未来。",
    ),
    "opt": (
        "OPT",
        "淘汰未来最长时间不再访问的页：需要预知完整访问序列，缺页次数最少，可作为理论下界。",
    ),
}
ALGO_OPTIONS = [("fifo", "FIFO"), ("lru", "LRU"), ("opt", "OPT")]


class PageReplacementView(ModuleView):
    title = "页面置换模拟"
    subtitle = "FIFO / LRU / OPT —— 逐列观察物理块的装入与淘汰"

    def __init__(self, master, app):
        super().__init__(master, app)
        self._result = None
        self._refs = []
        self._frame_count = 3
        self._algo = "fifo"
        self._current = 0
        self._play_job = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_params()
        self._build_bottom()
        self._build_matrix()
        self.simulate()

    # ---- 参数区 -----------------------------------------------------------
    def _build_params(self):
        card = Card(self, title="① 参数")
        card.grid(row=0, column=0, sticky="ew", pady=(0, s(10)))

        row = tk.Frame(card.body, bg=theme.SURFACE)
        row.pack(fill="x")

        tk.Label(row, text="参考串", font=theme.BODY, bg=theme.SURFACE,
                 fg=theme.MUTED).pack(side="left", padx=(0, s(8)))

        entry_wrap = tk.Frame(row, bg=theme.BORDER)
        entry_wrap.pack(side="left", fill="x", expand=True)
        self.ref_entry = tk.Entry(
            entry_wrap, width=30, font=theme.MONO, bd=0, relief="flat",
            bg=theme.SURFACE_ALT, fg=theme.TEXT, insertbackground=theme.ACCENT,
            highlightthickness=0,
        )
        self.ref_entry.pack(fill="x", padx=s(1), pady=s(1), ipady=s(3))
        self.ref_entry.insert(0, pr.DEFAULT_REFERENCE)

        tk.Label(row, text="物理块数", font=theme.BODY, bg=theme.SURFACE,
                 fg=theme.MUTED).pack(side="left", padx=(s(14), s(6)))
        self.frame_var = tk.StringVar(value="3")
        self.frame_spin = ttk.Spinbox(
            row, from_=1, to=6, width=4, justify="center",
            textvariable=self.frame_var, command=self.simulate,
            font=theme.MONO_BOLD,
        )
        self.frame_spin.pack(side="left")

        tk.Label(row, text="算法", font=theme.BODY, bg=theme.SURFACE,
                 fg=theme.MUTED).pack(side="left", padx=(s(14), s(6)))
        self.algo_seg = Segmented(row, ALGO_OPTIONS, value="fifo",
                                  command=self._set_algo)
        self.algo_seg.pack(side="left")

        ActionButton(row, "重新模拟", command=self.simulate).pack(
            side="left", padx=(s(14), 0))

        self.note = tk.Label(
            card.body, text="", font=theme.SMALL, bg=theme.SURFACE,
            fg=theme.FAINT, anchor="w", justify="left", wraplength=s(820),
        )
        self.note.pack(fill="x", pady=(s(6), 0))

        self.ref_entry.bind("<Return>", lambda _e: self.simulate())
        self.frame_spin.bind("<Return>", lambda _e: self.simulate())

    # ---- 矩阵与播放控制 ---------------------------------------------------
    def _build_matrix(self):
        card = Card(self, title="② 访问序列与物理块状态")
        card.grid(row=1, column=0, sticky="nsew")

        self.canvas = tk.Canvas(card.body, width=1, height=s(120),
                                bg=theme.SURFACE, bd=0, highlightthickness=0)
        self.canvas.bind("<Configure>", lambda _e: self.redraw())

        controls = tk.Frame(card.body, bg=theme.SURFACE)
        controls.pack(side="bottom", fill="x", pady=(s(8), 0))

        self.prev_btn = ActionButton(controls, "上一步", command=self._prev,
                                     kind="ghost")
        self.prev_btn.pack(side="left", padx=(0, s(6)))
        self.next_btn = ActionButton(controls, "下一步", command=self._next)
        self.next_btn.pack(side="left", padx=(0, s(6)))
        self.play_btn = ActionButton(controls, "自动播放", command=self._toggle_play,
                                     kind="ok", width=8)
        self.play_btn.pack(side="left", padx=(0, s(6)))
        self.reset_btn = ActionButton(controls, "重置", command=self._reset,
                                      kind="ghost")
        self.reset_btn.pack(side="left")

        self.step_label = tk.Label(controls, text="", font=theme.BODY,
                                   bg=theme.SURFACE, fg=theme.MUTED, anchor="w")
        self.step_label.pack(side="left", fill="x", expand=True, padx=(s(10), s(8)))
        self.counter_label = tk.Label(controls, text="", font=theme.MONO_BOLD,
                                      bg=theme.SURFACE, fg=theme.FAINT)
        self.counter_label.pack(side="right")

        self.canvas.pack(fill="both", expand=True)

    # ---- 底部统计 / 说明 / 图例 ------------------------------------------
    def _build_bottom(self):
        bottom = tk.Frame(self, bg=theme.BG)
        bottom.grid(row=2, column=0, sticky="ew", pady=(s(10), 0))
        bottom.grid_columnconfigure(0, minsize=s(340))
        bottom.grid_columnconfigure(1, weight=1, minsize=s(260))
        bottom.grid_columnconfigure(2, minsize=s(160))

        stats_card = Card(bottom, title="③ 统计", pad=10)
        stats_card.grid(row=0, column=0, sticky="nsew", padx=(0, s(8)))
        chip_row = tk.Frame(stats_card.body, bg=theme.SURFACE)
        chip_row.pack(fill="x")
        self.fault_chip = StatChip(chip_row, "缺页次数", "—", theme.DANGER)
        self.hit_chip = StatChip(chip_row, "命中次数", "—", theme.OK)
        self.fault_rate_chip = StatChip(chip_row, "缺页率", "—", theme.WARN)
        self.hit_rate_chip = StatChip(chip_row, "命中率", "—", theme.ACCENT)
        for column, chip in enumerate(
                (self.fault_chip, self.hit_chip, self.fault_rate_chip,
                 self.hit_rate_chip)):
            chip.grid(row=0, column=column, sticky="ew",
                      padx=(0 if column == 0 else s(6), 0))
            chip_row.grid_columnconfigure(column, weight=1)

        algo_card = Card(bottom, title="④ 算法说明", pad=10)
        algo_card.grid(row=0, column=1, sticky="nsew", padx=(0, s(8)))
        self.algo_name = tk.Label(algo_card.body, text="", font=theme.BODY_BOLD,
                                  bg=theme.SURFACE, fg=theme.ACCENT, anchor="w")
        self.algo_name.pack(fill="x")
        self.algo_desc = tk.Label(
            algo_card.body, text="", font=theme.SMALL, bg=theme.SURFACE,
            fg=theme.MUTED, anchor="w", justify="left", wraplength=s(320),
        )
        self.algo_desc.pack(fill="x", pady=(s(3), 0))

        legend_card = Card(bottom, title="⑤ 图例", pad=10)
        legend_card.grid(row=0, column=2, sticky="nsew")
        for color, text in ((theme.OK, "命中"), (theme.DANGER, "缺页"),
                            (theme.ORANGE, "淘汰")):
            line = tk.Frame(legend_card.body, bg=theme.SURFACE)
            line.pack(fill="x", pady=s(1))
            swatch = tk.Frame(line, bg=color, width=s(10), height=s(10))
            swatch.pack(side="left")
            tk.Label(line, text=text, font=theme.SMALL, bg=theme.SURFACE,
                     fg=theme.MUTED).pack(side="left", padx=(s(6), 0))

    # ---- 模拟与状态 -------------------------------------------------------
    def _set_note(self, text: str, error: bool = False):
        self.note.configure(text=text, fg=theme.DANGER if error else theme.FAINT)

    def _read_frame_count(self):
        raw = self.frame_var.get().strip()
        try:
            value = int(raw)
        except ValueError:
            self._set_note("输入有误：物理块数必须是 1~6 的整数。", error=True)
            return None
        if not 1 <= value <= 6:
            self._set_note("输入有误：物理块数需要在 1~6 之间。", error=True)
            return None
        return value

    def simulate(self):
        """读取参数并重新计算完整结果，成功后回到第一步。"""
        self._stop_play()
        frame_count = self._read_frame_count()
        if frame_count is None:
            return
        try:
            refs = pr.parse_reference(self.ref_entry.get())
            result = pr.simulate(refs, frame_count, self.algo_seg.get())
        except ValueError as exc:
            self._set_note(f"输入有误：{exc}", error=True)
            return

        self._refs = refs
        self._frame_count = frame_count
        self._algo = self.algo_seg.get()
        self._result = result
        self._current = 0
        self._set_note("序列用逗号或空格分隔；回车可重新模拟。")
        self._update_algo_text()
        self._refresh()

        name = ALGO_INFO[self._algo][0]
        self.app.set_status(
            f"页面置换模拟：{name} · {len(refs)} 次访问 · "
            f"缺页 {result['faults']} 次 · 缺页率 {result['fault_rate']:.1%}"
        )

    def _set_algo(self, algo: str):
        if algo not in ALGO_INFO:
            return
        self.algo_seg.set(algo)
        self.simulate()

    def _update_algo_text(self):
        name, description = ALGO_INFO[self._algo]
        self.algo_name.configure(text=name)
        self.algo_desc.configure(text=description)

    def _update_stats(self):
        if self._result is None:
            return
        result = self._result
        self.fault_chip.set(result["faults"], theme.DANGER)
        self.hit_chip.set(result["hits"], theme.OK)
        self.fault_rate_chip.set(f"{result['fault_rate']:.1%}", theme.WARN)
        self.hit_rate_chip.set(f"{result['hit_rate']:.1%}", theme.ACCENT)

    def _update_step_text(self):
        if self._result is None:
            self.step_label.configure(text="")
            self.counter_label.configure(text="")
            return
        steps = self._result["steps"]
        step = steps[self._current]
        if step["fault"]:
            if step["victim"] is not None:
                action = f"缺页，淘汰页 {step['victim']}"
            else:
                action = "缺页，装入空闲块"
        else:
            action = "命中"
        self.step_label.configure(
            text=f"第 {step['index'] + 1} 次访问页 {step['page']}：{action}")
        self.counter_label.configure(text=f"{self._current + 1} / {len(steps)}")

    def _update_controls(self):
        total = len(self._result["steps"]) if self._result else 0
        self.prev_btn.configure(state="normal" if self._current > 0 else "disabled")
        self.next_btn.configure(
            state="normal" if 0 <= self._current < total - 1 else "disabled")
        self.play_btn.configure(text="暂停" if self._play_job else "自动播放")

    def _refresh(self):
        self._update_stats()
        self._update_step_text()
        self._update_controls()
        self.redraw()

    # ---- 播放控制 ---------------------------------------------------------
    def _next(self):
        if self._result is None:
            return
        self._stop_play()
        if self._current < len(self._result["steps"]) - 1:
            self._current += 1
        self._refresh()

    def _prev(self):
        if self._result is None:
            return
        self._stop_play()
        if self._current > 0:
            self._current -= 1
        self._refresh()

    def _reset(self):
        if self._result is None:
            return
        self._stop_play()
        self._current = 0
        self._refresh()

    def _toggle_play(self):
        if self._play_job is not None:
            self._stop_play()
            self._update_controls()
            return
        if self._result is None:
            return
        if self._current >= len(self._result["steps"]) - 1:
            self._current = 0
        self._play_job = self.after(650, self._advance_play)
        self._refresh()

    def _advance_play(self):
        self._play_job = None
        if self._result is None:
            self._update_controls()
            return
        last = len(self._result["steps"]) - 1
        if self._current < last:
            self._current += 1
            if self._current < last:
                self._play_job = self.after(650, self._advance_play)
        self._refresh()

    def _stop_play(self):
        if self._play_job is not None:
            try:
                self.after_cancel(self._play_job)
            except tk.TclError:
                pass
            self._play_job = None

    # ---- 绘制矩阵 ---------------------------------------------------------
    def redraw(self):
        canvas = self.canvas
        canvas.delete("all")
        if self._result is None or self._frame_count < 1:
            return

        steps = self._result["steps"]
        total = len(steps)
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if total == 0 or width <= 1 or height <= 1:
            return

        left = s(54)
        right = s(3)
        top = s(2)
        header = s(44)
        bottom = s(4)
        usable_w = width - left - right
        usable_h = height - top - header - bottom
        if usable_w <= s(20) or usable_h <= s(10):
            return

        col_w = usable_w / total
        row_h = min(usable_h / self._frame_count, s(56))
        grid_top = top + header + max(0, (usable_h - row_h * self._frame_count) / 2)
        grid_bottom = grid_top + row_h * self._frame_count

        # 左上方行标题
        canvas.create_text(s(5), top + s(10), text="块 ＼ 访问", anchor="w",
                           fill=theme.FAINT, font=theme.SMALL)

        # 当前列底色，画在单元格下方
        if 0 <= self._current < total:
            x0 = left + self._current * col_w
            canvas.create_rectangle(x0, grid_top, x0 + col_w, grid_bottom,
                                    fill=theme.SURFACE_HOVER, outline="")

        dot_radius = max(s(2), min(s(4), col_w * 0.12))
        for column, step in enumerate(steps):
            center_x = left + (column + 0.5) * col_w
            color = theme.OK if not step["fault"] else theme.DANGER
            dot_y = top + s(8)

            if column == self._current:
                canvas.create_rectangle(
                    left + column * col_w + s(1), top,
                    left + (column + 1) * col_w - s(1), top + s(2),
                    fill=theme.ACCENT, outline="",
                )

            canvas.create_oval(
                center_x - dot_radius, dot_y - dot_radius,
                center_x + dot_radius, dot_y + dot_radius,
                fill=color, outline="",
            )
            if column == self._current:
                ring = dot_radius + s(3)
                canvas.create_oval(
                    center_x - ring, dot_y - ring, center_x + ring, dot_y + ring,
                    outline=theme.ACCENT, width=s(1),
                )

            if col_w >= s(10):
                canvas.create_text(center_x, top + s(24), text=str(step["page"]),
                                   fill=color, font=theme.MONO_SMALL)
            if col_w >= s(14):
                canvas.create_text(center_x, top + s(37), text=str(column + 1),
                                   fill=theme.ACCENT if column == self._current
                                   else theme.FAINT, font=theme.MONO_SMALL)

        cell_gap_x = min(s(2), col_w * 0.08)
        cell_gap_y = min(s(2), row_h * 0.08)

        for row in range(self._frame_count):
            row_top = grid_top + row * row_h
            row_bottom = row_top + row_h
            if row_h >= s(14):
                canvas.create_text(s(5), (row_top + row_bottom) / 2,
                                   text=f"块 {row + 1}", anchor="w",
                                   fill=theme.MUTED, font=theme.SMALL)

            for column, step in enumerate(steps):
                cell_x0 = left + column * col_w + cell_gap_x
                cell_x1 = left + (column + 1) * col_w - cell_gap_x
                cell_y0 = row_top + cell_gap_y
                cell_y1 = row_bottom - cell_gap_y
                page = step["frames"][row]
                fault = step["fault"]
                replaced = self._is_replaced(column, row)

                dash = ()
                if page is None:
                    fill = theme.SURFACE
                    outline = theme.BORDER
                    line_width = s(1)
                    dash = (s(2), s(2))
                else:
                    fill = theme.SURFACE_HOVER if column == self._current \
                        else theme.SURFACE_ALT
                    outline = theme.BORDER
                    line_width = s(1)
                    if not fault:
                        outline = theme.OK
                        line_width = s(2)
                    if replaced:
                        outline = theme.ORANGE
                        line_width = s(2)
                    elif column == self._current and fault:
                        outline = theme.ACCENT

                canvas.create_rectangle(
                    cell_x0, cell_y0, cell_x1, cell_y1,
                    fill=fill, outline=outline, width=line_width, dash=dash,
                )

                if page is None:
                    if row_h >= s(20) and col_w >= s(20):
                        canvas.create_text(
                            (cell_x0 + cell_x1) / 2, (cell_y0 + cell_y1) / 2,
                            text="空", fill=theme.FAINT, font=theme.SMALL,
                        )
                    continue

                if col_w < s(10) or row_h < s(14):
                    continue

                text_y = (cell_y0 + cell_y1) / 2
                if replaced:
                    text_y = cell_y0 + (cell_y1 - cell_y0) * 0.36
                canvas.create_text((cell_x0 + cell_x1) / 2, text_y,
                                   text=str(page), fill=theme.TEXT,
                                   font=theme.MONO_BOLD)

                if replaced and row_h >= s(28) and col_w >= s(16):
                    victim = step["victim"]
                    if col_w >= s(32):
                        label = f"淘汰{victim}"
                    else:
                        label = f"×{victim}"
                    canvas.create_text(
                        (cell_x0 + cell_x1) / 2,
                        cell_y0 + (cell_y1 - cell_y0) * 0.74,
                        text=label, fill=theme.ORANGE, font=theme.MONO_SMALL,
                    )

    def _is_replaced(self, step_index: int, row: int) -> bool:
        """当前步该物理块是否发生了淘汰置换。"""
        if self._result is None:
            return False
        step = self._result["steps"][step_index]
        if not step["fault"] or step["victim"] is None or step_index == 0:
            return False
        previous = self._result["steps"][step_index - 1]["frames"]
        return previous[row] == step["victim"] and step["frames"][row] == step["page"]

    # ---- 生命周期 ---------------------------------------------------------
    def on_show(self):
        if self._result is not None:
            name = ALGO_INFO[self._algo][0]
            self.app.set_status(
                f"页面置换模拟：{name} · {len(self._refs)} 次访问 · "
                f"缺页 {self._result['faults']} 次 · "
                f"缺页率 {self._result['fault_rate']:.1%}"
            )
        self.after_idle(self.redraw)

    def destroy(self):
        self._stop_play()
        super().destroy()
