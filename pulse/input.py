"""Global input hooks; all communication with Tk goes through a queue."""
import queue
import sys
from pynput import keyboard, mouse


def key_name(key):
    char = getattr(key, "char", None)
    return char.lower() if char else getattr(key, "name", "")


class InputBridge:
    def __init__(self, events):
        self.events = events
        self.controller = mouse.Controller()
        self._keys = set()
        options = {}
        if sys.platform == "win32":
            # LLMHF_INJECTED: our output must never become a physical hold event.
            options["win32_event_filter"] = lambda msg, data: not (data.flags & 1)
        self.mouse = mouse.Listener(on_click=self._mouse, **options)
        self.keyboard = keyboard.Listener(on_press=self._press, on_release=self._release)

    def start(self):
        self.mouse.start()
        self.keyboard.start()
        self.mouse.wait()
        self.keyboard.wait()

    def _send(self, event):
        try:
            self.events.put_nowait(event)
        except queue.Full:
            pass

    def _press(self, key, injected=False):
        if injected:
            return
        name = key_name(key)
        if name not in self._keys:
            self._keys.add(name)
            self._send(("key", name, True))

    def _release(self, key, injected=False):
        name = key_name(key)
        self._keys.discard(name)
        self._send(("key", name, False))

    def _mouse(self, x, y, button, pressed, injected=False):
        if not injected:
            self._send(("mouse", button.name, pressed))

    def click(self, settings):
        if settings.fixed:
            self.controller.position = (settings.x, settings.y)
        self.controller.click(getattr(mouse.Button, settings.button), 2 if settings.double else 1)

    def position(self):
        return self.controller.position

    def close(self):
        self.mouse.stop()
        self.keyboard.stop()
