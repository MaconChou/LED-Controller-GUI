"""Platform specific paths."""
from pathlib import Path
import os
import sys


def config_dir():
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", str(Path.home())))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    d = base / "LEDController"
    d.mkdir(parents=True, exist_ok=True)
    return d
