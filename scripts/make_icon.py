"""Draw a crisp vector-style cursor/pulse mark; no external image assets."""
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parent.parent / "assets"
root.mkdir(exist_ok=True)
image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((16, 16, 496, 496), radius=112, fill="#101929")
draw.arc((80, 72, 428, 420), 205, 335, fill="#59e3b0", width=24)
draw.arc((122, 114, 386, 378), 208, 328, fill="#66c7ff", width=15)
draw.polygon([(182, 163), (182, 370), (237, 318), (280, 404), (322, 382), (278, 297), (354, 293)], fill="#edf4ff")
image.resize((256, 256), Image.Resampling.LANCZOS).save(root / "icon.png")
image.save(root / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
