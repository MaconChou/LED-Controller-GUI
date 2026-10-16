"""Serial port discovery."""
from dataclasses import dataclass

from serial.tools import list_ports


@dataclass(frozen=True)
class PortInfo:
    device: str        # "COM3", "/dev/ttyUSB0" ...
    description: str
    is_usb: bool


def list_serial_ports():
    """Return available serial ports, USB devices first."""
    ports = sorted(list_ports.comports(), key=lambda p: (p.vid is None, p.device))
    out = []
    for p in ports:
        desc = p.description if p.description and p.description != "n/a" else "Serial device"
        out.append(PortInfo(p.device, desc, p.vid is not None))
    return out
