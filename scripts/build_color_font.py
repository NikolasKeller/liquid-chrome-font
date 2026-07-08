#!/usr/bin/env python3
"""Build the Liquid Chrome COLOR font: the real chrome PNGs inside a font.

Takes fonts/LiquidChrome-Regular.ttf (traced outlines, correct metrics) and
embeds the original chrome renders from glyphs/png/ as an Apple `sbix` color
bitmap strike. Renderers with sbix support (macOS apps, Safari, Chrome,
Photoshop, Figma, ...) show the pixel-perfect chrome texture; everything else
falls back to the traced monochrome outlines.

Usage:
  python scripts/build_font.py        # first: outlines + metrics
  python scripts/build_color_font.py  # then: color font
"""

from __future__ import annotations

import io
from pathlib import Path

from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables.sbixGlyph import Glyph as SbixGlyph
from fontTools.ttLib.tables.sbixStrike import Strike
from PIL import Image, ImageEnhance, ImageFilter

from build_font import BASE, GLYPH_DIR, METRICS, SIDE_BEARING, UPM

BASE_FONT = Path("fonts/LiquidChrome-Regular.ttf")
OUT_TTF = Path("fonts/LiquidChrome-Color.ttf")
OUT_WOFF2 = Path("fonts/LiquidChrome-Color.woff2")
PS_NAME = "LiquidChrome-Color"
STYLE = "Color"

# Two strikes. The big one keeps the native render resolution (at PPEM
# pixels per em the 'a' glyph is BASE/UPM * PPEM = 520 px tall). The small
# one targets body-text sizes: its bitmaps get a much stronger contrast /
# sharpen treatment so the chrome stays punchy when rendered small, where
# plain downsampling washes the reflections out to a pale gray.
#   (ppem, contrast, saturation, unsharp %, brightness)
STRIKES = (
    (1000, 1.18, 1.10, 60, 1.00),
    (200, 1.50, 1.30, 160, 1.10),
)


def enhance(img: Image.Image, contrast: float, saturation: float,
            unsharp_percent: int, brightness: float) -> Image.Image:
    """Boost the chrome texture without touching the alpha silhouette."""
    r, g, b, a = img.split()
    rgb = Image.merge("RGB", (r, g, b))
    if brightness != 1.0:
        rgb = ImageEnhance.Brightness(rgb).enhance(brightness)
    rgb = ImageEnhance.Contrast(rgb).enhance(contrast)
    rgb = ImageEnhance.Color(rgb).enhance(saturation)
    rgb = rgb.filter(
        ImageFilter.UnsharpMask(radius=2, percent=unsharp_percent, threshold=2)
    )
    out = rgb.convert("RGBA")
    out.putalpha(a)
    return out


def bitmap_for(char: str, ppem: int, contrast: float, saturation: float,
               unsharp_percent: int, brightness: float) -> tuple[bytes, int, int]:
    """Resample one chrome PNG for a strike.

    Returns (png bytes, originOffsetX, originOffsetY) in strike pixels.
    """
    img = Image.open(GLYPH_DIR / f"{char}.png").convert("RGBA")
    h_rel, dy_rel = METRICS[char]
    target_h = int(round(h_rel * BASE / UPM * ppem))
    target_w = max(1, int(round(img.width * target_h / img.height)))
    img = img.resize((target_w, target_h), Image.LANCZOS)
    img = enhance(img, contrast, saturation, unsharp_percent, brightness)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    off_x = int(round(SIDE_BEARING / UPM * ppem))
    off_y = int(round(-dy_rel * BASE / UPM * ppem))
    return buf.getvalue(), off_x, off_y


def main() -> None:
    font = TTFont(BASE_FONT)

    strikes = {}
    for ppem, contrast, saturation, unsharp_percent, brightness in STRIKES:
        strike = Strike(ppem=ppem, resolution=72)
        for char in METRICS:
            name = f"uni{ord(char):04X}" if char.isdigit() else char
            data, off_x, off_y = bitmap_for(
                char, ppem, contrast, saturation, unsharp_percent, brightness
            )
            strike.glyphs[name] = SbixGlyph(
                glyphName=name,
                graphicType="png ",
                imageData=data,
                originOffsetX=off_x,
                originOffsetY=off_y,
            )
        strikes[ppem] = strike

    sbix = newTable("sbix")
    sbix.version = 1
    sbix.flags = 1
    sbix.strikes = strikes
    font["sbix"] = sbix

    # Rename so both fonts can be installed side by side.
    name_table = font["name"]
    for name_id, value in (
        (1, "Liquid Chrome Color"),
        (3, f"2.000;{PS_NAME}"),
        (4, "Liquid Chrome Color"),
        (6, PS_NAME),
        (16, "Liquid Chrome Color"),
        (17, "Regular"),
    ):
        name_table.setName(value, name_id, 3, 1, 0x409)

    font.save(OUT_TTF)
    print(f"wrote {OUT_TTF}")

    woff2 = TTFont(OUT_TTF)
    woff2.flavor = "woff2"
    woff2.save(OUT_WOFF2)
    print(f"wrote {OUT_WOFF2}")


if __name__ == "__main__":
    main()
