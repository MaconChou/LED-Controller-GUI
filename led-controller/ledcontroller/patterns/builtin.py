"""Built-in procedural patterns."""
import math
import random

from ledcontroller.core.colors import hsv, lerp
from ledcontroller.patterns.base import C1, C2, Pattern, SPEED


class Solid(Pattern):
    id, name = "solid", "Solid"
    params = [C1("#ff9f0a")]

    def render(self, t):
        return [self.c1] * self.n


class Gradient(Pattern):
    id, name = "gradient", "Gradient"
    params = [C1("#0a84ff"), C2("#ff2d55"),
              ("speed", "Scroll", "float", 0.5, 0.0, 8.0)]

    def render(self, t):
        out = []
        for i in range(self.n):
            pos = (i / self.n + t * self.speed * 0.2) % 1.0
            out.append(lerp(self.c1, self.c2, 1 - abs(2 * pos - 1)))
        return out


class Rainbow(Pattern):
    id, name = "rainbow", "Rainbow"
    params = [SPEED, ("scale", "Cycles", "float", 1.0, 0.2, 5.0)]

    def render(self, t):
        sc = float(self.p.get("scale", 1.0))
        return [hsv(i / self.n * sc - t * self.speed * 0.2) for i in range(self.n)]


class Breathing(Pattern):
    id, name = "breathing", "Breathing"
    params = [C1("#bf5af2"), C2("#000000"), ("speed", "Speed", "float", 0.8, 0.1, 8.0)]

    def render(self, t):
        k = (1 - math.cos(2 * math.pi * t * self.speed * 0.4)) / 2
        return [lerp(self.c2, self.c1, k)] * self.n


class Wave(Pattern):
    id, name = "wave", "Wave"
    params = [C1("#30d158"), C2("#0a84ff"), SPEED,
              ("scale", "Waves", "float", 2.0, 0.5, 10.0)]

    def render(self, t):
        sc = float(self.p.get("scale", 2.0))
        return [lerp(self.c2, self.c1,
                     (math.sin(2 * math.pi * (i / self.n * sc - t * self.speed * 0.3)) + 1) / 2)
                for i in range(self.n)]


class Comet(Pattern):
    id, name = "comet", "Comet"
    params = [C1("#64d2ff"), C2("#000000"), SPEED,
              ("tail", "Tail", "float", 12.0, 2.0, 60.0)]

    def render(self, t):
        tail = float(self.p.get("tail", 12))
        head = (t * self.speed * 20) % (self.n + tail)
        out = []
        for i in range(self.n):
            d = head - i
            k = (1 - d / tail) ** 2 if 0 <= d < tail else 0
            out.append(lerp(self.c2, self.c1, k))
        return out


class Scanner(Pattern):
    id, name = "scanner", "Scanner"
    params = [C1("#ff3b30"), C2("#000000"), SPEED,
              ("width", "Width", "float", 4.0, 1.0, 20.0)]

    def render(self, t):
        w = float(self.p.get("width", 4))
        period = max(1, 2 * (self.n - 1))
        x = (t * self.speed * 20) % period
        pos = x if x <= self.n - 1 else period - x
        return [lerp(self.c2, self.c1, 1 - abs(i - pos) / w) for i in range(self.n)]


class TheaterChase(Pattern):
    id, name = "theater", "Theater Chase"
    params = [C1("#ffd60a"), C2("#000000"), ("speed", "Speed", "float", 1.0, 0.1, 8.0)]

    def render(self, t):
        step = int(t * self.speed * 6) % 3
        return [self.c1 if i % 3 == step else self.c2 for i in range(self.n)]


class ColorWipe(Pattern):
    id, name = "wipe", "Color Wipe"
    params = [C1("#30d158"), C2("#ff375f"), ("speed", "Speed", "float", 1.0, 0.1, 8.0)]

    def render(self, t):
        pos = (t * self.speed * 15) % (2 * self.n)
        if pos < self.n:
            return [self.c1 if i < pos else self.c2 for i in range(self.n)]
        pos -= self.n
        return [self.c2 if i < pos else self.c1 for i in range(self.n)]


class Twinkle(Pattern):
    id, name = "twinkle", "Twinkle"
    params = [C1("#ffffff"), C2("#10102a"), SPEED,
              ("density", "Density", "float", 0.3, 0.02, 1.0)]

    def setup(self):
        self.b = [0.0] * self.n
        self.last = 0.0

    def render(self, t):
        dt = max(0.0, t - self.last)
        self.last = t
        dens = float(self.p.get("density", 0.3))
        decay = math.exp(-dt * self.speed * 2.5)
        prob = min(1.0, dt * dens * self.speed * 3)
        for i in range(self.n):
            self.b[i] *= decay
            if random.random() < prob:
                self.b[i] = 1.0
        return [lerp(self.c2, self.c1, b) for b in self.b]


class Fire(Pattern):
    id, name = "fire", "Fire"
    params = [("cooling", "Cooling", "float", 55.0, 20.0, 120.0),
              ("sparking", "Sparking", "float", 120.0, 30.0, 220.0)]

    def setup(self):
        self.heat = [0] * self.n

    def render(self, t):
        n, h = self.n, self.heat
        cooling = int(self.p.get("cooling", 55))
        sparking = int(self.p.get("sparking", 120))
        for i in range(n):
            h[i] = max(0, h[i] - random.randint(0, (cooling * 10) // n + 2))
        for k in range(n - 1, 1, -1):
            h[k] = (h[k - 1] + h[k - 2] * 2) // 3
        if random.randint(0, 255) < sparking:
            y = random.randint(0, min(7, n - 1))
            h[y] = min(255, h[y] + random.randint(160, 255))
        out = []
        for v in h:
            t192 = round(v / 255 * 191)
            ramp = (t192 & 0x3F) << 2
            if t192 > 0x80:
                out.append((255, 255, ramp))
            elif t192 > 0x40:
                out.append((255, ramp, 0))
            else:
                out.append((ramp, 0, 0))
        return out


class Strobe(Pattern):
    id, name = "strobe", "Strobe"
    params = [C1("#ffffff"), C2("#000000"), ("speed", "Speed", "float", 1.0, 0.1, 4.0)]

    def render(self, t):
        return [self.c1 if int(t * self.speed * 4) % 2 == 0 else self.c2] * self.n


BUILTINS = [Solid, Gradient, Rainbow, Breathing, Wave, Comet, Scanner,
            TheaterChase, ColorWipe, Twinkle, Fire, Strobe]


BUILTIN_MAP = {c.id: c for c in BUILTINS}
