"""Debug console: live view of data sent to / received from the LED controller."""
import html
import time

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout,
)

from ledcontroller.serial_io.formatting import (
    ASCII, HEX, HEX_ASCII, describe_adalight, format_bytes, human_size, parse_hex,
)
from ledcontroller.ui.widgets.helpers import caption, plain_spin
from ledcontroller.ui.widgets.switch import Switch

COLORS = {"TX": "#64b5ff", "RX": "#5ee07d", "INFO": "#8e8e93",
          "STATE": "#c792ea", "ERROR": "#ff6b6b"}
FORMATS = [("Hex + ASCII", HEX_ASCII), ("Hex", HEX), ("ASCII", ASCII)]
RATES = [("5 frames / sec", 0.2), ("10 frames / sec", 0.1), ("2 frames / sec", 0.5),
         ("1 frame / sec", 1.0), ("Every frame", 0.0)]


class DebugPanel(QFrame):
    """Right-hand side panel; shown/hidden by the main window."""
    PANEL_WIDTH = 520
    closeRequested = Signal()

    def __init__(self, link):
        super().__init__()
        self.link = link
        self.setObjectName("DebugPanel")
        self.setFixedWidth(self.PANEL_WIDTH)
        self._last_tx_bytes, self._last_t = 0, time.time()

        v = QVBoxLayout(self)
        v.setContentsMargins(16, 20, 16, 14)
        v.setSpacing(10)

        head = QHBoxLayout()
        title = QLabel("Debug Console")
        title.setObjectName("h2")
        head.addWidget(title)
        head.addStretch(1)
        b_hide = QPushButton("Hide  ▸")
        b_hide.clicked.connect(self.closeRequested)
        head.addWidget(b_hide)
        v.addLayout(head)

        # filters
        row = QHBoxLayout()
        row.setSpacing(8)
        self.sw_tx, self.sw_rx, self.sw_pause = Switch(True), Switch(True), Switch(False)
        for sw, text in ((self.sw_tx, "TX"), (self.sw_rx, "RX"), (self.sw_pause, "Pause")):
            row.addWidget(sw)
            row.addWidget(QLabel(text))
            row.addSpacing(8)
        row.addStretch(1)
        v.addLayout(row)

        # display options
        opt = QHBoxLayout()
        self.fmt = QComboBox()
        for label, key in FORMATS:
            self.fmt.addItem(label, key)
        self.fmt.setCurrentIndex(1)          # plain hex fits the panel width best
        self.rate = QComboBox()
        for label, sec in RATES:
            self.rate.addItem(label, sec)
        self.rate.currentIndexChanged.connect(self._rate_changed)
        self.limit = plain_spin(QSpinBox())
        self.limit.setRange(8, 4096)
        self.limit.setValue(12)
        self.limit.setSuffix(" B")
        self.limit.setToolTip("Maximum bytes shown per line")
        opt.addWidget(self.fmt)
        opt.addWidget(self.rate, 1)
        opt.addWidget(self.limit)
        v.addLayout(opt)
        v.addWidget(caption("Format · TX frame log rate · bytes shown per line"))

        # console
        self.view = QPlainTextEdit()
        self.view.setObjectName("console")
        self.view.setReadOnly(True)
        self.view.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.view.setMaximumBlockCount(3000)
        mono = QFont()
        mono.setFamilies(["Menlo", "SF Mono", "Consolas", "DejaVu Sans Mono",
                          "Liberation Mono", "monospace"])
        mono.setStyleHint(QFont.Monospace)
        mono.setPixelSize(12)
        self.view.setFont(mono)
        v.addWidget(self.view, 1)

        self.stats = QLabel("")
        self.stats.setObjectName("caption")
        v.addWidget(self.stats)

        # manual send
        send = QHBoxLayout()
        self.send_edit = QLineEdit()
        self.send_edit.setPlaceholderText("Send…   hex: 41 64 61    or text")
        self.send_edit.returnPressed.connect(self._send)
        self.send_mode = QComboBox()
        self.send_mode.addItems(["Hex", "Text", "Text + LF"])
        b_send = QPushButton("Send")
        b_send.clicked.connect(self._send)
        send.addWidget(self.send_edit, 1)
        send.addWidget(self.send_mode)
        send.addWidget(b_send)
        v.addLayout(send)

        bot = QHBoxLayout()
        b_clear = QPushButton("Clear")
        b_clear.clicked.connect(self.view.clear)
        b_save = QPushButton("Save Log…")
        b_save.clicked.connect(self._save)
        bot.addWidget(b_clear)
        bot.addWidget(b_save)
        bot.addStretch(1)
        v.addLayout(bot)

        link.tx.connect(self.on_tx)
        link.rx.connect(self.on_rx)
        self._rate_changed()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_stats)
        self._timer.start(500)
        self._update_stats()

    # ---- logging API ---------------------------------------------------
    def log_info(self, text):
        self._line("INFO", time.time(), text)

    def log_state(self, text):
        self._line("STATE", time.time(), text)

    def log_error(self, text):
        self._line("ERROR", time.time(), text)

    def on_tx(self, ts, data):
        if self.sw_tx.isChecked():
            self._data_line("TX", ts, data, describe_adalight(data))

    def on_rx(self, ts, data):
        if self.sw_rx.isChecked():
            self._data_line("RX", ts, data)

    # ---- internals -----------------------------------------------------
    def _data_line(self, kind, ts, data, note=None):
        body = format_bytes(data, self.fmt.currentData(), self.limit.value())
        text = f"{len(data):>5} B  {body}"
        if note:
            text += f"   [{note}]"
        self._line(kind, ts, text)

    def _line(self, kind, ts, text):
        if self.sw_pause.isChecked():
            return
        stamp = time.strftime("%H:%M:%S", time.localtime(ts)) + f".{int(ts * 1000) % 1000:03d}"
        col = COLORS[kind]
        self.view.appendHtml(
            '<span style="white-space:pre">'
            f'<span style="color:#6e6e73">{stamp}</span>  '
            f'<span style="color:{col};font-weight:600">{kind:<5}</span> '
            f'<span style="color:#d4d4d4">{html.escape(text)}</span></span>')

    def _rate_changed(self):
        self.link.tx_interval = self.rate.currentData()

    def _update_stats(self):
        now = time.time()
        dt = max(1e-3, now - self._last_t)
        rate = max(0, self.link.tx_bytes - self._last_tx_bytes) / dt
        self._last_tx_bytes, self._last_t = self.link.tx_bytes, now
        self.stats.setText(
            f"TX {human_size(self.link.tx_bytes)} · {self.link.tx_frames} frames · "
            f"{human_size(int(rate))}/s     RX {human_size(self.link.rx_bytes)}")

    def _send(self):
        text = self.send_edit.text()
        if not text:
            return
        try:
            data = parse_hex(text) if self.send_mode.currentIndex() == 0 else text.encode()
        except ValueError as e:
            self.log_error(str(e))
            return
        if self.send_mode.currentIndex() == 2:
            data += b"\n"
        if not self.link.connected:
            self.log_error("Not connected – nothing sent")
            return
        self.link.send_raw(data)

    def _save(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Log", "led-debug.log", "Log (*.log *.txt)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.view.toPlainText())
