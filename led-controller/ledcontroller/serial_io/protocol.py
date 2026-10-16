"""Wire protocol encoding (Adalight / raw RGB)."""


def encode(frame, order, protocol):
    idx = ["RGB".index(ch) for ch in order]
    data = bytearray()
    for c in frame:
        data += bytes((c[idx[0]], c[idx[1]], c[idx[2]]))
    if protocol == "adalight":
        n = len(frame) - 1
        hi, lo = (n >> 8) & 0xFF, n & 0xFF
        return b"Ada" + bytes((hi, lo, hi ^ lo ^ 0x55)) + bytes(data)
    return bytes(data)
