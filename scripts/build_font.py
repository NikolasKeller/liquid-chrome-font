#!/usr/bin/env python3
"""Build the Liquid Chrome font family from the chrome PNG glyphs.

The letterforms come straight from the rendered chrome glyphs in glyphs/png/:
the alpha channel of every PNG is traced to vector outlines (potrace), so the
font has exactly the same shapes as the pixel-perfect chrome renders.

Pipeline:
  1. Load glyphs/png/<char>.png (a-z, 0-9), threshold the alpha channel.
  2. Trace the silhouette with potrace into smooth cubic outlines.
  3. Scale/position each glyph using the same hand-tuned vertical metrics the
     PNG composer uses (height + descender shift relative to the 'a' height).
  4. Map A-Z onto the a-z glyphs (the chrome set is single-case).
  5. Export TTF, OTF and WOFF2 into fonts/ as "Liquid Chrome".

Usage:
  python scripts/build_font.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pathops
import potrace
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageFilter

GLYPH_DIR = Path("glyphs/png")
OUT_DIR = Path("fonts")
FAMILY = "Liquid Chrome"
STYLE = "Regular"
PS_NAME = "LiquidChrome-Regular"
VERSION = "2.000"
UPM = 1000

# Font units for a glyph with metric h=1.0 (the 'a' height).
BASE = 520
# Side bearing in font units on each side of a glyph.
SIDE_BEARING = 26
ALPHA_THRESHOLD = 96

COPYRIGHT = (
    "Liquid Chrome, Copyright 2026 The Liquid Chrome Project Authors. "
    "Letterforms traced from the project's rendered chrome glyphs. "
    "Licensed under the SIL Open Font License, Version 1.1."
)

# Vertical metrics per glyph — identical to demo/composer.html.
# h: glyph height relative to BASE, dy: shift below the baseline.
# dy values are derived from the PNG alpha masks (scripts/derive_metrics.py):
# every glyph body rests on the baseline; descenders (g j p q y) dip below
# only as far as the actual thin tail measured in the bitmap.
METRICS = {
    "a": (1.00, 0.02), "b": (1.45, 0.02), "c": (1.05, 0.02),
    "d": (1.30, 0.02), "e": (1.05, 0.02), "f": (1.55, 0.02),
    "g": (1.35, 0.05), "h": (1.40, 0.02), "i": (1.30, 0.02),
    "j": (1.45, 0.03), "k": (1.35, 0.02), "l": (1.25, 0.02),
    "m": (1.00, 0.02), "n": (1.00, 0.02), "o": (1.05, 0.02),
    "p": (1.30, 0.14), "q": (1.30, 0.06), "r": (1.05, 0.02),
    "s": (1.10, 0.02), "t": (1.40, 0.02), "u": (1.00, 0.02),
    "v": (1.05, 0.02), "w": (1.05, 0.02), "x": (1.10, 0.02),
    "y": (1.30, 0.04), "z": (0.95, 0.02),
    "0": (1.35, 0.02), "1": (1.40, 0.02), "2": (1.35, 0.02),
    "3": (1.40, 0.02), "4": (1.45, 0.02), "5": (1.35, 0.02),
    "6": (1.40, 0.02), "7": (1.50, 0.02), "8": (1.40, 0.02),
    "9": (1.45, 0.02),
}


def trace_glyph(char: str) -> tuple[pathops.Path, int]:
    """Trace one PNG glyph. Returns (outline in font units, advance width)."""
    img = Image.open(GLYPH_DIR / f"{char}.png").convert("RGBA")
    alpha = Image.fromarray(np.array(img)[:, :, 3])
    # Dark chrome reflections leave pinholes and edge notches in the keyed
    # alpha. Clean up: soft threshold, generous morphological closing, then a
    # final blur+threshold to round the repaired boundary.
    mask_img = alpha.filter(ImageFilter.GaussianBlur(2))
    mask_img = mask_img.point(lambda p: 255 if p > 40 else 0)
    mask_img = mask_img.filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.MinFilter(15))
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(3))
    mask_img = mask_img.point(lambda p: 255 if p > 128 else 0)
    mask = np.array(mask_img) > 0

    h_rel, dy_rel = METRICS[char]
    height_units = h_rel * BASE
    scale = height_units / mask.shape[0]
    bottom = -dy_rel * BASE  # baseline shift of the bitmap's bottom edge
    top = bottom + height_units

    # potracer traces zero-valued pixels, hence the inversion.
    bmp = potrace.Bitmap(~mask)
    traced = bmp.trace(turdsize=250, alphamax=1.0, opticurve=1, opttolerance=0.2)

    def to_units(pt) -> tuple[float, float]:
        return (pt.x * scale + SIDE_BEARING, top - pt.y * scale)

    def signed_area(curve) -> float:
        pts = [curve.start_point] + [seg.end_point for seg in curve]
        area = 0.0
        for i, p in enumerate(pts):
            q = pts[(i + 1) % len(pts)]
            area += p.x * q.y - q.x * p.y
        return area / 2

    areas = [signed_area(c) for c in traced]
    outer_sign = 1 if max(areas, key=abs) > 0 else -1
    # Pinholes left by dark reflections are dropped: tiny outer islands and
    # small interior holes. Real counters are much larger than the holes.
    min_outer = (mask.shape[0] * 0.055) ** 2
    min_hole = (mask.shape[0] * 0.10) ** 2

    path = pathops.Path()
    pen = path.getPen()
    for curve, area in zip(traced, areas):
        is_outer = (area > 0) == (outer_sign > 0)
        if abs(area) < (min_outer if is_outer else min_hole):
            continue
        pen.moveTo(to_units(curve.start_point))
        for seg in curve:
            if seg.is_corner:
                pen.lineTo(to_units(seg.c))
                pen.lineTo(to_units(seg.end_point))
            else:
                pen.curveTo(
                    to_units(seg.c1), to_units(seg.c2), to_units(seg.end_point)
                )
        pen.closePath()
    path.simplify()

    advance = int(round(mask.shape[1] * scale + 2 * SIDE_BEARING))
    return path, advance


def main() -> None:
    glyph_paths: dict[str, pathops.Path] = {}
    metrics: dict[str, tuple[int, int]] = {}
    cmap: dict[int, str] = {}

    glyph_order = [".notdef", "space"]
    glyph_paths[".notdef"] = pathops.Path()
    metrics[".notdef"] = (int(BASE * 0.6), 0)
    glyph_paths["space"] = pathops.Path()
    metrics["space"] = (int(BASE * 0.45), 0)
    cmap[0x20] = "space"
    cmap[0xA0] = "space"

    for char in METRICS:
        name = f"uni{ord(char):04X}" if char.isdigit() else char
        path, advance = trace_glyph(char)
        glyph_paths[name] = path
        bounds = path.bounds
        metrics[name] = (advance, int(round(bounds[0])) if list(path.segments) else 0)
        glyph_order.append(name)
        cmap[ord(char)] = name
        if char.isalpha():
            # Single-case chrome set: uppercase input uses the same glyphs.
            cmap[ord(char.upper())] = name

    ascent = int(max(p.bounds[3] for p in glyph_paths.values() if list(p.segments))) + 20
    descent = int(min(p.bounds[1] for p in glyph_paths.values() if list(p.segments))) - 20

    # --- TTF (quadratic outlines) ------------------------------------------
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    ttf_glyphs = {}
    for name in glyph_order:
        pen = TTGlyphPen(None)
        glyph_paths[name].draw(Cu2QuPen(pen, 1.0))
        ttf_glyphs[name] = pen.glyph()
    fb.setupGlyf(ttf_glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ascent, descent=descent)
    fb.setupNameTable({
        "copyright": COPYRIGHT,
        "familyName": FAMILY,
        "styleName": STYLE,
        "uniqueFontIdentifier": f"{VERSION};{PS_NAME}",
        "fullName": f"{FAMILY} {STYLE}",
        "psName": PS_NAME,
        "version": f"Version {VERSION}",
        "licenseDescription": "SIL Open Font License, Version 1.1",
        "licenseInfoURL": "https://openfontlicense.org",
    })
    fb.setupOS2(
        sTypoAscender=ascent,
        sTypoDescender=descent,
        usWinAscent=ascent,
        usWinDescent=-descent,
        sxHeight=BASE,
        sCapHeight=int(1.45 * BASE),
        achVendID="LQCH",
        usWeightClass=400,
    )
    fb.setupPost()
    OUT_DIR.mkdir(exist_ok=True)
    ttf_path = OUT_DIR / f"{PS_NAME}.ttf"
    fb.save(ttf_path)
    print(f"wrote {ttf_path}")

    woff2 = TTFont(ttf_path)
    woff2.flavor = "woff2"
    woff2_path = OUT_DIR / f"{PS_NAME}.woff2"
    woff2.save(woff2_path)
    print(f"wrote {woff2_path}")

    # --- OTF (cubic/CFF outlines) ------------------------------------------
    fb = FontBuilder(UPM, isTTF=False)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    charstrings = {}
    for name in glyph_order:
        pen = T2CharStringPen(metrics[name][0], None)
        glyph_paths[name].draw(pen)
        charstrings[name] = pen.getCharString()
    fb.setupCFF(
        PS_NAME,
        {"FullName": f"{FAMILY} {STYLE}", "FamilyName": FAMILY, "Weight": STYLE,
         "Notice": COPYRIGHT},
        charstrings,
        {},
    )
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ascent, descent=descent)
    fb.setupNameTable({
        "copyright": COPYRIGHT,
        "familyName": FAMILY,
        "styleName": STYLE,
        "uniqueFontIdentifier": f"{VERSION};{PS_NAME}",
        "fullName": f"{FAMILY} {STYLE}",
        "psName": PS_NAME,
        "version": f"Version {VERSION}",
        "licenseDescription": "SIL Open Font License, Version 1.1",
        "licenseInfoURL": "https://openfontlicense.org",
    })
    fb.setupOS2(
        sTypoAscender=ascent,
        sTypoDescender=descent,
        usWinAscent=ascent,
        usWinDescent=-descent,
        sxHeight=BASE,
        sCapHeight=int(1.45 * BASE),
        achVendID="LQCH",
        usWeightClass=400,
    )
    fb.setupPost()
    otf_path = OUT_DIR / f"{PS_NAME}.otf"
    fb.save(otf_path)
    print(f"wrote {otf_path}")


if __name__ == "__main__":
    main()
