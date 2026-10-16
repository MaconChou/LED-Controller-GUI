"""JSON persistence for settings, presets, custom patterns and the sequence."""
import copy
import json

from ledcontroller.constants import DEFAULTS
from ledcontroller.core.paths import config_dir


class Store:
    def __init__(self):
        self.path = config_dir() / "data.json"
        self.data = copy.deepcopy(DEFAULTS)
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            for k, v in loaded.items():
                if isinstance(v, dict) and isinstance(self.data.get(k), dict):
                    self.data[k].update(v)
                else:
                    self.data[k] = v
        except Exception:
            pass

    @property
    def settings(self):
        return self.data["settings"]

    def save(self):
        try:
            self.path.write_text(json.dumps(self.data, indent=1), encoding="utf-8")
        except Exception as e:
            print("save failed:", e)
