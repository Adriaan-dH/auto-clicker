import os
import queue
import sys
import unittest


@unittest.skipUnless(sys.platform == "win32" or os.environ.get("DISPLAY"), "Input backend requires a desktop")
class InputTests(unittest.TestCase):
    def setUp(self):
        from pulse.input import InputBridge
        self.events = queue.Queue()
        self.bridge = InputBridge(self.events)

    def test_key_repeat_and_injected_events(self):
        from pynput.keyboard import Key
        self.bridge._press(Key.f6)
        self.bridge._press(Key.f6)
        self.assertEqual(self.events.get_nowait(), ("key", "f6", True))
        self.assertTrue(self.events.empty())
        self.bridge._release(Key.f6, injected=True)
        self.bridge._press(Key.f6)
        self.assertTrue(self.events.empty())
        self.bridge._release(Key.f6)
        self.assertEqual(self.events.get_nowait(), ("key", "f6", False))

    def test_mouse_injection_is_ignored(self):
        from pynput.mouse import Button
        self.bridge._mouse(1, 2, Button.right, True, injected=True)
        self.assertTrue(self.events.empty())
        self.bridge._mouse(1, 2, Button.right, True)
        self.assertEqual(self.events.get_nowait(), ("mouse", "right", True))

    def test_native_listeners_start_and_stop(self):
        try:
            self.bridge.start()
            self.assertTrue(self.bridge.mouse.is_alive())
            self.assertTrue(self.bridge.keyboard.is_alive())
        finally:
            self.bridge.close()
            self.bridge.mouse.join(timeout=2)
            self.bridge.keyboard.join(timeout=2)
        self.assertFalse(self.bridge.mouse.is_alive())
        self.assertFalse(self.bridge.keyboard.is_alive())
