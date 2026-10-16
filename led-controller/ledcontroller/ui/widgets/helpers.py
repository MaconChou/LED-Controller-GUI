"""Small widget factories shared by pages."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractSpinBox, QFrame, QLabel


def plain_spin(sb):
    sb.setButtonSymbols(QAbstractSpinBox.NoButtons)
    sb.setAlignment(Qt.AlignCenter)
    return sb


def make_card():
    f = QFrame()
    f.setObjectName("card")
    return f


def h1(text):
    l = QLabel(text)
    l.setObjectName("h1")
    return l


def caption(text):
    l = QLabel(text)
    l.setObjectName("caption")
    l.setWordWrap(True)
    return l


def primary(btn):
    btn.setObjectName("primary")
    return btn
