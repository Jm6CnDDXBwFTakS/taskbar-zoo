#!/usr/bin/env python3
"""Build the Taskbar Zoo icon set.

    python3 tools/build.py svg              # art/ + icons.json  ->  svg/        (needs fontTools + a font)
    python3 tools/build.py export           # svg/  ->  dist/ PNG, ICO, ICNS     (needs rsvg-convert + Pillow)
    python3 tools/build.py previews         # dist/ ->  previews/ contact sheets
    python3 tools/build.py all              # all of the above
    python3 tools/build.py svg alfa bravo   # limit any step to some icons

Art fragments in art/*.svgfrag are SVG snippets drawn on a 512x512 canvas using colour tokens:
    MAIN   icon colour (rendered as a soft top-to-bottom gradient)
    SHADE  darker tone of the icon colour
    LIGHT  lighter tone of the icon colour
    CREAM  shared off-white (muzzles, highlights)
    DARK   shared near-black (eyes, noses)
Size and position don't matter: each animal is measured and auto-fitted to the tile.
"""
import colorsys, json, math, os, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART, SVG, DIST, PREV = (os.path.join(ROOT, d) for d in ("art", "svg", "dist", "previews"))

# ---- palette & geometry -------------------------------------------------------------------
TILE_TOP, TILE_BOT, TILE_EDGE = "#2e2e33", "#1a1a1d", "#3c3c42"
CREAM, DARK = "#fdf1e8", "#1b1b1d"
TILE_RX = 112                       # tile corner radius
FIT_BOX = 396                       # animal fits inside a FIT_BOX square
BADGE_X, BADGE_Y, BADGE_R = 402, 402, 80
PNG_SIZES = (16, 24, 32, 48, 64, 128, 256, 512, 1024)
SMALL_MAX = 24                      # sizes <= this use the letter-only SVG
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
ICNS_SIZES = (16, 32, 64, 128, 256, 512, 1024)
FONT_CANDIDATES = [os.environ.get("ICON_FONT", ""),
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                   "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
                   "/Library/Fonts/DejaVuSans-Bold.ttf",
                   os.path.expanduser("~/Library/Fonts/DejaVuSans-Bold.ttf"),
                   "C:/Windows/Fonts/DejaVuSans-Bold.ttf"]


def hex_rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def darken(h, f):
    return "#%02x%02x%02x" % tuple(int(c * f) for c in hex_rgb(h))

def lighten(h, f):
    return "#%02x%02x%02x" % tuple(int(c + (255 - c) * f) for c in hex_rgb(h))

def complement(h):
    r, g, b = (c / 255 for c in hex_rgb(h))
    hh, _, s = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb((hh + 0.5) % 1, 0.70, min(1, max(s, 0.75)))
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))

def load_icons(names=None):
    meta = json.load(open(os.path.join(ROOT, "icons.json"), encoding="utf-8"))
    out = []
    for n in names or meta:
        e = dict(meta[n], name=n)
        e["art"] = open(os.path.join(ART, f"{n}.svgfrag"), encoding="utf-8").read()
        out.append(e)
    return out

def render(svg_path, png_path, size):
    subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size), svg_path, "-o", png_path], check=True)

# ---- SVG generation ----------------------------------------------------------------------
_font = None
def glyph(ch, cx, cy, height, width_max):
    """Outline of `ch` as an SVG path, centred on (cx, cy). Letters become paths, so the SVGs need no font."""
    global _font
    from fontTools.ttLib import TTFont
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.boundsPen import BoundsPen
    if _font is None:
        path = next((p for p in FONT_CANDIDATES if p and os.path.exists(p)), None)
        if not path:
            sys.exit("DejaVu Sans Bold not found; set ICON_FONT=/path/to/DejaVuSans-Bold.ttf")
        f = TTFont(path); _font = (f.getGlyphSet(), f.getBestCmap())
    gs, cmap = _font
    g = gs[cmap[ord(ch)]]
    bp = BoundsPen(gs); g.draw(bp); x0, y0, x1, y1 = bp.bounds
    s = min(height / (y1 - y0), width_max / (x1 - x0))
    pp = SVGPathPen(gs); g.draw(pp)
    return pp.getCommands(), f"translate({cx - (x0 + x1) / 2 * s:.2f},{cy + (y0 + y1) / 2 * s:.2f}) scale({s:.4f},{-s:.4f})", s

def tokens(icon, probe=False):
    c = icon["color"]
    return (icon["art"].replace("MAIN", c if probe else "url(#m)").replace("SHADE", darken(c, 0.6))
            .replace("LIGHT", lighten(c, 0.55)).replace("CREAM", CREAM).replace("DARK", DARK))

def fit(icon):
    """Render the art alone, measure its bounding box, and return a transform that centres it."""
    cx, cy = icon.get("center", (256, 256))
    probe = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-200 -200 912 912" width="912" height="912">'
             f'<g>{tokens(icon, True)}</g></svg>')
    from PIL import Image
    with tempfile.TemporaryDirectory() as t:
        sp, pp = os.path.join(t, "p.svg"), os.path.join(t, "p.png")
        open(sp, "w", encoding="utf-8").write(probe); render(sp, pp, 912)
        x0, y0, x1, y1 = Image.open(pp).getchannel("A").getbbox()
    x0, x1, y0, y1 = x0 - 200, x1 - 200, y0 - 200, y1 - 200
    s = min(FIT_BOX / (x1 - x0), FIT_BOX / (y1 - y0))
    return f"translate({cx:.1f},{cy:.1f}) scale({s:.4f}) translate({-(x0 + x1) / 2:.1f},{-(y0 + y1) / 2:.1f})"

def full_svg(icon):
    c, letter = icon["color"], icon["letter"]
    hexd = "M" + " L".join(f"{BADGE_X + BADGE_R * math.cos(math.radians(a)):.1f},"
                           f"{BADGE_Y + BADGE_R * math.sin(math.radians(a)):.1f}" for a in range(0, 360, 60)) + " Z"
    d, tf, s = glyph(letter, BADGE_X, BADGE_Y, 79, 104)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <title>{icon["name"].title()} ({letter}) - {icon["animal"]}</title>
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{TILE_TOP}"/><stop offset="1" stop-color="{TILE_BOT}"/>
    </linearGradient>
    <linearGradient id="m" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{lighten(c, 0.14)}"/><stop offset="1" stop-color="{darken(c, 0.93)}"/>
    </linearGradient>
    <clipPath id="tile"><rect x="8" y="8" width="496" height="496" rx="{TILE_RX}"/></clipPath>
  </defs>
  <rect x="8" y="8" width="496" height="496" rx="{TILE_RX}" fill="url(#g)"/>
  <g clip-path="url(#tile)">
  <g transform="{fit(icon)}">
{tokens(icon)}
  </g>
<path d="{hexd}" fill="{c}" stroke="{TILE_BOT}" stroke-width="14" stroke-linejoin="miter"/>
  <path d="{d}" transform="{tf}" fill="{complement(c)}" stroke="{DARK}" stroke-width="{9 / s:.1f}" stroke-linejoin="round" paint-order="stroke"/>
  </g>
  <rect x="8" y="8" width="496" height="496" rx="{TILE_RX}" fill="none" stroke="{TILE_EDGE}" stroke-width="6"/>
</svg>
'''

def small_svg(icon):
    d, tf, _ = glyph(icon["letter"], 256, 256, 330, 400)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <title>{icon["name"].title()} ({icon["letter"]}), small</title>
  <rect x="0" y="0" width="512" height="512" rx="{TILE_RX}" fill="{TILE_BOT}"/>
  <path d="{d}" transform="{tf}" fill="{icon["color"]}"/>
</svg>
'''

def step_svg(icons):
    os.makedirs(SVG, exist_ok=True)
    for ic in icons:
        n = ic["name"]
        open(os.path.join(SVG, f"{n}.svg"), "w", encoding="utf-8").write(full_svg(ic))
        open(os.path.join(SVG, f"{n}-small.svg"), "w", encoding="utf-8").write(small_svg(ic))
        print("svg   ", n)

# ---- raster export -----------------------------------------------------------------------
def step_export(icons):
    from PIL import Image
    for ic in icons:
        n = ic["name"]
        full, small = (os.path.join(SVG, f"{n}{s}.svg") for s in ("", "-small"))
        out = os.path.join(DIST, n); os.makedirs(os.path.join(out, "png"), exist_ok=True)
        imgs = {}
        for sz in PNG_SIZES:
            p = os.path.join(out, "png", f"{n}-{sz}.png")
            render(small if sz <= SMALL_MAX else full, p, sz)
            imgs[sz] = Image.open(p).convert("RGBA")
        imgs[256].save(os.path.join(out, f"{n}.ico"), format="ICO", sizes=[(s, s) for s in ICO_SIZES],
                       append_images=[imgs[s] for s in ICO_SIZES if s != 256])
        imgs[1024].save(os.path.join(out, f"{n}.icns"), format="ICNS",
                        append_images=[imgs[s] for s in ICNS_SIZES if s != 1024])
        for f in ("", "-small"):
            src = os.path.join(SVG, f"{n}{f}.svg")
            open(os.path.join(out, os.path.basename(src)), "wb").write(open(src, "rb").read())
        print("export", n)

# ---- previews ----------------------------------------------------------------------------
def step_previews(icons, cols=6):
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(PREV, exist_ok=True)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
    for dark in (True, False):
        cw, ch = 300, 260
        rows = (len(icons) + cols - 1) // cols
        sheet = Image.new("RGBA", (cols * cw + 20, rows * ch + 20), (32, 33, 36, 255) if dark else (245, 245, 245, 255))
        draw = ImageDraw.Draw(sheet)
        for i, ic in enumerate(icons):
            n = ic["name"]; x, y = 20 + (i % cols) * cw, 20 + (i // cols) * ch
            png = lambda s: Image.open(os.path.join(DIST, n, "png", f"{n}-{s}.png")).convert("RGBA")
            sheet.alpha_composite(png(256).resize((200, 200), Image.LANCZOS), (x, y))
            yy = y
            for s in (48, 32, 24, 16):
                sheet.alpha_composite(png(s), (x + 210, yy)); yy += s + 6
            draw.text((x, y + 210), f"{n.title()} {ic['letter']} – {ic['animal']}",
                      fill=(230, 230, 230) if dark else (30, 30, 30), font=font)
        p = os.path.join(PREV, f"full-set-{'dark' if dark else 'light'}.png")
        sheet.convert("RGB").save(p, optimize=True); print("preview", p)

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("svg", "export", "previews", "all"):
        sys.exit(__doc__)
    step, names = sys.argv[1], sys.argv[2:] or None
    icons = load_icons(names)
    if step in ("svg", "all"): step_svg(icons)
    if step in ("export", "all"): step_export(icons)
    if step in ("previews", "all"): step_previews(load_icons() if step == "all" else icons)
