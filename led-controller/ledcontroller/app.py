"""Application bootstrap."""
import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from ledcontroller.ui.main_window import MainWindow
from ledcontroller.ui.style import build_stylesheet

FONT_FAMILIES = ["SF Pro Text", ".AppleSystemUIFont", "Helvetica Neue", "Inter",
                 "Segoe UI Variable", "Segoe UI", "Ubuntu", "Noto Sans", "DejaVu Sans"]


def create_app(argv=None):
    app = QApplication(argv if argv is not None else sys.argv)
    app.setStyle("Fusion")
    font = QFont()
    font.setFamilies(FONT_FAMILIES)
    font.setPixelSize(13)
    app.setFont(font)
    app.setStyleSheet(build_stylesheet())
    return app


def main():
    app = create_app()
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
