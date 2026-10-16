import pytest

from ledcontroller.patterns import BUILTINS, default_instance, make_renderer


@pytest.mark.parametrize("cls", BUILTINS, ids=lambda c: c.id)
def test_builtin_renders_valid_frames(cls):
    r = make_renderer(default_instance(cls), 60)
    for k in range(10):
        frame = r.render(k * 0.1)
        assert len(frame) == 60
        assert all(0 <= v <= 255 for px in frame for v in px)


def test_custom_pattern_fade_and_resample():
    inst = {"kind": "custom", "name": "t", "frames": [
        {"colors": ["#000000"] * 10, "duration": 1.0, "fade": True},
        {"colors": ["#ffffff"] * 10, "duration": 1.0, "fade": False}]}
    r = make_renderer(inst, 20)               # resampled 10 -> 20
    assert len(r.render(0.0)) == 20
    assert r.render(0.5)[0] == (127, 127, 127)  # halfway fade
    assert r.render(1.5)[0] == (255, 255, 255)
