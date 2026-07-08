#!/usr/bin/env python3
"""Convert raw chrome glyph renders (on solid black) into cropped,
transparent PNGs.

Background removal strategy:
  1. Flood-fill from the image borders across near-black pixels to find the
     connected outside background.
  2. Additionally treat enclosed pure-black regions (letter counters) as
     background.
  3. Anti-alias the silhouette edge with a luminance ramp so the chrome rim
     blends smoothly on any backdrop.

Usage:
  python scripts/make_transparent.py [--src glyphs/raw] [--out glyphs/png]
"""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

# Luminance thresholds for the alpha ramp at the silhouette edge.
RAMP_LO = 12
RAMP_HI = 72
# Pixels darker than this are considered background wherever they are.
PURE_BLACK = 10
# Padding (px) kept around the cropped glyph.
PAD = 24


def flood_background(dark: np.ndarray) -> np.ndarray:
    """Return mask of dark pixels connected to the image border (4-neighbour)."""
    h, w = dark.shape
    seen = np.zeros_like(dark, dtype=bool)
    queue: deque[tuple[int, int]] = deque()
    for x in range(w):
        for y in (0, h - 1):
            if dark[y, x] and not seen[y, x]:
                seen[y, x] = True
                queue.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if dark[y, x] and not seen[y, x]:
                seen[y, x] = True
                queue.append((y, x))
    while queue:
        y, x = queue.popleft()
        if y > 0 and dark[y - 1, x] and not seen[y - 1, x]:
            seen[y - 1, x] = True
            queue.append((y - 1, x))
        if y < h - 1 and dark[y + 1, x] and not seen[y + 1, x]:
            seen[y + 1, x] = True
            queue.append((y + 1, x))
        if x > 0 and dark[y, x - 1] and not seen[y, x - 1]:
            seen[y, x - 1] = True
            queue.append((y, x - 1))
        if x < w - 1 and dark[y, x + 1] and not seen[y, x + 1]:
            seen[y, x + 1] = True
            queue.append((y, x + 1))
    return seen


def process(path: Path, out_dir: Path) -> None:
    img = Image.open(path).convert("RGB")
    rgb = np.asarray(img, dtype=np.uint8)
    lum = rgb.max(axis=2).astype(np.int16)

    dark = lum < RAMP_HI
    background = flood_background(dark)
    # Enclosed counters: pure black areas not reached by the flood fill.
    background |= lum < PURE_BLACK

    alpha = np.full(lum.shape, 255, dtype=np.uint8)
    ramp = np.clip((lum - RAMP_LO) * 255 // (RAMP_HI - RAMP_LO), 0, 255)
    alpha[background] = ramp[background].astype(np.uint8)

    rgba = np.dstack([rgb, alpha])
    out = Image.fromarray(rgba, "RGBA")

    bbox = Image.fromarray(alpha, "L").getbbox()
    if bbox:
        left = max(bbox[0] - PAD, 0)
        top = max(bbox[1] - PAD, 0)
        right = min(bbox[2] + PAD, out.width)
        bottom = min(bbox[3] + PAD, out.height)
        out = out.crop((left, top, right, bottom))

    name = path.stem.replace("glyph_", "")
    target = out_dir / f"{name}.png"
    out.save(target)
    print(f"{path.name} -> {target} ({out.width}x{out.height})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", default="glyphs/raw", type=Path)
    parser.add_argument("--out", default="glyphs/png", type=Path)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    files = sorted(args.src.glob("glyph_*.png"))
    if not files:
        raise SystemExit(f"no glyph_*.png files found in {args.src}")
    for f in files:
        process(f, args.out)


if __name__ == "__main__":
    main()
