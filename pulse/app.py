"""Pulse's UI. Tk is accessed exclusively from its main thread."""
from dataclasses import replace
from pathlib import Path
import queue
import sys
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from . import __version__
from .engine import ClickEngine
from .model import Settings, load_settings, save_settings

BG = "#0c111b"
PANEL = "#151d2c"
FIELD = "#202b3e"
TEXT = "#edf4ff"
MUTED = "#97a8c2"
ACCENTS = {"Mint": ("#59e3b0", "#36ba8a"), "Violet": ("#b29bff", "#9277e0"), "Sky": ("#66c7ff", "#409ed6")}


class App(ctk.CTk):
    def __init__(self, smoke=False):
        super().__init__()
        self.title("Pulse Clicker")
        self.geometry("560x850")
        self.minsize(530, 680)
        self.configure(fg_color=BG)
        self.smoke = smoke
        self.settings = load_settings()
        self.events = queue.Queue(maxsize=2048)
        self.armed = False
        self.capturing = False
        self.picking = False
        self.closing = False
        self._bounds = (0, 0, 0, 0)
        self._accent_widgets = []
        self.fields = {}
        self.bridge = None
        self.engine = ClickEngine(lambda settings: None)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self._build()
        self.apply_accent(self.settings.accent)
        self.attributes("-topmost", self.settings.topmost)
        root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
        try:
            self._icon = tk.PhotoImage(file=str(root / "assets/icon.png"))
            self.iconphoto(True, self._icon)
            if sys.platform == "win32":
                self.iconbitmap(str(root / "assets/icon.ico"))
        except tk.TclError:
            pass
        if not smoke:
            try:
                from .input import InputBridge
                self.bridge = InputBridge(self.events)
                self.engine.output = self.emit
                self.bridge.start()
            except Exception as exc:
                self.status.configure(text="Input unavailable", text_color="#ff8585")
                self.note.configure(text=f"Could not enable desktop input: {exc}")
                self.start_button.configure(state="disabled")
        self.after(30, self.poll)

    def label(self, parent, text, size=13, color=TEXT, **kw):
        return ctk.CTkLabel(parent, text=text, text_color=color, font=("Segoe UI", size), **kw)

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=26, pady=(22, 14))
        self.logo = self.label(header, "◈", 36)
        self.logo.pack(side="left", padx=(0, 12))
        title = ctk.CTkFrame(header, fg_color="transparent")
        title.pack(side="left")
        self.label(title, "PULSE", 24).pack(anchor="w")
        self.label(title, "Your rhythm. Every click.", 12, MUTED).pack(anchor="w")
        self.label(header, f"v{__version__}", 11, MUTED).pack(side="right")

        hero = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=18)
        hero.pack(fill="x", padx=24, pady=(0, 12))
        line = ctk.CTkFrame(hero, fg_color="transparent")
        line.pack(fill="x", padx=20, pady=(15, 4))
        self.status = self.label(line, "●  Ready", 16)
        self.status.pack(side="left")
        self.count = self.label(line, "0 clicks", 16)
        self.count.pack(side="right")
        self.note = self.label(hero, "F6 to start / stop  ·  Esc stops everything", 12, MUTED, wraplength=460)
        self.note.pack(anchor="w", padx=20, pady=(0, 14))

        bottom = ctk.CTkFrame(self, fg_color=BG)
        bottom.pack(side="bottom", fill="x", padx=24, pady=(12, 18))
        self.start_button = ctk.CTkButton(bottom, text="Start clicking", height=46, corner_radius=12,
                                         font=("Segoe UI", 15, "bold"), command=self.activate)
        self.start_button.pack(fill="x")
        self._accent_widgets.append(self.start_button)
        self.label(bottom, "ESC  •  emergency stop     |     Settings save automatically", 11, MUTED).pack(pady=(9, 0))

        body = ctk.CTkScrollableFrame(self, fg_color=BG, scrollbar_button_color=FIELD)
        body.pack(fill="both", expand=True, padx=18)
        body.grid_columnconfigure(0, weight=1)
        self.body = body

        rate = self.card("01  /  CLICK RHYTHM")
        rate.grid_columnconfigure((0, 1), weight=1)
        self.entry(rate, "Clicks per second", "cps", self.settings.cps, 0, 0)
        self.option(rate, "Output button", "button", ["left", "right", "middle"], self.settings.button, 0, 1)
        presets = ctk.CTkFrame(rate, fg_color="transparent")
        presets.grid(row=3, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 12))
        self.label(presets, "QUICK SET", 10, MUTED).pack(side="left", padx=(0, 12))
        for value in (1, 10, 25, 50, 100):
            ctk.CTkButton(presets, text=str(value), width=48, height=26, fg_color=FIELD,
                          hover_color="#32425c", command=lambda v=value: self.set_rate(v)).pack(side="left", padx=3)

        activation = self.card("02  /  ACTIVATION")
        activation.grid_columnconfigure((0, 1), weight=1)
        self.option(activation, "Mode", "mode", ["Toggle", "Hold key", "Hold mouse"], self.settings.mode, 0, 0, self.mode_changed)
        self.option(activation, "Mouse hold trigger", "hold_button", ["left", "right", "middle", "x1", "x2"], self.settings.hold_button, 0, 1)
        self.label(activation, "Keyboard shortcut", 12, MUTED).grid(row=3, column=0, sticky="w", padx=16)
        self.bind_button = ctk.CTkButton(activation, text=f"{self.settings.hotkey.upper()}  ·  Change", fg_color=FIELD,
                                       hover_color="#32425c", height=32, command=self.capture_key)
        self.bind_button.grid(row=4, column=0, sticky="ew", padx=16, pady=(4, 14))
        self.hotkey = self.settings.hotkey
        self.entry(activation, "Start delay (seconds)", "delay", self.settings.delay, 1, 1)

        options = self.card("03  /  FINE TUNE")
        options.grid_columnconfigure((0, 1), weight=1)
        self.entry(options, "Click limit · 0 = unlimited", "limit", self.settings.limit, 0, 0)
        self.entry(options, "Timing variation (%)", "jitter", self.settings.jitter, 0, 1)
        self.check(options, "Double-click each pulse", "double", self.settings.double, 3, 0)
        self.check(options, "Use fixed position", "fixed", self.settings.fixed, 3, 1)
        self.entry(options, "X coordinate", "x", self.settings.x, 3, 0)
        self.entry(options, "Y coordinate", "y", self.settings.y, 3, 1)
        self.pick_button = ctk.CTkButton(options, text="Pick cursor position  ·  3 second countdown", height=30,
                                       fg_color=FIELD, hover_color="#32425c", command=self.pick_position)
        self.pick_button.grid(row=9, column=0, columnspan=2, padx=16, pady=(0, 14), sticky="ew")

        appearance = self.card("04  /  MAKE IT YOURS")
        appearance.grid_columnconfigure((0, 1), weight=1)
        self.option(appearance, "Accent color", "accent", list(ACCENTS), self.settings.accent, 0, 0, self.apply_accent)
        self.check(appearance, "Always on top", "topmost", self.settings.topmost, 2, 1,
                   lambda: self.attributes("-topmost", self.fields["topmost"].get()))
        self.label(body, "Clicks pause over this window. Limits count pulses; a double pulse sends two clicks.",
                   11, MUTED, wraplength=460).pack(pady=(4, 12))
        self.mode_changed(self.settings.mode)

    def card(self, title):
        frame = ctk.CTkFrame(self.body, fg_color=PANEL, corner_radius=14)
        frame.pack(fill="x", padx=0, pady=(0, 12))
        self.label(frame, title, 11, MUTED).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(13, 8))
        return frame

    def entry(self, parent, title, name, value, row, col):
        self.label(parent, title, 12, MUTED).grid(row=row * 2 + 1, column=col, sticky="w", padx=16)
        var = tk.StringVar(value=str(value))
        self.fields[name] = var
        widget = ctk.CTkEntry(parent, textvariable=var, height=34, fg_color=FIELD, border_width=0)
        widget.grid(row=row * 2 + 2, column=col, sticky="ew", padx=16, pady=(4, 14))

    def option(self, parent, title, name, values, value, row, col, command=None):
        self.label(parent, title, 12, MUTED).grid(row=row * 2 + 1, column=col, sticky="w", padx=16)
        var = tk.StringVar(value=value)
        self.fields[name] = var
        widget = ctk.CTkOptionMenu(parent, variable=var, values=values, height=34, fg_color=FIELD,
                                  button_color="#2b3951", button_hover_color="#364967", command=command)
        widget.grid(row=row * 2 + 2, column=col, sticky="ew", padx=16, pady=(4, 14))
        setattr(self, f"{name}_widget", widget)

    def check(self, parent, title, name, value, row, col, command=None):
        var = tk.BooleanVar(value=value)
        self.fields[name] = var
        widget = ctk.CTkCheckBox(parent, text=title, variable=var, font=("Segoe UI", 12),
                                checkbox_width=18, checkbox_height=18, command=command)
        widget.grid(row=row, column=col, sticky="w", padx=16, pady=(4, 14))
        self._accent_widgets.append(widget)

    def apply_accent(self, value):
        color, hover = ACCENTS[value]
        self.logo.configure(text_color=color)
        for widget in self._accent_widgets:
            widget.configure(fg_color=color, hover_color=hover, text_color="#101726" if isinstance(widget, ctk.CTkButton) else TEXT)

    def mode_changed(self, value):
        self.hold_button_widget.configure(state="normal" if value == "Hold mouse" else "disabled")
        if self.armed or self.engine.active:
            self.stop()

    def set_rate(self, value):
        self.fields["cps"].set(str(value))

    def collect(self):
        data = {name: variable.get() for name, variable in self.fields.items()}
        for name in ("cps", "delay", "jitter"):
            data[name] = float(data[name])
        for name in ("limit", "x", "y"):
            data[name] = int(data[name])
        return Settings(**data, hotkey=self.hotkey).validate()

    def persist(self):
        try:
            self.settings = self.collect()
            if not self.smoke:
                save_settings(self.settings)
            return True
        except (ValueError, OSError) as exc:
            messagebox.showerror("Check settings", str(exc), parent=self)
            return False

    def capture_key(self):
        self.stop()
        self.capturing = True
        self.bind_button.configure(text="Press a key…  ·  Esc cancels")

    def pick_position(self):
        if self.picking:
            return
        self.stop()
        self.picking = True
        self._pick_countdown(3)

    def _pick_countdown(self, remaining):
        if self.closing or not self.picking:
            return
        if remaining:
            self.pick_button.configure(text=f"Move your cursor to the target… {remaining}")
            self.after(1000, lambda: self._pick_countdown(remaining - 1))
        else:
            if self.bridge:
                x, y = self.bridge.position()
                self.fields["x"].set(str(x))
                self.fields["y"].set(str(y))
                self.fields["fixed"].set(True)
            self.picking = False
            self.pick_button.configure(text="Pick cursor position  ·  3 second countdown")

    def activate(self):
        if self.picking or self.capturing:
            return
        if self.engine.active or self.armed:
            self.stop()
            return
        if not self.persist():
            return
        self.armed = True
        if self.settings.mode == "Toggle":
            self.engine.start(self.settings)

    def stop(self):
        self.armed = False
        self.engine.stop()

    def handle(self, kind, name, pressed):
        if kind == "key" and name == "esc" and pressed:
            self.stop()
            self.capturing = False
            self.picking = False
            self.pick_button.configure(text="Pick cursor position  ·  3 second countdown")
            self.bind_button.configure(text=f"{self.hotkey.upper()}  ·  Change")
            return
        if self.capturing:
            if kind == "key" and pressed:
                try:
                    replace(Settings(), hotkey=name).validate()
                except ValueError:
                    self.bind_button.configure(text="Unsupported key · try F6")
                else:
                    self.hotkey = name
                    self.capturing = False
                    self.bind_button.configure(text=f"{name.upper()}  ·  Change")
            return
        mode = self.fields["mode"].get()
        if kind == "key" and name == self.hotkey:
            if mode == "Toggle" and pressed:
                self.activate()
            elif mode == "Hold key":
                if pressed and not self.engine.active:
                    if self.persist():
                        self.armed = True
                        self.engine.start(self.settings)
                elif not pressed:
                    self.engine.stop()
        elif mode == "Hold mouse" and self.armed and kind == "mouse" and name == self.settings.hold_button:
            if pressed:
                x, y = self.bridge.position() if self.bridge else (-1, -1)
                if not self.inside(x, y):
                    self.engine.start(self.settings)
            else:
                self.engine.stop()

    def inside(self, x, y):
        left, top, right, bottom = self._bounds
        return left <= x <= right and top <= y <= bottom

    def emit(self, settings):
        position = (settings.x, settings.y) if settings.fixed else self.bridge.position()
        if self.inside(*position):
            return False
        self.bridge.click(settings)
        return True

    def poll(self):
        if self.closing:
            return
        self._bounds = (self.winfo_rootx(), self.winfo_rooty() - 32,
                        self.winfo_rootx() + self.winfo_width(), self.winfo_rooty() + self.winfo_height())
        for _ in range(100):
            try:
                self.handle(*self.events.get_nowait())
            except queue.Empty:
                break
        snapshot = self.engine.snapshot()
        if snapshot.state in ("Complete", "Error"):
            self.armed = False
        active = self.engine.active
        state = snapshot.state if active or not self.armed else "Armed"
        self.status.configure(text=f"●  {state}", text_color=ACCENTS[self.fields["accent"].get()][0])
        self.count.configure(text=f"{snapshot.clicks:,} pulses  ·  {snapshot.elapsed:.1f}s")
        mode = self.fields["mode"].get()
        if not self.bridge and not self.smoke:
            self.status.configure(text="●  Input unavailable", text_color="#ff8585")
        else:
            hint = {"Toggle": f"{self.hotkey.upper()} to start / stop", "Hold key": f"Hold {self.hotkey.upper()} to click", "Hold mouse": "Arm, then hold your trigger outside this window"}[mode]
            self.note.configure(text=snapshot.error or f"{hint}  ·  Esc stops everything")
        self.start_button.configure(text="Stop" if active or self.armed else ("Arm mouse hold" if mode == "Hold mouse" else "Start clicking" if mode == "Toggle" else "Arm key hold"))
        self.after(30, self.poll)

    def close(self):
        self.closing = True
        self.engine.close()
        if self.bridge:
            self.bridge.close()
        try:
            if not self.smoke:
                save_settings(self.collect())
        except (ValueError, OSError):
            pass
        for callback in self.tk.call("after", "info"):
            self.after_cancel(callback)
        self.destroy()


def main():
    ctk.set_appearance_mode("dark")
    app = App(smoke="--smoke-test" in sys.argv)
    if "--smoke-test" in sys.argv:
        def check():
            assert app.collect().validate()
            app.apply_accent("Violet")
            app.apply_accent("Mint")
            app.set_rate(25)
            assert app.collect().cps == 25
            app.set_rate(10)
            if "--screenshot" in sys.argv:
                from PIL import ImageGrab
                app.update()
                if sys.platform == "win32":
                    import ctypes
                    hwnd = ctypes.windll.user32.GetParent(app.winfo_id())
                    ImageGrab.grab(window=hwnd).save("preview.png")
            app.close()
        app.after(1200, check)
    app.mainloop()
