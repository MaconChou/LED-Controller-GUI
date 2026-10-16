"""Main application window."""
from PySide6.QtCore import QThread, QTimer, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QListWidget, QMainWindow, QMessageBox,
    QPushButton, QSlider, QStackedWidget, QVBoxLayout, QWidget,
)

from ledcontroller.constants import APP_NAME
from ledcontroller.core.engine import Engine
from ledcontroller.core.store import Store
from ledcontroller.patterns import BUILTINS, default_instance
from ledcontroller.serial_io.link import SerialLink
from ledcontroller.serial_io.protocol import encode
from ledcontroller.ui.debug_panel import DebugPanel
from ledcontroller.ui.pages.custom import CustomPage
from ledcontroller.ui.pages.device import DevicePage
from ledcontroller.ui.pages.library import LibraryPage
from ledcontroller.ui.pages.sequence import SequencePage
from ledcontroller.ui.widgets.strip import StripWidget

BASE_MIN_WIDTH = 940


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1120, 760)
        self.setMinimumSize(BASE_MIN_WIDTH, 640)

        self.store = Store()
        s = self.store.settings
        self.engine = Engine(s["led_count"], s["fps"], s["brightness"] / 100)
        self.link = SerialLink()
        self.link.error.connect(self._link_error)
        self.engine.frameReady.connect(self.on_frame)

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ---- sidebar
        side = QWidget()
        side.setObjectName("Sidebar")
        side.setFixedWidth(200)
        sv = QVBoxLayout(side)
        sv.setContentsMargins(0, 0, 0, 10)
        title = QLabel("LED CONTROLLER")
        title.setObjectName("AppTitle")
        sv.addWidget(title)
        self.nav = QListWidget()
        for name in ("Device", "Library", "Custom", "Sequence"):
            self.nav.addItem(name)
        sv.addWidget(self.nav, 1)
        outer.addWidget(side)

        # ---- pages + bottom bar
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        self.stack = QStackedWidget()
        self.page_device = DevicePage(self)
        self.page_lib = LibraryPage(self)
        self.page_custom = CustomPage(self)
        self.page_seq = SequencePage(self)
        for p in (self.page_device, self.page_lib, self.page_custom, self.page_seq):
            self.stack.addWidget(p)
        right.addWidget(self.stack, 1)
        right.addWidget(self._build_bottom_bar(s))
        outer.addLayout(right, 1)

        # ---- debug panel (collapsed, to the right of the main GUI)
        self.debug = DebugPanel(self.link)
        self.debug.hide()
        self.debug.closeRequested.connect(lambda: self.btn_debug.setChecked(False))
        outer.addWidget(self.debug)

        self.engine.stateChanged.connect(self.state.setText)
        self.engine.stateChanged.connect(self.debug.log_state)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav.setCurrentRow(1)
        self.preview.set_colors([(0, 0, 0)] * s["led_count"])
        QShortcut(QKeySequence("Ctrl+D"), self, activated=self.btn_debug.toggle)

    def _build_bottom_bar(self, s):
        bar = QFrame()
        bar.setObjectName("bar")
        bar.setStyleSheet("QFrame#bar{background:#fbfbfd;border-top:1px solid #dcdce1;}")
        bv = QVBoxLayout(bar)
        bv.setContentsMargins(20, 10, 20, 10)
        bv.setSpacing(8)
        self.preview = StripWidget(30)
        bv.addWidget(self.preview)
        row = QHBoxLayout()
        self.dot = QLabel("●")
        self.dot.setStyleSheet("color:#c7c7cc;")
        self.status = QLabel("Not connected")
        self.state = QLabel("Stopped")
        self.state.setObjectName("caption")
        row.addWidget(self.dot)
        row.addWidget(self.status)
        row.addSpacing(16)
        row.addWidget(self.state)
        row.addStretch(1)
        row.addWidget(QLabel("Brightness"))
        self.bright = QSlider(Qt.Horizontal)
        self.bright.setRange(0, 100)
        self.bright.setValue(s["brightness"])
        self.bright.setFixedWidth(160)
        self.bright.valueChanged.connect(self._brightness)
        row.addWidget(self.bright)
        self.bval = QLabel(f"{s['brightness']}%")
        self.bval.setMinimumWidth(34)
        row.addWidget(self.bval)
        b_stop = QPushButton("Blackout")
        b_stop.clicked.connect(self.engine.stop)
        row.addWidget(b_stop)
        self.btn_debug = QPushButton("Debug  ▸")
        self.btn_debug.setCheckable(True)
        self.btn_debug.setToolTip("Show / hide the debug console (Ctrl+D)")
        self.btn_debug.toggled.connect(self.toggle_debug)
        row.addWidget(self.btn_debug)
        bv.addLayout(row)
        return bar

    # ---- debug panel ---------------------------------------------------
    def toggle_debug(self, on):
        """Expand / collapse the debug console on the right of the main GUI."""
        w = DebugPanel.PANEL_WIDTH
        target = self.width() + (w if on else -w)      # compute before min-size changes
        self.btn_debug.setText("Debug  ◂" if on else "Debug  ▸")
        self.setMinimumWidth(BASE_MIN_WIDTH + (w if on else 0))
        self.debug.setVisible(on)
        if not (self.isMaximized() or self.isFullScreen()):
            self.resize(target, self.height())

    # ---- helpers used by pages ----------------------------------------
    def flash(self, msg):
        self.state.setText(msg)
        QTimer.singleShot(2200, lambda: self.state.setText(
            f"Playing  ·  {self.engine.inst['name']}" if self.engine.inst else "Stopped"))

    def go_page(self, i):
        self.nav.setCurrentRow(i)

    def all_patterns(self):
        return [("Built-in", [default_instance(c) for c in BUILTINS], "builtin"),
                ("My Presets", self.store.data["presets"], "preset"),
                ("Custom", self.store.data["customs"], "custom")]

    def led_count_changed(self):
        self.page_custom.led_count_changed()

    # ---- data path -----------------------------------------------------
    def on_frame(self, frame):
        self.preview.set_colors(frame)
        if self.link.connected:
            st = self.store.settings
            self.link.send(encode(frame, st["order"], st["protocol"]))

    def _brightness(self, v):
        self.engine.brightness = v / 100
        self.bval.setText(f"{v}%")
        self.store.settings["brightness"] = v

    def set_connected(self, on, text=None):
        self.dot.setStyleSheet(f"color:{'#34c759' if on else '#c7c7cc'};")
        self.status.setText(text or "Not connected")
        self.page_device.set_connected(on)
        self.debug.log_info(text if on else (text or "Disconnected"))

    def disconnect_serial(self):
        self.link.close()
        self.set_connected(False)

    def _link_error(self, msg):
        self.link.close()
        self.set_connected(False, "Connection lost")
        self.debug.log_error(msg)
        QMessageBox.warning(self, APP_NAME, f"Serial connection lost:\n{msg}")

    def closeEvent(self, e):
        self.engine.stop()
        if self.link.connected:
            QThread.msleep(120)
        self.link.close()
        self.store.save()
        super().closeEvent(e)
