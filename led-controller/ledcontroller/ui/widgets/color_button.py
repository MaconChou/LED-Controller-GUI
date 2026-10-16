"""Colour swatch button."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QPushButton


class ColorButton(QPushButton):
    changed = Signal(str)

    def __init__(self, hexc="#ffffff"):
        super().__init__()
        self.setFixedSize(52, 24)
        self.setCursor(Qt.PointingHandCursor)
        self.set_color(hexc)
        self.clicked.connect(self._pick)

    def set_color(self, h):
        self.hex = h
        self.setStyleSheet(
            f"QPushButton{{background:{h};border:1px solid rgba(0,0,0,70);"
            f"border-radius:6px;padding:0}}QPushButton:hover{{border:2px solid #0a84ff}}")

    def _pick(self):
        c = QColorDialog.getColor(QColor(self.hex), self.window(), "Choose Color")
        if c.isValid():
            self.set_color(c.name())
            self.changed.emit(c.name())
