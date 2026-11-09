#!/usr/bin/env python3
"""Build the Taskbar Zoo icon set.

    python3 tools/build.py svg              # art/ + icons.json  ->  svg/        (needs fontTools + a font)
    python3 tools/build.py export           # svg/  ->  dist/ PNG, ICO, ICNS     (needs rsvg-convert + Pillow)
    python3 tools/build.py previews         # dist/ ->  previews/ contact sheets (always the full set)
    python3 tools/build.py all              # all of the above
    python3 tools/build.py svg alfa bravo   # limit svg, export or all to some icons

Art fragments in art/*.svgfrag are SVG snippets drawn on a 512x512 canvas using colour tokens:
    MAIN   icon colour (rendered as a soft top-to-bottom gradient)
    SHADE  darker tone of the icon colour
    LIGHT  lighter tone of the icon colour
    CREAM  shared off-white (muzzles, highlights)
    DARK   shared near-black (eyes, noses)
Size and position don't matter: each animal is measured and auto-fitted to the tile.
"""
import colorsys, importlib.util, json, math, os, shutil, struct, subprocess, sys, tempfile
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART, SVG, DIST, PREV = (os.path.join(ROOT, d) for d in ("art", "svg", "dist", "previews"))

# ---- palette & geometry -------------------------------------------------------------------
TILE_TOP, TILE_BOT, TILE_EDGE = "#2e2e33", "#1a1a1d", "#3c3c42"
CREAM, DARK = "#fdf1e8", "#1b1b1d"
TILE_RX = 112                       # tile corner radius
FIT_BOX = 396                       # animal fits inside a FIT_BOX square
PROBE_PAD = 200                     # fit() measures the art from -PROBE_PAD to 512 + PROBE_PAD
PROBE = 512 + 2 * PROBE_PAD
BADGE_X, BADGE_Y, BADGE_R = 402, 402, 80
PNG_SIZES = (16, 24, 32, 48, 64, 128, 256, 512, 1024)
SMALL_MAX = 24                      # sizes <= this use the letter-only SVG
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
# ICNS entries (type, pixel size), the same set Apple's iconutil writes. ic11..ic14 are the @2x
# slots for 16, 32, 128 and 256 pt. Pillow's own writer has no 16 or 32 px @1x slot, so macOS would
# shrink the 32 px full icon for a 16 pt icon instead of using the letter-only one. ic04 and ic05
# hold raw ARGB like iconutil's: macOS misreads PNG data there (and in the older icp4/icp5 slots).
ICNS_ENTRIES = ((b"ic04", 16), (b"ic05", 32), (b"ic07", 128), (b"ic08", 256), (b"ic09", 512),
                (b"ic10", 1024), (b"ic11", 32), (b"ic12", 64), (b"ic13", 256), (b"ic14", 512))
ICNS_ARGB = (b"ic04", b"ic05")
BOLD_FONT, LABEL_FONT = "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"
FONT_DIRS = ["/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/TTF", "/Library/Fonts",
             os.path.expanduser("~/Library/Fonts"), "C:/Windows/Fonts"]


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

def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def write_text(path, text):
    # newline="\n": the same bytes on every OS, so a rebuild on Windows shows no git diff
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

def find_font(filename):
    """Path to a DejaVu font: $ICON_FONT (for the bold font) or its folder, then the usual font folders."""
    icon_font = os.environ.get("ICON_FONT", "")
    paths = [icon_font] if icon_font and filename == BOLD_FONT else []
    folders = ([os.path.dirname(icon_font)] if icon_font else []) + FONT_DIRS
    paths += [os.path.join(d, filename) for d in folders]
    return next((p for p in paths if p and os.path.exists(p)), None)

def title(icon):
    """Display name: "title" from icons.json if set (e.g. "X-ray"), else the capitalised name."""
    return icon.get("title", icon["name"].title())

def load_icons(names=None):
    meta = json.loads(read_text(os.path.join(ROOT, "icons.json")))
    unknown = [n for n in names or () if n not in meta]
    if unknown:
        sys.exit(f"Unknown icon name: {', '.join(unknown)}\nKnown names: {', '.join(meta)}")
    out = []
    for n in names or meta:
        e = dict(meta[n], name=n)
        e["art"] = read_text(os.path.join(ART, f"{n}.svgfrag"))
        out.append(e)
    return out

WHERE_FROM = {"rsvg-convert": "librsvg", "fontTools": "requirements.txt"}

def require(step, programs=(), modules=()):
    """Stop with one line naming whatever this step needs but can't find, before it writes anything.
    Programs are looked up on PATH, modules among the installed Python packages."""
    missing = [p for p in programs if shutil.which(p) is None]
    missing += [m for m in modules if importlib.util.find_spec(m) is None]
    if missing:
        sys.exit(f"{step} needs {' and '.join(f'{t} (from {WHERE_FROM[t]})' for t in missing)}, "
                 "not installed; see README, Building")

def render(svg_file, png_file, size):
    subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size), svg_file, "-o", png_file], check=True)

def png_path(name, size):
    return os.path.join(DIST, name, "png", f"{name}-{size}.png")

# ---- SVG generation ----------------------------------------------------------------------
_font = None
def glyph(ch, cx, cy, height, width_max):
    """Outline of `ch` as an SVG path, centred on (cx, cy). Letters become paths, so the SVGs need no font."""
    global _font
    from fontTools.ttLib import TTFont
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.boundsPen import BoundsPen
    if _font is None:
        path = find_font(BOLD_FONT)
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
    main = c if probe else f"url(#{icon['name']}-m)"
    return (icon["art"].replace("MAIN", main).replace("SHADE", darken(c, 0.6))
            .replace("LIGHT", lighten(c, 0.55)).replace("CREAM", CREAM).replace("DARK", DARK))

def fit(icon):
    """Render the art alone, measure its bounding box, and return a transform that centres it."""
    cx, cy = icon.get("center", (256, 256))
    probe = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-PROBE_PAD} {-PROBE_PAD} {PROBE} {PROBE}" '
             f'width="{PROBE}" height="{PROBE}"><g>{tokens(icon, True)}</g></svg>')
    from PIL import Image
    with tempfile.TemporaryDirectory() as t:
        sp, pp = os.path.join(t, "p.svg"), os.path.join(t, "p.png")
        write_text(sp, probe); render(sp, pp, PROBE)
        with Image.open(pp) as im:
            box = im.getchannel("A").getbbox()
    art = f"art/{icon['name']}.svgfrag"
    if box is None:
        sys.exit(f"{art} draws nothing visible")
    if box[0] == 0 or box[1] == 0 or box[2] == PROBE or box[3] == PROBE:
        sys.exit(f"{art} reaches past the measured area ({-PROBE_PAD} to {512 + PROBE_PAD}); "
                 "keep the drawing near the 512x512 canvas")
    x0, y0, x1, y1 = (v - PROBE_PAD for v in box)
    s = min(FIT_BOX / (x1 - x0), FIT_BOX / (y1 - y0))
    return f"translate({cx:.1f},{cy:.1f}) scale({s:.4f}) translate({-(x0 + x1) / 2:.1f},{-(y0 + y1) / 2:.1f})"

def full_svg(icon):
    # ids carry the icon name, so several icons can be inlined in one page without clashing
    c, letter, n = icon["color"], icon["letter"], icon["name"]
    hexd = "M" + " L".join(f"{BADGE_X + BADGE_R * math.cos(math.radians(a)):.1f},"
                           f"{BADGE_Y + BADGE_R * math.sin(math.radians(a)):.1f}" for a in range(0, 360, 60)) + " Z"
    d, tf, s = glyph(letter, BADGE_X, BADGE_Y, 79, 104)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <title>{escape(f"{title(icon)} ({letter}) - {icon['animal']}")}</title>
  <defs>
    <linearGradient id="{n}-g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{TILE_TOP}"/><stop offset="1" stop-color="{TILE_BOT}"/>
    </linearGradient>
    <linearGradient id="{n}-m" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{lighten(c, 0.14)}"/><stop offset="1" stop-color="{darken(c, 0.93)}"/>
    </linearGradient>
    <clipPath id="{n}-tile"><rect x="8" y="8" width="496" height="496" rx="{TILE_RX}"/></clipPath>
  </defs>
  <rect x="8" y="8" width="496" height="496" rx="{TILE_RX}" fill="url(#{n}-g)"/>
  <g clip-path="url(#{n}-tile)">
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
  <title>{escape(f"{title(icon)} ({icon['letter']}), small")}</title>
  <rect x="0" y="0" width="512" height="512" rx="{TILE_RX}" fill="{TILE_BOT}"/>
  <path d="{d}" transform="{tf}" fill="{icon["color"]}"/>
</svg>
'''

def step_svg(icons):
    require("svg", programs=("rsvg-convert",), modules=("fontTools",))   # fit() renders, glyph() reads the font
    os.makedirs(SVG, exist_ok=True)
    for ic in icons:
        n = ic["name"]
        write_text(os.path.join(SVG, f"{n}.svg"), full_svg(ic))
        write_text(os.path.join(SVG, f"{n}-small.svg"), small_svg(ic))
        print("svg   ", n)

# ---- raster export -----------------------------------------------------------------------
def icns_argb(im):
    """Apple's ARGB entry data: 'ARGB', then the A, R, G and B planes (straight, not premultiplied
    colour), each PackBits-coded. Written as literal runs only (a count byte n-1, then n bytes):
    valid PackBits, just not compressed, which costs about 4 KB for the 32 px image."""
    data = b"ARGB"
    for ch in "ARGB":
        raw = im.getchannel(ch).tobytes()
        for i in range(0, len(raw), 128):
            chunk = raw[i:i + 128]; data += bytes([len(chunk) - 1]) + chunk
    return data

def write_icns(path, name, imgs):
    """An .icns file is 'icns' + total length, then one (type, length, data) entry per slot."""
    body = b""
    for kind, size in ICNS_ENTRIES:
        if kind in ICNS_ARGB:
            data = icns_argb(imgs[size])
        else:
            with open(png_path(name, size), "rb") as f:
                data = f.read()
        body += kind + struct.pack(">I", 8 + len(data)) + data
    with open(path, "wb") as f:
        f.write(b"icns" + struct.pack(">I", 8 + len(body)) + body)

def step_export(icons):
    require("export", programs=("rsvg-convert",))
    from PIL import Image
    for ic in icons:
        n = ic["name"]
        full, small = (os.path.join(SVG, f"{n}{s}.svg") for s in ("", "-small"))
        out = os.path.join(DIST, n); os.makedirs(os.path.join(out, "png"), exist_ok=True)
        imgs = {}
        for sz in PNG_SIZES:
            render(small if sz <= SMALL_MAX else full, png_path(n, sz), sz)
            with Image.open(png_path(n, sz)) as im:
                imgs[sz] = im.convert("RGBA")
        imgs[256].save(os.path.join(out, f"{n}.ico"), format="ICO", sizes=[(s, s) for s in ICO_SIZES],
                       append_images=[imgs[s] for s in ICO_SIZES if s != 256])
        write_icns(os.path.join(out, f"{n}.icns"), n, imgs)
        for src in (full, small):
            shutil.copyfile(src, os.path.join(out, os.path.basename(src)))
        print("export", n)

# ---- previews ----------------------------------------------------------------------------
PREVIEW_SIDE = (48, 32, 24, 16)         # drawn in a column beside the big 256 px icon
PREVIEW_SIZES = (256,) + PREVIEW_SIDE

def missing_exports(icons):
    return [ic["name"] for ic in icons if not all(os.path.exists(png_path(ic["name"], s)) for s in PREVIEW_SIZES)]

def step_previews(icons, cols=6):
    """Contact sheets of the given icons, light and dark. The caller passes the full set."""
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(PREV, exist_ok=True)
    try:   # labels hold Greek and Cyrillic letters, which Pillow's built-in font lacks
        font = ImageFont.truetype(find_font(LABEL_FONT) or LABEL_FONT, 18)
    except OSError:
        sys.exit(f"DejaVu Sans ({LABEL_FONT}) not found for the preview labels; install DejaVu Sans, "
                 "or put the file next to $ICON_FONT")
    pngs = {}                           # (name, size) -> image, read once for both sheets
    for ic in icons:
        for s in PREVIEW_SIZES:
            with Image.open(png_path(ic["name"], s)) as im:
                pngs[ic["name"], s] = im.convert("RGBA")
    for dark in (True, False):
        cw, ch = 300, 260
        rows = (len(icons) + cols - 1) // cols
        sheet = Image.new("RGBA", (cols * cw + 20, rows * ch + 20), (32, 33, 36, 255) if dark else (245, 245, 245, 255))
        draw = ImageDraw.Draw(sheet)
        for i, ic in enumerate(icons):
            n = ic["name"]; x, y = 20 + (i % cols) * cw, 20 + (i // cols) * ch
            imgs = {s: pngs[n, s] for s in PREVIEW_SIZES}
            sheet.alpha_composite(imgs[256].resize((200, 200), Image.LANCZOS), (x, y))
            yy = y
            for s in PREVIEW_SIDE:
                sheet.alpha_composite(imgs[s], (x + 210, yy)); yy += s + 6
            draw.text((x, y + 210), f"{title(ic)} {ic['letter']} – {ic['animal']}",
                      fill=(230, 230, 230) if dark else (30, 30, 30), font=font)
        p = os.path.join(PREV, f"full-set-{'dark' if dark else 'light'}.png")
        sheet.convert("RGB").save(p, optimize=True); print("preview", p)

def main(argv):
    """Run the build steps named in argv (the command-line arguments, without the script name)."""
    if not argv or argv[0] not in ("svg", "export", "previews", "all"):
        sys.exit(__doc__)
    step, names = argv[0], argv[1:] or None
    if step == "previews" and names:
        sys.exit("previews always show the full set; run it without icon names")
    icons = load_icons(names)
    if step in ("svg", "all"): step_svg(icons)
    if step in ("export", "all"): step_export(icons)
    if step in ("previews", "all"):
        everything = icons if names is None else load_icons()
        missing = missing_exports(everything)
        if missing:
            msg = (f"previews need every icon in dist/; not exported yet: {', '.join(missing)}\n"
                   "Run: python3 tools/build.py export")
            if step == "previews": sys.exit(msg)
            print("previews skipped:", msg)
        else:
            step_previews(everything)

if __name__ == "__main__":
    main(sys.argv[1:])
