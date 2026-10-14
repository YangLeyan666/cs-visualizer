"""模块一：进制转换演示器。"""

import random
import tkinter as tk

from core import number_base
from . import theme
from .base_view import ModuleView
from .theme import s
from .widgets import ActionButton, Card, DataTable, Segmented, StatChip, BitStrip, hint


BASE_OPTIONS = [("2", "二进制"), ("8", "八进制"), ("10", "十进制"), ("16", "十六进制")]


class NumberBaseView(ModuleView):
    title = "进制转换演示器"
    subtitle = "除基取余 · 乘基取整 —— 看清每一步的商与余数"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.source_base = "10"
        self.target_base = "2"

        self._build_input()
        self._build_body()
        self.convert()

    # ---- 顶部输入区 -------------------------------------------------------
    def _build_input(self):
        card = Card(self, title="① 输入数值与进制")
        card.pack(fill="x", pady=(0, s(10)))
        row = tk.Frame(card.body, bg=theme.SURFACE)
        row.pack(fill="x")

        tk.Label(row, text="数值", font=theme.BODY, bg=theme.SURFACE,
                 fg=theme.MUTED).pack(side="left", padx=(0, s(8)))

        entry_wrap = tk.Frame(row, bg=theme.BORDER)
        entry_wrap.pack(side="left")
        self.entry = tk.Entry(
            entry_wrap, width=12, font=(theme.MONO[0], 14, "bold"), bd=0,
            bg=theme.SURFACE_ALT, fg=theme.TEXT, insertbackground=theme.ACCENT,
            justify="center",
        )
        self.entry.pack(padx=1, pady=1, ipady=s(4))
        self.entry.insert(0, "2024")
        self.entry.bind("<Return>", lambda _e: self.convert())

        ActionButton(row, "开始转换", command=self.convert).pack(side="left", padx=(s(14), 0))
        ActionButton(row, "随机示例", command=self.randomize, kind="ghost").pack(
            side="left", padx=(s(8), 0))

        row2 = tk.Frame(card.body, bg=theme.SURFACE)
        row2.pack(fill="x", pady=(s(8), 0))
        tk.Label(row2, text="源进制", font=theme.SMALL, bg=theme.SURFACE,
                 fg=theme.MUTED).pack(side="left", padx=(0, s(6)))
        self.source_seg = Segmented(row2, BASE_OPTIONS, value="10",
                                    command=self._on_source_change)
        self.source_seg.pack(side="left")

        tk.Label(row2, text="→", font=(theme.BODY[0], 14, "bold"), bg=theme.SURFACE,
                 fg=theme.ACCENT).pack(side="left", padx=s(12))

        tk.Label(row2, text="目标进制", font=theme.SMALL, bg=theme.SURFACE,
                 fg=theme.MUTED).pack(side="left", padx=(0, s(6)))
        self.target_seg = Segmented(row2, BASE_OPTIONS, value="2",
                                    command=self._on_target_change)
        self.target_seg.pack(side="left")

        self.error_label = tk.Label(card.body, text="", font=theme.SMALL,
                                    bg=theme.SURFACE, fg=theme.DANGER, anchor="w")
        self.error_label.pack(fill="x", pady=(s(6), 0))
        hint(card.body, "支持小数，例如 2024、1011.101、7E8。输入非法字符时会在下方提示。",
             wrap=900).pack(fill="x", pady=(s(2), 0))

    def _on_source_change(self, value):
        self.source_base = value
        self.convert()

    def _on_target_change(self, value):
        self.target_base = value
        self.convert()

    # ---- 主体：结果 + 过程 -------------------------------------------------
    def _build_body(self):
        body = tk.Frame(self, bg=theme.BG)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=0, minsize=s(330))
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        left = Card(body, title="② 转换结果")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, s(10)))
        self.result_label = tk.Label(
            left.body, text="—", font=(theme.MONO[0], 18, "bold"),
            bg=theme.SURFACE, fg=theme.ACCENT, anchor="w", justify="left",
            wraplength=s(290),
        )
        self.result_label.pack(fill="x")
        tk.Label(left.body, text="目标进制下的表示", font=theme.SMALL,
                 bg=theme.SURFACE, fg=theme.FAINT, anchor="w").pack(fill="x", pady=(0, s(8)))

        self.base_rows = {}
        for key, name in BASE_OPTIONS:
            line = tk.Frame(left.body, bg=theme.SURFACE)
            line.pack(fill="x", pady=s(1))
            tk.Label(line, text=name, font=theme.SMALL, bg=theme.SURFACE, fg=theme.MUTED,
                     width=7, anchor="w").pack(side="left")
            value = tk.Label(line, text="—", font=theme.MONO_BOLD, bg=theme.SURFACE,
                             fg=theme.TEXT, anchor="w")
            value.pack(side="left")
            self.base_rows[key] = value

        tk.Frame(left.body, bg=theme.BORDER, height=1).pack(fill="x", pady=s(8))
        tk.Label(left.body, text="二进制位（每 4 位一组）", font=theme.SMALL,
                 bg=theme.SURFACE, fg=theme.MUTED, anchor="w").pack(fill="x", pady=(0, s(4)))
        self.bit_container = tk.Frame(left.body, bg=theme.SURFACE)
        self.bit_container.pack(fill="x")

        chips = tk.Frame(left.body, bg=theme.SURFACE)
        chips.pack(fill="x", pady=(s(10), 0))
        self.len_chip = StatChip(chips, "二进制位数", "—")
        self.len_chip.pack(side="left", padx=(0, s(8)))
        self.int_chip = StatChip(chips, "十进制值", "—", theme.PURPLE)
        self.int_chip.pack(side="left")

        right = Card(body, title="③ 计算过程")
        right.grid(row=0, column=1, sticky="nsew")
        self.note = tk.Label(right.body, text="", font=theme.SMALL, bg=theme.SURFACE,
                             fg=theme.MUTED, anchor="w", justify="left", wraplength=s(560))
        self.note.pack(fill="x", pady=(0, s(6)))

        self.table = DataTable(
            right.body,
            ["#", "被除数", "除式", "商", "余数", "数位"],
            widths=[2, 7, 9, 6, 4, 3],
            anchors=["center", "e", "center", "e", "e", "center"],
        )
        self.table.pack(fill="x")

        self.frac_title = tk.Label(right.body, text="", font=theme.H2, bg=theme.SURFACE,
                                   fg=theme.TEXT, anchor="w")
        self.frac_table = DataTable(
            right.body,
            ["#", "小数", "× 基数", "积", "取整", "余下小数"],
            widths=[2, 7, 5, 6, 4, 7],
            anchors=["center", "e", "center", "e", "center", "e"],
        )
        hint(right.body, "整数部分：商为 0 时停止，余数从下往上读；小数部分：小数部分为 0 时停止，取整从上往下读。",
             wrap=520).pack(fill="x", pady=(s(8), 0))

    # ---- 交互 -------------------------------------------------------------
    def randomize(self):
        value = random.choice([2024, 255, 1024, 666, 4095, 8888, random.randint(1, 99999)])
        self.entry.delete(0, "end")
        self.entry.insert(0, str(value))
        self.source_seg.set("10")
        self.source_base = "10"
        self.target_seg.set(random.choice(["2", "8", "16"]))
        self.target_base = self.target_seg.get()
        self.convert()

    def convert(self):
        text = self.entry.get().strip()
        src, dst = int(self.source_base), int(self.target_base)
        try:
            data = number_base.convert(text, src, dst)
        except ValueError as exc:
            self.error_label.configure(text=f"输入错误：{exc}")
            return

        self.error_label.configure(text="")
        self.result_label.configure(text=data["result"])
        for base, widget in self.base_rows.items():
            widget.configure(text=number_base.to_base(data["int_value"], int(base))
                             + (" …" if data["fraction_value"] else ""))

        binary = number_base.to_base(data["int_value"], 2)
        self.len_chip.set(f"{len(binary)} bit")
        self.int_chip.set(data["int_value"])
        self._draw_bits(binary)

        rows, colors = [], {}
        for i, step in enumerate(data["int_steps"], start=1):
            rows.append([
                i, step["dividend"], f"÷ {step['divisor']}", step["quotient"],
                step["remainder"], step["digit"],
            ])
            colors[(i - 1, 5)] = (theme.ACCENT, "#17273f" if i % 2 == 0 else theme.SURFACE)
        self.table.set_rows(rows, colors)
        self.note.configure(
            text=f"{src} 进制 {text} → {dst} 进制，整数部分共 {len(data['int_steps'])} 步；"
                 f"余数序列倒序拼接得到 {data['result'].split('.')[0]}"
        )

        if data["frac_steps"]:
            self.frac_title.configure(text="小数部分：乘基取整")
            self.frac_title.pack(fill="x", pady=(s(12), s(4)))
            self.frac_table.pack(fill="x")
            frows = []
            for i, step in enumerate(data["frac_steps"], start=1):
                frows.append([
                    i, f"{step['operand']:.6f}", f"× {dst}", f"{step['product']:.6f}",
                    step["digit"], f"{step['remainder']:.6f}",
                ])
            self.frac_table.set_rows(frows)
        else:
            self.frac_title.pack_forget()
            self.frac_table.pack_forget()

        self.app.set_status(f"进制转换：{text}（{src} 进制） → {data['result']}（{dst} 进制）")

    def _draw_bits(self, binary: str):
        for child in self.bit_container.winfo_children():
            child.destroy()
        group_size = 4
        padded = binary.rjust((len(binary) + group_size - 1) // group_size * group_size, "0")
        if len(padded) > 36:
            padded = padded[-36:]
        strip = BitStrip(self.bit_container, count=len(padded), cell=22, gap=4, group=group_size)
        strip.pack(fill="x")
        strip.set_bits(padded, group=group_size)

    def on_show(self):
        self.app.set_status("进制转换：输入任意进制的数值，查看逐位换算过程")
