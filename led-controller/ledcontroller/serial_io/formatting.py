"""Pure-python helpers for the debug console (no Qt dependency, unit-testable)."""
import re

HEX, ASCII, HEX_ASCII = "hex", "ascii", "hex+ascii"


def _printable(b):
    if 32 <= b < 127:
        return chr(b)
    return "↵" if b == 10 else "."


def format_bytes(data, mode=HEX_ASCII, limit=48):
    """Format bytes for display.  Output is truncated to `limit` bytes."""
    shown = data[:limit]
    extra = len(data) - len(shown)
    hexs = " ".join(f"{b:02X}" for b in shown)
    asc = "".join(_printable(b) for b in shown)
    if mode == HEX:
        text = hexs
    elif mode == ASCII:
        text = asc
    else:
        text = f"{hexs}  |{asc}|"
    return text + (f"  … +{extra} B" if extra > 0 else "")


def describe_adalight(data):
    """Return a short description if `data` starts with an Adalight header."""
    if len(data) < 6 or data[:3] != b"Ada":
        return None
    hi, lo, chk = data[3], data[4], data[5]
    if chk != (hi ^ lo ^ 0x55):
        return "Adalight · bad checksum"
    return f"Adalight · {((hi << 8) | lo) + 1} LEDs"


def parse_hex(text):
    """'41 64 61', '0x41,0x64', '416461' -> bytes.  Raises ValueError."""
    cleaned = re.sub(r"0x|[\s,:\-]", "", text, flags=re.I)
    if not cleaned or len(cleaned) % 2 or not re.fullmatch(r"[0-9a-fA-F]+", cleaned):
        raise ValueError("Invalid hex string (expected pairs like 41 64 61)")
    return bytes.fromhex(cleaned)


def human_size(n):
    if n < 1024:
        return f"{n} B"
    if n < 1024 ** 2:
        return f"{n / 1024:.1f} KB"
    return f"{n / 1024 ** 2:.2f} MB"
