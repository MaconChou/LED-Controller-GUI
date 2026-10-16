"""Device page: serial port, baud rate and strip settings."""
import sys
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
)

from ledcontroller.constants import APP_NAME
from ledcontroller.serial_io.ports import list_serial_ports
from ledcontroller.ui.pages.base import Page
from ledcontroller.ui.widgets.helpers import caption, make_card, plain_spin, primary


class DevicePage(Page):
    def __init__(self, app):
        super().__init__(app, "Device", "Choose the USB serial port your LED controller is plugged into.")
        s = app.store.settings
        card = make_card()
        g = QGridLayout(card)
        g.setContentsMargins(20, 18, 20, 18)
        g.setVerticalSpacing(14)
        g.setHorizontalSpacing(14)

        self.port = QComboBox()
        self.port.setMinimumWidth(320)
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(lambda: self.refresh_ports(True))
        self.baud = QComboBox()
        self.baud.setEditable(True)
        for b in (9600, 57600, 115200, 230400, 250000, 460800, 500000, 921600, 1000000, 2000000):
            self.baud.addItem(str(b))
        self.baud.setCurrentText(str(s["baud"]))
        self.btn_connect = primary(QPushButton("Connect"))
        self.btn_connect.setMinimumWidth(110)
        self.btn_connect.clicked.connect(self.toggle_connect)

        self.leds = plain_spin(QSpinBox())
        self.leds.setRange(1, 2000)
        self.leds.setValue(s["led_count"])
        self.leds.valueChanged.connect(self._leds)
        self.proto = QComboBox()
        self.proto.addItem("Adalight  (Ada header)", "adalight")
        self.proto.addItem("Raw RGB stream", "raw")
        self.proto.setCurrentIndex(0 if s["protocol"] == "adalight" else 1)
        self.proto.currentIndexChanged.connect(self._proto)
        self.order = QComboBox()
        for o in ("RGB", "GRB", "BRG", "RBG", "GBR", "BGR"):
            self.order.addItem(o)
        self.order.setCurrentText(s["order"])
        self.order.currentTextChanged.connect(self._order)
        self.fps = plain_spin(QSpinBox())
        self.fps.setRange(5, 120)
        self.fps.setValue(s["fps"])
        self.fps.valueChanged.connect(self._fps)

        rows = [("Serial Port", self.port, self.btn_refresh),
                ("Baud Rate", self.baud, None),
                ("LED Count", self.leds, None),
                ("Protocol", self.proto, None),
                ("Color Order", self.order, None),
                ("Frame Rate", self.fps, None)]
        for r, (lab, w, extra) in enumerate(rows):
            g.addWidget(QLabel(lab), r, 0)
            g.addWidget(w, r, 1, Qt.AlignLeft)
            if extra:
                g.addWidget(extra, r, 2)
        g.addWidget(self.btn_connect, len(rows), 1, Qt.AlignLeft)
        g.setColumnStretch(3, 1)
        self.root.addWidget(card)

        # color test
        tcard = make_card()
        t = QHBoxLayout(tcard)
        t.setContentsMargins(20, 14, 20, 14)
        t.addWidget(QLabel("Quick test"))
        for name, col in (("Red", "#ff0000"), ("Green", "#00ff00"),
                          ("Blue", "#0000ff"), ("White", "#ffffff")):
            b = QPushButton(name)
            b.clicked.connect(lambda _=False, c=col, n=name: self.test(n, c))
            t.addWidget(b)
        t.addStretch(1)
        self.root.addWidget(tcard)

        if sys.platform.startswith("linux"):
            self.root.addWidget(caption(
                "Linux: if the port cannot be opened, add yourself to the serial group:  "
                "sudo usermod -aG dialout $USER   (then log out and in again)."))
        self.root.addWidget(caption(
            "Tip: some boards reset when the port is opened – the first ~2 seconds of output may be ignored."))
        self.root.addStretch(1)

        self._ports = None
        self.refresh_ports()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_ports)
        self.timer.start(2000)

    # settings handlers
    def _leds(self, v):
        self.app.store.settings["led_count"] = v
        self.app.engine.set_n(v)
        self.app.store.save()
        self.app.led_count_changed()

    def _proto(self):
        self.app.store.settings["protocol"] = self.proto.currentData()
        self.app.store.save()

    def _order(self, v):
        self.app.store.settings["order"] = v
        self.app.store.save()

    def _fps(self, v):
        self.app.store.settings["fps"] = v
        self.app.engine.set_fps(v)
        self.app.store.save()

    def test(self, name, col):
        inst = {"kind": "builtin", "id": "solid", "name": f"Test · {name}", "params": {"color1": col}}
        self.app.engine.play_instance(inst)

    def refresh_ports(self, force=False):
        if self.app.link.connected and not force:
            return
        ports = list_serial_ports()
        sig = [(p.device, p.description) for p in ports]
        if sig == self._ports and not force:
            return
        self._ports = sig
        cur = self.port.currentData() or self.app.store.settings.get("port", "")
        self.port.blockSignals(True)
        self.port.clear()
        for p in ports:
            self.port.addItem(f"{p.device}  —  {p.description}", p.device)
        if not ports:
            self.port.addItem("No serial ports found", "")
        i = self.port.findData(cur)
        self.port.setCurrentIndex(max(0, i))
        self.port.blockSignals(False)

    def toggle_connect(self):
        if self.app.link.connected:
            self.app.disconnect_serial()
            return
        port = self.port.currentData()
        if not port:
            QMessageBox.information(self, APP_NAME, "Select a serial port first.")
            return
        try:
            baud = int(self.baud.currentText())
        except ValueError:
            QMessageBox.warning(self, APP_NAME, "Invalid baud rate.")
            return
        try:
            self.app.link.open(port, baud)
        except Exception as e:
            QMessageBox.warning(self, APP_NAME, f"Could not open {port}:\n{e}")
            return
        st = self.app.store.settings
        st["port"], st["baud"] = port, baud
        self.app.store.save()
        self.app.set_connected(True, f"Connected  ·  {port} @ {baud}")

    def set_connected(self, on):
        self.btn_connect.setText("Disconnect" if on else "Connect")
        for w in (self.port, self.baud, self.btn_refresh):
            w.setEnabled(not on)
