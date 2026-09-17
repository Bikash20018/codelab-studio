#!/usr/bin/env python3
"""Draw the CodeLab Studio logo into assets/app.png and assets/app.ico.

Run after changing the colours:   python make_assets.py
Needs Pillow (pip install pillow); the app itself does not.
"""

import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")

SIZE = 512
TOP = (124, 92, 255)        # accent purple, matches C["accent"]
BOTTOM = (18, 184, 134)     # go green,     matches C["go"]
INK = (255, 255, 255)


def gradient(size, top, bottom):
    image = Image.new("RGB", (1, size))
    for y in range(size):
        t = y / (size - 1)
        image.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)))
    return image.resize((size, size))


def rounded_mask(size, radius):
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size * 4 - 1, size * 4 - 1),
                                           radius=radius * 4, fill=255)
    return mask.resize((size, size), Image.LANCZOS)


def build():
    tile = gradient(SIZE, TOP, BOTTOM).convert("RGBA")
    tile.putalpha(rounded_mask(SIZE, round(SIZE * 0.22)))

    # </>  drawn at 4x then scaled down, so the strokes stay smooth
    big = Image.new("RGBA", (SIZE * 4, SIZE * 4), (0, 0, 0, 0))
    pen = ImageDraw.Draw(big)
    s, w = SIZE * 4, round(SIZE * 4 * 0.055)
    mid, span, rise = s * 0.5, s * 0.17, s * 0.15

    pen.line([(mid - span * 0.55, mid - rise), (mid - span * 1.35, mid),
              (mid - span * 0.55, mid + rise)], fill=INK, width=w, joint="curve")
    pen.line([(mid + span * 0.55, mid - rise), (mid + span * 1.35, mid),
              (mid + span * 0.55, mid + rise)], fill=INK, width=w, joint="curve")
    pen.line([(mid + span * 0.30, mid - rise * 1.35),
              (mid - span * 0.30, mid + rise * 1.35)], fill=INK, width=w)
    for end in ((mid - span * 1.35, mid), (mid + span * 1.35, mid)):
        pen.ellipse((end[0] - w / 2, end[1] - w / 2, end[0] + w / 2, end[1] + w / 2), fill=INK)

    tile.alpha_composite(big.resize((SIZE, SIZE), Image.LANCZOS))

    os.makedirs(ASSETS, exist_ok=True)
    tile.resize((256, 256), Image.LANCZOS).save(os.path.join(ASSETS, "app.png"))
    tile.save(os.path.join(ASSETS, "app.ico"),
              sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("wrote assets/app.png and assets/app.ico")


if __name__ == "__main__":
    build()
