"""Per-LED paint widget used by the Custom page."""
import math
from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget


class PixelEditor(QWidget):
    """Click / drag to paint LEDs.  colors = list of '#rrggbb' (edited in place)."""
    edited = Signal()
    CELL, MAXCOLS = 24, 20

    def __init__(self):
        super().__init__()
        self.colors = []
        self.brush = "#ff3b30"
        self.setMouseTracking(False)
        self.setCursor(Qt.CrossCursor)

    def set_data(self, colors):
        self.colors = colors
        n = max(1, len(colors))
        cols = min(n, self.MAXCOLS)
        rows = math.ceil(n / cols)
        self.cols = cols
        self.setFixedSize(cols * self.CELL + 2, rows * self.CELL + 2)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = self.CELL
        for i, col in enumerate(self.colors):
            x, y = (i % self.cols) * c + 1, (i // self.cols) * c + 1
            p.setPen(QColor(0, 0, 0, 40))
            p.setBrush(QColor(col))
            p.drawRoundedRect(QRectF(x + 1, y + 1, c - 3, c - 3), 5, 5)

    def _paint_at(self, pos, erase):
        c = self.CELL
        i = (int(pos.y()) // c) * self.cols + int(pos.x()) // c
        if 0 <= i < len(self.colors):
            new = "#000000" if erase else self.brush
            if self.colors[i] != new:
                self.colors[i] = new
                self.update()
                self.edited.emit()

    def mousePressEvent(self, e):
        self._paint_at(e.position(), e.button() == Qt.RightButton)

    def mouseMoveEvent(self, e):
        self._paint_at(e.position(), bool(e.buttons() & Qt.RightButton))
