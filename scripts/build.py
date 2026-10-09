"""Build on the target OS: python scripts/build.py."""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent.parent
command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--windowed",
           "--name", "PulseClicker", "--collect-all", "customtkinter",
           "--add-data", f"{root / 'assets'}:assets",
           "--icon", str(root / "assets/icon.ico")]
for package in ("pynput", "pillow", "six", "packaging", "darkdetect"):
    command += ["--copy-metadata", package]
if sys.platform == "win32":
    command += ["--hidden-import", "pynput.keyboard._win32", "--hidden-import", "pynput.mouse._win32"]
else:
    command += ["--hidden-import", "pynput.keyboard._xorg", "--hidden-import", "pynput.mouse._xorg"]
subprocess.run(command + [str(root / "main.py")], cwd=root, check=True)
