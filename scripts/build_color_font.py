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

import numpy as np
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables.sbixGlyph import Glyph as SbixGlyph
from fontTools.ttLib.tables.sbixStrike import Strike
from PIL import Image

from build_font import BASE, GLYPH_DIR, METRICS, SIDE_BEARING, UPM

BASE_FONT = Path("fonts/LiquidChrome-Regular.ttf")
OUT_TTF = Path("fonts/LiquidChrome-Color.ttf")
OUT_WOFF2 = Path("fonts/LiquidChrome-Color.woff2")
PS_NAME = "LiquidChrome-Color"
STYLE = "Color"

# One high-res strike: at PPEM pixels per em the 'a' glyph is
# BASE/UPM * PPEM = 520 px tall, close to the native render resolution.
PPEM = 1000


def bitmap_for(char: str) -> tuple[bytes, int, int]:
    """Resample one chrome PNG for the strike.

    Returns (png bytes, originOffsetX, originOffsetY) in strike pixels.
    """
    img = Image.open(GLYPH_DIR / f"{char}.png").convert("RGBA")
    h_rel, dy_rel = METRICS[char]
    target_h = int(round(h_rel * BASE / UPM * PPEM))
    target_w = max(1, int(round(img.width * target_h / img.height)))
    img = img.resize((target_w, target_h), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    off_x = int(round(SIDE_BEARING / UPM * PPEM))
    off_y = int(round(-dy_rel * BASE / UPM * PPEM))
    return buf.getvalue(), off_x, off_y


def main() -> None:
    font = TTFont(BASE_FONT)

    strike = Strike(ppem=PPEM, resolution=72)
    for char in METRICS:
        name = f"uni{ord(char):04X}" if char.isdigit() else char
        data, off_x, off_y = bitmap_for(char)
        strike.glyphs[name] = SbixGlyph(
            glyphName=name,
            graphicType="png ",
            imageData=data,
            originOffsetX=off_x,
            originOffsetY=off_y,
        )

    sbix = newTable("sbix")
    sbix.version = 1
    sbix.flags = 1
    sbix.strikes = {PPEM: strike}
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
