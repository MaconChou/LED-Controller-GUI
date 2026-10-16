import os
import sys
import time

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    from ledcontroller.app import create_app
    return QApplication.instance() or create_app([])


def pump(app, sec):
    end = time.time() + sec
    while time.time() < end:
        app.processEvents()


@pytest.mark.skipif(sys.platform.startswith("win"), reason="needs a pty")
def test_link_tx_rx_via_pty(qapp):
    import pty
    from ledcontroller.serial_io.link import SerialLink

    master, slave = pty.openpty()
    link = SerialLink()
    tx, rx = [], []
    link.tx.connect(lambda ts, d: tx.append(d))
    link.rx.connect(lambda ts, d: rx.append(d))
    link.tx_interval = 0
    link.open(os.ttyname(slave), 115200)
    link.send(b"hello")
    os.write(master, b"pong\n")
    pump(qapp, 0.4)
    link.close()
    assert b"hello" in tx and b"pong\n" in b"".join(rx)
    assert link.tx_bytes == 5 and link.rx_bytes == 5


def test_debug_panel_toggle_and_log(qapp, tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("APPDATA", str(tmp_path))
    from ledcontroller.ui.main_window import MainWindow
    w = MainWindow()
    w.show()
    assert not w.debug.isVisible()
    width = w.width()
    w.btn_debug.setChecked(True)
    pump(qapp, 0.1)
    assert w.debug.isVisible() and w.width() == width + w.debug.PANEL_WIDTH
    w.debug.on_tx(time.time(), b"Ada\x00\x00\x55\x01\x02\x03")
    w.debug.on_rx(time.time(), b"OK\n")
    text = w.debug.view.toPlainText()
    assert "TX" in text and "RX" in text and "Adalight" in text
    w.btn_debug.setChecked(False)
    pump(qapp, 0.1)
    assert not w.debug.isVisible() and w.width() == width
    w.close()
