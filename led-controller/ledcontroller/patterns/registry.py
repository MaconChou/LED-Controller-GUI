"""Factory helpers for pattern instances."""
from ledcontroller.patterns.builtin import BUILTIN_MAP
from ledcontroller.patterns.custom import CustomPattern


def default_instance(cls):
    return {"kind": "builtin", "id": cls.id, "name": cls.name,
            "params": {s[0]: s[3] for s in cls.params}}


def make_renderer(inst, n):
    if inst["kind"] == "custom":
        return CustomPattern(n, inst)
    cls = BUILTIN_MAP[inst["id"]]
    params = {s[0]: s[3] for s in cls.params}
    params.update(inst.get("params", {}))
    return cls(n, params)
