"""Validated settings and atomic, per-user persistence (no GUI dependencies)."""
from dataclasses import asdict, dataclass
import json
import math
import os
from pathlib import Path
import sys

MAX_CPS = 10_000
CPS_WARNING_THRESHOLD = 200


@dataclass(frozen=True)
class Settings:
    cps: float = 10.0
    button: str = "left"
    mode: str = "Toggle"
    hotkey: str = "f6"
    hold_button: str = "right"
    limit: int = 0
    delay: float = 0.5
    jitter: float = 0.0
    double: bool = False
    fixed: bool = False
    x: int = 0
    y: int = 0
    accent: str = "Mint"
    topmost: bool = False

    def validate(self):
        for name, low, high in (("cps", 0.1, MAX_CPS), ("delay", 0, 30), ("jitter", 0, 50)):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f"{name.upper()} must be between {low} and {high}.")
        if type(self.limit) is not int or not 0 <= self.limit <= 10_000_000:
            raise ValueError("Click limit must be a whole number from 0 to 10,000,000.")
        for name in ("x", "y"):
            if type(getattr(self, name)) is not int or not -100_000 <= getattr(self, name) <= 100_000:
                raise ValueError("Coordinates must be whole numbers between -100,000 and 100,000.")
        for name in ("double", "fixed", "topmost"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be true or false.")
        for name, choices in (("button", ("left", "right", "middle")),
                              ("mode", ("Toggle", "Hold key", "Hold mouse")),
                              ("hold_button", ("left", "right", "middle", "x1", "x2")),
                              ("accent", ("Mint", "Violet", "Sky"))):
            if getattr(self, name) not in choices:
                raise ValueError(f"Invalid {name}.")
        keys = {f"f{i}" for i in range(1, 13)} | set("abcdefghijklmnopqrstuvwxyz0123456789") | {"space", "insert", "home", "end", "page_up", "page_down"}
        if self.hotkey not in keys:
            raise ValueError("Choose one letter, digit, F1–F12, Space, Insert, Home, End, Page Up or Page Down.")
        if self.mode == "Hold mouse" and self.hold_button == self.button:
            raise ValueError("Use different trigger and output mouse buttons to avoid a stuck physical hold.")
        return self


def config_path():
    if sys.platform == "win32":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "PulseClicker" / "settings.json"


def load_settings(path=None):
    try:
        data = json.loads((path or config_path()).read_text(encoding="utf-8"))
        return Settings(**data).validate()
    except (OSError, ValueError, TypeError):
        return Settings()


def save_settings(settings, path=None):
    settings.validate()
    target = path or config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(asdict(settings), indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
