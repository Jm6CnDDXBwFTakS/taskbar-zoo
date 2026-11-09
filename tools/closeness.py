#!/usr/bin/env python3
"""Measure how close the icons are to each other, by colour and by letter shape.

    python3 tools/closeness.py report                 # the closest pairs in the set as it is
    python3 tools/closeness.py color papa '#66ff75'   # try other colours for one icon
    python3 tools/closeness.py letter victor √ V ✔    # try other letters for one icon
    ... --sheet out.png                               # also draw a comparison sheet
    ... --top 12                                      # how many rows to list (default 8)

Run it before changing a colour or a letter (CLAUDE.md, Colours and Letters), and look at the sheet.

Three measures, each explained where it is computed below:

- Colour closeness is CIEDE2000 (ΔE), the standard formula for how different two colours look to
  the eye. About 2 is barely noticeable side by side; in this set anything under about 12 is close.
- Every colour is also measured as seen with deuteranopia, the most common red-green colour
  blindness, by simulating it first (Machado, Oliveira and Fernandes, 2009).
- Shape closeness is the overlap of two letter-only icons at 16 and 24 px: the share of inked
  pixels they have in common (0 = nothing shared, 1 = identical). Letters are compared with their
  colour removed, so only the shape counts.

A pair is risky when it is close in both: "risk" = overlap × 20 / ΔE, a ranking aid with no unit.
For example overlap 0.66 at ΔE 10.7 gives 1.23, while the same overlap at ΔE 20 gives 0.66.

Needs rsvg-convert and Pillow, like build.py's export. `color` and `letter` build the candidate
icons with build.py's own templates, so they also need fontTools and DejaVu Sans Bold. `report`
reads the committed svg/ files, so it does not.
"""
import argparse, math, os, re, sys, tempfile
from itertools import combinations

# tools/ is not a package: when run as a script, this file's folder is on sys.path, so build.py
# imports by name. Its helpers (load_icons, render, small_svg ...) are reused rather than copied.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # noqa: E402  (the import has to follow the sys.path line above)

SHAPE_SIZES = (16, 24)          # the sizes where only the letter shows (build.SMALL_MAX)
RISK_SCALE = 20                 # risk = overlap * RISK_SCALE / ΔE: scales typical risks to about 1

# ---- colour --------------------------------------------------------------------------------
# A hex colour like "#66ff75" is three sRGB values, 0-255. sRGB is "gamma encoded": the numbers
# grow faster than the light they stand for, so maths on light (mixing, colour blindness) first
# converts them to linear values, 0-1, and back afterwards.

def srgb_to_linear(c):
    """One sRGB channel, 0-255, to linear light, 0-1 (the sRGB standard's curve)."""
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def linear_to_srgb(c):
    """The inverse of srgb_to_linear, clipped to 0-255 (simulation can step slightly outside)."""
    c = min(1.0, max(0.0, c))
    return 255 * (12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055)

def to_lab(rgb):
    """sRGB (0-255 each) to CIE L*a*b*, the colour space CIEDE2000 works in: L* is lightness
    (0 black to 100 white), a* runs green to red, b* blue to yellow. Via CIE XYZ with the D65
    white point, which is what sRGB screens use."""
    r, g, b = (srgb_to_linear(c) for c in rgb)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    def f(t):
        return t ** (1 / 3) if t > (6 / 29) ** 3 else t / (3 * (6 / 29) ** 2) + 4 / 29
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)

def ciede2000(lab1, lab2):
    """CIEDE2000 colour difference (ΔE00) between two L*a*b* colours.

    Plain distance in L*a*b* overstates differences between strong colours and misjudges blues,
    so CIEDE2000 corrects it: it re-weights lightness, chroma (colourfulness) and hue by where the
    colours sit, and adds a rotation term for blues. Follows Sharma, Wu and Dalal (2005), whose
    published test pairs are in tests/test_closeness.py."""
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2
    C_bar = (math.hypot(a1, b1) + math.hypot(a2, b2)) / 2
    G = 0.5 * (1 - math.sqrt(C_bar ** 7 / (C_bar ** 7 + 25 ** 7)))
    a1p, a2p = a1 * (1 + G), a2 * (1 + G)
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360 if C1p else 0.0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360 if C2p else 0.0

    dLp, dCp = L2 - L1, C2p - C1p
    if C1p * C2p == 0:              # a grey has no hue, so there is no hue difference
        dhp = 0.0
    else:
        dhp = h2p - h1p
        if dhp > 180:               # take the short way round the colour wheel
            dhp -= 360
        elif dhp < -180:
            dhp += 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp / 2))

    Lp_bar, Cp_bar = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0:
        hp_bar = h1p + h2p
    elif abs(h1p - h2p) > 180:
        hp_bar = (h1p + h2p + 360) / 2 if h1p + h2p < 360 else (h1p + h2p - 360) / 2
    else:
        hp_bar = (h1p + h2p) / 2
    T = (1 - 0.17 * math.cos(math.radians(hp_bar - 30)) + 0.24 * math.cos(math.radians(2 * hp_bar))
         + 0.32 * math.cos(math.radians(3 * hp_bar + 6)) - 0.20 * math.cos(math.radians(4 * hp_bar - 63)))
    S_L = 1 + 0.015 * (Lp_bar - 50) ** 2 / math.sqrt(20 + (Lp_bar - 50) ** 2)
    S_C = 1 + 0.045 * Cp_bar
    S_H = 1 + 0.015 * Cp_bar * T
    d_theta = 30 * math.exp(-(((hp_bar - 275) / 25) ** 2))
    R_T = -2 * math.sqrt(Cp_bar ** 7 / (Cp_bar ** 7 + 25 ** 7)) * math.sin(math.radians(2 * d_theta))
    return math.sqrt((dLp / S_L) ** 2 + (dCp / S_C) ** 2 + (dHp / S_H) ** 2
                     + R_T * (dCp / S_C) * (dHp / S_H))

# Deuteranopia (no working green-sensitive cones), severity 1.0, from Machado et al. 2009. The
# matrix acts on linear RGB: each row says how much of R, G and B the eye mixes into that channel.
DEUTERANOPIA = ((0.367322, 0.860646, -0.227968),
                (0.280085, 0.672501, 0.047413),
                (-0.011820, 0.042940, 0.968881))

def deuteranopia(rgb):
    """The sRGB colour (0-255 each) as seen with deuteranopia, also 0-255 (floats)."""
    lin = [srgb_to_linear(c) for c in rgb]
    return tuple(linear_to_srgb(sum(m * v for m, v in zip(row, lin))) for row in DEUTERANOPIA)

def color_distances(rgb1, rgb2):
    """(ΔE for normal vision, ΔE as seen with deuteranopia) between two sRGB colours."""
    return (ciede2000(to_lab(rgb1), to_lab(rgb2)),
            ciede2000(to_lab(deuteranopia(rgb1)), to_lab(deuteranopia(rgb2))))

# ---- shape ---------------------------------------------------------------------------------
# A letter-only SVG is a charcoal tile with one path, the letter. With the tile removed, the
# rendered image's alpha channel says how much of each pixel the letter covers (0-255, partly
# covered pixels at the edges in between), whatever its colour: a "coverage mask".

TILE = re.compile(r"\s*<rect [^>]*/>")

def coverage(small_svg_text, size):
    """The letter's coverage mask at size x size px: a list of floats, 0-1, row by row."""
    from PIL import Image
    letter_only = TILE.sub("", small_svg_text, count=1)
    with tempfile.TemporaryDirectory() as t:
        svg, png = os.path.join(t, "letter.svg"), os.path.join(t, "letter.png")
        build.write_text(svg, letter_only)
        build.render(svg, png, size)
        with Image.open(png) as im:
            return [v / 255 for v in im.convert("RGBA").getchannel("A").tobytes()]

def overlap(mask1, mask2):
    """How much two coverage masks have in common, 0-1: the ink both share divided by the ink
    either has ("intersection over union", with partly covered pixels counting in part)."""
    both = sum(map(min, mask1, mask2))
    either = sum(map(max, mask1, mask2))
    return both / either if either else 0.0

def shape_overlap(masks1, masks2):
    """The larger overlap over SHAPE_SIZES: a pair counts as close if it is close at any size.
    masks1 and masks2 map each size to a coverage mask."""
    return max(overlap(masks1[s], masks2[s]) for s in SHAPE_SIZES)

def risk(shape, delta_e):
    """Ranking aid: high when two icons are close in shape and in colour. ΔE below 1 counts as 1."""
    return shape * RISK_SCALE / max(1.0, delta_e)

def pair_risk(shape, delta_e_normal, delta_e_deuteranopia):
    """A pair's risk: the worse of normal vision and deuteranopia. The one place that decides how
    the two are combined, so the printed risk and every ranking by it always agree."""
    return max(risk(shape, delta_e_normal), risk(shape, delta_e_deuteranopia))

# ---- the set -------------------------------------------------------------------------------

hex_rgb = build.hex_rgb             # "#66ff75" -> (102, 255, 117)

def committed_masks(icons):
    """{name: {size: mask}} from the committed letter-only SVGs in svg/."""
    return {ic["name"]: {s: coverage(build.read_text(os.path.join(build.SVG, f"{ic['name']}-small.svg")), s)
                         for s in SHAPE_SIZES}
            for ic in icons}

def pair_rows(icons, masks):
    """One row per pair of icons:
    (name1, name2, shape overlap, ΔE normal, ΔE deuteranopia, risk)."""
    rows = []
    for a, b in combinations(icons, 2):
        dn, dd = color_distances(hex_rgb(a["color"]), hex_rgb(b["color"]))
        sh = shape_overlap(masks[a["name"]], masks[b["name"]])
        rows.append((a["name"], b["name"], sh, dn, dd, pair_risk(sh, dn, dd)))
    return rows

def neighbours(candidate_rgb, candidate_masks, others, masks):
    """How one candidate (a colour and a letter's masks) compares with every other icon:
    rows of (name, shape overlap, ΔE normal, ΔE deuteranopia, worst risk), riskiest first."""
    rows = []
    for ic in others:
        dn, dd = color_distances(candidate_rgb, hex_rgb(ic["color"]))
        sh = shape_overlap(candidate_masks, masks[ic["name"]])
        rows.append((ic["name"], sh, dn, dd, pair_risk(sh, dn, dd)))
    return sorted(rows, key=lambda r: -r[4])

# ---- output --------------------------------------------------------------------------------

def label(icon):
    return f"{build.title(icon)} {icon['letter']}"

def print_report(icons, rows, top):
    by = {ic["name"]: ic for ic in icons}
    def line(r):
        a, b, sh, dn, dd, rk = r
        return (f"  {label(by[a]):<12} {label(by[b]):<12} shape {sh:.2f}   ΔE {dn:5.1f}   "
                f"deuteranopia ΔE {dd:5.1f}   risk {rk:.2f}")
    sections = (("Closest colours, normal vision", lambda r: r[3]),
                ("Closest colours with deuteranopia", lambda r: r[4]),
                ("Closest letter shapes", lambda r: -r[2]),
                ("Riskiest pairs (close in shape and colour)", lambda r: -r[5]))
    for title, key in sections:
        print(title + ":")
        for r in sorted(rows, key=key)[:top]:
            print(line(r))

def print_candidates(target, results, icons, top):
    """results: [(caption, neighbour rows)] for each candidate, best (lowest worst risk) first."""
    by = {ic["name"]: ic for ic in icons}
    print(f"Candidates for {build.title(target)}, safest first (risk of the riskiest neighbour):")
    for caption, rows in results:
        print(f"  {caption}: risk {rows[0][4]:.2f}")
        for name, sh, dn, dd, rk in rows[:top]:
            print(f"      {label(by[name]):<12} shape {sh:.2f}   ΔE {dn:5.1f}   deuteranopia ΔE {dd:5.1f}   risk {rk:.2f}")

SHEET_ZOOM = 3          # each pixel drawn as a 3x3 block, without smoothing
SHEET_GAP = 8           # px between images, and the sheet's margin
SHEET_CAPTION = 20      # px from the top of a row to its first image, below the caption

def sheet_position(row, icon, size):
    """Top-left corner of one image on a sheet (before the deuteranopia copy is added below):
    `icon` counts from 0 within the row, `size` is 16, 24 or 32. draw_sheet places every image
    here, and tests use it to find one. Images are centred vertically in a 32 px row."""
    z, gap = SHEET_ZOOM, SHEET_GAP
    cell = (16 + 24 + 32) * z + 3 * gap         # one icon: its three sizes, each followed by a gap
    x = gap + icon * cell + (6 * gap + (icon - 1) * 3 * gap if icon else 0)
    for s in (16, 24, 32):                      # step past the smaller sizes of the same icon
        if s == size:
            break
        x += s * z + gap
    y = gap + row * (32 * z + 30) + SHEET_CAPTION + (32 - size) * z // 2
    return x, y

def draw_sheet(path, sheet_rows):
    """A comparison sheet: each row is a caption and a list of icons, each drawn letter-only at 16
    and 24 px and full at 32 px, enlarged without smoothing so real pixels show. The same sheet
    as seen with deuteranopia is drawn below it, SHEET_GAP px lower.
    sheet_rows: [(caption, [(full_svg, small_svg)])], at least one row."""
    from PIL import Image, ImageDraw, ImageFont
    zoom, gap = SHEET_ZOOM, SHEET_GAP
    cell = (16 + 24 + 32) * zoom + 3 * gap      # one icon: its three sizes, each followed by a gap
    row_h = 32 * zoom + 30
    n = max(len(icons) for _, icons in sheet_rows)
    # where an icon after the last one would start (sheet_position), which leaves a right margin
    width = sheet_position(0, n, 16)[0]
    sheet = Image.new("RGBA", (width, len(sheet_rows) * row_h + gap), (32, 33, 36, 255))
    draw = ImageDraw.Draw(sheet)
    font_path = build.find_font(build.LABEL_FONT)
    font = ImageFont.truetype(font_path, 14) if font_path else ImageFont.load_default()
    with tempfile.TemporaryDirectory() as t:
        for r, (caption, row_icons) in enumerate(sheet_rows):
            y = gap + r * row_h
            draw.text((gap, y), caption, fill=(225, 225, 225), font=font)
            for i, (full, small) in enumerate(row_icons):
                for size, svg_text in ((16, small), (24, small), (32, full)):
                    svg, png = os.path.join(t, "i.svg"), os.path.join(t, "i.png")
                    build.write_text(svg, svg_text)
                    build.render(svg, png, size)
                    with Image.open(png) as im:
                        big = im.convert("RGBA").resize((size * zoom, size * zoom), Image.NEAREST)
                    sheet.alpha_composite(big, sheet_position(r, i, size))
    normal = sheet.convert("RGB")
    seen = {}                                           # each distinct colour is converted once
    def simulate(p):
        if p not in seen:
            seen[p] = tuple(round(v) for v in deuteranopia(p))
        return seen[p]
    simulated = Image.new("RGB", normal.size)
    simulated.putdata([simulate(p) for p in zip(*(iter(normal.tobytes()),) * 3)])
    out = Image.new("RGB", (normal.width, normal.height * 2 + gap), (15, 15, 17))
    out.paste(normal, (0, 0))
    out.paste(simulated, (0, normal.height + gap))
    out.save(path)
    print("sheet", path)

def committed_svgs(name):
    return (build.read_text(os.path.join(build.SVG, f"{name}.svg")),
            build.read_text(os.path.join(build.SVG, f"{name}-small.svg")))

# ---- commands ------------------------------------------------------------------------------

def cmd_report(args):
    build.require("report", programs=("rsvg-convert",), modules=("PIL",))
    icons = build.load_icons()
    rows = pair_rows(icons, committed_masks(icons))
    print_report(icons, rows, args.top)
    if args.sheet:
        by = {ic["name"]: ic for ic in icons}
        worst = sorted(rows, key=lambda r: -r[5])[:args.top]
        draw_sheet(args.sheet, [(f"{label(by[a])} / {label(by[b])}", [committed_svgs(a), committed_svgs(b)])
                                for a, b, *_ in worst])

def try_candidates(args, variants):
    """Shared by `color` and `letter`: variants is [(caption, icon dict with the change applied)]."""
    build.require(args.command, programs=("rsvg-convert",), modules=("PIL", "fontTools"))
    icons = build.load_icons()
    target = next((ic for ic in icons if ic["name"] == args.name), None)
    if target is None:
        sys.exit(f"Unknown icon name: {args.name}\nKnown names: {', '.join(ic['name'] for ic in icons)}")
    others = [ic for ic in icons if ic["name"] != args.name]
    masks = committed_masks(others)
    results, sheet_rows = [], []
    for caption, icon in variants(target):
        small = build.small_svg(icon)
        cand_masks = {s: coverage(small, s) for s in SHAPE_SIZES}
        rows = neighbours(hex_rgb(icon["color"]), cand_masks, others, masks)
        results.append((caption, rows))
        if args.sheet:
            sheet_rows.append((caption, [(build.full_svg(icon), small)]
                               + [committed_svgs(name) for name, *_ in rows[:4]]))
    order = sorted(range(len(results)), key=lambda i: results[i][1][0][4])
    print_candidates(target, [results[i] for i in order], icons, args.top)
    if args.sheet:
        draw_sheet(args.sheet, [sheet_rows[i] for i in order])

def cmd_color(args):
    for c in args.colors:
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", c):
            sys.exit(f"{c!r} is not a colour like #66ff75")
    try_candidates(args, lambda target: [(f"{target['letter']} in {c.lower()}"
                                          + (" (current)" if c.lower() == target["color"] else ""),
                                          dict(target, color=c.lower())) for c in args.colors])

def cmd_letter(args):
    # Check every letter before measuring any: build.glyph would stop at the first bad one with a
    # message about icons.json, which the person running this didn't touch. A "letter" that looks
    # like one character can be two code points, e.g. ✌️ is ✌ plus an emoji-style selector.
    build.require("letter", modules=("fontTools",))
    from fontTools.ttLib import TTFont
    font = build.find_font(build.BOLD_FONT)
    if not font:
        sys.exit("DejaVu Sans Bold not found; set ICON_FONT=/path/to/DejaVuSans-Bold.ttf")
    cmap = TTFont(font).getBestCmap()
    def code_points(ch):            # U+270C U+FE0F: shows characters that print as nothing
        return " ".join(f"U+{ord(c):04X}" for c in ch)
    bad = [f"{ch} ({code_points(ch)}) is {len(ch)} characters, not one" if len(ch) != 1
           else f"the font has no {ch} ({code_points(ch)})"
           for ch in args.letters if len(ch) != 1 or ord(ch) not in cmap]
    if bad:
        sys.exit("Can't try these letters: " + "; ".join(bad))
    try_candidates(args, lambda target: [(f"{ch} in {target['color']}"
                                          + (" (current)" if ch == target["letter"] else ""),
                                          dict(target, letter=ch)) for ch in args.letters])

def positive_int(text):
    """argparse type for --top: a whole number of at least 1."""
    n = int(text)
    if n < 1:
        raise argparse.ArgumentTypeError(f"must be 1 or more, not {n}")
    return n

def main(argv):
    # The output holds ΔE and Greek and Cyrillic letters. On Windows, output sent to a file or a
    # pipe uses the old code page (cp1252), which has none of them, and print would fail; UTF-8
    # works everywhere. (A StringIO, as in the tests, has no reconfigure and needs none.)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="closeness.py", description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog="Commands: report, color NAME #HEX..., letter NAME CHAR...")
    sub = p.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--top", type=positive_int, default=8, help="rows to list per section (default 8)")
    common.add_argument("--sheet", metavar="PNG", help="also draw a comparison sheet to this file")
    sub.add_parser("report", parents=[common], help="the closest pairs in the set as it is")
    c = sub.add_parser("color", parents=[common], help="try colours for one icon")
    c.add_argument("name")
    c.add_argument("colors", nargs="+", metavar="#HEX")
    lt = sub.add_parser("letter", parents=[common], help="try letters for one icon")
    lt.add_argument("name")
    lt.add_argument("letters", nargs="+", metavar="CHAR")
    args = p.parse_args(argv)
    {"report": cmd_report, "color": cmd_color, "letter": cmd_letter}[args.command](args)

if __name__ == "__main__":
    main(sys.argv[1:])
