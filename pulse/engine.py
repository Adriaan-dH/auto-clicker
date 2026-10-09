"""Interruptible click scheduling. Hooks and GUI never perform click loops."""
from dataclasses import dataclass
import random
import threading
import time
from .model import Settings


@dataclass(frozen=True)
class Snapshot:
    state: str
    clicks: int
    elapsed: float
    error: str


class ClickEngine:
    def __init__(self, output):
        self.output = output
        self._lock = threading.RLock()
        self._wake = threading.Event()
        self._closed = False
        self._active = False
        self._generation = 0
        self._settings = Settings()
        self._count = 0
        self._started = 0.0
        self._elapsed = 0.0
        self._state = "Ready"
        self._error = ""
        self._thread = threading.Thread(target=self._run, daemon=True, name="click-scheduler")
        self._thread.start()

    def start(self, settings):
        settings.validate()
        with self._lock:
            if self._closed or self._active:
                return
            self._settings = settings
            self._count = 0
            self._started = time.monotonic()
            self._error = ""
            self._active = True
            self._generation += 1
            self._state = "Starting" if settings.delay else "Clicking"
            self._wake.set()

    def stop(self, state="Stopped"):
        with self._lock:
            if self._active:
                self._elapsed = time.monotonic() - self._started
            self._active = False
            self._generation += 1
            self._state = state
            self._wake.set()

    def snapshot(self):
        with self._lock:
            elapsed = time.monotonic() - self._started if self._active else self._elapsed
            return Snapshot(self._state, self._count, elapsed, self._error)

    @property
    def active(self):
        with self._lock:
            return self._active

    def close(self):
        with self._lock:
            self.stop()
            self._closed = True
            self._wake.set()
        self._thread.join(timeout=2)

    def _run(self):
        generation = -1
        deadline = 0.0
        while True:
            with self._lock:
                if self._closed:
                    return
                self._wake.clear()
                if not self._active:
                    wait = None
                else:
                    settings = self._settings
                    if generation != self._generation:
                        generation = self._generation
                        deadline = time.monotonic() + settings.delay
                    wait = max(0, deadline - time.monotonic())
            if wait is None or wait > 0:
                self._wake.wait(wait)
                continue
            # Synchronize stop with emission: once stop returns no new click starts.
            with self._lock:
                if not self._active or generation != self._generation:
                    continue
                try:
                    emitted = self.output(settings) is not False
                    if emitted:
                        self._count += 1
                    self._state = "Clicking" if emitted else "Paused over app"
                    if settings.limit and self._count >= settings.limit:
                        self.stop("Complete")
                    factor = random.uniform(1 - settings.jitter / 100, 1 + settings.jitter / 100)
                    interval = factor / settings.cps
                    deadline = max(deadline + interval, time.monotonic())
                except Exception as exc:
                    self._error = str(exc)
                    self.stop("Error")
