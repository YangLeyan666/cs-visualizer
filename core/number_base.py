"""进制转换核心算法（与界面无关，可单独测试）。

提供"除基取余 / 乘基取整"的逐步过程，供界面展示。
"""

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def to_base(value: int, base: int) -> str:
    """把非负整数转换为任意进制字符串。"""
    if not 2 <= base <= 36:
        raise ValueError("进制必须在 2~36 之间")
    if value < 0:
        raise ValueError("暂不支持负数，请使用补码模块")
    if value == 0:
        return "0"
    digits = []
    while value:
        value, rem = divmod(value, base)
        digits.append(DIGITS[rem])
    return "".join(reversed(digits))


def parse_number(text: str, base: int) -> int:
    """解析指定进制的字符串，非法字符抛出 ValueError。"""
    text = text.strip().upper().replace(" ", "").replace("_", "")
    if not text:
        raise ValueError("请输入数值")
    if text.startswith("-"):
        raise ValueError("请输入非负整数")
    value = 0
    for ch in text:
        index = DIGITS.find(ch)
        if index < 0 or index >= base:
            raise ValueError(f"字符 {ch!r} 不是合法的 {base} 进制数字")
        value = value * base + index
    return value


def integer_steps(value: int, base: int) -> list[dict]:
    """返回整数部分的除法过程：被除数 / 除数 = 商 …… 余数。"""
    steps = []
    if value == 0:
        return [{"dividend": 0, "divisor": base, "quotient": 0,
                 "remainder": 0, "digit": "0"}]
    while value > 0:
        quotient, remainder = divmod(value, base)
        steps.append({
            "dividend": value,
            "divisor": base,
            "quotient": quotient,
            "remainder": remainder,
            "digit": DIGITS[remainder],
        })
        value = quotient
    return steps


def fraction_steps(frac: float, base: int, max_digits: int = 8) -> list[dict]:
    """返回小数部分的乘法过程：小数 × 基数 = 积，取整数位。"""
    steps = []
    for _ in range(max_digits):
        if frac <= 1e-12:
            break
        operand = frac
        product = frac * base
        int_part = int(product)
        frac = product - int_part
        steps.append({
            "operand": operand,
            "product": product,
            "digit": DIGITS[int_part],
            "remainder": frac,
        })
    return steps


def convert(text: str, from_base: int, to_base_value: int) -> dict:
    """完整转换：返回数值、目标串以及整数/小数步骤。"""
    raw = text.strip().upper().replace(" ", "").replace("_", "")
    if "." in raw:
        int_text, frac_text = raw.split(".", 1)
    else:
        int_text, frac_text = raw, ""

    int_value = parse_number(int_text or "0", from_base)
    frac_value = 0.0
    if frac_text:
        for i, ch in enumerate(frac_text, start=1):
            index = DIGITS.find(ch)
            if index < 0 or index >= from_base:
                raise ValueError(f"字符 {ch!r} 不是合法的 {from_base} 进制数字")
            frac_value += index / (from_base ** i)

    int_result = to_base(int_value, to_base_value)
    frac_digits = []
    steps = fraction_steps(frac_value, to_base_value)
    for step in steps:
        frac_digits.append(step["digit"])
    frac_result = "".join(frac_digits)
    result = int_result + ("." + frac_result if frac_result else "")

    return {
        "int_value": int_value,
        "fraction_value": frac_value,
        "result": result,
        "int_steps": integer_steps(int_value, to_base_value),
        "frac_steps": steps,
        "exact": frac_value == 0.0 or len(frac_digits) < 8,
    }


if __name__ == "__main__":
    assert to_base(2024, 2) == "11111101000"
    assert to_base(2024, 16) == "7E8"
    assert parse_number("7E8", 16) == 2024
    assert len(integer_steps(2024, 2)) == 11
    print(convert("2024", 10, 16)["result"], "ok")
