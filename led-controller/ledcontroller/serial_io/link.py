"""Background serial link.

* Writer thread : sends the *latest* LED frame (older frames are dropped when
  the device cannot keep up) and any queued raw writes (from the debug console).
* Reader thread : collects incoming bytes (e.g. device replies / debug text).

`tx` / `rx` signals carry (timestamp, bytes) for the debug console.  TX frame
signals are rate limited via `tx_interval` so a 30 fps stream does not flood the UI.
"""
import threading
import time
from collections import deque

import serial
from PySide6.QtCore import QObject, Signal


class SerialLink(QObject):
    error = Signal(str)
    tx = Signal(float, bytes)
    rx = Signal(float, bytes)

    def __init__(self):
        super().__init__()
        self.ser = None
        self.tx_interval = 0.2          # seconds between logged TX frames (0 = all)
        self._latest = None
        self._raw = deque()
        self._cv = threading.Condition()
        self._run = False
        self._threads = []
        self._last_tx_emit = 0.0
        self.reset_counters()

    # ---- state ---------------------------------------------------------
    @property
    def connected(self):
        return self._run

    def reset_counters(self):
        self.tx_bytes = self.tx_frames = self.rx_bytes = 0

    # ---- lifecycle -----------------------------------------------------
    def open(self, port, baud):
        self.close()
        self.ser = serial.Serial(port, baud, timeout=0.05, write_timeout=1.0)
        self.reset_counters()
        self._latest = None
        self._raw.clear()
        self._run = True
        self._threads = [
            threading.Thread(target=self._writer, args=(self.ser,), daemon=True),
            threading.Thread(target=self._reader, args=(self.ser,), daemon=True),
        ]
        for t in self._threads:
            t.start()

    def close(self):
        with self._cv:
            self._run = False
            self._cv.notify_all()
        for t in self._threads:
            if t is not threading.current_thread():
                t.join(1.0)
        self._threads = []
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
            self.ser = None

    # ---- API -----------------------------------------------------------
    def send(self, data):
        """Queue an LED frame (only the newest pending frame is kept)."""
        with self._cv:
            self._latest = data
            self._cv.notify()

    def send_raw(self, data):
        """Queue arbitrary bytes (sent before the next LED frame)."""
        with self._cv:
            self._raw.append(data)
            self._cv.notify()

    # ---- threads -------------------------------------------------------
    def _fail(self, exc):
        if self._run:
            self._run = False
            self.error.emit(str(exc))

    def _writer(self, ser):
        while True:
            with self._cv:
                while self._run and self._latest is None and not self._raw:
                    self._cv.wait(0.5)
                if not self._run:
                    return
                if self._raw:
                    data, is_frame = self._raw.popleft(), False
                else:
                    data, self._latest, is_frame = self._latest, None, True
            try:
                ser.write(data)
            except Exception as e:
                self._fail(e)
                return
            self.tx_bytes += len(data)
            now = time.time()
            if is_frame:
                self.tx_frames += 1
            if not is_frame or now - self._last_tx_emit >= self.tx_interval:
                self._last_tx_emit = now
                self.tx.emit(now, data)

    def _reader(self, ser):
        while self._run:
            try:
                data = ser.read(ser.in_waiting or 1)
            except Exception as e:
                self._fail(e)
                return
            if data:
                self.rx_bytes += len(data)
                self.rx.emit(time.time(), data)
