"""Tests for tools/closeness.py that need only Python 3 and Pillow.

Run from the repository root:

    python3 -m unittest discover -s tests -v

The colour maths is checked against published reference values (CIEDE2000 test pairs from Sharma,
Wu and Dalal, 2005). rsvg-convert is replaced by a small stand-in that turns an SVG into an image
whose alpha channel the test chooses, so the shape and command code runs without it.
"""
import contextlib, importlib.util, io, os, sys, tempfile, unittest
from unittest import mock

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# tools/ is not a package, so load closeness.py from its path. It imports build.py by name, from
# its own folder; tests patch that same module object through closeness.build.
_spec = importlib.util.spec_from_file_location("closeness", os.path.join(ROOT, "tools", "closeness.py"))
closeness = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(closeness)
build = closeness.build


def opaque_render(svg_file, png_file, size):
    """Stand-in for rsvg-convert: every SVG becomes a fully covered square."""
    Image.new("RGBA", (size, size), (255, 255, 255, 255)).save(png_file)


class ColorTests(unittest.TestCase):
    # (L*a*b* 1, L*a*b* 2, ΔE00) from Sharma, Wu and Dalal (2005), "The CIEDE2000 color-difference
    # formula: implementation notes, supplementary test data and mathematical observations".
    # The pairs cover the cases that implementations get wrong: two hues almost exactly opposite,
    # where a tiny change in b* flips which way round the colour wheel the mean hue is taken
    # (pairs 14 and 15: 7.1792 becomes 7.2195), a grey against a colour (7), large differences (17)
    # and blues (1, 25).
    SHARMA = [((50.0, 2.6772, -79.7751), (50.0, 0.0, -82.7485), 2.0425),
              ((50.0, 0.0, 0.0), (50.0, -1.0, 2.0), 2.3669),
              ((50.0, 2.49, -0.001), (50.0, -2.49, 0.0010), 7.1792),
              ((50.0, 2.49, -0.001), (50.0, -2.49, 0.0011), 7.2195),
              ((50.0, 2.5, 0.0), (73.0, 25.0, -18.0), 27.1492),
              ((60.2574, -34.0099, 36.2677), (60.4626, -34.1751, 39.4387), 1.2644)]

    def test_ciede2000_matches_the_published_test_pairs(self):
        for lab1, lab2, want in self.SHARMA:
            with self.subTest(lab1=lab1, lab2=lab2):
                self.assertAlmostEqual(closeness.ciede2000(lab1, lab2), want, places=4)
                self.assertAlmostEqual(closeness.ciede2000(lab2, lab1), want, places=4)   # symmetric

    def test_lab_of_known_colours(self):
        for rgb, want in (((255, 255, 255), (100, 0, 0)), ((0, 0, 0), (0, 0, 0)),
                          ((255, 0, 0), (53.24, 80.09, 67.20))):       # sRGB red, a standard value
            with self.subTest(rgb=rgb):
                for got, w in zip(closeness.to_lab(rgb), want):
                    self.assertAlmostEqual(got, w, delta=0.05)

    def test_deuteranopia_keeps_greys_and_merges_red_with_green(self):
        for v in (0, 64, 128, 255):
            with self.subTest(grey=v):
                for got in closeness.deuteranopia((v, v, v)):
                    self.assertAlmostEqual(got, v, delta=1)
        # the confusion this simulates: a red and a green that differ strongly for normal vision
        normal, simulated = closeness.color_distances((200, 80, 60), (110, 130, 40))
        self.assertGreater(normal, 20)
        self.assertLess(simulated, normal / 3)

    def test_risk_treats_differences_below_one_as_one(self):
        self.assertEqual(closeness.risk(0.5, 0.2), 0.5 * closeness.RISK_SCALE)
        self.assertEqual(closeness.risk(0.5, 10), 0.5 * closeness.RISK_SCALE / 10)


class ShapeTests(unittest.TestCase):
    def test_overlap(self):
        self.assertEqual(closeness.overlap([1, 1, 0, 0], [1, 1, 0, 0]), 1.0)
        self.assertEqual(closeness.overlap([1, 1, 0, 0], [0, 0, 1, 1]), 0.0)
        self.assertEqual(closeness.overlap([1, 1, 0, 0], [1, 0, 0, 0]), 0.5)
        self.assertEqual(closeness.overlap([0.5, 0], [1, 0]), 0.5)      # partly covered pixels
        self.assertEqual(closeness.overlap([0, 0], [0, 0]), 0.0)        # no ink at all

    def test_shape_overlap_takes_the_closer_size(self):
        a = {16: [1, 0], 24: [1, 1]}
        b = {16: [0, 1], 24: [1, 1]}
        self.assertEqual(closeness.shape_overlap(a, b), 1.0)

    def test_coverage_measures_the_letter_without_its_tile(self):
        seen = []
        def render(svg_file, png_file, size):
            seen.append(build.read_text(svg_file))
            im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            im.putpixel((0, 0), (255, 255, 255, 255))
            im.putpixel((1, 0), (255, 255, 255, 51))
            im.save(png_file)
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">\n'
               '  <rect x="0" y="0" width="512" height="512" rx="112" fill="#1a1a1d"/>\n'
               '  <path d="M0 0Z" fill="#66ff75"/>\n</svg>\n')
        with mock.patch.object(build, "render", render):
            mask = closeness.coverage(svg, 4)
        self.assertNotIn("<rect", seen[0])          # the tile would cover every pixel
        self.assertIn("<path", seen[0])
        self.assertEqual(len(mask), 16)
        self.assertEqual(mask[:3], [1.0, 0.2, 0.0])

    def test_neighbours_rank_by_risk_and_leave_out_nothing_else(self):
        others = [dict(name="far", color="#000000"), dict(name="near", color="#66ff70"),
                  dict(name="shape", color="#0000ff")]
        same, other = {16: [1, 1], 24: [1, 1]}, {16: [0, 1], 24: [0, 1]}
        masks = {"far": same, "near": other, "shape": same}
        rows = closeness.neighbours((0x66, 0xff, 0x75), same, others, masks)
        self.assertEqual([r[0] for r in rows][0], "near")       # almost the same colour
        self.assertEqual(sorted(r[0] for r in rows), ["far", "near", "shape"])
        self.assertEqual(rows, sorted(rows, key=lambda r: -r[4]))


class CommandTests(unittest.TestCase):
    def setUp(self):
        """rsvg-convert is replaced by the stand-in, so the check for it (and fontTools) is skipped."""
        for name, value in (("render", opaque_render), ("require", lambda *a, **k: None)):
            patcher = mock.patch.object(build, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_main(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            closeness.main(list(argv))
        return out.getvalue()

    def test_report_lists_every_section(self):
        out = self.run_main("report", "--top", "2")
        for title in ("Closest colours, normal vision:", "Closest colours with deuteranopia:",
                      "Closest letter shapes:", "Riskiest pairs (close in shape and colour):"):
            self.assertIn(title, out)
        self.assertEqual(out.count("shape 1.00"), 8)              # the stand-in covers everything

    def test_a_bad_colour_or_name_stops_with_a_message(self):
        for argv, message in ((("color", "papa", "lime"), "'lime' is not a colour like #66ff75"),
                              (("color", "panda", "#66ff75"), "Unknown icon name: panda")):
            with self.subTest(argv=argv), self.assertRaises(SystemExit) as cm:
                self.run_main(*argv)
            self.assertIn(message, str(cm.exception))

    def test_sheet_shows_the_rows_twice_the_second_time_as_with_deuteranopia(self):
        with tempfile.TemporaryDirectory() as t:
            path = os.path.join(t, "sheet.png")
            red = '<svg xmlns="http://www.w3.org/2000/svg"><rect fill="red"/></svg>'
            def render(svg_file, png_file, size):
                Image.new("RGBA", (size, size), (220, 40, 40, 255)).save(png_file)
            with mock.patch.object(build, "render", render), contextlib.redirect_stdout(io.StringIO()):
                closeness.draw_sheet(path, [("one", [(red, red), (red, red)])])
            with Image.open(path) as im:
                im = im.convert("RGB")
                # the first icon's 16 px image: x from the 8 px margin, y below the 20 px caption
                # line, centred in the 32 px row (16 px enlarged 3x starts 24 px down)
                x, y = 8 + 5, 8 + 20 + 24 + 5
                sheet_height = (im.height - 8) // 2     # two sheets with an 8 px gap between
                top = im.getpixel((x, y))
                bottom = im.getpixel((x, sheet_height + 8 + y))
        self.assertEqual(top, (220, 40, 40))
        self.assertEqual(bottom, tuple(round(v) for v in closeness.deuteranopia((220, 40, 40))))


if __name__ == "__main__":
    unittest.main()
