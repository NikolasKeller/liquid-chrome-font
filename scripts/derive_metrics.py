#!/usr/bin/env python3
"""Derive the baseline shift (dy) for every glyph from its PNG alpha mask.

The goal is that all letters visually sit on one line: the "body" of each
glyph (without ascenders/descenders) rests on the baseline. Non-descender
glyphs simply sit with their bitmap bottom edge on the baseline (dy = 0.02,
a slight optical overlap). For descender glyphs (g j p q y) the thin tail
may dip below the baseline, but only as far as the actual tail in the image.

The tail is measured from the row ink-width profile of the cleaned mask
(same cleanup as build_font.py): scanning up from the ink bottom, rows are
"tail" while their ink width stays below 45% of the glyph's typical body
width (75th percentile of all inked rows — more robust than the max, which
is dominated by single wide bulges). dy is then the tail extent in units of
BASE, minus the same 0.02 overlap.

Usage:
  python scripts/derive_metrics.py    # prints a dy table for METRICS
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter

from build_font import GLYPH_DIR, METRICS

DESCENDERS = set("gjpqy")
BODY_WIDTH_FRAC = 0.45
BASELINE_OVERLAP = 0.02


def clean_mask(char: str) -> np.ndarray:
    """Same alpha cleanup as build_font.trace_glyph."""
    img = Image.open(GLYPH_DIR / f"{char}.png").convert("RGBA")
    alpha = Image.fromarray(np.array(img)[:, :, 3])
    m = alpha.filter(ImageFilter.GaussianBlur(2))
    m = m.point(lambda p: 255 if p > 40 else 0)
    m = m.filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.MinFilter(15))
    m = m.filter(ImageFilter.GaussianBlur(3))
    m = m.point(lambda p: 255 if p > 128 else 0)
    return np.array(m) > 0


def derive_dy(char: str) -> float:
    if char not in DESCENDERS:
        return BASELINE_OVERLAP

    mask = clean_mask(char)
    height = mask.shape[0]
    widths = mask.sum(axis=1)
    ink = np.nonzero(widths)[0]
    body_width = np.percentile(widths[ink[0] : ink[-1] + 1], 75)
    threshold = body_width * BODY_WIDTH_FRAC

    body_bottom = ink[-1]
    for row in range(ink[-1], ink[0] - 1, -1):
        if widths[row] >= threshold:
            body_bottom = row
            break

    h_rel = METRICS[char][0]
    tail = (height - 1 - body_bottom) / height * h_rel
    return round(max(BASELINE_OVERLAP, tail - BASELINE_OVERLAP), 2)


def main() -> None:
    print("char  h     dy_old  dy_new")
    for char, (h_rel, dy_old) in METRICS.items():
        dy_new = derive_dy(char)
        flag = "  <-- change" if abs(dy_new - dy_old) > 0.005 else ""
        print(f"{char:>4}  {h_rel:.2f}  {dy_old:.2f}    {dy_new:.2f}{flag}")


if __name__ == "__main__":
    main()
