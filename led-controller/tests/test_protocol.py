from ledcontroller.serial_io.formatting import (
    describe_adalight, format_bytes, human_size, parse_hex)
from ledcontroller.serial_io.protocol import encode


def test_adalight_header_and_payload():
    data = encode([(1, 2, 3)] * 3, "RGB", "adalight")
    assert data[:3] == b"Ada"
    assert data[3:6] == bytes((0, 2, 0 ^ 2 ^ 0x55))
    assert data[6:] == bytes((1, 2, 3) * 3)
    assert describe_adalight(data) == "Adalight · 3 LEDs"


def test_color_order_and_raw():
    assert encode([(1, 2, 3)], "GRB", "raw") == bytes((2, 1, 3))


def test_bad_checksum():
    assert "bad checksum" in describe_adalight(b"Ada\x00\x01\x00")


def test_format_bytes_truncates():
    out = format_bytes(bytes(range(100)), "hex", 4)
    assert out.startswith("00 01 02 03") and "+96 B" in out


def test_parse_hex():
    assert parse_hex("41 64,0x61") == b"Ada"
    for bad in ("", "4", "zz"):
        try:
            parse_hex(bad)
            assert False
        except ValueError:
            pass


def test_human_size():
    assert human_size(10) == "10 B" and human_size(2048) == "2.0 KB"
