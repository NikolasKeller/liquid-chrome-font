# Liquid Chrome

An open-source liquid-chrome lettering kit: glossy, molten-silver letterforms
inspired by 90s/Y2K chrome type.

![Liquid Chrome Color font — real chrome texture, just type](assets/preview-color-font.png)

The look is captured in three complementary ways so you can pick whatever
fits your project:

1. **Color font** (`fonts/LiquidChrome-Color.ttf`) — the real chrome renders
   embedded in an installable font (Apple `sbix` color bitmaps). Type text in
   Photoshop, Figma, macOS apps or the browser and get the pixel-perfect
   chrome texture (shown above). Falls back to monochrome outlines where
   color fonts are not supported.
2. **PNG glyphs** (`glyphs/png/`) — pre-rendered chrome letters `a-z` and
   `0-9` with transparent backgrounds. Pixel-perfect, works on any backdrop.
3. **Outline font** (`fonts/LiquidChrome-Regular.*`) — lightweight
   `TTF` / `OTF` / `WOFF2` traced from the same glyphs.

| Reference (dark) | Reference (light) |
| --- | --- |
| ![dark](reference/iykyk-black.png) | ![light](reference/iykyk-cream.png) |

## Glyph set

All 36 pre-rendered chrome glyphs from `glyphs/png/` (transparent backgrounds,
shown here on GitHub's page background):

<table>
  <tr>
    <td align="center"><img src="glyphs/png/a.png" width="56" alt="a"><br>a</td>
    <td align="center"><img src="glyphs/png/b.png" width="56" alt="b"><br>b</td>
    <td align="center"><img src="glyphs/png/c.png" width="56" alt="c"><br>c</td>
    <td align="center"><img src="glyphs/png/d.png" width="56" alt="d"><br>d</td>
    <td align="center"><img src="glyphs/png/e.png" width="56" alt="e"><br>e</td>
    <td align="center"><img src="glyphs/png/f.png" width="56" alt="f"><br>f</td>
    <td align="center"><img src="glyphs/png/g.png" width="56" alt="g"><br>g</td>
    <td align="center"><img src="glyphs/png/h.png" width="56" alt="h"><br>h</td>
    <td align="center"><img src="glyphs/png/i.png" width="56" alt="i"><br>i</td>
  </tr>
  <tr>
    <td align="center"><img src="glyphs/png/j.png" width="56" alt="j"><br>j</td>
    <td align="center"><img src="glyphs/png/k.png" width="56" alt="k"><br>k</td>
    <td align="center"><img src="glyphs/png/l.png" width="56" alt="l"><br>l</td>
    <td align="center"><img src="glyphs/png/m.png" width="56" alt="m"><br>m</td>
    <td align="center"><img src="glyphs/png/n.png" width="56" alt="n"><br>n</td>
    <td align="center"><img src="glyphs/png/o.png" width="56" alt="o"><br>o</td>
    <td align="center"><img src="glyphs/png/p.png" width="56" alt="p"><br>p</td>
    <td align="center"><img src="glyphs/png/q.png" width="56" alt="q"><br>q</td>
    <td align="center"><img src="glyphs/png/r.png" width="56" alt="r"><br>r</td>
  </tr>
  <tr>
    <td align="center"><img src="glyphs/png/s.png" width="56" alt="s"><br>s</td>
    <td align="center"><img src="glyphs/png/t.png" width="56" alt="t"><br>t</td>
    <td align="center"><img src="glyphs/png/u.png" width="56" alt="u"><br>u</td>
    <td align="center"><img src="glyphs/png/v.png" width="56" alt="v"><br>v</td>
    <td align="center"><img src="glyphs/png/w.png" width="56" alt="w"><br>w</td>
    <td align="center"><img src="glyphs/png/x.png" width="56" alt="x"><br>x</td>
    <td align="center"><img src="glyphs/png/y.png" width="56" alt="y"><br>y</td>
    <td align="center"><img src="glyphs/png/z.png" width="56" alt="z"><br>z</td>
    <td align="center"><img src="glyphs/png/0.png" width="56" alt="0"><br>0</td>
  </tr>
  <tr>
    <td align="center"><img src="glyphs/png/1.png" width="56" alt="1"><br>1</td>
    <td align="center"><img src="glyphs/png/2.png" width="56" alt="2"><br>2</td>
    <td align="center"><img src="glyphs/png/3.png" width="56" alt="3"><br>3</td>
    <td align="center"><img src="glyphs/png/4.png" width="56" alt="4"><br>4</td>
    <td align="center"><img src="glyphs/png/5.png" width="56" alt="5"><br>5</td>
    <td align="center"><img src="glyphs/png/6.png" width="56" alt="6"><br>6</td>
    <td align="center"><img src="glyphs/png/7.png" width="56" alt="7"><br>7</td>
    <td align="center"><img src="glyphs/png/8.png" width="56" alt="8"><br>8</td>
    <td align="center"><img src="glyphs/png/9.png" width="56" alt="9"><br>9</td>
  </tr>
</table>

Uppercase input maps to the same lowercase-style glyphs (as in the reference
lettering).

## Quick start

### Option A — Color font (real chrome texture, just type)

Double-click `fonts/LiquidChrome-Color.ttf` and press "Install Font". Select
**Liquid Chrome Color** in any app with color-font support (macOS apps,
Photoshop, Figma, Safari/Chrome) and type — every letter is one of the
rendered chrome glyphs. On the web:

```html
<link rel="stylesheet" href="css/liquid-chrome.css">
<h1 class="liquid-chrome-color">iykyk</h1>
```

Note: the embedded bitmaps make this file ~10 MB — use the PNG glyphs or the
outline webfont when payload size matters.

### Option B — PNG glyphs (pixel-perfect chrome)

Every character is a transparent PNG in `glyphs/png/` (`a.png` … `z.png`,
`0.png` … `9.png`). Compose words in any design tool, or use the bundled
composer:

```bash
# from the repo root
python3 -m http.server 8000
# open http://localhost:8000/demo/composer.html
```

Type a word, adjust size/spacing, toggle between black and cream backgrounds.

In plain HTML:

```html
<img src="glyphs/png/i.png" style="height: 120px" alt="i">
<img src="glyphs/png/y.png" style="height: 156px; margin-bottom: -5px" alt="y">
```

(Descenders like `g j p q y` need a small negative bottom margin; see the
metrics table in `demo/composer.html`.)

### Option C — Outline font

Double-click `fonts/LiquidChrome-Regular.otf` (or `.ttf`) and press
"Install Font". The family is available as **Liquid Chrome** — the same
letterforms as the chrome glyphs, as a lightweight monochrome font.

See the color font and the PNG glyphs side by side: `demo/index.html`.

## Building it yourself

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 1. Regenerate transparent glyphs from raw renders (glyphs/raw/)
.venv/bin/python scripts/make_transparent.py

# 2. Rebuild the outline font files from the PNG glyphs
.venv/bin/python scripts/build_font.py

# 3. Rebuild the color font (embeds the PNGs as sbix bitmaps)
.venv/bin/python scripts/build_color_font.py
```

`scripts/build_font.py` builds the font directly from the chrome renders:
the alpha channel of every PNG in `glyphs/png/` is cleaned up (morphological
closing removes pinholes left by dark reflections) and traced to vector
outlines with potrace, so the font has exactly the same letterforms as the
pixel-perfect glyphs. Vertical placement is derived from the PNG masks
themselves (`scripts/derive_metrics.py`): every glyph body rests on a common
baseline, and descenders (`g j p q y`) dip below only as far as their
measured tail. `A-Z` maps onto the single-case `a-z` shapes. Exports TTF,
OTF and WOFF2.

`scripts/build_color_font.py` embeds two `sbix` strikes: a 1000 ppem strike
at the native render resolution and a contrast-boosted 200 ppem strike so
the chrome stays punchy at body-text sizes.

## Repository layout

```
fonts/            LiquidChrome-Color.ttf / .woff2 (chrome bitmaps),
                  LiquidChrome-Regular.ttf / .otf / .woff2 (outlines)
glyphs/png/       transparent chrome letters (a-z, 0-9)
glyphs/raw/       original AI renders on black (build input)
css/              @font-face declarations for both webfonts
assets/           preview image (+ optional chrome texture for CSS effects)
demo/             index.html (overview), composer.html (word builder)
scripts/          make_transparent.py, build_font.py, build_color_font.py
reference/        the two original reference images
```

## Licensing

- **Font files** (`fonts/`, `scripts/build_font.py` output): licensed under
  the [SIL Open Font License 1.1](LICENSE). The letterforms are traced from
  this project's own rendered chrome glyphs — no third-party font is used.
- **PNG glyphs and reference images** (`glyphs/`, `reference/`): licensed
  under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — use them
  anywhere, credit "Liquid Chrome contributors".
- **Code** (`scripts/`, `demo/`, `css/`): MIT, do what you want.
