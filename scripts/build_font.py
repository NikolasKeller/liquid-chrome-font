#!/usr/bin/env python3
"""Build the Liquid Chrome font family from an OFL base font.

Pipeline:
  1. Download / load Mystery Quest (SIL OFL 1.1) — a wavy, psychedelic
     display face whose irregular letterforms match the melted look of the
     reference chrome packs.
  2. Subset to Basic Latin + Latin-1.
  3. Dilate every glyph outline with a round-join stroke (skia-pathops) and
     merge it with the original fill. Corners, spurs and curls melt together
     into fat organic blobs while the counters stay open.
  4. Export TTF, OTF and WOFF2 into fonts/ under the family name
     "Liquid Chrome" (Mystery Quest's Reserved Font Name is not used).

Usage:
  python scripts/build_font.py
"""

from __future__ import annotations

from pathlib import Path

import pathops
from fontTools import subset
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

BASE_FONT = Path("build/MysteryQuest.ttf")
OUT_DIR = Path("fonts")
FAMILY = "Liquid Chrome"
STYLE = "Regular"
PS_NAME = "LiquidChrome-Regular"
VERSION = "1.200"
# Dilation radius in font units (Mystery Quest: 1024 upm). Fat enough to melt
# the wavy details into blobs, small enough to keep the counters open.
RADIUS = 68
# No condensation: the reference blob lettering is wide and fat.
CONDENSE = 1.0

COPYRIGHT = (
    "Liquid Chrome: derived from Mystery Quest, "
    "Copyright 2012 Font Diner Inc, "
    "licensed under the SIL Open Font License, Version 1.1."
)

UNICODES = "U+0020-007E,U+00A0-00FF"


def skia_path_for_glyph(glyph_set, name: str) -> pathops.Path:
    path = pathops.Path()
    glyph_set[name].draw(path.getPen(glyphSet=glyph_set))
    return path


def dilate(path: pathops.Path, radius: int) -> pathops.Path:
    """Return the outline of `path` grown by `radius` with round joints."""
    if not list(path.segments):
        return path
    stroked = pathops.Path(path)
    stroked.stroke(radius * 2, pathops.LineCap.ROUND_CAP, pathops.LineJoin.ROUND_JOIN, 4)
    stroked.convertConicsToQuads()
    result = pathops.op(path, stroked, pathops.PathOp.UNION)
    result.simplify()
    return result


def main() -> None:
    font = TTFont(BASE_FONT)

    subsetter = subset.Subsetter(subset.Options(notdef_outline=True))
    subsetter.populate(unicodes=subset.parse_unicodes(UNICODES))
    subsetter.subset(font)

    glyph_set = font.getGlyphSet()
    glyf = font["glyf"]
    hmtx = font["hmtx"]

    blob_paths: dict[str, pathops.Path] = {}
    new_metrics: dict[str, tuple[int, int]] = {}

    for name in font.getGlyphOrder():
        advance, _lsb = hmtx[name]
        condensed_advance = int(round(advance * CONDENSE))
        raw = skia_path_for_glyph(glyph_set, name)
        # Condense the skeleton before dilation so strokes stay round.
        path = pathops.Path()
        raw.draw(TransformPen(path.getPen(), (CONDENSE, 0, 0, 1, 0, 0)))
        if not list(path.segments):
            blob_paths[name] = path
            new_metrics[name] = (
                condensed_advance + 2 * RADIUS if advance else condensed_advance,
                0,
            )
            continue
        blob = dilate(path, RADIUS)
        # Shift right by RADIUS so the left sidebearing is preserved and
        # widen the advance to keep symmetric spacing.
        shifted = pathops.Path()
        blob.draw(TransformPen(shifted.getPen(), (1, 0, 0, 1, RADIUS, 0)))
        blob_paths[name] = shifted
        bounds = shifted.bounds
        new_metrics[name] = (condensed_advance + 2 * RADIUS, int(round(bounds[0])))

    # --- TTF (quadratic outlines) ------------------------------------------
    for name, path in blob_paths.items():
        pen = TTGlyphPen(None)
        path.draw(Cu2QuPen(pen, 1.0))
        glyf[name] = pen.glyph()
        hmtx[name] = new_metrics[name]

    # Give the swollen outlines vertical breathing room.
    for table, attrs in (
        ("hhea", ("ascent", "descent")),
        ("OS/2", ("sTypoAscender", "sTypoDescender")),
    ):
        t = font[table]
        setattr(t, attrs[0], getattr(t, attrs[0]) + RADIUS)
        setattr(t, attrs[1], getattr(t, attrs[1]) - RADIUS)
    font["OS/2"].usWinAscent += RADIUS
    font["OS/2"].usWinDescent += RADIUS
    font["OS/2"].usWeightClass = 400

    name_table = font["name"]
    for name_id, value in (
        (0, COPYRIGHT),
        (1, FAMILY),
        (2, STYLE),
        (3, f"{VERSION};{PS_NAME}"),
        (4, f"{FAMILY} {STYLE}"),
        (6, PS_NAME),
        (16, FAMILY),
        (17, STYLE),
    ):
        name_table.setName(value, name_id, 3, 1, 0x409)
    # Drop stale records (mac platform, designer URLs referencing the base font).
    name_table.removeNames(platformID=1)
    for nid in (7, 8, 9, 11, 12, 13, 14):
        name_table.removeNames(nameID=nid)
    name_table.setName("SIL Open Font License, Version 1.1", 13, 3, 1, 0x409)
    name_table.setName("https://openfontlicense.org", 14, 3, 1, 0x409)

    if "DSIG" in font:
        del font["DSIG"]

    OUT_DIR.mkdir(exist_ok=True)
    ttf_path = OUT_DIR / f"{PS_NAME}.ttf"
    font.save(ttf_path)
    print(f"wrote {ttf_path}")

    woff2 = TTFont(ttf_path)
    woff2.flavor = "woff2"
    woff2_path = OUT_DIR / f"{PS_NAME}.woff2"
    woff2.save(woff2_path)
    print(f"wrote {woff2_path}")

    # --- OTF (cubic/CFF outlines) ------------------------------------------
    upm = font["head"].unitsPerEm
    glyph_order = font.getGlyphOrder()
    charstrings = {}
    for name in glyph_order:
        pen = T2CharStringPen(new_metrics[name][0], None)
        # BasePen converts quadratic segments (incl. implied on-curve points)
        # to cubics for the T2 charstring automatically.
        blob_paths[name].draw(pen)
        charstrings[name] = pen.getCharString()

    fb = FontBuilder(upm, isTTF=False)
    fb.setupGlyphOrder(list(glyph_order))
    fb.setupCharacterMap(font.getBestCmap())
    fb.setupCFF(
        PS_NAME,
        {"FullName": f"{FAMILY} {STYLE}", "FamilyName": FAMILY, "Weight": STYLE,
         "Notice": COPYRIGHT},
        charstrings,
        {},
    )
    fb.setupHorizontalMetrics({g: new_metrics[g] for g in glyph_order})
    hhea = font["hhea"]
    fb.setupHorizontalHeader(ascent=hhea.ascent, descent=hhea.descent)
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
    os2 = font["OS/2"]
    fb.setupOS2(
        sTypoAscender=os2.sTypoAscender,
        sTypoDescender=os2.sTypoDescender,
        usWinAscent=os2.usWinAscent,
        usWinDescent=os2.usWinDescent,
        sxHeight=os2.sxHeight,
        sCapHeight=os2.sCapHeight,
        achVendID="LQCH",
        usWeightClass=400,
    )
    fb.setupPost()
    otf_path = OUT_DIR / f"{PS_NAME}.otf"
    fb.save(otf_path)
    print(f"wrote {otf_path}")


if __name__ == "__main__":
    main()
