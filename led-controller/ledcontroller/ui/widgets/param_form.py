"""Auto-generated parameter form for built-in patterns."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QSlider, QWidget

from ledcontroller.patterns.builtin import BUILTIN_MAP
from ledcontroller.ui.widgets.color_button import ColorButton


class ParamForm(QWidget):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setVerticalSpacing(12)
        self.inst = None

    def load(self, inst):
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.inst = inst
        if inst["kind"] != "builtin":
            return
        cls = BUILTIN_MAP[inst["id"]]
        params = inst.setdefault("params", {})
        for r, (key, label, kind, default, lo, hi) in enumerate(cls.params):
            val = params.get(key, default)
            self.grid.addWidget(QLabel(label), r, 0)
            if kind == "color":
                b = ColorButton(val)
                b.changed.connect(lambda h, k=key: self._set(k, h))
                self.grid.addWidget(b, r, 1, 1, 2, Qt.AlignLeft)
            else:
                s = QSlider(Qt.Horizontal)
                s.setRange(0, 1000)
                s.setValue(int((float(val) - lo) / (hi - lo) * 1000))
                lab = QLabel(f"{float(val):.2f}")
                lab.setMinimumWidth(42)
                lab.setObjectName("caption")
                s.valueChanged.connect(
                    lambda v, k=key, lo=lo, hi=hi, lab=lab: self._slide(k, lo, hi, v, lab))
                self.grid.addWidget(s, r, 1)
                self.grid.addWidget(lab, r, 2)
        self.grid.setColumnStretch(1, 1)

    def _set(self, k, v):
        self.inst["params"][k] = v
        self.changed.emit()

    def _slide(self, k, lo, hi, v, lab):
        val = lo + (hi - lo) * v / 1000
        lab.setText(f"{val:.2f}")
        self._set(k, round(val, 3))
