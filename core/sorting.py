"""排序算法逐步过程（与界面无关，可单独运行自检）。

四种排序都实现为生成器：每次 yield 得到一帧可供界面绘制的状态快照。
"""

PSEUDOCODE = {
    "bubble": [
        "for i in range(n - 1):",
        "    swapped = False",
        "    for j in range(n - 1 - i):",
        "        if arr[j] > arr[j + 1]:",
        "            swap(arr[j], arr[j + 1])",
        "            swapped = True",
        "    if not swapped: break",
        "return arr",
    ],
    "selection": [
        "for i in range(n - 1):",
        "    min_idx = i",
        "    for j in range(i + 1, n):",
        "        if arr[j] < arr[min_idx]:",
        "            min_idx = j",
        "    swap(arr[i], arr[min_idx])",
        "return arr",
    ],
    "insertion": [
        "for i in range(1, n):",
        "    j = i",
        "    while j > 0 and arr[j - 1] > arr[j]:",
        "        swap(arr[j - 1], arr[j])",
        "        j -= 1",
        "    # 前 i + 1 个元素已有序",
        "return arr",
    ],
    "quick": [
        "def quick_sort(lo, hi):",
        "    if lo >= hi: return",
        "    pivot = arr[hi]",
        "    i = lo",
        "    for j in range(lo, hi):",
        "        if arr[j] < pivot:",
        "            swap(arr[i], arr[j])",
        "            i += 1",
        "    swap(arr[i], arr[hi])",
        "    quick_sort(lo, i - 1)",
        "    quick_sort(i + 1, hi)",
        "return arr",
    ],
}


def _snapshot(array, *, compare=None, swap=None, pivot=None, sorted_indices=(),
              line=1, comparisons=0, swaps=0, message=""):
    """生成一帧状态：列表和集合都复制，避免后续修改影响已保存的帧。"""
    return {
        "array": list(array),
        "compare": list(compare) if compare is not None else None,
        "swap": list(swap) if swap is not None else None,
        "pivot": pivot,
        "sorted": set(sorted_indices),
        "line": line,
        "comparisons": comparisons,
        "swaps": swaps,
        "message": message,
    }


def bubble_steps(arr):
    """冒泡排序：每轮把未排序区间的最大值推到末尾。"""
    data = list(arr)
    n = len(data)
    comparisons = swaps = 0
    placed = set()
    final_line = len(PSEUDOCODE["bubble"])

    yield _snapshot(data, line=1, message=f"开始冒泡排序：共 {n} 个元素")
    if n <= 1:
        yield _snapshot(data, sorted_indices=range(n), line=final_line,
                        comparisons=comparisons, swaps=swaps, message="排序完成")
        return

    for i in range(n - 1):
        swapped = False
        for j in range(n - 1 - i):
            comparisons += 1
            yield _snapshot(
                data, compare=(j, j + 1), sorted_indices=placed, line=4,
                comparisons=comparisons, swaps=swaps,
                message=f"比较 arr[{j}]={data[j]} 与 arr[{j + 1}]={data[j + 1]}",
            )
            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
                swaps += 1
                swapped = True
                yield _snapshot(
                    data, swap=(j, j + 1), sorted_indices=placed, line=5,
                    comparisons=comparisons, swaps=swaps,
                    message=f"左侧更大，交换 arr[{j}] 与 arr[{j + 1}]",
                )

        placed.add(n - 1 - i)
        yield _snapshot(
            data, sorted_indices=placed, line=7,
            comparisons=comparisons, swaps=swaps,
            message=f"第 {i + 1} 轮结束，下标 {n - 1 - i} 已就位",
        )
        if not swapped:
            placed.update(range(n - 1 - i))
            yield _snapshot(
                data, sorted_indices=placed, line=7,
                comparisons=comparisons, swaps=swaps,
                message="本轮没有发生交换，数组已经有序，提前结束",
            )
            break

    yield _snapshot(data, sorted_indices=range(n), line=final_line,
                    comparisons=comparisons, swaps=swaps, message="排序完成")


def selection_steps(arr):
    """选择排序：每轮从剩余区间挑出最小值放到区间首部。"""
    data = list(arr)
    n = len(data)
    comparisons = swaps = 0
    placed = set()
    final_line = len(PSEUDOCODE["selection"])

    yield _snapshot(data, line=1, message=f"开始选择排序：共 {n} 个元素")
    if n <= 1:
        yield _snapshot(data, sorted_indices=range(n), line=final_line,
                        comparisons=comparisons, swaps=swaps, message="排序完成")
        return

    for i in range(n - 1):
        min_idx = i
        yield _snapshot(
            data, sorted_indices=placed, line=2,
            comparisons=comparisons, swaps=swaps,
            message=f"第 {i + 1} 轮：在区间 [{i}, {n - 1}] 中找最小值",
        )
        for j in range(i + 1, n):
            comparisons += 1
            yield _snapshot(
                data, compare=(min_idx, j), sorted_indices=placed, line=4,
                comparisons=comparisons, swaps=swaps,
                message=f"比较 arr[{j}]={data[j]} 与当前最小值 arr[{min_idx}]={data[min_idx]}",
            )
            if data[j] < data[min_idx]:
                yield _snapshot(
                    data, compare=(min_idx, j), sorted_indices=placed, line=5,
                    comparisons=comparisons, swaps=swaps,
                    message=f"发现更小值，最小值下标更新为 {j}",
                )
                min_idx = j

        smallest = data[min_idx]
        if min_idx != i:
            data[i], data[min_idx] = data[min_idx], data[i]
            swaps += 1
            placed.add(i)
            yield _snapshot(
                data, swap=(i, min_idx), sorted_indices=placed, line=6,
                comparisons=comparisons, swaps=swaps,
                message=f"最小值 {smallest} 放到下标 {i}",
            )
        else:
            placed.add(i)
            yield _snapshot(
                data, sorted_indices=placed, line=6,
                comparisons=comparisons, swaps=swaps,
                message=f"最小值已在原位，下标 {i} 就位",
            )

    placed.add(n - 1)
    yield _snapshot(data, sorted_indices=placed, line=final_line,
                    comparisons=comparisons, swaps=swaps, message="排序完成")


def insertion_steps(arr):
    """插入排序：把新元素经相邻交换逐步移到有序前缀中的正确位置。"""
    data = list(arr)
    n = len(data)
    comparisons = swaps = 0
    placed = set()
    final_line = len(PSEUDOCODE["insertion"])

    yield _snapshot(data, line=1, message=f"开始插入排序：共 {n} 个元素")
    if n <= 1:
        yield _snapshot(data, sorted_indices=range(n), line=final_line,
                        comparisons=comparisons, swaps=swaps, message="排序完成")
        return

    for i in range(1, n):
        j = i
        yield _snapshot(
            data, sorted_indices=placed, line=2,
            comparisons=comparisons, swaps=swaps,
            message=f"取出下标 {i} 的元素，向前插入",
        )
        while j > 0:
            comparisons += 1
            yield _snapshot(
                data, compare=(j - 1, j), sorted_indices=placed, line=3,
                comparisons=comparisons, swaps=swaps,
                message=f"比较 arr[{j - 1}]={data[j - 1]} 与 arr[{j}]={data[j]}",
            )
            if data[j - 1] <= data[j]:
                break
            data[j - 1], data[j] = data[j], data[j - 1]
            swaps += 1
            yield _snapshot(
                data, swap=(j - 1, j), sorted_indices=placed, line=4,
                comparisons=comparisons, swaps=swaps,
                message=f"左侧更大，交换 arr[{j - 1}] 与 arr[{j}]",
            )
            j -= 1

        placed = set(range(i + 1))
        yield _snapshot(
            data, sorted_indices=placed, line=6,
            comparisons=comparisons, swaps=swaps,
            message=f"前 {i + 1} 个元素已经有序",
        )

    yield _snapshot(data, sorted_indices=range(n), line=final_line,
                    comparisons=comparisons, swaps=swaps, message="排序完成")


def quick_steps(arr):
    """快速排序：Lomuto 划分，取区间末尾元素为基准。"""
    data = list(arr)
    n = len(data)
    comparisons = swaps = 0
    placed = set()
    final_line = len(PSEUDOCODE["quick"])

    def snapshot(**kwargs):
        return _snapshot(data, sorted_indices=placed, comparisons=comparisons,
                         swaps=swaps, **kwargs)

    yield snapshot(line=1, message=f"开始快速排序：共 {n} 个元素")
    if n == 0:
        yield snapshot(line=final_line, message="排序完成")
        return

    def sort(lo, hi):
        nonlocal comparisons, swaps

        if lo > hi:
            return
        if lo == hi:
            placed.add(lo)
            yield snapshot(line=2, message=f"子区间 [{lo}, {hi}] 只有一个元素，已就位")
            return

        pivot_value = data[hi]
        yield snapshot(line=3, pivot=hi,
                       message=f"选择 arr[{hi}]={pivot_value} 作为基准")
        i = lo
        yield snapshot(line=4, pivot=hi, message=f"左指针 i = {lo}，开始划分")

        for j in range(lo, hi):
            comparisons += 1
            yield snapshot(
                line=6, compare=(j, hi), pivot=hi,
                message=f"比较 arr[{j}]={data[j]} 与基准 {pivot_value}",
            )
            if data[j] < pivot_value:
                if i != j:
                    data[i], data[j] = data[j], data[i]
                    swaps += 1
                    yield snapshot(
                        line=7, swap=(i, j), pivot=hi,
                        message=f"小于基准，交换到左区间位置 {i}",
                    )
                i += 1

        if i != hi:
            data[i], data[hi] = data[hi], data[i]
            swaps += 1
        placed.add(i)
        yield snapshot(
            line=9, swap=(i, hi) if i != hi else None, pivot=i,
            message=f"基准归位到下标 {i}",
        )

        if lo <= i - 1:
            yield snapshot(line=10, message=f"递归排序左区间 [{lo}, {i - 1}]")
        yield from sort(lo, i - 1)
        if i + 1 <= hi:
            yield snapshot(line=11, message=f"递归排序右区间 [{i + 1}, {hi}]")
        yield from sort(i + 1, hi)

    yield from sort(0, n - 1)
    placed.update(range(n))
    yield snapshot(line=final_line, message="排序完成")


if __name__ == "__main__":
    generators = {
        "bubble": bubble_steps,
        "selection": selection_steps,
        "insertion": insertion_steps,
        "quick": quick_steps,
    }
    samples = [
        [5, 2, 9, 1, 7, 3],
        [12, 4, 9, 1, 15, 6, 3, 8],
        [3, 1, 2],
    ]

    for sample in samples:
        expected = sorted(sample)
        original = list(sample)
        for name, generate in generators.items():
            frames = list(generate(sample))
            assert sample == original, f"{name} 修改了输入列表"
            assert frames[0]["array"] == original, f"{name} 初始帧与输入不一致"
            assert frames[-1]["array"] == expected, f"{name} 排序结果错误"
            assert frames[-1]["message"] == "排序完成", f"{name} 最终帧说明错误"
            assert frames[-1]["sorted"] == set(range(len(sample))), f"{name} 最终帧未包含全部下标"
            assert frames[-1]["comparisons"] > 0, f"{name} 比较次数应为正"
            assert frames[-1]["swaps"] > 0, f"{name} 交换次数应为正"
            assert all(1 <= frame["line"] <= len(PSEUDOCODE[name]) for frame in frames), \
                f"{name} 伪代码行号越界"

    for size in (0, 1):
        sample = list(range(size))
        for name, generate in generators.items():
            frames = list(generate(sample))
            assert frames[-1]["array"] == sample, f"{name} 小数组结果错误"
            assert frames[-1]["sorted"] == set(range(size)), f"{name} 小数组下标错误"
            assert frames[-1]["message"] == "排序完成"

    print(f"排序自检通过：{len(samples)} 组数据 × 4 种算法")
