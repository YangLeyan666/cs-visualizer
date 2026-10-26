"""ASCII 与奇偶校验核心算法（与界面无关，可单独测试）。

8 位帧的位序：最高位（字符串下标 0）是校验位，低 7 位是 ASCII 数据位。
"""

VALID_MODES = ("even", "odd")


def _check_mode(mode: str) -> None:
    if mode not in VALID_MODES:
        raise ValueError("校验方式只能是 'even' 或 'odd'")


def _check_bits(bits: str, width: int) -> None:
    if (not isinstance(bits, str) or len(bits) != width
            or any(bit not in "01" for bit in bits)):
        raise ValueError(f"需要 {width} 位二进制串")


def ascii_bits(ch: str) -> str:
    """返回单个 ASCII 字符的 7 位编码。"""
    if not isinstance(ch, str) or len(ch) != 1:
        raise ValueError("只能编码单个字符")
    code = ord(ch)
    if code > 0x7F:
        raise ValueError(f"字符 {ch!r} 不是 ASCII 字符（编码 {code}）")
    return f"{code:07b}"


def parity_bit(bits7: str, mode: str = "even") -> str:
    """按偶校验或奇校验计算 1 位校验位。"""
    _check_mode(mode)
    _check_bits(bits7, 7)
    ones = bits7.count("1")
    if mode == "even":
        return str(ones % 2)
    return str((ones + 1) % 2)


def encode(ch: str, mode: str = "even") -> str:
    """把字符编码为 8 位帧：校验位放在最高位。"""
    _check_mode(mode)
    data = ascii_bits(ch)
    return parity_bit(data, mode) + data


def check(frame: str, mode: str = "even") -> bool:
    """接收方校验整帧的奇偶性是否满足约定。"""
    _check_mode(mode)
    _check_bits(frame, 8)
    ones = frame.count("1")
    return ones % 2 == 0 if mode == "even" else ones % 2 == 1


def flip(bits: str, index: int) -> str:
    """翻转字符串下标 index 处的二进制位。"""
    if not isinstance(bits, str) or not bits or any(bit not in "01" for bit in bits):
        raise ValueError("需要二进制串")
    if not isinstance(index, int) or not 0 <= index < len(bits):
        raise ValueError("位下标越界")
    flipped = "1" if bits[index] == "0" else "0"
    return bits[:index] + flipped + bits[index + 1:]


def transmit(text: str, mode: str = "even", flips=None) -> dict:
    """模拟发送全过程。

    flips: {(字符下标, 帧字符串位下标): True}，位下标 0 表示最高位。
    返回每帧的发送帧、信道帧、接收帧与检出/漏检标记，以及汇总统计。
    """
    _check_mode(mode)
    if not isinstance(text, str):
        raise ValueError("文本必须是字符串")
    flips = flips or {}
    if not isinstance(flips, dict):
        raise ValueError("flips 必须是字典")

    per_char = {}
    for key, value in flips.items():
        if not value:
            continue
        if (not isinstance(key, tuple) or len(key) != 2
                or not isinstance(key[0], int) or not isinstance(key[1], int)):
            raise ValueError("flips 的键应为 (字符下标, 位下标)")
        char_index, bit_index = key
        if not 0 <= char_index < len(text):
            raise ValueError("flips 中的字符下标越界")
        if not 0 <= bit_index < 8:
            raise ValueError("flips 中的位下标越界")
        per_char.setdefault(char_index, []).append(bit_index)

    frames = []
    for index, ch in enumerate(text):
        data = ascii_bits(ch)
        parity = parity_bit(data, mode)
        sender = parity + data
        channel = sender
        for bit_index in per_char.get(index, ()):
            channel = flip(channel, bit_index)
        ok = check(channel, mode)
        changed = channel != sender
        frames.append({
            "char": ch,
            "code": ord(ch),
            "ascii": data,
            "parity": parity,
            "sender": sender,
            "channel": channel,
            "receiver": channel,
            "flips": sorted(per_char.get(index, ())),
            "has_error": changed,
            "ok": ok,
            "detected": changed and not ok,
            "missed": changed and ok,
        })

    return {
        "text": text,
        "mode": mode,
        "frames": frames,
        "frame_count": len(frames),
        "flipped_frames": sum(1 for frame in frames if frame["has_error"]),
        "detected_count": sum(1 for frame in frames if frame["detected"]),
        "missed_count": sum(1 for frame in frames if frame["missed"]),
    }


if __name__ == "__main__":
    assert ascii_bits("A") == "1000001"
    assert encode("A", "even") == "01000001"
    assert encode("A", "odd") == "11000001"

    # 单比特错误在两种校验方式下都一定被检出
    for parity_mode in VALID_MODES:
        base_frame = encode("A", parity_mode)
        for bit_index in range(8):
            assert not check(flip(base_frame, bit_index), parity_mode)

    # 奇校验帧翻转最高位后不再满足奇校验
    assert flip(encode("A", "odd"), 0) == "01000001"

    # 双比特错误改变 1 的个数为偶数个，奇偶性不变，必然漏检
    double_error = flip(flip(encode("A", "even"), 0), 7)
    assert check(double_error, "even")

    result = transmit("Hello", "even", {(0, 0): True})
    assert result["flipped_frames"] == 1
    assert result["detected_count"] == 1
    assert result["missed_count"] == 0
    assert result["frames"][0]["receiver"] == result["frames"][0]["channel"]

    result = transmit("Hello", "even", {(0, 0): True, (0, 7): True})
    assert result["flipped_frames"] == 1
    assert result["detected_count"] == 0
    assert result["missed_count"] == 1

    for bad in ("中", "", "AB"):
        try:
            ascii_bits(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"{bad!r} 应抛出 ValueError")

    print("parity self-check passed")
