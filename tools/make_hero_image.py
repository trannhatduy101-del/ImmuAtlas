"""Build the hero background image for page 1A.

The source is a photograph-style mockup of a slide deck. It is blurred on the
way in, which is the point of this script rather than a side effect: the
mockup carries legible text of its own, including a large title that would sit
directly behind the hero headline. Blurring reduces it to shape and colour, so
it reads as texture and never competes with the words on top of it.

    python tools/make_hero_image.py
"""
from pathlib import Path

from PIL import Image, ImageFilter

SOURCE = Path(r"D:/Sem B 2026/background landgin page.jpeg")
TARGET = Path(__file__).resolve().parent.parent / "src/static/img/hero-slides.webp"

WIDTH = 1600
# Below about 4 the title in the middle of the mockup becomes readable again.
BLUR_RADIUS = 6
QUALITY = 80


def main() -> None:
    im = Image.open(SOURCE).convert("RGB")
    height = round(im.height * WIDTH / im.width)
    im = im.resize((WIDTH, height), Image.LANCZOS)
    im = im.filter(ImageFilter.GaussianBlur(BLUR_RADIUS))
    im.save(TARGET, "WEBP", quality=QUALITY, method=6)
    print(f"{TARGET.name}: {im.width}x{im.height}, {TARGET.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
