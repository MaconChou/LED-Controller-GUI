"""Sequence page: chain patterns with durations."""
from pathlib import Path
import copy
import json
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from ledcontroller.constants import APP_NAME
from ledcontroller.patterns.registry import make_renderer
from ledcontroller.ui.pages.base import Page
from ledcontroller.ui.widgets.helpers import caption, plain_spin, primary
from ledcontroller.ui.widgets.switch import Switch


class SequencePage(Page):
    def __init__(self, app):
        super().__init__(app, "Sequence",
                         "Chain patterns together and set how long each one runs.")
        self.seq = app.store.data["sequence"]
        self.items = self.seq["items"]

        bar = QHBoxLayout()
        self.b_add = QPushButton("Add Pattern  ▾")
        self.menu = QMenu(self)
        self.menu.aboutToShow.connect(self._fill_menu)
        self.b_add.setMenu(self.menu)
        self.b_up = QPushButton("Move Up")
        self.b_up.clicked.connect(lambda: self._move(-1))
        self.b_down = QPushButton("Move Down")
        self.b_down.clicked.connect(lambda: self._move(1))
        self.b_dup = QPushButton("Duplicate")
        self.b_dup.clicked.connect(self._dup)
        self.b_rm = QPushButton("Remove")
        self.b_rm.setObjectName("danger")
        self.b_rm.clicked.connect(self._remove)
        for b in (self.b_add, self.b_up, self.b_down, self.b_dup, self.b_rm):
            bar.addWidget(b)
        bar.addStretch(1)
        self.root.addLayout(bar)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Pattern", "Duration"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 130)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.root.addWidget(self.table, 1)

        self.bar = QProgressBar()
        self.bar.setRange(0, 1000)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(5)
        self.root.addWidget(self.bar)

        foot = QHBoxLayout()
        foot.addWidget(QLabel("Loop"))
        self.loop = Switch(self.seq.get("loop", True))
        self.loop.toggled.connect(self._loop)
        foot.addWidget(self.loop)
        self.total = caption("")
        foot.addSpacing(12)
        foot.addWidget(self.total, 1)
        b_exp = QPushButton("Export…")
        b_exp.clicked.connect(self.export)
        b_imp = QPushButton("Import…")
        b_imp.clicked.connect(self.import_)
        self.b_play = primary(QPushButton("Play"))
        self.b_play.setMinimumWidth(100)
        self.b_play.clicked.connect(self.toggle_play)
        foot.addWidget(b_exp)
        foot.addWidget(b_imp)
        foot.addWidget(self.b_play)
        self.root.addLayout(foot)

        e = app.engine
        e.seqIndexChanged.connect(lambda i: self.table.selectRow(i))
        e.progress.connect(lambda i, el, d: self.bar.setValue(int(el / d * 1000)))
        e.stateChanged.connect(self._state)
        self.refresh()

    def _fill_menu(self):
        self.menu.clear()
        for title, insts, _ in self.app.all_patterns():
            sub = self.menu.addMenu(title)
            if not insts:
                sub.addAction("(none)").setEnabled(False)
            for inst in insts:
                act = sub.addAction(inst["name"])
                act.triggered.connect(lambda _=False, i=inst: self.add(i))

    def add(self, inst, duration=10.0):
        self.items.append({"inst": copy.deepcopy(inst), "duration": duration})
        self.refresh(select=len(self.items) - 1)
        self.app.store.save()

    def refresh(self, select=None):
        self.table.clearSelection()
        self.table.setRowCount(0)
        self.table.setRowCount(len(self.items))
        for r, it in enumerate(self.items):
            self.table.setItem(r, 0, QTableWidgetItem(f"  {r + 1}.   {it['inst']['name']}"))
            sp = plain_spin(QDoubleSpinBox())
            sp.setRange(0.5, 86400)
            sp.setDecimals(1)
            sp.setSingleStep(1)
            sp.setSuffix(" s")
            sp.setValue(it["duration"])
            sp.valueChanged.connect(lambda v, r=r: self._set_dur(r, v))
            w = QWidget()
            h = QHBoxLayout(w)
            h.setContentsMargins(8, 4, 8, 4)
            h.addWidget(sp)
            self.table.setCellWidget(r, 1, w)
        if select is not None and 0 <= select < len(self.items):
            self.table.selectRow(select)
        self._update_total()

    def _update_total(self):
        t = sum(i["duration"] for i in self.items)
        m, s = divmod(int(t), 60)
        self.total.setText(f"{len(self.items)} step(s)  ·  total {m}m {s:02d}s")

    def _set_dur(self, r, v):
        self.items[r]["duration"] = v
        self._update_total()
        self.app.store.save()

    def _row(self):
        r = self.table.currentRow()
        return r if 0 <= r < len(self.items) else None

    def _move(self, d):
        r = self._row()
        if r is None or not 0 <= r + d < len(self.items):
            return
        self.items[r], self.items[r + d] = self.items[r + d], self.items[r]
        self.refresh(select=r + d)
        self.app.store.save()

    def _dup(self):
        r = self._row()
        if r is not None:
            self.items.insert(r + 1, copy.deepcopy(self.items[r]))
            self.refresh(select=r + 1)
            self.app.store.save()

    def _remove(self):
        r = self._row()
        if r is not None:
            del self.items[r]
            self.refresh(select=min(r, len(self.items) - 1))
            self.app.store.save()

    def _loop(self, on):
        self.seq["loop"] = on
        self.app.store.save()
        if self.app.engine.mode == "seq":
            self.app.engine.loop = on

    def toggle_play(self):
        e = self.app.engine
        if e.mode == "seq":
            e.stop()
        elif self.items:
            e.play_sequence(self.items, self.loop.isChecked())
        else:
            QMessageBox.information(self, APP_NAME, "Add at least one pattern to the sequence first.")

    def _state(self, _txt):
        playing = self.app.engine.mode == "seq"
        self.b_play.setText("Stop" if playing else "Play")
        if not playing:
            self.bar.setValue(0)

    def export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Sequence", "sequence.json", "JSON (*.json)")
        if path:
            Path(path).write_text(json.dumps(self.seq, indent=1), encoding="utf-8")

    def import_(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Sequence", "", "JSON (*.json)")
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            items = data["items"]
            for it in items:
                make_renderer(it["inst"], 4)
                float(it["duration"])
        except Exception as e:
            QMessageBox.warning(self, APP_NAME, f"Invalid sequence file:\n{e}")
            return
        self.items[:] = items
        self.loop.setChecked(bool(data.get("loop", True)))
        self.refresh()
        self.app.store.save()
