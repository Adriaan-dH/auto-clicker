from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from pulse.model import Settings, load_settings, save_settings


class SettingsTests(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "config/settings.json"
            settings = Settings(cps=1234.5, hotkey="g", accent="Violet", x=-100)
            save_settings(settings, path)
            self.assertEqual(load_settings(path), settings)
            self.assertFalse(path.with_suffix(".tmp").exists())

    def test_corrupt_and_unknown_config_falls_back(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            for content in ("invalid", "[]", '{"cps": 0}', '{"surprise": 1}', '{"cps": "fast"}'):
                path.write_text(content)
                self.assertEqual(load_settings(path), Settings())

    def test_boundaries_and_conflicts(self):
        for field, value in (("cps", float("nan")), ("cps", float("inf")), ("cps", 10000.1), ("cps", .09),
                             ("delay", -1), ("jitter", 51), ("limit", 1.2), ("x", "a"),
                             ("hotkey", "esc"), ("hotkey", "ctrl"), ("double", "false")):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                replace(Settings(), **{field: value}).validate()
        with self.assertRaises(ValueError):
            Settings(mode="Hold mouse", hold_button="left").validate()
        Settings(cps=.1, x=-1920).validate()
        for cps in (201, 500, 1000, 4321.5, 9999.9, 10000):
            with self.subTest(cps=cps):
                Settings(cps=cps).validate()


if __name__ == "__main__":
    unittest.main()
