"""Application-wide constants and default settings."""


APP_NAME = "LED Controller"


DEFAULTS = {
    "settings": {"port": "", "baud": 115200, "led_count": 60, "protocol": "adalight",
                 "order": "RGB", "fps": 30, "brightness": 80},
    "presets": [],
    "customs": [],
    "sequence": {"items": [], "loop": True},
}
