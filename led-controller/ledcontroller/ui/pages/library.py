"""Library page: built-in patterns, presets and custom patterns."""
import copy
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ledcontroller.patterns.registry import make_renderer
from ledcontroller.ui.pages.base import Page
from ledcontroller.ui.widgets.helpers import caption, make_card
from ledcontroller.ui.widgets.param_form import ParamForm
from ledcontroller.ui.widgets.strip import StripWidget


class LibraryPage(Page):
    def __init__(self, app):
        super().__init__(app, "Library", "Built-in effects, your saved presets and custom patterns. Click one to play it.")
        body = QHBoxLayout()
        body.setSpacing(16)
        self.list = QListWidget()
        self.list.setMinimumWidth(300)
        self.list.setSpacing(1)
        self.list.currentItemChanged.connect(self.on_select)
        body.addWidget(self.list, 3)

        card = make_card()
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 18, 20, 18)
        v.setSpacing(14)
        self.title = QLabel("Select a pattern")
        self.title.setObjectName("h2")
        v.addWidget(self.title)
        self.form = ParamForm()
        self.form.changed.connect(self._params_changed)
        v.addWidget(self.form)
        self.hint = caption("")
        v.addWidget(self.hint)
        v.addStretch(1)
        row = QHBoxLayout()
        self.b_save = QPushButton("Save as Preset…")
        self.b_save.clicked.connect(self.save_preset)
        self.b_add = QPushButton("Add to Sequence")
        self.b_add.clicked.connect(self.add_seq)
        self.b_edit = QPushButton("Edit…")
        self.b_edit.clicked.connect(self.edit_custom)
        self.b_del = QPushButton("Delete")
        self.b_del.setObjectName("danger")
        self.b_del.clicked.connect(self.delete)
        for b in (self.b_save, self.b_edit, self.b_add, self.b_del):
            row.addWidget(b)
        v.addLayout(row)
        body.addWidget(card, 2)
        self.root.addLayout(body, 1)

        self.work, self.cat = None, None
        self.rebuild()

    @staticmethod
    def _thumb(inst, n=28):
        try:
            r = make_renderer(inst, n)
            f = None
            for k in range(12):
                f = r.render(0.1 + k * 0.07)
            return f
        except Exception:
            return []

    def rebuild(self, select=None):
        self.list.blockSignals(True)
        self.list.clear()
        groups = self.app.all_patterns()
        target = None
        for title, insts, cat in groups:
            if not insts:
                continue
            hdr = QListWidgetItem(title.upper())
            hdr.setFlags(Qt.NoItemFlags)
            f = hdr.font()
            f.setPointSize(9)
            f.setBold(True)
            hdr.setFont(f)
            hdr.setForeground(QColor("#86868b"))
            self.list.addItem(hdr)
            for inst in insts:
                it = QListWidgetItem()
                it.setData(Qt.UserRole, {"inst": inst, "cat": cat})
                it.setSizeHint(QSize(0, 36))
                self.list.addItem(it)
                w = QWidget()
                h = QHBoxLayout(w)
                h.setContentsMargins(8, 0, 8, 0)
                lab = QLabel(inst["name"])
                lab.setObjectName("rowlabel")
                lab.setStyleSheet("color:#1d1d1f;background:transparent;")
                lab.setAttribute(Qt.WA_TransparentForMouseEvents)
                strip = StripWidget(10, dark=False)
                strip.setFixedWidth(110)
                strip.set_colors(self._thumb(inst))
                strip.setAttribute(Qt.WA_TransparentForMouseEvents)
                h.addWidget(lab, 1)
                h.addWidget(strip)
                self.list.setItemWidget(it, w)
                if select is inst:
                    target = it
        self.list.blockSignals(False)
        if target:
            self.list.setCurrentItem(target)

    def _recolor(self, cur):
        for i in range(self.list.count()):
            it = self.list.item(i)
            w = self.list.itemWidget(it)
            if w:
                w.findChild(QLabel, "rowlabel").setStyleSheet(
                    f"color:{'white' if it is cur else '#1d1d1f'};background:transparent;")

    def on_select(self, cur, _prev):
        if cur is None:
            return
        self._recolor(cur)
        d = cur.data(Qt.UserRole)
        if not d:
            return
        self.work = copy.deepcopy(d["inst"])
        self.cat = d["cat"]
        self.src = d["inst"]
        self.title.setText(self.work["name"])
        self.form.load(self.work)
        custom = self.cat == "custom"
        self.b_edit.setVisible(custom)
        self.b_save.setVisible(not custom)
        self.b_del.setVisible(self.cat != "builtin")
        self.hint.setText("Custom pattern – open the Custom page to edit its frames." if custom else "")
        self.app.engine.play_instance(self.work)

    def _params_changed(self):
        if self.app.engine.inst is self.work:
            self.app.engine.refresh()

    def save_preset(self):
        if not self.work:
            return
        name, ok = QInputDialog.getText(self, "Save Preset", "Preset name:", text=self.work["name"])
        if not ok or not name.strip():
            return
        inst = copy.deepcopy(self.work)
        inst["name"] = name.strip()
        self.app.store.data["presets"].append(inst)
        self.app.store.save()
        self.rebuild(select=inst)

    def add_seq(self):
        if self.work:
            self.app.page_seq.add(self.work)
            self.app.flash(f"Added “{self.work['name']}” to sequence")

    def edit_custom(self):
        if self.work and self.cat == "custom":
            self.app.page_custom.open_custom(self.src)
            self.app.go_page(2)

    def delete(self):
        if not self.work:
            return
        key = "presets" if self.cat == "preset" else "customs"
        lst = self.app.store.data[key]
        if self.src in lst:
            lst.remove(self.src)
            self.app.store.save()
        self.work = None
        self.title.setText("Select a pattern")
        self.form.load({"kind": "none"})
        self.rebuild()
        self.app.page_custom.reload_list()
