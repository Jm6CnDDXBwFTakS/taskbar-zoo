"""Tests for tools/build.py that need only Python 3 and Pillow: no rsvg-convert, fontTools or fonts.

Run from the repository root:

    python3 -m unittest discover -s tests -v

rsvg-convert and the font are replaced by small stand-ins, so these tests check build.py's own logic:
the SVG templates, the .icns writer and how the build steps fit together. All output goes to a
temporary folder, so svg/, dist/ and previews/ are never touched. On a Mac, the .icns test also
round-trips the file through Apple's iconutil.
"""
import contextlib, importlib.util, io, os, re, shutil, struct, subprocess, tempfile, unittest
import xml.dom.minidom
from unittest import mock

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# tools/ is not a package, so load build.py from its path
_spec = importlib.util.spec_from_file_location("build", os.path.join(ROOT, "tools", "build.py"))
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)

RED, BLUE = (255, 0, 0), (0, 0, 255)


def fake_render(svg_file, png_file, size):
    """Stand-in for rsvg-convert: letter-only SVGs become a red tile, full ones a blue tile. Both
    have see-through corners and a half-transparent band, like the soft edges of real icons."""
    c = RED if svg_file.endswith("-small.svg") else BLUE
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=max(2, size // 5), fill=c + (255,))
    d.rectangle((0, size // 2, size - 1, size // 2 + max(1, size // 8)), fill=c + (128,))
    im.save(png_file)


def read_icns(path):
    """{type: data} for each entry of an .icns file, checking that the lengths add up."""
    with open(path, "rb") as f:
        data = f.read()
    assert data[:4] == b"icns" and struct.unpack(">I", data[4:8])[0] == len(data), "bad header"
    entries, i = {}, 8
    while i < len(data):
        kind, n = data[i:i + 4], struct.unpack(">I", data[i + 4:i + 8])[0]
        entries[kind] = data[i + 8:i + n]
        i += n
    assert i == len(data), "entry lengths overrun the file"
    return entries


def decode_argb(data, size):
    """The inverse of build.icns_argb: an RGBA image from an ARGB entry (PackBits per plane)."""
    assert data[:4] == b"ARGB"
    raw, j = bytearray(), 4
    while j < len(data):
        h = data[j]; j += 1
        if h < 128:
            raw += data[j:j + h + 1]; j += h + 1
        else:                               # Apple's run form: h - 125 copies of the next byte
            raw += bytes([data[j]]) * (h - 125); j += 1
    n = size * size
    a, r, g, b = (Image.frombytes("L", (size, size), bytes(raw[k * n:(k + 1) * n])) for k in range(4))
    return Image.merge("RGBA", (r, g, b, a))


def same_visible_pixels(a, b, tolerance=0):
    """True if two RGBA images differ by at most `tolerance` per channel wherever a pixel is visible
    in either (fully transparent pixels carry no colour, so their RGB is ignored)."""
    a, b = a.convert("RGBA"), b.convert("RGBA")
    if a.size != b.size:
        return False
    # blank out pixels transparent in both images, then compare channel by channel
    visible = ImageChops.lighter(*(im.getchannel("A").point(lambda v: 255 if v else 0) for im in (a, b)))
    blank = Image.new("RGBA", a.size, (0, 0, 0, 0))
    diff = ImageChops.difference(Image.composite(a, blank, visible), Image.composite(b, blank, visible))
    return max(high for _, high in diff.getextrema()) <= tolerance


class TempOutput(unittest.TestCase):
    """Points build.py's svg/, dist/ and previews/ at an empty temporary folder for each test."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        for name in ("SVG", "DIST", "PREV"):
            folder = os.path.join(self.tmp, name.lower())
            os.makedirs(folder)
            patcher = mock.patch.object(build, name, folder)
            patcher.start(); self.addCleanup(patcher.stop)
        self.quiet = contextlib.redirect_stdout(io.StringIO())

    def export_fakes(self, names):
        """dist/<name>/png/ files for these icons, drawn by the stand-in renderer."""
        for n in names:
            os.makedirs(os.path.dirname(build.png_path(n, 16)), exist_ok=True)
            for s in build.PNG_SIZES:
                fake_render(f"{n}{'-small' if s <= build.SMALL_MAX else ''}.svg", build.png_path(n, s), s)


class TemplateTests(unittest.TestCase):
    def setUp(self):
        for name, value in (("glyph", lambda *a: ("M0 0Z", "scale(1)", 1.0)), ("fit", lambda icon: "scale(1)")):
            patcher = mock.patch.object(build, name, value)
            patcher.start(); self.addCleanup(patcher.stop)
        self.icon = dict(name="test", letter="<", animal="Fish & chips", color="#123456",
                         art='<path d="M0 0" fill="MAIN"/>')

    def test_titles_are_escaped(self):
        for svg, text in ((build.full_svg(self.icon), "Test (<) - Fish & chips"),
                          (build.small_svg(self.icon), "Test (<), small")):
            dom = xml.dom.minidom.parseString(svg.encode())
            self.assertEqual(dom.getElementsByTagName("title")[0].firstChild.data, text)

    def test_ids_carry_the_icon_name_and_every_reference_resolves(self):
        svg = build.full_svg(self.icon)
        ids = set(re.findall(r'id="([^"]+)"', svg))
        self.assertEqual(ids, {"test-g", "test-m", "test-tile"})
        self.assertLessEqual(set(re.findall(r"url\(#([^)]+)\)", svg)), ids)

    def test_display_title(self):
        self.assertEqual(build.title({"name": "xray", "title": "X-ray"}), "X-ray")
        self.assertEqual(build.title({"name": "alfa"}), "Alfa")


class CommittedSvgTests(unittest.TestCase):
    def test_svg_folder_matches_art_and_icons_json(self):
        """svg/ is what build.py makes from art/ and icons.json. The two measured values (the art's
        fit transform and the letter outlines) need rsvg-convert and the font, so they are taken
        from the committed files; everything else (colours, ids, titles, art) must match."""
        def committed(name):
            path = os.path.join(ROOT, "svg", name)
            if not os.path.exists(path):
                self.fail(f"svg/{name} is missing: run ./build.sh --full")
            with open(path, encoding="utf-8") as f:
                return f.read()
        fits, glyphs = {}, {}
        icons = build.load_icons()
        for ic in icons:
            full, small = committed(f"{ic['name']}.svg"), committed(f"{ic['name']}-small.svg")
            fits[ic["name"]] = re.search(r'<g transform="([^"]+)">', full).group(1)
            m = re.search(r'<path d="([^"]+)" transform="([^"]+)" fill="[^"]+" stroke="[^"]+" stroke-width="([^"]+)"', full)
            glyphs[ic["letter"], 79] = (m.group(1), m.group(2), 9 / float(m.group(3)))
            m = re.search(r'<path d="([^"]+)" transform="([^"]+)" fill=', small)
            glyphs[ic["letter"], 330] = (m.group(1), m.group(2), None)
        with mock.patch.object(build, "fit", lambda icon: fits[icon["name"]]), \
             mock.patch.object(build, "glyph", lambda ch, cx, cy, height, width: glyphs[ch, height]):
            for ic in icons:
                with self.subTest(icon=ic["name"]):
                    self.assertEqual(build.full_svg(ic), committed(f"{ic['name']}.svg"),
                                     "svg/ is out of date: run ./build.sh --full")
                    self.assertEqual(build.small_svg(ic), committed(f"{ic['name']}-small.svg"),
                                     "svg/ is out of date: run ./build.sh --full")


class FitTests(unittest.TestCase):
    icon = dict(name="test", color="#123456", art="")

    def fit_with(self, box):
        """fit() with rsvg-convert replaced by a probe image holding one filled box (or nothing)."""
        def render(svg_file, png_file, size):
            im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            if box:
                ImageDraw.Draw(im).rectangle(box, fill="black")
            im.save(png_file)
        with mock.patch.object(build, "render", render):
            return build.fit(self.icon)

    def test_centres_and_scales_the_art(self):
        # probe pixels 300..599 are art coordinates 100..399: 300 wide, centred on 250
        self.assertEqual(self.fit_with((300, 300, 599, 599)),
                         "translate(256.0,256.0) scale(1.3200) translate(-250.0,-250.0)")

    def test_empty_art_stops_with_a_message(self):
        with self.assertRaises(SystemExit) as cm:
            self.fit_with(None)
        self.assertIn("draws nothing visible", str(cm.exception))

    def test_art_past_the_measured_area_stops_with_a_message(self):
        with self.assertRaises(SystemExit) as cm:
            self.fit_with((0, 300, 599, 599))
        self.assertIn("reaches past the measured area", str(cm.exception))


class ExportTests(TempOutput):
    def test_ico_and_icns(self):
        for suffix in ("", "-small"):
            with open(os.path.join(build.SVG, f"test{suffix}.svg"), "w") as f:
                f.write("<svg/>")
        with mock.patch.object(build, "render", fake_render), self.quiet:
            build.step_export([{"name": "test"}])
        out = os.path.join(build.DIST, "test")
        src = {}
        for s in build.PNG_SIZES:
            with Image.open(build.png_path("test", s)) as im:
                src[s] = im.convert("RGBA")

        with Image.open(os.path.join(out, "test.ico")) as ico:
            self.assertEqual(sorted(ico.info["sizes"]), [(s, s) for s in build.ICO_SIZES])

        entries = read_icns(os.path.join(out, "test.icns"))
        self.assertEqual(list(entries), [kind for kind, _ in build.ICNS_ENTRIES])
        for kind, size in build.ICNS_ENTRIES:
            with self.subTest(entry=kind.decode()):
                if kind in build.ICNS_ARGB:
                    self.assertTrue(same_visible_pixels(decode_argb(entries[kind], size), src[size]))
                else:
                    with open(build.png_path("test", size), "rb") as f:
                        self.assertEqual(entries[kind], f.read())
        # the 16 px slot holds the letter-only icon (red), the 32 px one the full icon (blue)
        self.assertEqual(decode_argb(entries[b"ic04"], 16).getpixel((8, 4))[:3], RED)
        self.assertEqual(decode_argb(entries[b"ic05"], 32).getpixel((16, 8))[:3], BLUE)

        for svg in ("test.svg", "test-small.svg"):
            self.assertTrue(os.path.exists(os.path.join(out, svg)))

    @unittest.skipUnless(shutil.which("iconutil"), "needs macOS iconutil")
    def test_icns_round_trips_through_iconutil(self):
        for suffix in ("", "-small"):
            with open(os.path.join(build.SVG, f"test{suffix}.svg"), "w") as f:
                f.write("<svg/>")
        with mock.patch.object(build, "render", fake_render), self.quiet:
            build.step_export([{"name": "test"}])
        iconset = os.path.join(self.tmp, "test.iconset")
        subprocess.run(["iconutil", "-c", "iconset", os.path.join(build.DIST, "test", "test.icns"),
                        "-o", iconset], check=True)
        want = {"16x16": 16, "16x16@2x": 32, "32x32": 32, "32x32@2x": 64, "128x128": 128,
                "128x128@2x": 256, "256x256": 256, "256x256@2x": 512, "512x512": 512, "512x512@2x": 1024}
        self.assertEqual(sorted(f[5:-4] for f in os.listdir(iconset)), sorted(want))
        # iconutil decodes through macOS's own image code, which may round a channel by a step or
        # two; a wrong slot or channel order is off by far more than that
        for name, size in want.items():
            with self.subTest(file=name), Image.open(os.path.join(iconset, f"icon_{name}.png")) as got, \
                 Image.open(build.png_path("test", size)) as source:
                self.assertTrue(same_visible_pixels(got, source, tolerance=2))


class MainTests(TempOutput):
    def run_main(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            build.main(list(argv))
        return out.getvalue()

    def test_unknown_name_lists_the_known_ones(self):
        with self.assertRaises(SystemExit) as cm:
            self.run_main("svg", "alpha")
        self.assertIn("Unknown icon name: alpha", str(cm.exception))
        self.assertIn("alfa, bravo", str(cm.exception))

    def test_previews_refuse_names(self):
        with self.assertRaises(SystemExit) as cm:
            self.run_main("previews", "alfa")
        self.assertIn("full set", str(cm.exception))

    def test_previews_need_every_icon_exported(self):
        self.export_fakes(["alfa"])
        with self.assertRaises(SystemExit) as cm:
            self.run_main("previews")
        self.assertIn("not exported yet: bravo,", str(cm.exception))

    def test_all_with_names_builds_those_and_skips_previews(self):
        calls = []
        with mock.patch.object(build, "step_svg", lambda icons: calls.append(("svg", [i["name"] for i in icons]))), \
             mock.patch.object(build, "step_export", lambda icons: calls.append(("export", [i["name"] for i in icons]))):
            out = self.run_main("all", "alfa")
        self.assertEqual(calls, [("svg", ["alfa"]), ("export", ["alfa"])])
        self.assertIn("previews skipped", out)
        self.assertEqual(os.listdir(build.PREV), [])

    def test_previews_draw_the_full_set_reading_each_png_once(self):
        icons = build.load_icons()
        self.export_fakes([ic["name"] for ic in icons])
        opened = []
        real_open = Image.open
        def counting_open(path, *a, **k):
            opened.append(path); return real_open(path, *a, **k)
        # any font will do here: the test checks the sheets, not the lettering. Load it before
        # patching, because load_default() itself calls truetype().
        font = ImageFont.load_default()
        with mock.patch.object(ImageFont, "truetype", lambda *a, **k: font), \
             mock.patch.object(Image, "open", counting_open):
            self.run_main("previews")
        self.assertEqual(len(opened), len(icons) * len(build.PREVIEW_SIZES))
        self.assertEqual(len(set(opened)), len(opened))
        for sheet in ("full-set-dark.png", "full-set-light.png"):
            with Image.open(os.path.join(build.PREV, sheet)) as im:
                self.assertEqual(im.size, (6 * 300 + 20, 5 * 260 + 20))

    def test_missing_label_font_says_how_to_get_it(self):
        self.export_fakes([ic["name"] for ic in build.load_icons()])
        with mock.patch.object(build, "find_font", lambda name: None), \
             mock.patch.object(ImageFont, "truetype", mock.Mock(side_effect=OSError)):
            with self.assertRaises(SystemExit) as cm:
                self.run_main("previews")
        self.assertIn("install DejaVu Sans", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
