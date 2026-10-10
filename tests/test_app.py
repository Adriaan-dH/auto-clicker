"""Run explicitly with a desktop or xvfb; no hooks or real clicks are emitted."""
import os
import sys
import time
import unittest
from unittest.mock import patch
from pulse.model import Settings


@unittest.skipUnless(sys.platform == "win32" or os.environ.get("DISPLAY"), "GUI requires a display")
class AppTests(unittest.TestCase):
    def setUp(self):
        from pulse.app import App
        with patch("pulse.app.load_settings", return_value=Settings(delay=0)):
            self.app = App(smoke=True)
        self.app.withdraw()
        self.app.update()

    def tearDown(self):
        self.app.close()

    def test_toggle_and_emergency_stop(self):
        self.app.handle("key", "f6", True)
        self.assertTrue(self.app.engine.active)
        self.app.handle("key", "f6", False)
        self.assertTrue(self.app.engine.active)
        self.app.handle("key", "esc", True)
        self.assertFalse(self.app.engine.active)
        self.assertFalse(self.app.armed)

    def test_key_hold_release_cancels_delay(self):
        self.app.fields["mode"].set("Hold key")
        self.app.fields["delay"].set("5")
        self.app.handle("key", "f6", True)
        self.assertTrue(self.app.engine.active)
        self.app.handle("key", "f6", False)
        self.assertFalse(self.app.engine.active)
        self.assertEqual(self.app.engine.snapshot().clicks, 0)

    def test_mouse_hold_requires_arm_and_release_stops(self):
        self.app.fields["mode"].set("Hold mouse")
        self.app.handle("mouse", "right", True)
        self.assertFalse(self.app.engine.active)
        self.app.activate()
        self.app.handle("mouse", "right", True)
        self.assertTrue(self.app.engine.active)
        self.app.handle("mouse", "right", False)
        self.assertFalse(self.app.engine.active)
        self.assertTrue(self.app.armed)

    def test_binding_and_cancel(self):
        self.app.capture_key()
        self.app.handle("key", "ctrl", True)
        self.assertTrue(self.app.capturing)
        self.app.handle("key", "g", True)
        self.assertEqual(self.app.hotkey, "g")
        self.assertFalse(self.app.capturing)
        self.app.pick_position()
        self.assertTrue(self.app.picking)
        self.app.handle("key", "esc", True)
        self.assertFalse(self.app.picking)

    def test_themes_and_output_guard(self):
        for accent in ("Mint", "Violet", "Sky"):
            self.app.apply_accent(accent)
        self.app._bounds = (10, 10, 200, 200)
        self.assertFalse(self.app.emit(Settings(fixed=True, x=100, y=100)))

    def test_custom_rate_warning_tracks_edits_and_presets(self):
        for value, warned in ((200, False), (200.1, True), (500, True), (1000, True), (4321.5, True), (10000, True), (10, False)):
            with self.subTest(value=value):
                self.app.set_rate(value)
                self.assertEqual(self.app.collect().cps, value)
                self.assertEqual(bool(self.app.rate_warning.grid_info()), warned)
        self.app.fields["cps"].set("")
        self.assertFalse(self.app.rate_warning.grid_info())


if __name__ == "__main__":
    unittest.main()
