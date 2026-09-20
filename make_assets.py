#!/usr/bin/env python3
"""Draw the CodeLab Studio logo into assets/ and the MSIX asset set into assets/msix/.

    python make_assets.py            # app.png + app.ico + assets/msix/
    python make_assets.py --check    # regenerate, then verify every file and size

Needs Pillow (pip install pillow); the app itself does not.
"""

import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
MSIX = os.path.join(ASSETS, "msix")

SIZE = 512
MASTER = 1280               # biggest logo any MSIX asset needs is 1240 (Square310x310 @400%)
TOP = (124, 92, 255)        # accent purple, matches C["accent"]
BOTTOM = (18, 184, 134)     # go green,     matches C["go"]
INK = (255, 255, 255)

SCALES = (100, 125, 150, 200, 400)
TARGET_SIZES = (16, 20, 24, 30, 32, 36, 40, 48, 60, 64, 72, 80, 96, 256)

# manifest name, base width, base height, logo size as a fraction of the short side.
# The fractions are Microsoft's tile safe areas: a 44 px mark in a 71 px small tile,
# 88 px in a 150 px medium tile, 176 px in a 310 px large tile.
FORMS = (
    ("Square44x44Logo",    44,  44, 1.00),
    ("Square71x71Logo",    71,  71, 0.62),
    ("Square150x150Logo", 150, 150, 0.60),
    ("Wide310x150Logo",   310, 150, 0.60),
    ("Square310x310Logo", 310, 310, 0.57),
    ("StoreLogo",          50,  50, 1.00),
    ("SplashScreen",      620, 300, 0.62),
)


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


def glyph(size, fill=INK):
    """The  </>  mark on transparency, drawn supersampled so the strokes stay smooth."""
    s = min(size * 4, 2560)
    big = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    pen = ImageDraw.Draw(big)
    w = round(s * 0.055)
    mid, span, rise = s * 0.5, s * 0.17, s * 0.15

    pen.line([(mid - span * 0.55, mid - rise), (mid - span * 1.35, mid),
              (mid - span * 0.55, mid + rise)], fill=fill, width=w, joint="curve")
    pen.line([(mid + span * 0.55, mid - rise), (mid + span * 1.35, mid),
              (mid + span * 0.55, mid + rise)], fill=fill, width=w, joint="curve")
    pen.line([(mid + span * 0.30, mid - rise * 1.35),
              (mid - span * 0.30, mid + rise * 1.35)], fill=fill, width=w)
    for end in ((mid - span * 1.35, mid), (mid + span * 1.35, mid)):
        pen.ellipse((end[0] - w / 2, end[1] - w / 2, end[0] + w / 2, end[1] + w / 2), fill=fill)
    return big.resize((size, size), Image.LANCZOS)


def logo_tile(size):
    """Rounded gradient tile with the  </>  cut into it, on a transparent background."""
    tile = gradient(size, TOP, BOTTOM).convert("RGBA")
    tile.putalpha(rounded_mask(size, round(size * 0.22)))
    tile.alpha_composite(glyph(size))
    return tile


# ---- MSIX asset set -------------------------------------------------------
def _px(base, scale):
    """Scaled pixel size. Windows rounds half up: StoreLogo 50 @125% is 63, not 62."""
    return max(1, math.floor(base * scale / 100 + 0.5))


def _centred(master, w, h, frac):
    """Logo centred on a transparent w x h canvas, filling `frac` of the short side."""
    side = _px(min(w, h), frac * 100)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(master.resize((side, side), Image.LANCZOS),
                        ((w - side) // 2, (h - side) // 2))
    return out


def _save(image, name):
    image.save(os.path.join(MSIX, name + ".png"))


def build_msix(master=None):
    """Emit every in-package image an MSIX Store submission needs into assets/msix/."""
    master = master if master is not None else logo_tile(MASTER)
    os.makedirs(MSIX, exist_ok=True)

    for name, bw, bh, frac in FORMS:
        for scale in SCALES:
            _save(_centred(master, _px(bw, scale), _px(bh, scale), frac), f"{name}.scale-{scale}")
        # Unqualified copy too, so the package still renders before makepri builds the PRI.
        _save(_centred(master, bw, bh, frac), name)

    # Square44x44Logo target-size family. Our mark is a self-contained coloured tile,
    # so plated and unplated share the same art -- what matters is that the unplated
    # files exist, or Windows paints a grey backplate behind the taskbar/Start icon.
    for n in TARGET_SIZES:
        icon = master.resize((n, n), Image.LANCZOS)
        for altform in ("", "_altform-unplated", "_altform-lightunplated"):
            _save(icon, f"Square44x44Logo.targetsize-{n}{altform}")

    # BadgeLogo is optional (Windows 10 lock screen) and must be white on transparent.
    badge = glyph(MASTER)
    for scale in SCALES:
        n = _px(24, scale)
        _save(badge.resize((n, n), Image.LANCZOS), f"BadgeLogo.scale-{scale}")
    _save(badge.resize((24, 24), Image.LANCZOS), "BadgeLogo")


def expected():
    """filename -> (w, h) for the whole assets/msix/ set."""
    want = {}
    for name, bw, bh, frac in FORMS:
        want[f"{name}.png"] = (bw, bh)
        for scale in SCALES:
            want[f"{name}.scale-{scale}.png"] = (_px(bw, scale), _px(bh, scale))
    for n in TARGET_SIZES:
        for altform in ("", "_altform-unplated", "_altform-lightunplated"):
            want[f"Square44x44Logo.targetsize-{n}{altform}.png"] = (n, n)
    want["BadgeLogo.png"] = (24, 24)
    for scale in SCALES:
        want[f"BadgeLogo.scale-{scale}.png"] = (_px(24, scale),) * 2
    return want


def check():
    # Microsoft's published scale table, as a guard on the half-up rounding.
    assert (_px(50, 125), _px(150, 125), _px(71, 150), _px(310, 400),
            _px(44, 200), _px(620, 400)) == (63, 188, 107, 1240, 88, 2480)
    want = expected()
    for filename, size in want.items():
        path = os.path.join(MSIX, filename)
        assert os.path.exists(path), "missing " + filename
        with Image.open(path) as image:
            assert image.size == size, f"{filename}: {image.size} != {size}"
            assert image.mode == "RGBA", f"{filename}: {image.mode} is not RGBA"
            assert image.getextrema()[3][0] == 0, f"{filename}: no transparent pixels"
    print(f"ok: {len(want)} MSIX assets in {MSIX}")


def build():
    tile = logo_tile(SIZE)
    os.makedirs(ASSETS, exist_ok=True)
    tile.resize((256, 256), Image.LANCZOS).save(os.path.join(ASSETS, "app.png"))
    tile.save(os.path.join(ASSETS, "app.ico"),
              sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("wrote assets/app.png and assets/app.ico")
    build_msix()
    print(f"wrote {len(expected())} files into assets/msix/")


if __name__ == "__main__":
    build()
    if "--check" in sys.argv:
        check()
