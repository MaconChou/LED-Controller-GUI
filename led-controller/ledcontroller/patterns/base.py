"""Pattern base class and parameter-spec helpers."""
from ledcontroller.core.colors import hex2rgb


class Pattern:
    id = ""
    name = ""
    params = []

    def __init__(self, n, p):
        self.n = n
        self.p = p
        self.c1 = hex2rgb(p.get("color1", "#000000"))
        self.c2 = hex2rgb(p.get("color2", "#000000"))
        self.speed = float(p.get("speed", 1.0))
        self.setup()

    def setup(self):
        pass

    def render(self, t):
        raise NotImplementedError


SPEED = ("speed", "Speed", "float", 1.0, 0.1, 8.0)


def C1(d="#ff3b30"):
    return ("color1", "Color 1", "color", d, None, None)


def C2(d="#000000"):
    return ("color2", "Color 2", "color", d, None, None)
