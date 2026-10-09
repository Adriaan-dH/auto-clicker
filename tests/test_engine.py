import threading
import time
import unittest
from pulse.engine import ClickEngine
from pulse.model import Settings


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.engine = ClickEngine(lambda settings: self.calls.append(time.monotonic()))

    def tearDown(self):
        self.engine.close()

    def wait_complete(self):
        deadline = time.monotonic() + 2
        while self.engine.active and time.monotonic() < deadline:
            time.sleep(.005)
        self.assertFalse(self.engine.active)

    def test_limit_and_rate(self):
        self.engine.start(Settings(cps=50, delay=0, limit=5))
        self.wait_complete()
        self.assertEqual(len(self.calls), 5)
        self.assertEqual(self.engine.snapshot().state, "Complete")
        self.assertGreaterEqual(self.calls[-1] - self.calls[0], .06)

    def test_stop_interrupts_delay(self):
        self.engine.start(Settings(delay=10))
        time.sleep(.02)
        self.engine.stop()
        time.sleep(.04)
        self.assertEqual(self.calls, [])

    def test_stop_has_no_late_clicks(self):
        self.engine.start(Settings(cps=200, delay=0))
        time.sleep(.04)
        self.engine.stop()
        count = len(self.calls)
        time.sleep(.04)
        self.assertEqual(count, len(self.calls))

    def test_restart_resets_count(self):
        for _ in range(2):
            self.engine.start(Settings(cps=200, delay=0, limit=2))
            self.wait_complete()
            self.assertEqual(self.engine.snapshot().clicks, 2)
        self.assertEqual(len(self.calls), 4)

    def test_failed_output_stops(self):
        def fail(settings):
            raise OSError("Input denied")
        self.engine.output = fail
        self.engine.start(Settings(delay=0))
        self.wait_complete()
        self.assertEqual(self.engine.snapshot().error, "Input denied")
        self.assertEqual(self.engine.snapshot().clicks, 0)

    def test_paused_output_does_not_consume_limit(self):
        self.engine.output = lambda settings: False
        self.engine.start(Settings(cps=100, delay=0, limit=1))
        time.sleep(.04)
        self.assertTrue(self.engine.active)
        self.assertEqual(self.engine.snapshot().clicks, 0)
        self.engine.output = lambda settings: True
        self.wait_complete()
        self.assertEqual(self.engine.snapshot().clicks, 1)

    def test_invalid_settings_do_not_start(self):
        with self.assertRaises(ValueError):
            self.engine.start(Settings(cps=0))
        self.assertFalse(self.engine.active)
