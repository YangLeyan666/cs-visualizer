"""模块三：ASCII 与奇偶校验演示器。"""

import tkinter as tk

from core import parity

from . import theme
from .base_view import ModuleView
from .theme import s
from .widgets import (
    ActionButton,
    BitStrip,
    Card,
    DataTable,
    ScrollFrame,
    Segmented,
    StatChip,
    hint,
)


MODE_OPTIONS = [("even", "偶校验"), ("odd", "奇校验")]
MODE_NAMES = {"even": "偶校验", "odd": "奇校验"}


class ParityView(ModuleView):
    title = "ASCII 与奇偶校验"
    subtitle = "7 位 ASCII · 1 位校验"

    def __init__(self, master, app):
        super().__init__(master, app)

        self.mode = "even"
        self.flips = {}                 # {(字符下标, 帧字符串位下标): True}
        self.data = None
        self._last_text = None
        self._frame_index = 0
        self._suspend_select = False

        self._build_input()
        self._build_body()
        self._send(force=True)

    # ---- 顶部输入区 -------------------------------------------------------
    def _build_input(self):
        card = Card(self, title="① 文本与校验方式", pad=12)
        card.pack(fill="x", pady=(0, s(10)))
        row = tk.Frame(card.body, bg=theme.SURFACE)
        row.pack(fill="x")

        tk.Label(row, text="文本", font=theme.BODY, bg=theme.SURFACE,
                 fg=theme.MUTED).pack(side="left", padx=(0, s(8)))

        entry_wrap = tk.Frame(row, bg=theme.BORDER)
        entry_wrap.pack(side="left")
        self.entry = tk.Entry(
            entry_wrap, width=20, font=theme.MONO_BOLD, bd=0,
            bg=theme.SURFACE_ALT, fg=theme.TEXT, insertbackground=theme.ACCENT,
            selectbackground=theme.ACCENT_DARK, selectforeground=theme.TEXT,
            highlightthickness=0,
        )
        self.entry.pack(padx=s(1), pady=s(1), ipady=s(4))
        self.entry.insert(0, "CS")
        self.entry.bind("<KeyRelease>", self._on_text_key)
        self.entry.bind("<Return>", lambda _e: self._send(reset_flips=True, force=True))

        tk.Label(row, text="校验方式", font=theme.BODY, bg=theme.SURFACE,
                 fg=theme.MUTED).pack(side="left", padx=(s(20), s(8)))
        self.mode_seg = Segmented(row, MODE_OPTIONS, value="even",
                                  command=self._on_mode_change)
        self.mode_seg.pack(side="left")

        ActionButton(row, "重新发送", command=self.resend, kind="ghost").pack(
            side="left", padx=(s(14), 0))

        self.message = tk.Label(
            card.body, text="", font=theme.SMALL, bg=theme.SURFACE,
            fg=theme.FAINT, anchor="w", justify="left", wraplength=s(860),
        )
        self.message.pack(fill="x", pady=(s(8), 0))

    # ---- 主体：发送方表格 + 信道演示 --------------------------------------
    def _build_body(self):
        body = tk.Frame(self, bg=theme.BG)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=0, minsize=s(432))
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        left = Card(body, title="② 发送方编码", subtitle="校验位在最高位", pad=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, s(10)))
        self.table_scroll = ScrollFrame(left.body, bg=theme.SURFACE)
        self.table_scroll.pack(fill="both", expand=True)
        self.table_scroll.canvas.bind(
            "<Configure>", lambda _e: self._sync_table_scroll(), add="+")

        self.table = DataTable(
            self.table_scroll.inner,
            ["字符", "十进制", "7 位 ASCII", "校验位", "8 位帧"],
            widths=[6, 7, 11, 7, 11],
            anchors=["center", "center", "center", "center", "center"],
        )
        self.table.pack(fill="x")
        hint(left.body, "bit 7 为校验位，bit 0 为最低位；点击表格行可切换当前查看的帧。",
             wrap=385).pack(fill="x", pady=(s(6), 0))

        right = Card(body, title="③ 信道与接收方", subtitle="错误注入 · 实时判决", pad=12)
        right.grid(row=0, column=1, sticky="nsew")

        self.frame_title = tk.Label(
            right.body, text="当前帧：—", font=theme.BODY_BOLD, bg=theme.SURFACE,
            fg=theme.TEXT, anchor="w",
        )
        self.frame_title.pack(fill="x")

        self.sender_strip = self._build_strip(right.body, "发送方帧")
        self.channel_strip = self._build_strip(right.body, "信道帧")
        self.receiver_strip = self._build_strip(right.body, "接收方帧")

        self._build_injection(right.body)
        self._build_verdict(right.body)
        self._build_stats(right.body)

        hint(right.body, "偶校验使 1 的个数为偶数，奇校验使 1 的个数为奇数；\n"
                         "单比特错误必被检出，双比特错误可能漏检。",
             wrap=430).pack(fill="x", pady=(s(6), 0))

    def _build_strip(self, master, label: str) -> BitStrip:
        row = tk.Frame(master, bg=theme.SURFACE)
        row.pack(fill="x")
        tk.Label(row, text=label, font=theme.SMALL, bg=theme.SURFACE,
                 fg=theme.MUTED, width=8, anchor="w").pack(side="left")
        strip = BitStrip(row, count=8, cell=28, gap=5)
        strip.pack(side="left", fill="x", expand=True)
        return strip

    def _build_injection(self, master):
        tk.Frame(master, bg=theme.BORDER, height=s(1)).pack(fill="x", pady=s(3))
        row = tk.Frame(master, bg=theme.SURFACE)
        row.pack(fill="x")

        tk.Label(row, text="错误注入", font=theme.H2, bg=theme.SURFACE,
                 fg=theme.TEXT).pack(side="left", padx=(0, s(10)))
        tk.Label(row, text="字符序号", font=theme.SMALL, bg=theme.SURFACE,
                 fg=theme.MUTED).pack(side="left")

        self.frame_var = tk.StringVar(value="1")
        self.frame_spin = self._make_spin(row, self.frame_var, 1, 1, width=3)
        self.frame_spin.pack(side="left", padx=(s(4), s(10)))
        self.frame_var.trace_add("write", self._on_frame_var)
        self.frame_spin.bind("<FocusOut>", lambda _e: self._normalize_frame_spin())
        self.frame_spin.bind("<Return>", lambda _e: self._normalize_frame_spin())

        tk.Label(row, text="位序号", font=theme.SMALL, bg=theme.SURFACE,
                 fg=theme.MUTED).pack(side="left")

        self.bit_var = tk.StringVar(value="0")
        self.bit_spin = self._make_spin(row, self.bit_var, 0, 7, width=2)
        self.bit_spin.pack(side="left", padx=(s(4), s(10)))
        self.bit_var.trace_add("write", self._on_bit_var)
        self.bit_spin.bind("<FocusOut>", lambda _e: self._normalize_bit_spin())
        self.bit_spin.bind("<Return>", lambda _e: self._normalize_bit_spin())

        self.flip_button = ActionButton(row, "翻转该位", command=self._toggle_bit,
                                        kind="danger")
        self.flip_button.pack(side="left")
        self.restore_button = ActionButton(row, "恢复", command=self._restore,
                                           kind="ghost")
        self.restore_button.pack(side="left", padx=(s(6), 0))

    def _make_spin(self, master, variable, from_value, to_value, width=3) -> tk.Spinbox:
        return tk.Spinbox(
            master, from_=from_value, to=to_value, textvariable=variable,
            width=width, font=theme.MONO, justify="center",
            bg=theme.SURFACE_ALT, fg=theme.TEXT, insertbackground=theme.TEXT,
            buttonbackground=theme.SURFACE_ALT, relief="flat", bd=0,
            highlightthickness=s(1), highlightbackground=theme.BORDER,
            highlightcolor=theme.ACCENT,
        )

    def _build_verdict(self, master):
        tk.Frame(master, bg=theme.BORDER, height=s(1)).pack(fill="x", pady=s(3))
        row = tk.Frame(master, bg=theme.SURFACE)
        row.pack(fill="x")
        self.verdict = tk.Label(row, text="—", font=theme.H2, bg=theme.SURFACE,
                                fg=theme.OK, anchor="w")
        self.verdict.pack(side="left")
        self.verdict_detail = tk.Label(
            row, text="", font=theme.SMALL, bg=theme.SURFACE, fg=theme.MUTED,
            anchor="w", justify="left", wraplength=s(330),
        )
        self.verdict_detail.pack(side="left", fill="x", expand=True, padx=(s(10), 0))

    def _build_stats(self, master):
        chips = tk.Frame(master, bg=theme.SURFACE)
        chips.pack(fill="x", pady=(s(6), 0))
        self.frame_chip = StatChip(chips, "帧数", "0", theme.ACCENT)
        self.frame_chip.pack(side="left", padx=(0, s(6)))
        self.flipped_chip = StatChip(chips, "被翻转帧数", "0", theme.WARN)
        self.flipped_chip.pack(side="left", padx=(0, s(6)))
        self.detected_chip = StatChip(chips, "检出数", "0", theme.OK)
        self.detected_chip.pack(side="left", padx=(0, s(6)))
        self.missed_chip = StatChip(chips, "漏检数", "0", theme.DANGER)
        self.missed_chip.pack(side="left")

    # ---- 发送与刷新 -------------------------------------------------------
    def _on_text_key(self, _event):
        if self.entry.get() != self._last_text:
            self._send(reset_flips=True)

    def _on_mode_change(self, value):
        if value == self.mode:
            return
        self.mode = value
        self._send(reset_flips=True, force=True)

    def resend(self):
        self._send(reset_flips=True, force=True)

    def _send(self, reset_flips: bool = False, force: bool = False):
        text = self.entry.get()
        if not force and text == self._last_text:
            return
        self._last_text = text
        if reset_flips:
            self.flips.clear()

        if not text:
            self._show_error("请输入至少 1 个 ASCII 字符。")
            self.app.set_status("ASCII 校验：请输入文本")
            return

        try:
            data = parity.transmit(text, self.mode, self.flips)
        except ValueError as exc:
            self._show_error(f"输入错误：{exc}")
            self.app.set_status(f"ASCII 校验：{exc}")
            return

        self.data = data
        self._frame_index = 0
        self.message.configure(
            text=f"已生成 {data['frame_count']} 帧，每帧 = 1 位{MODE_NAMES[self.mode]}位"
                 f" + 7 位 ASCII；输入变化会自动重新编码。",
            fg=theme.FAINT,
        )
        self._enable_controls(True)
        self.frame_spin.configure(to=max(1, data["frame_count"]))
        self._suspend_select = True
        self.frame_var.set("1")
        self.bit_var.set("0")
        self._suspend_select = False

        self._refresh_table()
        self._refresh_current()
        self._refresh_stats()
        self._update_status()

    def _show_error(self, message: str):
        self.data = None
        self.flips.clear()
        self.message.configure(text=message, fg=theme.DANGER)
        self._enable_controls(False)
        self.frame_spin.configure(to=1)
        self._suspend_select = True
        self.frame_var.set("1")
        self.bit_var.set("0")
        self._suspend_select = False
        self.table.set_rows([])
        self._sync_table_scroll()
        self._clear_results()
        self._refresh_stats()

    def _enable_controls(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.frame_spin.configure(state=state)
        self.bit_spin.configure(state=state)
        self.flip_button.configure(state=state)
        self.restore_button.configure(state=state)

    # ---- 表格 -------------------------------------------------------------
    def _refresh_table(self):
        if not self.data or not self.data["frames"]:
            self.table.set_rows([])
            self._sync_table_scroll()
            return

        rows = []
        colors = {}
        for index, frame in enumerate(self.data["frames"]):
            selected = index == self._frame_index
            for column in range(5):
                if selected:
                    bg = theme.SURFACE_HOVER
                else:
                    bg = theme.SURFACE if index % 2 == 0 else theme.SURFACE_ALT
                fg = theme.ACCENT if column == 3 else theme.TEXT
                colors[(index, column)] = (fg, bg)
            rows.append([
                self._char_display(frame["char"]),
                frame["code"],
                frame["ascii"],
                frame["parity"],
                frame["sender"],
            ])

        self.table.set_rows(rows, colors)
        self._bind_table_rows()
        self.after_idle(self._sync_table_scroll)

    def _bind_table_rows(self):
        for cell in self.table.grid_slaves():
            try:
                row = int(cell.grid_info()["row"])
            except (KeyError, ValueError):
                continue
            if row <= 0:
                continue
            cell.configure(cursor="hand2")
            cell.bind("<Button-1>",
                      lambda _event, index=row - 1: self._select_row(index))

    def _select_row(self, index: int):
        if not self.data or not 0 <= index < self.data["frame_count"]:
            return
        self.frame_var.set(str(index + 1))

    def _sync_table_scroll(self):
        if not self.table.winfo_exists():
            return
        available = self.table_scroll.canvas.winfo_height()
        if available <= 1:
            return
        needed = self.table.winfo_reqheight() > available
        managed = bool(self.table_scroll.vbar.winfo_manager())
        if needed and not managed:
            self.table_scroll.vbar.pack(side="right", fill="y")
        elif not needed and managed:
            self.table_scroll.vbar.pack_forget()
            self.table_scroll.canvas.yview_moveto(0)

    # ---- 当前帧与判决 -----------------------------------------------------
    def _refresh_current(self):
        if not self.data or not self.data["frames"]:
            self._clear_results()
            return

        count = self.data["frame_count"]
        self._frame_index = max(0, min(self._frame_index, count - 1))
        frame = self.data["frames"][self._frame_index]
        selected_bit = 7 - self._read_bit_position()
        flipped = set(frame["flips"])

        self.frame_title.configure(
            text=f"第 {self._frame_index + 1}/{count} 帧 · "
                 f"字符 {self._char_display(frame['char'])} · "
                 f"十进制 {frame['code']} · ASCII {frame['ascii']}"
        )

        sender_colors = {}
        for index in range(8):
            bg = theme.SURFACE_HOVER if index == selected_bit else theme.SURFACE_ALT
            fg = theme.PURPLE if index == 0 else theme.ACCENT
            sender_colors[index] = (bg, fg)

        channel_colors = {}
        for index in range(8):
            if index in flipped:
                channel_colors[index] = (theme.DANGER, theme.BG)
            elif index == selected_bit:
                channel_colors[index] = (theme.SURFACE_HOVER, theme.ACCENT)
            elif index == 0:
                channel_colors[index] = (theme.SURFACE_ALT, theme.PURPLE)

        receiver_colors = {}
        for index in range(8):
            bg = theme.SURFACE_HOVER if index == selected_bit else theme.SURFACE_ALT
            receiver_colors[index] = (bg, theme.OK if frame["ok"] else theme.DANGER)

        self.sender_strip.set_bits(frame["sender"], colors=sender_colors)
        self.channel_strip.set_bits(frame["channel"], colors=channel_colors)
        self.receiver_strip.set_bits(frame["channel"], colors=receiver_colors)

        rule = "偶数" if self.mode == "even" else "奇数"
        flip_count = len(frame["flips"])
        if frame["ok"]:
            self.verdict.configure(text="校验通过", fg=theme.OK)
            if frame["missed"]:
                detail = f"实际翻转 {flip_count} 位，1 的个数仍为{rule}，属于漏检。"
                color = theme.WARN
            else:
                detail = f"整帧 1 的个数为{rule}，符合{MODE_NAMES[self.mode]}规则。"
                color = theme.MUTED
        else:
            self.verdict.configure(text="检测到 1 位错误", fg=theme.DANGER)
            if flip_count > 1:
                detail = (f"实际翻转 {flip_count} 位（奇数），奇偶性不符，"
                          f"接收方请求重传。")
            elif flip_count == 1:
                detail = "翻转 1 位改变了奇偶性，接收方请求重传。"
            else:
                detail = "校验位与数据位的奇偶性不一致。"
            color = theme.MUTED
        self.verdict_detail.configure(text=detail, fg=color)

    def _clear_results(self):
        self.frame_title.configure(text="当前帧：—")
        self.sender_strip.set_bits("00000000")
        self.channel_strip.set_bits("00000000")
        self.receiver_strip.set_bits("00000000")
        self.verdict.configure(text="—", fg=theme.FAINT)
        self.verdict_detail.configure(text="输入有效文本后显示接收方判决。", fg=theme.FAINT)

    def _refresh_stats(self):
        if not self.data:
            self.frame_chip.set(0, theme.ACCENT)
            self.flipped_chip.set(0, theme.WARN)
            self.detected_chip.set(0, theme.OK)
            self.missed_chip.set(0, theme.DANGER)
            return
        self.frame_chip.set(self.data["frame_count"], theme.ACCENT)
        self.flipped_chip.set(self.data["flipped_frames"], theme.WARN)
        self.detected_chip.set(self.data["detected_count"], theme.OK)
        self.missed_chip.set(self.data["missed_count"], theme.DANGER)

    def _update_status(self):
        if not self.data:
            return
        text = self.data["text"]
        shown = text if len(text) <= 18 else text[:18] + "…"
        flip_bits = sum(len(frame["flips"]) for frame in self.data["frames"])
        if flip_bits:
            tail = (f"注入 {self.data['flipped_frames']} 帧/{flip_bits} 位 · "
                    f"检出 {self.data['detected_count']} · "
                    f"漏检 {self.data['missed_count']}")
        else:
            tail = "信道无差错"
        self.app.set_status(
            f"ASCII 校验：{shown!r} · {self.data['frame_count']} 帧 · "
            f"{MODE_NAMES[self.mode]} · {tail}"
        )

    # ---- 错误注入 ---------------------------------------------------------
    def _toggle_bit(self):
        if not self.data or not self.data["frames"]:
            return
        frame_index = self._read_frame_index()
        bit_position = self._read_bit_position()
        self._suspend_select = True
        self.frame_var.set(str(frame_index + 1))
        self.bit_var.set(str(bit_position))
        self._suspend_select = False

        # 界面位序号 0 是最低位，对应帧字符串末尾的下标 7
        bit_index = 7 - bit_position
        key = (frame_index, bit_index)
        if key in self.flips:
            del self.flips[key]
        else:
            self.flips[key] = True
        self._rebuild_after_flip()

    def _restore(self):
        if not self.flips:
            return
        self.flips.clear()
        self._rebuild_after_flip()

    def _rebuild_after_flip(self):
        self.data = parity.transmit(self.entry.get(), self.mode, self.flips)
        self._refresh_table()
        self._refresh_current()
        self._refresh_stats()
        self._update_status()

    # ---- 选择控件 ---------------------------------------------------------
    def _on_frame_var(self, *_args):
        if self._suspend_select or not self.data or not self.data["frames"]:
            return
        try:
            value = int(self.frame_var.get())
        except (TypeError, ValueError):
            return
        if not 1 <= value <= self.data["frame_count"]:
            return
        self._frame_index = value - 1
        self._refresh_table()
        self._refresh_current()

    def _on_bit_var(self, *_args):
        if self._suspend_select or not self.data or not self.data["frames"]:
            return
        try:
            value = int(self.bit_var.get())
        except (TypeError, ValueError):
            return
        if 0 <= value <= 7:
            self._refresh_current()

    def _normalize_frame_spin(self):
        if not self.data:
            return
        self.frame_var.set(str(self._read_frame_index() + 1))

    def _normalize_bit_spin(self):
        self.bit_var.set(str(self._read_bit_position()))

    def _read_frame_index(self) -> int:
        try:
            value = int(self.frame_var.get())
        except (TypeError, ValueError):
            value = 1
        if not self.data or self.data["frame_count"] == 0:
            return 0
        return max(0, min(value - 1, self.data["frame_count"] - 1))

    def _read_bit_position(self) -> int:
        try:
            value = int(self.bit_var.get())
        except (TypeError, ValueError):
            value = 0
        return max(0, min(value, 7))

    @staticmethod
    def _char_display(ch: str) -> str:
        if ch == " ":
            return "空格"
        if ch.isprintable():
            return ch
        return f"\\x{ord(ch):02X}"

    def on_show(self):
        if self.data:
            self._update_status()
        else:
            self.app.set_status("ASCII 与奇偶校验：输入文本，查看 7 位编码与 1 位校验")
