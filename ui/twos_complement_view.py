"""模块二：补码加减法演示器。"""

import tkinter as tk

from core import twos_complement
from . import theme
from .base_view import ModuleView
from .theme import s
from .widgets import ActionButton, BitStrip, Card, DataTable, Segmented, StatChip

WIDTH = 8
MIN_VALUE, MAX_VALUE = twos_complement.signed_range(WIDTH)
PRESETS = [
    ("127+1", 127, 1, "+"),
    ("-128-1", -128, 1, "-"),
    ("5-3", 5, 3, "-"),
    ("-5+3", -5, 3, "+"),
]
ROW_ALT = "#17273f"


class TwosComplementView(ModuleView):
    title = "补码加减法"
    subtitle = "8 位补码 · 进位与溢出"

    def __init__(self, master, app):
        super().__init__(master, app)
        self._steps = []
        self._build_input()
        self._build_body()
        self.convert()

    # ---- 顶部输入区 -------------------------------------------------------
    def _build_input(self):
        card = Card(self, title="① 输入数值与运算",
                    subtitle="8 位补码 · 范围 -128 ~ 127", pad=8)
        card.pack(fill="x", pady=(0, s(8)))
        row = tk.Frame(card.body, bg=theme.SURFACE)
        row.pack(fill="x")

        self.entry_a = self._entry_group(row, "被加数 A", 25)
        self.entry_b = self._entry_group(row, "加数 B", -13, left_pad=16)

        tk.Label(row, text="运算", font=theme.BODY, bg=theme.SURFACE,
                 fg=theme.MUTED).pack(side="left", padx=(s(18), s(6)))
        self.op_seg = Segmented(
            row, [("+", "加法"), ("-", "减法")], value="+", command=self._on_op_change)
        self.op_seg.pack(side="left")

        ActionButton(row, "计算", command=self.convert).pack(side="left", padx=(s(16), 0))

        self.preset_box = tk.Frame(row, bg=theme.SURFACE)
        self.preset_box.pack(side="right")
        tk.Label(self.preset_box, text="示例", font=theme.SMALL, bg=theme.SURFACE,
                 fg=theme.FAINT).pack(side="left", padx=(0, s(4)))
        for text, a, b, op in PRESETS:
            ActionButton(
                self.preset_box, text, kind="ghost",
                command=lambda a=a, b=b, op=op: self._preset(a, b, op),
            ).pack(side="left", padx=(0, s(5)))

        self.error_label = tk.Label(row, text="", font=theme.SMALL, bg=theme.SURFACE,
                                    fg=theme.DANGER, anchor="e",
                                    wraplength=s(300), justify="right")

    def _entry_group(self, parent, label, value, left_pad=0):
        group = tk.Frame(parent, bg=theme.SURFACE)
        group.pack(side="left", padx=(s(left_pad), 0))
        tk.Label(group, text=label, font=theme.BODY, bg=theme.SURFACE,
                 fg=theme.MUTED).pack(side="left", padx=(0, s(6)))

        wrap = tk.Frame(group, bg=theme.BORDER)
        wrap.pack(side="left")
        entry = tk.Entry(
            wrap, width=6, font=(theme.MONO[0], theme.TITLE[1] - 5, "bold"), bd=0,
            bg=theme.SURFACE_ALT, fg=theme.TEXT, insertbackground=theme.ACCENT,
            justify="center",
        )
        entry.pack(padx=s(1), pady=s(1), ipady=s(2))
        entry.insert(0, str(value))
        entry.bind("<Return>", lambda _event: self.convert())
        return entry

    def _on_op_change(self, _value):
        self.convert()

    # ---- 主体：运算过程 + 溢出验证 ----------------------------------------
    def _build_body(self):
        body = tk.Frame(self, bg=theme.BG)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=3, minsize=s(520))
        body.grid_columnconfigure(1, weight=2, minsize=s(290))
        body.grid_rowconfigure(0, weight=1)

        left = Card(body, title="② 运算过程", subtitle="符号位高亮 · 由低位算起", pad=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, s(8)))
        right = Card(body, title="③ 溢出与验证", pad=8)
        right.grid(row=0, column=1, sticky="nsew")

        self._build_strips(left.body)
        self._build_table(left.body)
        self._build_result(right.body)

    def _build_strips(self, parent):
        ruler_row = tk.Frame(parent, bg=theme.SURFACE)
        ruler_row.pack(fill="x", pady=(0, s(1)))
        ruler_meta = tk.Frame(ruler_row, bg=theme.SURFACE, width=s(120))
        ruler_meta.pack(side="left", fill="y")
        ruler_meta.pack_propagate(False)
        tk.Label(ruler_meta, text="位号", font=theme.SMALL, bg=theme.SURFACE,
                 fg=theme.FAINT, anchor="w").pack(expand=True, fill="x")

        self.ruler_canvas = tk.Canvas(
            ruler_row, bg=theme.SURFACE, width=1, height=s(20),
            highlightthickness=0, bd=0,
        )
        self.ruler_canvas.pack(side="left", fill="x", expand=True)
        self.ruler_canvas.bind("<Configure>", lambda _event: self._draw_ruler())

        self.strip_a, self.title_a, self.value_a = self._strip_row(parent, "被加数 A")
        self.strip_b, self.title_b, self.value_b = self._strip_row(parent, "加数 B")
        self.strip_sum, self.title_sum, self.value_sum = self._strip_row(parent, "结果 SUM")

        carry_row = tk.Frame(parent, bg=theme.SURFACE)
        carry_row.pack(fill="x", pady=(s(1), s(2)))
        carry_meta = tk.Frame(carry_row, bg=theme.SURFACE, width=s(120))
        carry_meta.pack(side="left", fill="y")
        carry_meta.pack_propagate(False)
        tk.Label(carry_meta, text="进位输入", font=theme.SMALL, bg=theme.SURFACE,
                 fg=theme.FAINT, anchor="w").pack(expand=True, fill="x")

        self.carry_canvas = tk.Canvas(
            carry_row, bg=theme.SURFACE, width=1, height=s(22),
            highlightthickness=0, bd=0,
        )
        self.carry_canvas.pack(side="left", fill="x", expand=True)
        self.carry_canvas.bind("<Configure>", lambda _event: self._draw_carry())

    def _strip_row(self, parent, title):
        row = tk.Frame(parent, bg=theme.SURFACE)
        row.pack(fill="x", pady=(0, s(1)))

        meta = tk.Frame(row, bg=theme.SURFACE, width=s(120))
        meta.pack(side="left", fill="y")
        meta.pack_propagate(False)
        inner = tk.Frame(meta, bg=theme.SURFACE)
        inner.pack(expand=True, fill="x")
        title_label = tk.Label(inner, text=title, font=theme.SMALL, bg=theme.SURFACE,
                               fg=theme.MUTED, anchor="w")
        title_label.pack(side="left")
        value_label = tk.Label(inner, text="—", font=theme.MONO_BOLD, bg=theme.SURFACE,
                               fg=theme.TEXT, anchor="w")
        value_label.pack(side="left", padx=(s(5), 0))

        strip = BitStrip(row, count=WIDTH, cell=24, gap=5, show_index=False)
        strip.configure(height=strip.cell + s(2))
        strip.pack(side="left", fill="x", expand=True)
        return strip, title_label, value_label

    def _build_table(self, parent):
        self.table = DataTable(
            parent,
            ["位", "A", "B", "进位输入", "本位和", "进位输出"],
            widths=[3, 4, 4, 8, 5, 8],
            anchors=["center"] * 6,
        )
        self.table.pack(fill="x")

    def _build_result(self, parent):
        tk.Label(parent, text="十进制结果", font=theme.SMALL, bg=theme.SURFACE,
                 fg=theme.MUTED, anchor="w").pack(fill="x")
        self.result_value = tk.Label(
            parent, text="—", font=(theme.MONO[0], theme.TITLE[1] + 10, "bold"),
            bg=theme.SURFACE, fg=theme.OK, anchor="w",
        )
        self.result_value.pack(fill="x")

        bits_line = tk.Frame(parent, bg=theme.SURFACE)
        bits_line.pack(fill="x")
        tk.Label(bits_line, text="8 位补码", font=theme.SMALL, bg=theme.SURFACE,
                 fg=theme.FAINT).pack(side="left")
        self.result_bits = tk.Label(bits_line, text="—", font=theme.MONO_BOLD,
                                    bg=theme.SURFACE, fg=theme.ACCENT)
        self.result_bits.pack(side="left", padx=(s(6), 0))

        chips = tk.Frame(parent, bg=theme.SURFACE)
        chips.pack(fill="x", pady=(s(5), 0))
        self.overflow_chip = StatChip(chips, "是否溢出", "—", theme.OK)
        self.overflow_chip.pack(side="left", padx=(0, s(6)))
        self.carry_chip = StatChip(chips, "最高位进位 Cn", "—", theme.ACCENT)
        self.carry_chip.pack(side="left", padx=(0, s(6)))
        self.range_chip = StatChip(chips, "结果范围", "—", theme.OK)
        self.range_chip.pack(side="left")

        tk.Frame(parent, bg=theme.BORDER, height=s(1)).pack(fill="x", pady=s(7))
        tk.Label(parent, text="溢出判断", font=theme.H2, bg=theme.SURFACE,
                 fg=theme.TEXT, anchor="w").pack(fill="x")
        tk.Label(parent, text="判据：同号相加结果异号，或 Cn-1 ⊕ Cn = 1",
                 font=theme.SMALL, bg=theme.SURFACE, fg=theme.FAINT,
                 anchor="w", justify="left", wraplength=s(290)).pack(
            fill="x", pady=(0, s(3)))
        self.overflow_label = tk.Label(
            parent, text="", font=theme.SMALL, bg=theme.SURFACE, fg=theme.MUTED,
            anchor="w", justify="left", wraplength=s(290),
        )
        self.overflow_label.pack(fill="x")

        box = tk.Frame(parent, bg=theme.SURFACE_ALT, highlightbackground=theme.BORDER,
                       highlightthickness=s(1))
        box.pack(fill="x", pady=(s(8), 0))
        tk.Label(box, text="补码原理", font=theme.H2, bg=theme.SURFACE_ALT,
                 fg=theme.PURPLE, anchor="w").pack(
            fill="x", padx=s(10), pady=(s(6), s(1)))
        tk.Label(
            box, text="负数 = 各位取反再加 1；减法 A - B 转为 A + (-B)，"
                      "符号位参与运算，最高位进位舍去。",
            font=theme.SMALL, bg=theme.SURFACE_ALT, fg=theme.MUTED,
            anchor="w", justify="left", wraplength=s(250),
        ).pack(fill="x", padx=s(10), pady=(0, s(6)))

    # ---- 交互与渲染 -------------------------------------------------------
    def _preset(self, a, b, op):
        self._set_entry(self.entry_a, a)
        self._set_entry(self.entry_b, b)
        self.op_seg.set(op)
        self.convert()

    @staticmethod
    def _set_entry(entry, value):
        entry.delete(0, "end")
        entry.insert(0, str(value))

    def _read_entry(self, entry, label):
        text = entry.get().strip()
        if not text:
            raise ValueError(f"{label} 不能为空")
        try:
            value = int(text, 10)
        except ValueError:
            raise ValueError(f"{label} 必须是十进制整数") from None
        if not MIN_VALUE <= value <= MAX_VALUE:
            raise ValueError(f"{label} 超出范围 {MIN_VALUE} ~ {MAX_VALUE}")
        return value

    def _show_error(self, text):
        self.preset_box.pack_forget()
        self.error_label.pack_forget()
        if text:
            self.error_label.configure(text=f"输入错误：{text}")
            self.error_label.pack(side="right")
        else:
            self.preset_box.pack(side="right")

    def convert(self):
        try:
            a = self._read_entry(self.entry_a, "被加数 A")
            b = self._read_entry(self.entry_b, "加数 B")
            op = self.op_seg.get()
            data = twos_complement.analyze(a, b, op=op, width=WIDTH)
        except ValueError as exc:
            self._show_error(str(exc))
            self.app.set_status(f"补码运算：{exc}")
            return

        self._show_error("")
        self._render(a, b, op, data)

        symbol = "+" if op == "+" else "-"
        b_text = f"({b})" if b < 0 else str(b)
        verdict = "溢出" if data["overflow"] else "未溢出"
        self.app.set_status(
            f"补码运算：{a} {symbol} {b_text} = {data['decimal_result']}"
            f"（8 位补码 {data['result_bits']}，{verdict}）"
        )

    def _render(self, a, b, op, data):
        self._steps = data["steps"]

        self.value_a.configure(text=f"原值 {a}", fg=theme.TEXT)
        self.strip_a.set_bits(
            data["a_bits"], colors=self._bit_colors(data["a_bits"], "a"))

        if op == "-":
            self.title_b.configure(text="加数 -B")
            self.value_b.configure(text=f"原值 {b}", fg=theme.ORANGE)
            self.strip_b.set_bits(
                data["b_bits"], colors=self._bit_colors(data["b_bits"], "b_neg"))
        else:
            self.title_b.configure(text="加数 B")
            self.value_b.configure(text=f"原值 {b}", fg=theme.TEXT)
            self.strip_b.set_bits(
                data["b_bits"], colors=self._bit_colors(data["b_bits"], "b"))

        self.strip_sum.set_bits(
            data["result_bits"],
            colors=self._bit_colors(data["result_bits"], "sum", data["overflow"]),
        )
        self.value_sum.configure(
            text=f"{data['decimal_result']}",
            fg=theme.DANGER if data["overflow"] else theme.OK,
        )

        self._draw_carry()
        self._render_table(data["steps"])

        overflow = data["overflow"]
        self.result_value.configure(
            text=str(data["decimal_result"]),
            fg=theme.DANGER if overflow else theme.OK,
        )
        self.result_bits.configure(
            text=data["result_bits"],
            fg=theme.DANGER if overflow else theme.ACCENT,
        )
        self.overflow_chip.set("是" if overflow else "否",
                               theme.DANGER if overflow else theme.OK)
        self.carry_chip.set(data["carry_out"],
                            theme.WARN if data["carry_out"] else theme.MUTED)
        self.range_chip.set("合法" if data["in_range"] else "越界",
                            theme.OK if data["in_range"] else theme.DANGER)
        self.overflow_label.configure(text=data["overflow_reason"])

    def _bit_colors(self, bits, kind, overflow=False):
        colors = {}
        for index, bit in enumerate(bits):
            if index == 0:
                if kind == "sum" and overflow:
                    colors[index] = (theme.DANGER, theme.BG)
                else:
                    colors[index] = (theme.ACCENT_DARK,
                                     theme.TEXT if bit == "1" else theme.MUTED)
                continue
            if bit == "1":
                if kind == "b_neg":
                    fg = theme.ORANGE
                elif kind == "sum":
                    fg = theme.OK
                else:
                    fg = theme.ACCENT
            else:
                fg = theme.FAINT
            colors[index] = (theme.SURFACE_ALT, fg)
        return colors

    def _render_table(self, steps):
        rows, colors = [], {}
        for step in reversed(steps):
            row_index = len(rows)
            rows.append([
                step["index"], step["a"], step["b"],
                step["carry_in"], step["sum"], step["carry_out"],
            ])
            bg = theme.SURFACE if row_index % 2 == 0 else ROW_ALT
            if step["index"] == WIDTH - 1:
                colors[(row_index, 0)] = (theme.PURPLE, bg)
            if step["carry_in"]:
                colors[(row_index, 3)] = (theme.WARN, bg)
            if step["sum"]:
                colors[(row_index, 4)] = (theme.ACCENT, bg)
            if step["carry_out"]:
                colors[(row_index, 5)] = (theme.OK, bg)
        self.table.set_rows(rows, colors)

    def _draw_ruler(self):
        canvas = self.ruler_canvas
        canvas.delete("all")
        cell = self.strip_a.cell
        gap = self.strip_a.gap
        count = self.strip_a.count
        total = count * cell + (count - 1) * gap
        start = max(s(8), (canvas.winfo_width() - total) / 2)
        y = canvas.winfo_height() / 2
        for column in range(count):
            x = start + column * (cell + gap) + cell / 2
            canvas.create_text(x, y, text=str(count - 1 - column), anchor="center",
                               fill=theme.FAINT, font=theme.MONO_SMALL)

    def _draw_carry(self):
        canvas = self.carry_canvas
        canvas.delete("all")
        if not self._steps:
            return
        cell = self.strip_a.cell
        gap = self.strip_a.gap
        count = self.strip_a.count
        total = count * cell + (count - 1) * gap
        start = max(s(8), (canvas.winfo_width() - total) / 2)
        y = canvas.winfo_height() / 2
        for step in self._steps:
            column = count - 1 - step["index"]
            x = start + column * (cell + gap) + cell / 2
            color = theme.WARN if step["carry_in"] else theme.FAINT
            canvas.create_text(x, y, text=str(step["carry_in"]), anchor="center",
                               fill=color, font=theme.MONO_SMALL)

    def on_show(self):
        self.convert()
