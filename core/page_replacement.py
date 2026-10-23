"""页面置换算法：FIFO / LRU / OPT 的纯逻辑实现。

每一步返回物理块快照，供界面逐列绘制；不依赖 tkinter。
"""

import re

DEFAULT_REFERENCE = "7,0,1,2,0,3,0,4,2,3,0,3,2,1,2,0,1,7,0,1"


def parse_reference(text: str) -> list[int]:
    """解析逗号或空格分隔的页号序列，非法输入抛出 ValueError。"""
    if not isinstance(text, str):
        raise ValueError("参考串必须是文本")
    cleaned = text.strip().replace("，", ",")
    if not cleaned:
        raise ValueError("参考串不能为空")

    tokens = [token for token in re.split(r"[,\s]+", cleaned) if token]
    if not tokens:
        raise ValueError("参考串不能为空")

    pages = []
    for token in tokens:
        try:
            page = int(token)
        except ValueError:
            raise ValueError(f"“{token}”不是合法的页号") from None
        if page < 0:
            raise ValueError(f"页号不能为负数：{page}")
        pages.append(page)
    return pages


def _check_args(refs, frame_count: int) -> list[int]:
    if not isinstance(frame_count, int) or isinstance(frame_count, bool) or frame_count < 1:
        raise ValueError("物理块数必须是大于 0 的整数")
    pages = list(refs)
    if not pages:
        raise ValueError("参考串不能为空")
    return pages


def _step(index: int, page: int, frames: list, fault: bool, victim,
          hits: int, faults: int) -> dict:
    """生成单步快照；frames 必须复制，避免后续写入影响历史步骤。"""
    return {
        "index": index,
        "page": page,
        "frames": list(frames),
        "fault": fault,
        "victim": victim,
        "hits": hits,
        "faults": faults,
    }


def _summarize(steps: list[dict], faults: int) -> dict:
    total = len(steps)
    hits = total - faults
    return {
        "steps": steps,
        "faults": faults,
        "hits": hits,
        "fault_rate": faults / total,
        "hit_rate": hits / total,
    }


def fifo(refs, frame_count: int) -> dict:
    """先进先出：按装入物理块的先后顺序淘汰。"""
    pages = _check_args(refs, frame_count)
    frames = [None] * frame_count
    load_order = []                     # 已占用帧的下标，按装入先后排列
    steps = []
    hits = faults = 0

    for index, page in enumerate(pages):
        fault = page not in frames
        victim = None
        if fault:
            faults += 1
            empty = next((slot for slot, value in enumerate(frames) if value is None), None)
            if empty is not None:
                frames[empty] = page
                load_order.append(empty)
            else:
                slot = load_order.pop(0)
                victim = frames[slot]
                frames[slot] = page
                load_order.append(slot)
        else:
            hits += 1
        steps.append(_step(index, page, frames, fault, victim, hits, faults))

    return _summarize(steps, faults)


def lru(refs, frame_count: int) -> dict:
    """最近最少使用：淘汰最长时间没有被访问的页。"""
    pages = _check_args(refs, frame_count)
    frames = [None] * frame_count
    last_used = {}                      # 页号 -> 最近一次访问的下标
    steps = []
    hits = faults = 0

    for index, page in enumerate(pages):
        fault = page not in frames
        victim = None
        if fault:
            faults += 1
            empty = next((slot for slot, value in enumerate(frames) if value is None), None)
            if empty is not None:
                frames[empty] = page
            else:
                victim = min((value for value in frames if value is not None),
                             key=lambda value: last_used[value])
                slot = frames.index(victim)
                frames[slot] = page
                del last_used[victim]
        else:
            hits += 1
        last_used[page] = index
        steps.append(_step(index, page, frames, fault, victim, hits, faults))

    return _summarize(steps, faults)


def _farthest_slot(frames: list, pages: list[int], current: int) -> int:
    """返回未来最长时间不再使用的帧下标；未来不出现视为无穷远。"""
    best_slot = 0
    best_distance = -1
    for slot, value in enumerate(frames):
        if value is None:
            return slot
        future = next((i for i in range(current + 1, len(pages)) if pages[i] == value),
                      None)
        distance = len(pages) + 1 if future is None else future
        if distance > best_distance:
            best_distance = distance
            best_slot = slot
    return best_slot


def opt(refs, frame_count: int) -> dict:
    """最佳置换：淘汰未来最长时间不再使用的页（需要预知访问序列）。"""
    pages = _check_args(refs, frame_count)
    frames = [None] * frame_count
    steps = []
    hits = faults = 0

    for index, page in enumerate(pages):
        fault = page not in frames
        victim = None
        if fault:
            faults += 1
            empty = next((slot for slot, value in enumerate(frames) if value is None), None)
            if empty is not None:
                frames[empty] = page
            else:
                slot = _farthest_slot(frames, pages, index)
                victim = frames[slot]
                frames[slot] = page
        else:
            hits += 1
        steps.append(_step(index, page, frames, fault, victim, hits, faults))

    return _summarize(steps, faults)


ALGORITHMS = {"fifo": fifo, "lru": lru, "opt": opt}


def simulate(refs, frame_count: int, algorithm: str) -> dict:
    """按算法名称分发到具体实现。"""
    key = str(algorithm).lower()
    if key not in ALGORITHMS:
        raise ValueError(f"未知的置换算法：{algorithm}")
    return ALGORITHMS[key](refs, frame_count)


if __name__ == "__main__":
    default_pages = parse_reference(DEFAULT_REFERENCE)
    assert len(default_pages) == 20
    assert fifo(default_pages, 3)["faults"] == 15
    assert lru(default_pages, 3)["faults"] == 12
    assert opt(default_pages, 3)["faults"] == 9

    # 单块边界：所有访问都必须换入，页号交替时全部缺页
    one_frame = parse_reference("1 2 1 2")
    assert fifo(one_frame, 1)["faults"] == 4
    assert lru(one_frame, 1)["faults"] == 4
    assert opt(one_frame, 1)["faults"] == 4

    # 物理块多于参考串：多余块保持空
    for algorithm in (fifo, lru, opt):
        wide = algorithm([1, 2], 4)
        assert wide["faults"] == 2
        assert wide["steps"][-1]["frames"] == [1, 2, None, None]

        # 重复页：只有第一次缺页
        repeated = algorithm([3, 3, 3], 2)
        assert repeated["faults"] == 1 and repeated["hits"] == 2

        # 空参考串与非法块数都要拒绝
        for bad_refs in ([], ()):
            try:
                algorithm(bad_refs, 3)
            except ValueError:
                pass
            else:
                raise AssertionError("空参考串未被拒绝")

    # 手工核对序列：1,2,3,4,1,2,5,1,2,3,4,5，3 块
    check_pages = parse_reference("1,2,3,4,1,2,5,1,2,3,4,5")
    assert fifo(check_pages, 3)["faults"] == 9
    assert lru(check_pages, 3)["faults"] == 10
    assert opt(check_pages, 3)["faults"] == 7

    for bad in ("", "  ", "1,a", "1;2", "-1,2"):
        try:
            parse_reference(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"非法输入未被拒绝：{bad!r}")

    for bad_count in (0, -1):
        for algorithm in (fifo, lru, opt):
            try:
                algorithm([1], bad_count)
            except ValueError:
                pass
            else:
                raise AssertionError("非法物理块数未被拒绝")

    print("page_replacement self-check ok: FIFO 15, LRU 12, OPT 9")
