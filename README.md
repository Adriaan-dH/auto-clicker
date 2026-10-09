# Pulse Clicker

A compact Python auto clicker with a dark interface, mint / violet / sky accents, and global controls. Built for Windows and Linux desktops.

[Download for Windows](https://github.com/Adriaan-dH/auto-clicker/releases/latest/download/PulseClicker-Windows-x64.exe) · [Download for Linux](https://github.com/Adriaan-dH/auto-clicker/releases/latest/download/PulseClicker-Linux-x64) · [All releases](https://github.com/Adriaan-dH/auto-clicker/releases)

## Use it

On Windows, download and open **PulseClicker-Windows-x64.exe**. Python and installation are not required. The current build is x64 and unsigned; Windows may display a reputation prompt. Verify the downloaded file against its `.sha256` release asset if needed.

On Linux, use an **X11 desktop**, download **PulseClicker-Linux-x64**, then run:

```sh
chmod +x PulseClicker-Linux-x64
./PulseClicker-Linux-x64
```

Linux builds target Ubuntu 22.04 or newer (glibc 2.35+). Native Wayland global input is not supported; choose an X11 / Xorg desktop session. WSL is useful for development, but run the Windows executable to control the Windows desktop.

1. Set the click rate (0.1–200 pulses per second) and output mouse button.
2. Choose an activation mode:
   - **Toggle:** press **F6** or Start to start / stop.
   - **Hold key:** hold **F6** to click; release to stop. The Arm button marks the app ready; holding the shortcut also works directly.
   - **Hold mouse:** click **Arm mouse hold**, then hold the selected trigger outside the app. Release it to stop. Trigger and output buttons must differ.
3. Click **Change** to record a different single keyboard key. Supported keys: letters, digits, F1–F12, Space, Insert, Home, End, Page Up, Page Down. Shortcuts are global; avoid keys used by the target application.
4. **Esc** stops clicking, disarms hold mode, and cancels shortcut / position capture. Closing the app stops the worker and removes hooks.

## Options

| Setting | Behavior |
| --- | --- |
| Click limit | Stop after this many pulses; 0 means unlimited. |
| Start delay | Wait 0–30 seconds at the start of each run or hold. Releasing during the delay cancels it. |
| Double click | Each pulse emits two clicks. A limit of 10 means 20 individual clicks. |
| Timing variation | Randomize each interval by ±0–50%; 0 gives steady timing. |
| Fixed position | Click the specified screen coordinates instead of following the cursor; negative coordinates support monitors left of the primary display. |
| Pick cursor position | Capture the cursor after a three-second countdown, then enable fixed position. Esc cancels. |
| Accent / always on top | Customize the interface and window behavior. |

Clicks pause while the target is over the Pulse window; paused pulses do not consume the limit. Rates are scheduling targets: OS timing and target-app processing can reduce the actual rate. Input into elevated Windows programs may require running Pulse with matching permissions.

Settings save when starting / arming and on exit. Windows stores them in `%APPDATA%\PulseClicker\settings.json`; Linux uses `$XDG_CONFIG_HOME/PulseClicker/settings.json` (default `~/.config/PulseClicker/settings.json`). Invalid settings files fall back to defaults. No network requests or account are required by the app.

## Run from source

Python 3.12 is the tested version. Tkinter is included with standard Windows Python installers. On Ubuntu / Debian install Tk support first (`sudo apt install python3-tk python3-venv`).

```sh
git clone https://github.com/Adriaan-dH/auto-clicker.git
cd auto-clicker
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Use `python3` instead of `python` where required. CustomTkinter supplies the UI; pynput supplies desktop input. The standard-library scheduler uses an interruptible worker thread, while hooks send events to the UI through a queue.

## Test and build

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python main.py --smoke-test
python scripts/build.py
```

The smoke test renders the UI, validates the controls and theme changes, and exits without generating mouse input. On headless Linux run it with `xvfb-run -a`. The build produces `dist/PulseClicker.exe` on Windows or `dist/PulseClicker` on Linux, including the custom icon and UI resources. Build on each target OS; PyInstaller is not a cross-compiler. Regenerate the original icon with `python scripts/make_icon.py`.

Pushes and pull requests run tests and build both platforms in GitHub Actions. To publish a release:

```sh
git tag v1.0.1
git push origin main v1.0.1
```

The release workflow uploads portable binaries and SHA-256 checksums. Future releases should update `pulse/__init__.py` and use a new matching `vX.Y.Z` tag. Release artifacts are unsigned; no signing certificate is configured.

## Dependencies and platform notes

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — modern Tk widgets (MIT).
- [pynput](https://pynput.readthedocs.io/en/latest/) — global keyboard and mouse input (LGPL-3.0). See its [platform limitations](https://pynput.readthedocs.io/en/latest/limitations.html).
- [PyInstaller](https://pyinstaller.org/en/stable/usage.html) — executable packaging (GPL with distribution exception); builds must run on the target OS.
- [Pillow](https://python-pillow.github.io/) — icon generation during development (MIT-CMU).

Dependency licenses remain applicable to bundled distributions. Use automation only where you have permission and where the target application's rules allow it.
