"""
Rotate the site's blue hues to green, once.

    python tools/recolour.py            # rewrite the files
    python tools/recolour.py --dry-run  # print what would change

Every blue in the stylesheets was picked against a contrast target -- --ink at
~13:1 on paper, --accent at ~5.6:1 -- and those targets are what a hand-edited
palette quietly loses. So this does not replace colours: it converts each one to
OKLCH, keeps its lightness and chroma exactly, and moves only the hue. Contrast
is a function of lightness, so it survives the move.

Only colours inside HUE_RANGE are touched, and only when they carry enough
chroma to read as a colour at all. Warm colours (the coral outcome figure, the
amber persona, the flag washes) and near-greys therefore come out untouched,
which is what keeps "declined" bars orange on a green site.

Run again with a different TARGET_HUE to retune. It is not imported by the app.
"""

import os
import re
import sys

TARGET_HUE = 158.0          # emerald
HUE_RANGE = (190.0, 265.0)  # the blue/cyan band, in OKLCH degrees
# Low, because the page paper (#f4f9fd) and the near-black ink carry only a
# hint of blue and still set the whole page's temperature. Below this a colour
# is a true grey and moving it would change nothing a reader could see.
MIN_CHROMA = 0.003

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = [
    "src/static/css/style.css",
    "src/static/css/landing.css",
    "src/templates/base.html",
    "src/routes/improvement.py",
]

COLOUR = re.compile(
    r"#([0-9a-fA-F]{6})\b"
    r"|#([0-9a-fA-F]{3})\b"
    r"|rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(,[^)]*)?\)"
)


def _srgb_to_linear(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c):
    c = c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return max(0, min(255, round(c * 255)))


def rgb_to_oklch(r, g, b):
    r, g, b = _srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b)
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    lightness = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    bb = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    import math
    return lightness, math.hypot(a, bb), math.degrees(math.atan2(bb, a)) % 360


def oklch_to_rgb(lightness, chroma, hue):
    import math
    a = chroma * math.cos(math.radians(hue))
    b = chroma * math.sin(math.radians(hue))
    l = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (lightness - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (_linear_to_srgb(+4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s),
            _linear_to_srgb(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
            _linear_to_srgb(-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s))


def shifted(r, g, b):
    """The green with this colour's lightness and chroma, or None to leave it."""
    lightness, chroma, hue = rgb_to_oklch(r, g, b)
    if chroma < MIN_CHROMA or not (HUE_RANGE[0] <= hue <= HUE_RANGE[1]):
        return None
    return oklch_to_rgb(lightness, chroma, TARGET_HUE)


def convert(text, changes):
    def replace(match):
        hex6, hex3, r, g, b, alpha = match.groups()
        if hex6:
            rgb = tuple(int(hex6[i:i + 2], 16) for i in (0, 2, 4))
        elif hex3:
            rgb = tuple(int(c * 2, 16) for c in hex3)
        else:
            rgb = (int(r), int(g), int(b))
        new = shifted(*rgb)
        if new is None:
            return match.group(0)
        if hex6 or hex3:
            out = "#%02x%02x%02x" % new
        else:
            out = "rgba(%d, %d, %d%s)" % (new + (alpha or "",)) if alpha \
                else "rgb(%d, %d, %d)" % new
        changes.append((match.group(0), out))
        return out
    return COLOUR.sub(replace, text)


def main():
    dry = "--dry-run" in sys.argv
    for name in TARGETS:
        path = os.path.join(ROOT, name)
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        changes = []
        out = convert(text, changes)
        print("%s: %d colours moved" % (name, len(changes)))
        seen = set()
        for before, after in changes:
            if before not in seen:
                seen.add(before)
                print("    %-24s -> %s" % (before, after))
        if not dry and changes:
            with open(path, "w", encoding="utf-8", newline="") as handle:
                handle.write(out)


if __name__ == "__main__":
    main()
