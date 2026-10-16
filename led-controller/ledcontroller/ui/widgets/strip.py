"""Read-only LED strip preview widget."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget


class StripWidget(QWidget):
    """Read-only LED strip preview."""

    def __init__(self, height=28, dark=True):
        super().__init__()
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.colors, self.dark = [], dark

    def set_colors(self, cols):
        self.colors = cols
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#1c1c1e" if self.dark else "#e5e5ea"))
        p.drawRoundedRect(r, 6, 6)
        n = len(self.colors)
        if not n:
            return
        pad = 4
        w = (r.width() - 2 * pad) / n
        h = r.height() - 2 * pad
        for i, c in enumerate(self.colors):
            p.setBrush(QColor(*c))
            if w >= 7:
                p.drawRoundedRect(QRectF(pad + i * w + 1, pad, w - 2, h), 3, 3)
            else:
                p.drawRect(QRectF(pad + i * w, pad, w + 0.6, h))
