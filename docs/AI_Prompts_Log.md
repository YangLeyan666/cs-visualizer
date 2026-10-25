# AI 结对编程记录（AI_Prompts_Log）

> 记录本项目中使用大语言模型（Kimi / DeepSeek）进行 Vibe Coding 的**代表性提示词**、**AI 原始输出**与**人工介入修改**。
>
> 工具形态：Kimi Code CLI（可读写仓库、执行命令的编程智能体）
> 记录原则：只记录真实发生过的交互；AI 的错误原样保留，修复过程可复现。

---

## 0. 提示词方法论

经过前两轮试探，团队把有效提示词固定为五段式：

1. **角色**：明确 AI 的身份与经验（如"资深 Python GUI 开发者"）。
2. **上下文**：技术栈、目录结构、已有代码的约定（颜色、控件、命名）。
3. **具体需求**：输入、输出、交互、边界条件，逐条列出。
4. **约束**：可用库、文件范围、不得修改的文件、性能与尺寸限制。
5. **验收方式**：要求 AI 自己运行哪些命令、达到什么结果才算完成。

> 经验：**约束越具体，返工越少**。"做一个好看的可视化"会得到无法验收的代码；"窗口 1210×700、左侧导航 220 px、字号 9 pt、所有像素走 theme.s()"才能一次成型。

---

## 1. 案例一：主框架与设计系统

### 1.1 提示词（节选）

```text
你是资深 Python GUI 开发者。请在 E:/.../cs-visualizer 中搭建 Tkinter 桌面应用主框架：
- 暗色主题，左侧 220px 导航（6 个模块），右侧标题区 + 内容区 + 状态栏
- 提供 ui/theme.py（配色、字体、DPI 缩放）、ui/widgets.py（Card、Segmented、
  DataTable、BitStrip）、ui/base_view.py（ModuleView 基类）
- 所有像素尺寸必须走 theme.s()；字号用 pt
- 参照 ui/number_base_view.py 的写法实现「进制转换」模块
- 验收：python main.py 能启动，切换模块不报错，截图无裁切
```

### 1.2 AI 原始输出（关键片段）

AI 生成了 `Segmented` 组件，用列表保存选项：

```python
class Segmented(tk.Frame):
    def __init__(self, master, options, ...):
        self._options = list(options)      # ← 问题所在
        ...
        self._buttons[key] = btn
```

运行后立即报错：

```text
File "ui/number_base_view.py", line 53, in _build_input
    self.source_seg.pack(side="left")
TypeError: 'list' object is not callable
```

### 1.3 人工定位

`tkinter.Frame` 内部有一个同名方法 `_options()`，被实例属性覆盖；`pack()` 内部调用 `self._options(cnf, kw)` 时实际调用了列表，于是报"list object is not callable"。

这不是业务代码错误，而是 **AI 对 Tkinter 内部 API 的"合理想象"**——命名看起来无害，却与基类私有方法冲突。

### 1.4 修复

```python
self._choices = list(options)   # 改名，避开 tkinter 内部方法
```

同时把同类风险检查了一遍：`_value`、`_buttons` 与 tkinter 无冲突，保留。

### 1.5 结果

应用正常启动。该问题被记入团队规范：**继承 tkinter 控件时，自定义属性一律加业务前缀或避开下划线开头的名字**。

---

## 2. 案例二：补码加减法与 DPI 布局

### 2.1 提示词（节选）

```text
实现「8 位补码加减法」模块，要求：
- core/twos_complement.py 提供 to_bits / from_bits / add_bits / analyze
- 逐位进位链：每列显示 A、B、进位输入、本位和、进位输出
- 溢出判据同时给出"同号相加结果异号"和"Cn-1 异或 Cn"
- 界面：三条 BitStrip + 进位行 + 8 行表格 + 溢出结论卡
- 必须处理 -128 取反溢出的特例，不能静默给出错误结果
- 验收：python -m core.twos_complement 自检通过；GUI 冒烟测试通过
```

### 2.2 AI 原始输出（节选）

核心位运算正确，但界面首次运行时右侧内容被裁切：

```text
窗口 rect: 1266×871，屏幕 1280×800
右侧「计算过程」卡片只露出前两列
```

AI 的第一版按 `1240×800` 设计，并假设"窗口像素 = 设计像素"。

### 2.3 人工定位

用三行命令确认了真实环境：

```text
SM_CXSCREEN 1280  SM_CYSCREEN 800        # 逻辑分辨率
Tk scaling 2.664  fpixels 191.8          # 实际 192 DPI（200% 缩放）
DPI-aware 窗口: 2560×1600 物理像素
```

结论：屏幕是 **2560×1600 @ 200%**。字体按 pt 自动放大 2 倍，但 `geometry`、`padx`、Canvas 尺寸仍是物理像素，导致"字大、容器小"。

### 2.4 修复

在 `ui/theme.py` 增加统一缩放：

```python
SCALE = 1.0
def init_scale(root):
    global SCALE
    SCALE = max(1.0, round(root.winfo_fpixels("1i") / 96.0, 2))

def s(value: float) -> int:
    return int(round(value * SCALE))
```

所有窗口尺寸、内边距、Canvas 格子、表格间距改为 `theme.s(...)`；窗口改为 1210×700 设计稿，在 200% 下实际 2420×1400。

### 2.5 结果

六个模块在同一套缩放下截图无裁切。该修复也解释了此前"表格列宽异常""按钮被挤出卡片"等一系列现象。

> **教训**：涉及界面尺寸时，必须让 AI 先报告 `winfo_screenwidth()`、`tk scaling`、`winfo_fpixels('1i')`，再动手写布局。

---

## 3. 案例三：排序动画的播放生命周期

### 3.1 提示词（节选）

```text
实现排序算法可视化模块：
- core/sorting.py：冒泡/选择/插入/快速排序，均写成生成器，每步 yield 快照
  {array, compare, swap, pivot, sorted, line, comparisons, swaps, message}
- 快照必须是副本，不能污染历史帧
- 界面：Canvas 柱状图、播放/暂停/单步/重置、速度滑块、伪代码高亮
- 约束：切换算法、修改数据规模、关闭窗口时必须取消未执行的 after 回调
- 验收：逐帧检查颜色与统计一致；播放中销毁窗口不报错
```

### 3.2 AI 原始输出（关键片段）

第一版播放逻辑：

```python
def _play(self):
    self._after_id = self.after(int(self.delay * 1000), self._tick)

def _tick(self):
    self._step()
    self._play()          # 无条件续播
```

单步与重置正常，但**关闭窗口后**仍会触发一次 `_tick`，抛出 `TclError: invalid command name`。

### 3.3 人工定位

`app.destroy()` 只销毁控件，已排队的 `after` 回调仍会执行；`_play()` 没有检查控件是否还存在，也没有在 `_reset()` 与算法切换时 `after_cancel`。

### 3.4 修复

```python
def _cancel_pending(self):
    if self._after_id is not None:
        self.after_cancel(self._after_id)
        self._after_id = None

def _tick(self):
    self._after_id = None
    if not self.winfo_exists():
        return
    self._step()
    if self.playing:
        self._play()
```

并在 `_reset`、`_on_algorithm_change`、`_on_size_change` 与窗口关闭时调用 `_cancel_pending()`。

### 3.5 结果

自检输出 `DESTROY CANCEL OK`；播放中直接关窗无异常。该模式后来被复用到页面置换的自动播放。

---

## 4. 案例四：AI 自检断言与实现不一致（页面置换）

### 4.1 提示词（节选）

```text
实现 FIFO / LRU / OPT 页面置换，默认参考串 7,0,1,2,0,3,0,4,2,3,0,3,2,1,2,0,1,7,0,1，
3 个物理块。自检中断言 FIFO 缺页 15、LRU 12、OPT 9。
如果实现结果与断言不同，先用纸笔核对，不要修改断言去迁就实现。
```

### 4.2 AI 输出与人工核对

AI 首轮自检直接通过。人工又用第二条参考串复核：

```text
1,2,3,4,1,2,5,1,2,3,4,5（3 块）
FIFO 9 / LRU 10 / OPT 7
```

与纸笔计算一致，说明断言不是"为了让测试变绿而凑出来的"。

### 4.3 说明

这一条不是"AI 出错"，而是**防止 AI 迎合测试**的提示词设计：明确要求"先核对、不许改断言"，避免出现"测试通过但算法错误"的假阳性。

---

## 5. 其他被修正的 AI 低级错误

| 现象 | 原因 | 修复 |
|---|---|---|
| `BitStrip.__init__() got an unexpected keyword argument 'group'` | AI 调用时加了参数，但构造函数没定义 | 构造函数补 `group` 参数并保存默认值 |
| 左侧卡片被撑到 775 px，右侧表格被挤出窗口 | Canvas 默认请求宽度 378 px，AI 未显式设置 `width=1` | Canvas 一律 `width=1` + `fill` + `<Configure>` 重绘 |
| 长提示文字单行 755 px，卡片被撑宽 | `tk.Label` 无 `wraplength` | 统一 `hint(..., wrap=...)`，长文本自动换行 |
| 表格 6 列请求 846 px | 列宽按字符数设置过大 | 列宽压缩到合计 ≤ 40 字符，并统一 `padx=theme.s(6)` |
| RR 时间片结束后新到达进程入队顺序错误 | AI 先入队被抢占进程 | 改为"新到达先入队，被抢占进程再入队尾" |

---

## 6. 提示词效果统计

| 模块 | 主要提示词轮次 | 首轮可运行 | 人工修复点 |
|---|---:|---|---|
| 主框架 + 进制转换 | 6 | 否 | `_options` 命名冲突、BitStrip 参数、DPI 缩放 |
| 补码加减 | 3 | 是 | 布局压缩、`-128` 取反特例说明 |
| ASCII 奇偶校验 | 3 | 是 | 位序编号换算、长文本滚动 |
| 排序可视化 | 4 | 是 | after 生命周期、窄柱文字抽稀 |
| 进程调度 | 3 | 是 | RR 入队顺序、甘特图缩放下限 |
| 页面置换 | 3 | 是 | 列宽自适应、淘汰标记在窄格下的省略 |

**结论**：AI 能快速产出结构完整、可运行的代码，但**边界条件、框架内部 API、真实运行环境（DPI、窗口尺寸）**仍必须由人验证。团队的审查重点固定为三处：启动即崩的命名冲突、极端输入的算法边界、动画与窗口的生命周期。

---

## 7. 可复用的提示词模板

```text
你是<角色>。项目位于<路径>，技术栈<...>，已有约定<主题/控件/命名>。
需求：
1. <功能点，含输入输出>
2. <交互细节>
3. <边界条件>
约束：
- 只修改<文件清单>，不引入第三方库
- 所有像素走 theme.s()，字号用 theme 常量
- 长文本 wraplength，Canvas width=1
验收：
- 运行<命令>，输出<预期>
- 若结果与断言不符，先核对算法，不得修改断言迁就实现
完成后报告：改动文件、函数清单、验证输出、已知限制。
```
