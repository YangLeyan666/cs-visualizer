"""补码加减法核心算法：位串转换、逐位相加与溢出判断。

只依赖标准库，不涉及界面，可单独运行自检。
"""


def signed_range(width: int = 8) -> tuple[int, int]:
    """返回 width 位补码能表示的十进制范围。"""
    if not isinstance(width, int) or isinstance(width, bool) or width < 1:
        raise ValueError("位宽必须是正整数")
    return -(1 << (width - 1)), (1 << (width - 1)) - 1


def to_bits(value: int, width: int = 8) -> str:
    """把十进制整数转换为 width 位补码位串。"""
    low, high = signed_range(width)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("数值必须是整数")
    if not low <= value <= high:
        raise ValueError(f"{value} 超出 {width} 位补码范围 {low} ~ {high}")
    if value < 0:
        value += 1 << width
    return format(value, f"0{width}b")


def from_bits(bits: str) -> int:
    """把补码位串转换为有符号十进制整数。"""
    if not isinstance(bits, str):
        raise ValueError("补码位串必须是字符串")
    bits = bits.strip()
    if not bits:
        raise ValueError("补码位串不能为空")
    if any(ch not in "01" for ch in bits):
        raise ValueError("补码位串只能包含 0 和 1")
    value = int(bits, 2)
    if bits[0] == "1":
        value -= 1 << len(bits)
    return value


def add_bits(a: str, b: str) -> tuple[str, list[dict]]:
    """逐列相加两个等长补码位串，返回结果位串和从低位到高位的步骤。"""
    a, b = str(a), str(b)
    if not a or not b:
        raise ValueError("位串不能为空")
    if len(a) != len(b):
        raise ValueError("两个位串长度必须相同")
    if any(ch not in "01" for ch in a) or any(ch not in "01" for ch in b):
        raise ValueError("位串只能包含 0 和 1")

    width = len(a)
    carry = 0
    result = []
    steps = []
    for position in range(width - 1, -1, -1):
        abit, bbit = int(a[position]), int(b[position])
        total = abit + bbit + carry
        sum_bit = total & 1
        carry_out = total >> 1
        steps.append({
            "index": width - 1 - position,
            "a": abit,
            "b": bbit,
            "carry_in": carry,
            "total": total,
            "sum": sum_bit,
            "carry_out": carry_out,
        })
        result.append(str(sum_bit))
        carry = carry_out
    return "".join(reversed(result)), steps


def _sign_name(sign: int) -> str:
    return "正" if sign == 0 else "负"


def _overflow_reason(a: int, b: int, op: str, width: int, low: int, high: int,
                     a_sign: int, b_sign: int, sum_sign: int,
                     carry_in_msb: int, carry_out: int, math_result: int,
                     in_range: bool, overflow: bool, negation_overflow: bool,
                     decimal_result: int) -> str:
    """生成结合当前数值的溢出判断说明。"""
    if negation_overflow:
        return (
            f"减数 B={b}，取反后得到 {-b}，超出 {width} 位补码范围；"
            f"符号位与进位判据不再适用。按模 {1 << width} 相加，8 位结果为 "
            f"{decimal_result}；数学结果 {math_result} "
            f"{'在' if in_range else '不在'} {low}~{high} 范围内，"
            f"{'故溢出。' if overflow else '故未溢出。'}"
        )

    if op == "-":
        prefix = "减法转为 A+(-B)；"
        b_text = f"-B={-b}"
    else:
        prefix = ""
        b_text = f"B={b}"

    relation = "同号" if a_sign == b_sign else "异号"
    if relation == "同号":
        if sum_sign != a_sign:
            sign_text = f"同号相加却得到{_sign_name(sum_sign)}号结果，符号位异常"
        else:
            sign_text = f"同号相加仍为{_sign_name(sum_sign)}号结果，符号位正常"
    else:
        sign_text = "两数异号，不具备同号溢出条件"

    carry_text = (
        f"Cn-1={carry_in_msb}、Cn={carry_out}，"
        f"异或为 {carry_in_msb ^ carry_out}"
    )
    range_text = (
        f"数学结果 {math_result} {'在' if in_range else '不在'} "
        f"{low}~{high} 范围内"
    )
    verdict = "故溢出。" if overflow else "故未溢出。"
    return (
        f"{prefix}A={a}（{_sign_name(a_sign)}）、{b_text}"
        f"（{_sign_name(b_sign)}）{relation}；{sign_text}；"
        f"{carry_text}；{range_text}，{verdict}"
    )


def analyze(a: int, b: int, op: str = "+", width: int = 8) -> dict:
    """分析一次补码加减法，返回位串、逐位步骤与溢出信息。"""
    low, high = signed_range(width)
    if op not in ("+", "-"):
        raise ValueError("运算只能是 '+' 或 '-'")
    if not isinstance(a, int) or not isinstance(b, int):
        raise ValueError("操作数必须是整数")
    if not low <= a <= high or not low <= b <= high:
        raise ValueError(f"操作数必须是 {width} 位补码范围内的整数（{low} ~ {high}）")

    a_bits = to_bits(a, width)
    b_original_bits = to_bits(b, width)

    negation_overflow = False
    if op == "-":
        if b == low:
            # 最小负数的相反数无法表示，其位型取模后仍是最小负数本身
            b_bits = b_original_bits
            negation_overflow = True
        else:
            b_bits = to_bits(-b, width)
    else:
        b_bits = b_original_bits

    result_bits, steps = add_bits(a_bits, b_bits)
    decimal_result = from_bits(result_bits)
    carry_in_msb = steps[-1]["carry_in"]
    carry_out = steps[-1]["carry_out"]

    math_result = a + b if op == "+" else a - b
    in_range = low <= math_result <= high

    a_sign = int(a_bits[0])
    b_sign = int(b_bits[0])
    sum_sign = int(result_bits[0])
    same_sign = a_sign == b_sign
    sign_overflow = same_sign and sum_sign != a_sign
    carry_overflow = carry_in_msb != carry_out
    overflow = sign_overflow or carry_overflow
    if negation_overflow:
        overflow = not in_range

    return {
        "a_bits": a_bits,
        "b_bits": b_bits,
        "b_original_bits": b_original_bits,
        "result_bits": result_bits,
        "decimal_result": decimal_result,
        "carry_out": carry_out,
        "overflow": overflow,
        "overflow_reason": _overflow_reason(
            a, b, op, width, low, high, a_sign, b_sign, sum_sign,
            carry_in_msb, carry_out, math_result, in_range, overflow,
            negation_overflow, decimal_result,
        ),
        "steps": steps,
        "in_range": in_range,
        "math_result": math_result,
        "carry_in_msb": carry_in_msb,
        "negation_overflow": negation_overflow,
    }


if __name__ == "__main__":
    assert analyze(127, 1)["overflow"] is True
    assert analyze(127, 1)["result_bits"] == "10000000"
    assert analyze(-128, 1, op="-")["overflow"] is True
    assert analyze(-128, 1, op="-")["decimal_result"] == 127
    assert analyze(5, 3, op="-")["decimal_result"] == 2
    assert analyze(-5, 3)["decimal_result"] == -2
    assert analyze(100, 100, op="-")["decimal_result"] == 0

    for value in (-128, -127, -1, 0, 1, 127):
        assert from_bits(to_bits(value)) == value

    assert to_bits(-128) == "10000000"
    assert to_bits(127) == "01111111"
    assert from_bits("11111111") == -1
    for bad in (-129, 128):
        try:
            to_bits(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("越界数值应抛出 ValueError")

    result, steps = add_bits("01111111", "00000001")
    assert result == "10000000"
    assert len(steps) == 8
    assert steps[0]["index"] == 0
    assert steps[-1]["carry_in"] == 1 and steps[-1]["carry_out"] == 0

    print("twos_complement self-check ok")
