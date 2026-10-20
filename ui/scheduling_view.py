"""模块五：进程调度模拟 —— FCFS / SJF / 时间片轮转。"""

import math
import tkinter as tk
from tkinter import ttk

from core import scheduling
from . import theme
from .base_view import ModuleView
from .theme import s
from .widgets import ActionButton, Card, DataTable, Segmented, StatChip

ALGOS = [("fcfs", "FCFS"), ("sjf", "SJF"), ("rr", "RR")]

ALGO_HINTS = {
    "fcfs": "按到达顺序执行，非抢占。",
    "sjf": "已到达进程中选运行最短者，非抢占。",
    "rr": "按时间片轮流执行，用完排到队尾。",
}

PROCESS_COLORS = (
    theme.ACCENT,
    theme.OK,
    theme.WARN,
    theme.PURPLE,
    theme.ORANGE,
    "#5ad1c8",
    "#f78fb3",
    "#9ccc65",
    "#7aa2f7",
    "#d7aefb",
)


class SchedulingView(ModuleView):
    title = "进程调度模拟"
    subtitle = "FCFS / SJF / 时间片轮转"

    def __init__(self, master, app):
        super().__init__(master, app)
        self._algo = "fcfs"
        self._rows = []
        self._result = None
        self._colors = {}

        self._build_process_card()
        self._build_param_card()
        self._build_bottom()
        self._build_gantt()
        self._load_defaults()
        self._refresh_algo()
        self._run()

    # ---- 顶部：进程列表 ---------------------------------------------------
    def _build_process_card(self):
        card = Card(self, title="", pad=6)
        card.pack(fill="x", pady=(0, s(4)))

        header = tk.Frame(card.body, bg=theme.SURFACE)
        header.pack(fill="x", pady=(0, s(2)))
        self._config_columns(header)
        tk.Label(header, text="① 进程列表", font=theme.H2, bg=theme.SURFACE,
                 fg=theme.TEXT, anchor="w").grid(
            row=0, column=0, sticky="w", padx=(0, s(8)))
        for column, text in enumerate(("进程名", "到达时间", "运行时间"), start=1):
            tk.Label(header, text=text, font=theme.SMALL, bg=theme.SURFACE,
                     fg=theme.MUTED, anchor="w").grid(
                row=0, column=column, sticky="w", padx=(0, s(8)))
        tk.Label(header, text="到达 ≥ 0 · 运行 > 0", font=theme.SMALL,
                 bg=theme.SURFACE, fg=theme.FAINT, anchor="e").grid(
            row=0, column=4, sticky="e", padx=(0, s(8)))
        tk.Label(header, text="操作", font=theme.SMALL, bg=theme.SURFACE,
                 fg=theme.MUTED, anchor="center").grid(row=0, column=5, sticky="ew")

        self.list_body = tk.Frame(card.body, bg=theme.SURFACE)
        self.list_body.pack(fill="x")

        actions = tk.Frame(card.body, bg=theme.SURFACE)
        actions.pack(fill="x", pady=(s(4), 0))
        ActionButton(actions, "添加进程", command=self._add_process,
                     kind="ghost").pack(side="left")
        ActionButton(actions, "运行模拟", command=self._run).pack(side="right")
        self.message_label = tk.Label(
            actions, text="", font=theme.SMALL, bg=theme.SURFACE,
            fg=theme.MUTED, anchor="w",
        )
        self.message_label.pack(side="left", fill="x", expand=True,
                                padx=(s(10), s(10)))

    def _config_columns(self, frame):
        frame.grid_columnconfigure(0, minsize=s(108))
        frame.grid_columnconfigure(1, minsize=s(250))
        frame.grid_columnconfigure(2, minsize=s(112))
        frame.grid_columnconfigure(3, minsize=s(112))
        frame.grid_columnconfigure(4, weight=1)
        frame.grid_columnconfigure(5, minsize=s(64))

    def _entry_cell(self, master):
        wrapper = tk.Frame(master, bg=theme.BORDER)
        entry = tk.Entry(
            wrapper, width=1, font=theme.MONO, bd=0, relief="flat",
            bg=theme.SURFACE_ALT, fg=theme.TEXT, insertbackground=theme.ACCENT,
            justify="center",
        )
        entry.pack(fill="both", expand=True, padx=s(1), pady=s(1), ipady=s(1))
        return wrapper, entry

    def _add_row(self, pid, arrival, burst):
        row = tk.Frame(self.list_body, bg=theme.SURFACE)
        row.pack(fill="x")
        self._config_columns(row)

        name_wrap, name_entry = self._entry_cell(row)
        name_wrap.grid(row=0, column=1, sticky="ew", padx=(0, s(8)))
        name_entry.insert(0, str(pid))

        arrival_wrap, arrival_entry = self._entry_cell(row)
        arrival_wrap.grid(row=0, column=2, sticky="ew", padx=(0, s(8)))
        arrival_entry.insert(0, str(arrival))

        burst_wrap, burst_entry = self._entry_cell(row)
        burst_wrap.grid(row=0, column=3, sticky="ew", padx=(0, s(8)))
        burst_entry.insert(0, str(burst))

        item = {
            "frame": row,
            "pid": name_entry,
            "arrival": arrival_entry,
            "burst": burst_entry,
        }
        tk.Button(
            row, text="删除", font=theme.SMALL, bd=0, relief="flat",
            bg=theme.SURFACE_ALT, fg=theme.DANGER, activebackground=theme.DANGER,
            activeforeground=theme.BG, cursor="hand2", padx=s(8), pady=s(2),
            command=lambda target=item: self._remove_row(target),
        ).grid(row=0, column=5, sticky="ew")
        self._rows.append(item)

    def _remove_row(self, item):
        item["frame"].destroy()
        if item in self._rows:
            self._rows.remove(item)
        self._mark_dirty()

    def _next_pid(self):
        used = {row["pid"].get().strip() for row in self._rows}
        number = 1
        while f"P{number}" in used:
            number += 1
        return f"P{number}"

    def _add_process(self):
        self._add_row(self._next_pid(), 0, 1)
        item = self._rows[-1]
        item["pid"].focus_set()
        item["pid"].selection_range(0, "end")
        self._mark_dirty()

    def _set_message(self, text, color):
        self.message_label.configure(text=text, fg=color)

    def _mark_dirty(self):
        self._set_message("列表已修改，点击「运行模拟」", theme.WARN)
        self.app.set_status("进程调度：进程列表已修改，点击「运行模拟」更新结果")

    def _load_defaults(self):
        for pid, arrival, burst in (
            ("P1", 0, 5),
            ("P2", 1, 3),
            ("P3", 2, 8),
            ("P4", 4, 2),
        ):
            self._add_row(pid, arrival, burst)

    # ---- 中部：算法参数 ---------------------------------------------------
    def _build_param_card(self):
        card = Card(self, title="", pad=6)
        card.pack(fill="x", pady=(0, s(4)))

        row = tk.Frame(card.body, bg=theme.SURFACE)
        row.pack(fill="x")

        tk.Label(row, text="② 算法参数", font=theme.H2, bg=theme.SURFACE,
                 fg=theme.TEXT, anchor="w").pack(side="left", padx=(0, s(12)))
        tk.Frame(row, bg=theme.BORDER, width=s(1),
                 height=s(20)).pack(side="left", padx=(0, s(12)))

        self.algo_seg = Segmented(row, ALGOS, value="fcfs", command=self._on_algo)
        self.algo_seg.pack(side="left")

        tk.Label(row, text="时间片", font=theme.BODY, bg=theme.SURFACE,
                 fg=theme.MUTED).pack(side="left", padx=(s(20), s(8)))
        self.quantum_var = tk.StringVar(value="2")
        self.quantum_spin = ttk.Spinbox(
            row, from_=1, to=99, width=4, font=theme.MONO, justify="center",
            textvariable=self.quantum_var, command=self._on_quantum,
        )
        self.quantum_spin.pack(side="left")
        self.quantum_spin.bind("<Return>", self._on_quantum)
        self.quantum_spin.bind("<FocusOut>", self._on_quantum)

        self.algo_hint = tk.Label(
            row, text="", font=theme.SMALL, bg=theme.SURFACE, fg=theme.MUTED,
            anchor="w", justify="left", wraplength=theme.s(360),
        )
        self.algo_hint.pack(side="left", fill="x", expand=True, padx=(s(20), 0))

    def _refresh_algo(self):
        self.algo_hint.configure(text=ALGO_HINTS[self._algo])
        self.quantum_spin.configure(
            state="normal" if self._algo == "rr" else "disabled")

    def _on_algo(self, value):
        self.algo_seg.set(value)
        self._algo = value
        self._refresh_algo()
        self._run()

    def _on_quantum(self, _event=None):
        if self._algo == "rr":
            self._run()

    # ---- 底部：指标表格与汇总 ---------------------------------------------
    def _build_bottom(self):
        bottom = tk.Frame(self, bg=theme.BG)
        bottom.pack(side="bottom", fill="x", pady=(s(4), 0))
        bottom.grid_columnconfigure(0, weight=3, uniform="bottom")
        bottom.grid_columnconfigure(1, weight=2, uniform="bottom")
        bottom.grid_rowconfigure(0, weight=1)

        table_card = Card(bottom, title="④ 进程指标", subtitle="单位：时间片", pad=8)
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0, s(6)))
        self.table = DataTable(
            table_card.body,
            ["进程", "到达", "运行", "完成", "周转", "等待"],
            widths=[6, 5, 5, 5, 5, 5],
        )
        self.table.pack(fill="both", expand=True)

        stat_card = Card(bottom, title="⑤ 调度汇总", pad=8)
        stat_card.grid(row=0, column=1, sticky="nsew")
        chips = tk.Frame(stat_card.body, bg=theme.SURFACE)
        chips.pack(fill="both", expand=True)
        chips.grid_columnconfigure(0, weight=1, uniform="chip")
        chips.grid_columnconfigure(1, weight=1, uniform="chip")
        chips.grid_rowconfigure(0, weight=1)
        chips.grid_rowconfigure(1, weight=1)

        self.chip_waiting = StatChip(chips, "平均等待时间", "—", theme.WARN)
        self.chip_turnaround = StatChip(chips, "平均周转时间", "—", theme.ACCENT)
        self.chip_cpu = StatChip(chips, "CPU 利用率", "—", theme.OK)
        self.chip_switch = StatChip(chips, "上下文切换次数", "—", theme.PURPLE)

        self.chip_waiting.grid(row=0, column=0, sticky="nsew",
                               padx=(0, s(6)), pady=(0, s(6)))
        self.chip_turnaround.grid(row=0, column=1, sticky="nsew", pady=(0, s(6)))
        self.chip_cpu.grid(row=1, column=0, sticky="nsew", padx=(0, s(6)))
        self.chip_switch.grid(row=1, column=1, sticky="nsew")

    # ---- 主体：甘特图 -----------------------------------------------------
    def _build_gantt(self):
        card = Card(self, title="", pad=6)
        card.pack(fill="both", expand=True)

        head = tk.Frame(card.body, bg=theme.SURFACE)
        head.pack(fill="x", pady=(0, s(3)))
        tk.Label(head, text="③ 甘特图", font=theme.H2, bg=theme.SURFACE,
                 fg=theme.TEXT, anchor="w").pack(side="left")
        tk.Label(head, text="灰色表示 CPU 空闲", font=theme.SMALL,
                 bg=theme.SURFACE, fg=theme.FAINT).pack(side="left", padx=(s(10), 0))
        self.gantt_meta = tk.Label(head, text="", font=theme.SMALL,
                                   bg=theme.SURFACE, fg=theme.MUTED, anchor="e")
        self.gantt_meta.pack(side="right")

        self.canvas = tk.Canvas(
            card.body, bg=theme.SURFACE, width=1, height=theme.s(70),
            highlightthickness=0, bd=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _event: self._draw_gantt())

    # ---- 模拟与渲染 -------------------------------------------------------
    def _collect_processes(self):
        if not self._rows:
            raise ValueError("至少需要一个进程")

        processes = []
        for index, item in enumerate(self._rows, start=1):
            pid = item["pid"].get().strip()
            if not pid:
                raise ValueError(f"第 {index} 行的进程名不能为空")

            arrival_text = item["arrival"].get().strip()
            burst_text = item["burst"].get().strip()
            try:
                arrival = int(arrival_text)
            except ValueError:
                raise ValueError(f"第 {index} 行「{pid}」的到达时间必须是整数") from None
            try:
                burst = int(burst_text)
            except ValueError:
                raise ValueError(f"第 {index} 行「{pid}」的运行时间必须是整数") from None
            if arrival < 0:
                raise ValueError(f"第 {index} 行「{pid}」的到达时间不能为负")
            if burst <= 0:
                raise ValueError(f"第 {index} 行「{pid}」的运行时间必须大于 0")

            processes.append({"pid": pid, "arrival": arrival, "burst": burst})
        return processes

    def _read_quantum(self):
        text = self.quantum_var.get().strip()
        try:
            quantum = int(text)
        except ValueError:
            raise ValueError("时间片必须是大于 0 的整数") from None
        if quantum <= 0:
            raise ValueError("时间片必须是大于 0 的整数")
        return quantum

    def _run(self):
        try:
            processes = self._collect_processes()
            quantum = None
            if self._algo == "fcfs":
                result = scheduling.fcfs(processes)
                label = "FCFS"
            elif self._algo == "sjf":
                result = scheduling.sjf(processes)
                label = "SJF"
            else:
                quantum = self._read_quantum()
                result = scheduling.rr(processes, quantum)
                label = f"RR（时间片 {quantum}）"
        except ValueError as exc:
            self._set_message(f"输入错误：{exc}", theme.DANGER)
            self.app.set_status(f"进程调度：{exc}")
            return

        self._result = result
        self._sync_colors(processes)
        self._render_metrics()
        self._update_chips()
        self._draw_gantt()

        self._set_message(f"{len(processes)} 个进程 · {label}", theme.MUTED)
        total = result["timeline"][-1]["end"] if result["timeline"] else 0
        self.gantt_meta.configure(text=f"{label} · 总时长 {total}")
        self.app.set_status(
            f"进程调度 · {label} · 平均等待 {result['avg_waiting']:.2f} · "
            f"平均周转 {result['avg_turnaround']:.2f}"
        )

    def _sync_colors(self, processes):
        active = {process["pid"] for process in processes}
        self._colors = {
            pid: color for pid, color in self._colors.items() if pid in active
        }
        for process in processes:
            self._pid_color(process["pid"])

    def _pid_color(self, pid):
        if pid in self._colors:
            return self._colors[pid]
        used = set(self._colors.values())
        color = next((item for item in PROCESS_COLORS if item not in used), None)
        if color is None:
            color = PROCESS_COLORS[len(self._colors) % len(PROCESS_COLORS)]
        self._colors[pid] = color
        return color

    def _render_metrics(self):
        rows = []
        colors = {}
        for index, item in enumerate(self._result["metrics"]):
            rows.append([
                item["pid"], item["arrival"], item["burst"],
                item["finish"], item["turnaround"], item["waiting"],
            ])
            row_bg = theme.SURFACE if index % 2 == 0 else "#17273f"
            colors[(index, 0)] = (self._pid_color(item["pid"]), row_bg)
        self.table.set_rows(rows, colors)

    def _update_chips(self):
        data = self._result
        self.chip_waiting.set(f"{data['avg_waiting']:.2f}")
        self.chip_turnaround.set(f"{data['avg_turnaround']:.2f}")
        self.chip_cpu.set(f"{data['cpu_util']:.1f}%")
        self.chip_switch.set(f"{data['context_switches']} 次")

    # ---- 甘特图绘制 -------------------------------------------------------
    def _draw_gantt(self):
        canvas = self.canvas
        canvas.delete("all")
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1 or height <= 1:
            return

        if self._result is None:
            canvas.create_text(width / 2, height / 2, text="运行模拟后显示甘特图",
                               fill=theme.FAINT, font=theme.BODY)
            return
        if height < s(56):
            canvas.create_text(width / 2, height / 2, text="窗口过小，无法绘制甘特图",
                               fill=theme.FAINT, font=theme.SMALL)
            return

        timeline = self._result["timeline"]
        if not timeline:
            return
        total = timeline[-1]["end"]
        if total <= 0:
            return

        left = s(26)
        right = width - s(26)
        if right - left < s(40):
            return

        axis_y = height - s(18)
        block_top = s(4)
        block_bottom = axis_y - s(19)
        plot_width = right - left

        step = self._tick_step(total, plot_width)
        tick = 0
        last_x = None
        while tick <= total:
            x = left + plot_width * tick / total
            canvas.create_line(x, block_top, x, axis_y,
                               fill=theme.SURFACE_ALT, dash=(s(2), s(4)))
            canvas.create_line(x, axis_y, x, axis_y + s(4), fill=theme.BORDER)
            canvas.create_text(x, height - s(8), text=str(tick),
                               fill=theme.FAINT, font=theme.MONO_SMALL)
            last_x = x
            tick += step
        if tick - step != total:
            x = left + plot_width
            if last_x is None or x - last_x >= s(20):
                canvas.create_line(x, block_top, x, axis_y,
                                   fill=theme.SURFACE_ALT, dash=(s(2), s(4)))
                canvas.create_line(x, axis_y, x, axis_y + s(4), fill=theme.BORDER)
                canvas.create_text(x, height - s(8), text=str(total),
                                   fill=theme.FAINT, font=theme.MONO_SMALL)

        canvas.create_line(left, axis_y, right, axis_y,
                           fill=theme.BORDER, width=s(1))

        for segment in timeline:
            x0 = left + plot_width * segment["start"] / total
            x1 = left + plot_width * segment["end"] / total
            if x1 - x0 < s(2):
                x1 = x0 + s(2)

            idle = segment["pid"] == scheduling.IDLE
            fill = theme.FAINT if idle else self._pid_color(segment["pid"])
            canvas.create_rectangle(x0, block_top, x1, block_bottom,
                                    fill=fill, outline=theme.SURFACE, width=s(1))

            label = "空闲" if idle else segment["pid"]
            units = sum(2 if ord(char) > 127 else 1 for char in label)
            if x1 - x0 >= s(24) and units * s(7) + s(6) <= x1 - x0:
                canvas.create_text((x0 + x1) / 2,
                                   (block_top + block_bottom) / 2,
                                   text=label, fill=theme.BG, font=theme.MONO_BOLD)

            span = f"{segment['start']}–{segment['end']}"
            if x1 - x0 >= len(span) * s(7) + s(8):
                canvas.create_text((x0 + x1) / 2, axis_y - s(9),
                                   text=span, fill=theme.MUTED, font=theme.MONO_SMALL)

    @staticmethod
    def _tick_step(total, plot_width):
        max_ticks = max(2, int(plot_width / s(56)))
        raw = total / max_ticks
        magnitude = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
        for factor in (1, 2, 5, 10):
            step = magnitude * factor
            if step >= raw:
                return max(1, int(step))
        return max(1, int(magnitude * 10))

    def on_show(self):
        self._run()
