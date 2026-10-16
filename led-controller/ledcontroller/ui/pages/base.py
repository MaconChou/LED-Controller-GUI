"""Common page scaffold."""
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ledcontroller.ui.widgets.helpers import caption, h1


class Page(QWidget):
    def __init__(self, app, title, subtitle=""):
        super().__init__()
        self.app = app
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(28, 24, 28, 12)
        self.root.setSpacing(14)
        self.root.addWidget(h1(title))
        if subtitle:
            self.root.addWidget(caption(subtitle))
