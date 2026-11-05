"""Render original plots from the synthetic replay. Only this script needs Pillow."""
import json
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from align import replay

OUT = ROOT / "diagrams"
INK = "#172e49"
BLUE = "#007382"
ORANGE = "#a33a14"
GRID = "#d4e4ec"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def canvas(title):
    image = Image.new("RGB", (840, 420), "#f3f8fa")
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((12, 12, 828, 408), 18, fill="white", outline=GRID, width=2)
    d.text((42, 36), title, fill=INK, font=ImageFont.truetype(FONT, 36))
    return image, d


def text(d, xy, label, color=INK, anchor=None):
    d.text(xy, label, fill=color, font=ImageFont.truetype(FONT, 28), anchor=anchor)


def save(image, name):
    image.save(OUT / f"{name}.webp", "WEBP", quality=86, method=6)


data = json.loads((ROOT / "examples/moving.json").read_text())
rows = replay(data, 80, 50)
im, d = canvas("One frame, two camera poses")
a = rows[0]
for t, label, color in ((0, "0", INK), (a["capture_ms"], "Capture", BLUE),
                        (a["arrival_ms"], "Arrival", ORANGE)):
    x = 110 + t * 7.5
    d.line((x, 144, x, 305), fill=GRID, width=2)
    d.ellipse((x-8, 223, x+8, 239), fill=color)
    text(d, (x, 126), label, color, "mt")
    text(d, (x, 275), f"{t} ms", color, "mt")
d.line((110, 231, 710, 231), fill=INK, width=2)
text(d, (260, 193), "Camera X = 4 mm", BLUE, "mt")
text(d, (710, 193), "16 mm", ORANGE, "mt")
text(d, (42, 350), f"Frame delay: {a['age_ms']} ms  •  Camera travel: {a['arrival_bias_mm']:.0f} mm")
save(im, "camera-pose-timeline")

im, d = canvas("Estimated landmark position")
for x in (96, 100, 104, 108, 112):
    px = 180 + (x - 96) * 29
    d.line((px, 142, px, 331), fill=GRID, width=2)
    text(d, (px, 350), str(x), anchor="mt")
for y, r in zip((187, 269), rows):
    text(d, (45, y), f"{r['age_ms']} ms", anchor="lm")
    a = 180 + (r["target_at_capture_mm"] - 96) * 29
    b = 180 + (r["target_using_arrival_mm"] - 96) * 29
    d.line((a, y, b, y), fill=GRID, width=5)
    d.ellipse((a-10, y-10, a+10, y+10), fill=BLUE)
    d.rectangle((b-9, y-9, b+9, y+9), fill=ORANGE)
text(d, (42, 96), "● Capture pose", BLUE)
text(d, (395, 96), "■ Arrival pose", ORANGE)
text(d, (750, 350), "mm", anchor="mt")
save(im, "camera-latency-bias")
