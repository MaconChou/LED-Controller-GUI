"""Custom page: frame based pattern editor."""
from collections import deque
import copy
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
)

from ledcontroller.core.colors import hex2rgb, hsv, lerp, resample, rgb2hex
from ledcontroller.ui.pages.base import Page
from ledcontroller.ui.widgets.color_button import ColorButton
from ledcontroller.ui.widgets.helpers import make_card, plain_spin, primary
from ledcontroller.ui.widgets.pixel_editor import PixelEditor
from ledcontroller.ui.widgets.switch import Switch


class CustomPage(Page):
    def __init__(self, app):
        super().__init__(app, "Custom Pattern",
                         "Paint each LED frame by frame. Left-click / drag to paint, right-click to erase.")
        body = QHBoxLayout()
        body.setSpacing(16)

        left = QVBoxLayout()
        self.list = QListWidget()
        self.list.setFixedWidth(200)
        self.list.currentRowChanged.connect(self._pick_saved)
        left.addWidget(self.list, 1)
        b_new = QPushButton("New Pattern")
        b_new.clicked.connect(self.new)
        b_del = QPushButton("Delete")
        b_del.setObjectName("danger")
        b_del.clicked.connect(self.delete)
        left.addWidget(b_new)
        left.addWidget(b_del)
        body.addLayout(left)

        card = make_card()
        v = QVBoxLayout(card)
        v.setContentsMargins(18, 16, 18, 16)
        v.setSpacing(12)

        top = QHBoxLayout()
        self.name = QLineEdit()
        self.name.setPlaceholderText("Pattern name")
        self.b_prev = QPushButton("Preview")
        self.b_prev.clicked.connect(self.preview)
        self.b_save = primary(QPushButton("Save"))
        self.b_save.clicked.connect(self.save)
        top.addWidget(self.name, 1)
        top.addWidget(self.b_prev)
        top.addWidget(self.b_save)
        v.addLayout(top)

        mid = QHBoxLayout()
        fl = QVBoxLayout()
        self.frames = QListWidget()
        self.frames.setFixedWidth(210)
        self.frames.setFixedHeight(130)
        self.frames.currentRowChanged.connect(self._pick_frame)
        fl.addWidget(self.frames)
        fb = QHBoxLayout()
        for txt, fn in (("+", self.add_frame), ("Dup", self.dup_frame), ("−", self.del_frame)):
            b = QPushButton(txt)
            b.clicked.connect(fn)
            fb.addWidget(b)
        fl.addLayout(fb)
        mid.addLayout(fl)

        fp = QGridLayout()
        fp.setVerticalSpacing(10)
        fp.addWidget(QLabel("Duration"), 0, 0)
        self.dur = plain_spin(QDoubleSpinBox())
        self.dur.setRange(0.05, 60)
        self.dur.setSingleStep(0.1)
        self.dur.setSuffix(" s")
        self.dur.valueChanged.connect(self._dur)
        fp.addWidget(self.dur, 0, 1)
        fp.addWidget(QLabel("Fade to next frame"), 1, 0)
        self.fade = Switch()
        self.fade.toggled.connect(self._fade)
        fp.addWidget(self.fade, 1, 1, Qt.AlignLeft)
        fp.addWidget(QLabel("Brush"), 2, 0)
        self.brush = ColorButton("#ff3b30")
        self.brush.changed.connect(self._brush)
        fp.addWidget(self.brush, 2, 1, Qt.AlignLeft)
        fp.addWidget(QLabel("Color 2"), 3, 0)
        self.col2 = ColorButton("#0a84ff")
        fp.addWidget(self.col2, 3, 1, Qt.AlignLeft)
        fp.setColumnStretch(2, 1)
        mid.addLayout(fp, 1)
        v.addLayout(mid)

        tools = QHBoxLayout()
        tools.setSpacing(6)
        for txt, fn in (("Fill", self.t_fill), ("Gradient", self.t_grad), ("Rainbow", self.t_rainbow),
                        ("Mirror", self.t_mirror), ("◀ Shift", lambda: self.t_shift(1)),
                        ("Shift ▶", lambda: self.t_shift(-1)), ("Clear", self.t_clear)):
            b = QPushButton(txt)
            b.clicked.connect(fn)
            tools.addWidget(b)
        tools.addStretch(1)
        v.addLayout(tools)

        self.pix = PixelEditor()
        self.pix.edited.connect(self._edited)
        sc = QScrollArea()
        sc.setWidget(self.pix)
        sc.setWidgetResizable(False)
        sc.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        sc.setFrameShape(QFrame.NoFrame)
        sc.setStyleSheet("QScrollArea{background:#f2f2f7;border-radius:8px}")
        v.addWidget(sc, 1)
        body.addWidget(card, 1)
        self.root.addLayout(body, 1)

        self.edit, self.orig, self.cur = None, None, 0
        self.reload_list()
        self.new()

    # data
    @property
    def n(self):
        return self.app.store.settings["led_count"]

    def _blank_frame(self):
        return {"colors": ["#000000"] * self.n, "duration": 1.0, "fade": False}

    def reload_list(self):
        self.list.blockSignals(True)
        self.list.clear()
        for c in self.app.store.data["customs"]:
            self.list.addItem(c["name"])
        self.list.blockSignals(False)

    def new(self):
        self.list.blockSignals(True)
        self.list.clearSelection()
        self.list.setCurrentRow(-1)
        self.list.blockSignals(False)
        self.orig = None
        self._load({"kind": "custom", "name": "My Pattern", "frames": [self._blank_frame()]})

    def open_custom(self, inst):
        lst = self.app.store.data["customs"]
        if inst in lst:
            self.list.blockSignals(True)
            self.list.setCurrentRow(lst.index(inst))
            self.list.blockSignals(False)
            self.orig = lst.index(inst)
        self._load(copy.deepcopy(inst))

    def _pick_saved(self, row):
        lst = self.app.store.data["customs"]
        if 0 <= row < len(lst):
            self.orig = row
            self._load(copy.deepcopy(lst[row]))

    def _load(self, inst):
        for f in inst["frames"]:
            f["colors"] = resample(f["colors"], self.n)
        self.edit = inst
        self.name.setText(inst["name"])
        self.cur = 0
        self._refresh_frames()

    def _refresh_frames(self):
        self.frames.blockSignals(True)
        self.frames.clear()
        for i, f in enumerate(self.edit["frames"]):
            self.frames.addItem(f"Frame {i + 1}  ·  {f['duration']:.2f}s" + ("  ·  fade" if f.get("fade") else ""))
        self.cur = min(self.cur, len(self.edit["frames"]) - 1)
        self.frames.setCurrentRow(self.cur)
        self.frames.blockSignals(False)
        self._show_frame()

    def _show_frame(self):
        f = self.edit["frames"][self.cur]
        self.pix.set_data(f["colors"])
        self.dur.blockSignals(True)
        self.fade.blockSignals(True)
        self.dur.setValue(f["duration"])
        self.fade.setChecked(bool(f.get("fade")))
        self.dur.blockSignals(False)
        self.fade.blockSignals(False)
        self.fade.update()

    def _pick_frame(self, row):
        if row >= 0:
            self.cur = row
            self._show_frame()

    def _frame(self):
        return self.edit["frames"][self.cur]

    def _dur(self, v):
        self._frame()["duration"] = v
        self._refresh_frames()
        self._edited()

    def _fade(self, on):
        self._frame()["fade"] = on
        self._refresh_frames()
        self._edited()

    def _brush(self, h):
        self.pix.brush = h

    def _edited(self):
        if self.app.engine.inst is self.edit:
            self.app.engine.refresh()

    # frames
    def add_frame(self):
        self.edit["frames"].insert(self.cur + 1, self._blank_frame())
        self.cur += 1
        self._refresh_frames()
        self._edited()

    def dup_frame(self):
        self.edit["frames"].insert(self.cur + 1, copy.deepcopy(self._frame()))
        self.cur += 1
        self._refresh_frames()
        self._edited()

    def del_frame(self):
        if len(self.edit["frames"]) > 1:
            del self.edit["frames"][self.cur]
            self._refresh_frames()
            self._edited()

    # tools
    def _apply(self, cols):
        self._frame()["colors"][:] = cols
        self.pix.update()
        self._edited()

    def t_fill(self):
        self._apply([self.brush.hex] * self.n)

    def t_clear(self):
        self._apply(["#000000"] * self.n)

    def t_grad(self):
        a, b, n = hex2rgb(self.brush.hex), hex2rgb(self.col2.hex), self.n
        self._apply([rgb2hex(lerp(a, b, i / max(1, n - 1))) for i in range(n)])

    def t_rainbow(self):
        self._apply([rgb2hex(hsv(i / self.n)) for i in range(self.n)])

    def t_mirror(self):
        c = list(self._frame()["colors"])
        for i in range(len(c) // 2):
            c[len(c) - 1 - i] = c[i]
        self._apply(c)

    def t_shift(self, d):
        dq = deque(self._frame()["colors"])
        dq.rotate(d)
        self._apply(list(dq))

    # save / preview
    def preview(self):
        self.edit["name"] = self.name.text().strip() or "Untitled"
        self.app.engine.play_instance(self.edit)

    def save(self):
        name = self.name.text().strip() or "Untitled"
        self.edit["name"] = name
        lst = self.app.store.data["customs"]
        idx = self.orig
        if idx is None or idx >= len(lst):
            idx = next((i for i, c in enumerate(lst) if c["name"] == name), None)
        saved = copy.deepcopy(self.edit)
        if idx is None:
            lst.append(saved)
            idx = len(lst) - 1
        else:
            lst[idx] = saved
        self.orig = idx
        self.app.store.save()
        self.reload_list()
        self.list.blockSignals(True)
        self.list.setCurrentRow(idx)
        self.list.blockSignals(False)
        self.app.page_lib.rebuild()
        self.app.flash(f"Saved “{name}”")

    def delete(self):
        lst = self.app.store.data["customs"]
        if self.orig is not None and self.orig < len(lst):
            del lst[self.orig]
            self.app.store.save()
            self.reload_list()
            self.app.page_lib.rebuild()
        self.new()

    def led_count_changed(self):
        if self.edit:
            for f in self.edit["frames"]:
                f["colors"] = resample(f["colors"], self.n)
            self._show_frame()
