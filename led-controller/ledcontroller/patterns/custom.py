"""Frame based custom patterns (painted in the Custom page)."""
from ledcontroller.core.colors import hex2rgb, lerp, resample


class CustomPattern:
    """Frame-based custom pattern (each frame = per-LED colours)."""

    def __init__(self, n, inst):
        frames = inst.get("frames") or [{"colors": ["#000000"], "duration": 1, "fade": False}]
        self.frames = []
        for f in frames:
            cols = [hex2rgb(c) for c in resample(f["colors"], n)]
            self.frames.append((cols, max(0.05, float(f["duration"])), bool(f.get("fade"))))
        self.total = sum(d for _, d, _ in self.frames)

    def render(self, t):
        t %= self.total
        for idx, (cols, d, fade) in enumerate(self.frames):
            if t < d:
                if fade and len(self.frames) > 1:
                    nxt = self.frames[(idx + 1) % len(self.frames)][0]
                    k = t / d
                    return [lerp(a, b, k) for a, b in zip(cols, nxt)]
                return cols
            t -= d
        return self.frames[-1][0]
