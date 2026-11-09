# Taskbar Zoo: notes for Claude

26 app icons, one per ICAO name (alfa … zulu), for telling apart multiple copies of the same app
on a taskbar or dock. The set is deliberately app-neutral: don't brand it for any one app.

## Design priorities (in order)
1. **Contrast and distinctness at taskbar size**: every icon must be telling-apart-able at 16–32 px.
2. **Recognizable animal**: geometric, flat, not realistic.
3. Variety is welcome, but never at the cost of 1.

## Style rules
- Shared charcoal rounded tile (same for all icons). The animal carries the colour.
- Flat angular shapes; tones per icon: `MAIN` (gradient), `SHADE`, `LIGHT`, plus shared `CREAM` and `DARK`.
- **Front-facing heads preferred.** Side profiles are allowed (flamingo, quetzal, unicorn, X-ray fish)
  and must **face left**, away from the badge. They're mirrored with a
  `<g transform="translate(512,0) scale(-1,1)">` wrapper in their art file and nudged up-left via
  `"center": [240, 244]` in icons.json.
- Letter badge: flat-topped hexagon, bottom-right, filled with the icon colour; the letter is the
  **complementary colour** with a thin dark outline. Don't put the letter on the animal itself.
- Sizes ≤ 24 px use the letter-only `-small.svg` (letter in icon colour on charcoal).
- The panda smiles (it's deliberately different from the bear).

## Colours
Each icon has its own colour in `icons.json`. Before changing one, check its neighbours at small sizes.
Known near-pairs that were deliberately resolved: hippo is the only bright pink; the flamingo is
violet, not pink, for the same reason. The rhino is warm grey: rose-clay clashed with the hippo, and
terracotta with the bear's caramel (almost identical with red-green colour blindness). The koala is
sage-grey: light blue sat too close to X-ray, Echo and Sierra. The vampire bat is cream: green
crowded Quebec, Papa and India (whose I is close to √ in shape). The lion's gold, bear's caramel and
turtle's orange sit close together, so keep new warm colours away from them. Measure colour
closeness as the eye sees it (CIEDE2000), also as seen with deuteranopia, and render a comparison
sheet next to the nearest-coloured icons before committing a change.

## Letters
Chosen for distinctness first. See README "About the letters". Notably Hotel = Һ, Kilo = Ϟ,
Oscar = Θ, Quebec = Щ (no Q exists in Greek/Cyrillic), Sierra = ς, Victor = √. Don't "fix" these
to look more correct without asking. Before changing a letter, compare its shape (all letters in one
colour) against the whole set at 16 and 24 px, then check it against its colour neighbours.

## Workflow
- Source of truth: `art/<name>.svgfrag` + `icons.json`. `svg/` is generated **and committed**.
  `dist/` is generated and git-ignored.
- `./build.sh --full` regenerates svg/, dist/ (with `dist/taskbar-zoo.zip`) and previews/. Steps
  can be limited: `python3 tools/build.py svg|export|zip|previews|all [names…]`. Names limit svg and
  export only: the zip always holds the full set, with LICENSE and a generated README.txt, and
  previews always draw it (they overwrite the committed `full-set-*.png`). Both refuse an icon whose
  files in dist/ are missing or older than its SVGs: after `svg`, run `export` before them. The zip
  runs first because it needs nothing beyond Python, and is byte-identical for the same dist/ files.
- Needs `rsvg-convert`, Pillow, fontTools and DejaVu Sans Bold (`ICON_FONT` env var to override);
  previews also need DejaVu Sans (regular), looked for next to `ICON_FONT` first.
  The fit step renders each animal with rsvg-convert to measure it, so it is required for `svg` too.
- Python packages live in `.venv/` (README, Setup), the supported setup: run the build and the tests
  with `.venv/bin/python` or with the venv activated, and never install packages globally.
- `.icns` files are written by build.py itself, not Pillow (whose writer has no 16/32 px @1x
  slots). The tests round-trip them through `iconutil` on a Mac.
- Tests: `python3 -m unittest discover -s tests` (needs only Pillow; stand-ins replace rsvg-convert
  and the font). Run them after changing build.py, art/ or icons.json: they also check that svg/
  is up to date and that README's icon table matches icons.json.
- After any visual change: rebuild, then **look at** `previews/full-set-dark.png` (and a crop at
  16–32 px) before committing. Regenerating unchanged art should produce no git diff.

## Privacy
The repo may be made public, so its whole history must stay free of personal data.
- **No personal data in any committed file or commit message**, even indirectly: no real names,
  user names, host names, home-folder paths (`/Users/…`, `C:\Users\…`) or personal email addresses.
- **No links to private pages**, such as Claude session links (`Claude-Session:` lines) in commit
  messages. `Co-Authored-By` lines are fine.
- **Commits use the identity in the repo's git config** (the GitHub no-reply address). Don't
  override it per commit. A clone doesn't copy that config, so on a fresh clone check
  `git config user.email` before the first commit; if it isn't the no-reply address, set it:
  `git config user.name "Jm6CnDDXBwFTakS"` and
  `git config user.email "58570069+Jm6CnDDXBwFTakS@users.noreply.github.com"`.
- **Images and SVGs carry no metadata**: no author, software, date or path fields. If a tool starts
  adding them, strip them before committing.
- Rewriting history to remove something is a destructive step: ask first (see below).

## Working with the owner
- Show options as side-by-side preview images before changing the set, including nearby icons
  that might clash.
- Ask before deleting files or running destructive commands; explain where they run.
- Licence: MIT for everything, code and artwork alike (LICENSE; the holder is the GitHub handle,
  never a real name). The letter outlines come from DejaVu Sans Bold; if the font changes, update
  the font credit in README's Licence section to match.
