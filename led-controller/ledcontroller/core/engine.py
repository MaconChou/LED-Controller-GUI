"""Frame engine: renders the active pattern / sequence on a timer."""
import copy
import time
from PySide6.QtCore import QObject, QTimer, Qt, Signal

from ledcontroller.patterns.registry import make_renderer


class Engine(QObject):
    frameReady = Signal(list)
    seqIndexChanged = Signal(int)
    progress = Signal(int, float, float)
    stateChanged = Signal(str)
    finished = Signal()

    def __init__(self, n, fps, brightness):
        super().__init__()
        self.n, self.brightness = n, brightness
        self.mode = "off"          # off | pattern | seq
        self.inst = None
        self.renderer = None
        self.seq, self.idx, self.loop = [], 0, True
        self.t0 = 0.0
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self._tick)
        self.set_fps(fps)

    def set_fps(self, fps):
        self.timer.setInterval(int(1000 / max(1, fps)))

    def set_n(self, n):
        self.n = n
        if self.inst is not None and self.mode != "off":
            self.renderer = make_renderer(self.inst, n)

    def refresh(self):
        if self.mode in ("pattern", "seq") and self.inst is not None:
            self.renderer = make_renderer(self.inst, self.n)

    def play_instance(self, inst):
        self.mode, self.inst = "pattern", inst
        self.renderer = make_renderer(inst, self.n)
        self.t0 = time.perf_counter()
        self.timer.start()
        self.stateChanged.emit(f"Playing  ·  {inst['name']}")

    def play_sequence(self, items, loop):
        if not items:
            return
        self.seq, self.loop, self.idx = copy.deepcopy(items), loop, 0
        self.mode = "seq"
        self._start_step()
        self.timer.start()

    def _start_step(self):
        step = self.seq[self.idx]
        self.inst = step["inst"]
        self.renderer = make_renderer(self.inst, self.n)
        self.t0 = time.perf_counter()
        self.seqIndexChanged.emit(self.idx)
        self.stateChanged.emit(
            f"Sequence {self.idx + 1}/{len(self.seq)}  ·  {self.inst['name']}")

    def stop(self):
        self.timer.stop()
        was_seq = self.mode == "seq"
        self.mode, self.inst = "off", None
        self.frameReady.emit([(0, 0, 0)] * self.n)
        self.stateChanged.emit("Stopped")
        if was_seq:
            self.finished.emit()

    def _tick(self):
        now = time.perf_counter()
        if self.mode == "seq":
            el = now - self.t0
            dur = self.seq[self.idx]["duration"]
            if el >= dur:
                self.idx += 1
                if self.idx >= len(self.seq):
                    if self.loop:
                        self.idx = 0
                    else:
                        self.stop()
                        return
                self._start_step()
                now = self.t0
            else:
                self.progress.emit(self.idx, el, dur)
        if self.renderer is None:
            return
        frame = self.renderer.render(now - self.t0)
        b = self.brightness
        self.frameReady.emit([(min(255, int(r * b)), min(255, int(g * b)), min(255, int(bl * b)))
                              for r, g, bl in frame])
