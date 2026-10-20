"""进程调度核心算法（纯逻辑，与界面无关）。

提供 FCFS、SJF、RR 三种调度策略，返回甘特图时间轴与各项指标。
"""

from collections import deque

IDLE = "空闲"


def _prepare(processes):
    """校验并规范化进程列表，非法数据统一抛出 ValueError。"""
    if not processes:
        raise ValueError("至少需要一个进程")

    prepared = []
    seen = set()
    for item in processes:
        try:
            pid = str(item["pid"]).strip()
            arrival = item["arrival"]
            burst = item["burst"]
        except (KeyError, TypeError) as exc:
            raise ValueError("进程数据必须包含 pid、arrival、burst") from exc

        if not pid:
            raise ValueError("进程名不能为空")
        if pid == IDLE:
            raise ValueError(f"进程名「{IDLE}」为保留名称")
        if pid in seen:
            raise ValueError(f"进程名 {pid} 重复")
        if isinstance(arrival, bool) or not isinstance(arrival, (int, float)):
            raise ValueError(f"{pid} 的到达时间必须是数字")
        if isinstance(burst, bool) or not isinstance(burst, (int, float)):
            raise ValueError(f"{pid} 的运行时间必须是数字")
        if arrival < 0:
            raise ValueError(f"{pid} 的到达时间不能为负")
        if burst <= 0:
            raise ValueError(f"{pid} 的运行时间必须大于 0")

        seen.add(pid)
        prepared.append({"pid": pid, "arrival": arrival, "burst": burst})

    if not prepared:
        raise ValueError("至少需要一个进程")
    return prepared


def _build_timeline(slices):
    """在运行片段之间补上空闲段，形成从 0 开始的完整时间轴。"""
    timeline = []
    cursor = 0
    for segment in slices:
        if segment["start"] > cursor:
            timeline.append({"pid": IDLE, "start": cursor, "end": segment["start"]})
        timeline.append(segment)
        cursor = segment["end"]
    return timeline


def _count_switches(timeline):
    """统计进程之间的切换次数；空闲段不视为上下文切换。"""
    switches = 0
    previous = None
    for segment in timeline:
        if segment["pid"] == IDLE:
            continue
        if previous is not None and segment["pid"] != previous:
            switches += 1
        previous = segment["pid"]
    return switches


def _summarise(processes, slices):
    """根据运行片段计算每进程指标与整体指标。"""
    timeline = _build_timeline(slices)

    finish = {}
    for segment in timeline:
        if segment["pid"] != IDLE:
            finish[segment["pid"]] = segment["end"]

    metrics = []
    for process in processes:
        turnaround = finish[process["pid"]] - process["arrival"]
        metrics.append({
            "pid": process["pid"],
            "arrival": process["arrival"],
            "burst": process["burst"],
            "finish": finish[process["pid"]],
            "turnaround": turnaround,
            "waiting": turnaround - process["burst"],
        })

    count = len(metrics)
    total_time = timeline[-1]["end"] if timeline else 0
    busy_time = sum(
        segment["end"] - segment["start"]
        for segment in timeline
        if segment["pid"] != IDLE
    )

    return {
        "timeline": timeline,
        "metrics": metrics,
        "avg_waiting": sum(m["waiting"] for m in metrics) / count,
        "avg_turnaround": sum(m["turnaround"] for m in metrics) / count,
        "cpu_util": busy_time / total_time * 100 if total_time else 0.0,
        "context_switches": _count_switches(timeline),
    }


def fcfs(processes):
    """先来先服务：按到达时间顺序执行，非抢占。"""
    prepared = _prepare(processes)
    order = sorted(prepared, key=lambda p: (p["arrival"], p["pid"]))

    slices = []
    now = 0
    for process in order:
        start = max(now, process["arrival"])
        end = start + process["burst"]
        slices.append({"pid": process["pid"], "start": start, "end": end})
        now = end
    return _summarise(prepared, slices)


def sjf(processes):
    """短作业优先：只在已到达进程中选择运行时间最短者，非抢占。"""
    prepared = _prepare(processes)
    pending = sorted(prepared, key=lambda p: (p["arrival"], p["pid"]))

    slices = []
    now = 0
    while pending:
        ready = [p for p in pending if p["arrival"] <= now]
        if not ready:
            now = min(p["arrival"] for p in pending)
            continue

        chosen = min(ready, key=lambda p: (p["burst"], p["arrival"], p["pid"]))
        pending.remove(chosen)
        end = now + chosen["burst"]
        slices.append({"pid": chosen["pid"], "start": now, "end": end})
        now = end
    return _summarise(prepared, slices)


def rr(processes, quantum):
    """时间片轮转：就绪队列按到达顺序，新到达进程先于被抢占进程入队。"""
    if isinstance(quantum, bool) or not isinstance(quantum, (int, float)) or quantum <= 0:
        raise ValueError("时间片必须是大于 0 的数")

    prepared = _prepare(processes)
    order = sorted(prepared, key=lambda p: (p["arrival"], p["pid"]))
    remaining = {p["pid"]: p["burst"] for p in prepared}

    ready = deque()
    slices = []
    index = 0
    now = 0

    def enqueue_arrived(limit):
        nonlocal index
        while index < len(order) and order[index]["arrival"] <= limit:
            ready.append(order[index])
            index += 1

    enqueue_arrived(0)
    while ready or index < len(order):
        if not ready:
            now = max(now, order[index]["arrival"])
            enqueue_arrived(now)
            continue

        process = ready.popleft()
        pid = process["pid"]
        run_time = min(quantum, remaining[pid])
        start = now
        end = start + run_time
        slices.append({"pid": pid, "start": start, "end": end})
        remaining[pid] -= run_time
        now = end

        enqueue_arrived(now)
        if remaining[pid] > 0:
            ready.append(process)

    return _summarise(prepared, slices)


if __name__ == "__main__":
    demo = [
        {"pid": "P1", "arrival": 0, "burst": 5},
        {"pid": "P2", "arrival": 1, "burst": 3},
        {"pid": "P3", "arrival": 2, "burst": 8},
        {"pid": "P4", "arrival": 4, "burst": 2},
    ]

    fcfs_result = fcfs(demo)
    sjf_result = sjf(demo)
    rr_result = rr(demo, 2)

    for name, data in (
        ("FCFS", fcfs_result),
        ("SJF", sjf_result),
        ("RR(时间片 2)", rr_result),
    ):
        print(f"{name}: 平均周转 {data['avg_turnaround']:.2f}，"
              f"平均等待 {data['avg_waiting']:.2f}，"
              f"CPU 利用率 {data['cpu_util']:.1f}%，"
              f"上下文切换 {data['context_switches']} 次")

    sequence = [(s["pid"], s["start"], s["end"]) for s in rr_result["timeline"]]
    print("RR(时间片 2) 时间轴: " + " → ".join(
        f"{pid}[{start},{end})" for pid, start, end in sequence))

    assert round(fcfs_result["avg_turnaround"], 2) == 10.0
    assert round(fcfs_result["avg_waiting"], 2) == 5.5
    assert round(sjf_result["avg_turnaround"], 2) == 8.25
    assert round(sjf_result["avg_waiting"], 2) == 3.75
    assert round(rr_result["avg_turnaround"], 2) == 11.5
    assert round(rr_result["avg_waiting"], 2) == 7.0
    assert rr_result["context_switches"] == 8
    assert sequence == [
        ("P1", 0, 2), ("P2", 2, 4), ("P3", 4, 6),
        ("P1", 6, 8), ("P4", 8, 10), ("P2", 10, 11),
        ("P3", 11, 13), ("P1", 13, 14), ("P3", 14, 16),
        ("P3", 16, 18),
    ]

    idle_result = fcfs([
        {"pid": "P1", "arrival": 2, "burst": 1},
        {"pid": "P2", "arrival": 5, "burst": 2},
    ])
    idle_segments = [s for s in idle_result["timeline"] if s["pid"] == IDLE]
    print("空闲段示例:", idle_segments)
    assert idle_segments == [
        {"pid": IDLE, "start": 0, "end": 2},
        {"pid": IDLE, "start": 3, "end": 5},
    ]
    assert round(idle_result["cpu_util"], 2) == 42.86

    # 手工核对：P1 0/3、P2 1/1，FCFS 与 SJF 都应得到平均周转 3、平均等待 1
    small = [
        {"pid": "P1", "arrival": 0, "burst": 3},
        {"pid": "P2", "arrival": 1, "burst": 1},
    ]
    for name, data in (("FCFS", fcfs(small)), ("SJF", sjf(small))):
        print(f"小数据 {name}: 平均周转 {data['avg_turnaround']:.2f}，"
              f"平均等待 {data['avg_waiting']:.2f}")
        assert round(data["avg_turnaround"], 2) == 3.0
        assert round(data["avg_waiting"], 2) == 1.0

    # SJF 与 FCFS 的差异：P2、P3 同时到达，SJF 先执行更短的 P3
    compare = [
        {"pid": "P1", "arrival": 0, "burst": 1},
        {"pid": "P2", "arrival": 1, "burst": 5},
        {"pid": "P3", "arrival": 1, "burst": 2},
    ]
    assert fcfs(compare)["timeline"] == [
        {"pid": "P1", "start": 0, "end": 1},
        {"pid": "P2", "start": 1, "end": 6},
        {"pid": "P3", "start": 6, "end": 8},
    ]
    assert sjf(compare)["timeline"] == [
        {"pid": "P1", "start": 0, "end": 1},
        {"pid": "P3", "start": 1, "end": 3},
        {"pid": "P2", "start": 3, "end": 8},
    ]

    invalid_cases = (
        [{"pid": "P1", "arrival": -1, "burst": 3}],
        [{"pid": "P1", "arrival": 0, "burst": 0}],
        [{"pid": IDLE, "arrival": 0, "burst": 1}],
        [],
    )
    for case in invalid_cases:
        try:
            fcfs(case)
        except ValueError as exc:
            print(f"非法输入已拒绝: {exc}")
        else:
            raise AssertionError("非法输入未被拒绝")

    try:
        rr(demo, 0)
    except ValueError as exc:
        print(f"非法时间片已拒绝: {exc}")
    else:
        raise AssertionError("非法时间片未被拒绝")

    print("自检通过")
