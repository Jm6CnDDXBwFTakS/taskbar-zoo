# Taskbar Zoo: notes for AI coding assistants

Context for AI tools working on this repository, in one file so every tool reads the same text
(the AGENTS.md convention). Claude Code reads it through CLAUDE.md, which pulls this file in.
Humans are welcome to read it too.

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
- Papa is a penguin, the set's only upright full body. It was a panda until 0.11.0, but a round
  head with round ears looked too much like the bear and koala at 32 px and up.

## Colours
Each icon has its own colour in `icons.json`. Before changing one, check its neighbours at small sizes.
Known near-pairs that were deliberately resolved: hippo is the only bright pink; the flamingo is
violet, not pink, for the same reason. The rhino is warm grey: rose-clay clashed with the hippo, and
terracotta with the bear's caramel (almost identical with red-green colour blindness). The koala is
sage-grey: light blue sat too close to X-ray, Echo and Sierra. The vampire bat is cream: green
crowded Quebec, Papa and India (whose I is close to √ in shape). Papa is lime (#66ff75): its
earlier mint green (#59e0a0) sat between November and Quebec, the closest colours in the set, and π is
close in shape to both Щ (a bar on legs, upside down) and N (two uprights). Five colours
changed in 0.11.0 because pairs merged with deuteranopia, which keeps lightness but not the
red-green difference, so each pair now differs in lightness. Darker: the deer (#199bb0; #22bcc6
matched the unicorn's pink), the axolotl (#3a80de; #4a9af0 matched the flamingo's violet) and
the crab (#f5506e; #ff4f4f matched the bear's caramel). Lighter: the walrus (#f2c49a; #e8a882
matched the owl's tan) and the iguana (#b5e04a; #a6d63a matched the lion's gold). The three
darker ones sit at the edge: any lighter and their old clashes, or new ones with the gecko,
return. Keep colours at L* 50 or lighter on the charcoal tile (the yak, at 53, is the darkest):
contrast at small sizes comes first. The lion's gold, bear's
caramel and turtle's orange sit close together, so keep new warm colours away from them. Measure colour
closeness as the eye sees it (CIEDE2000), also as seen with deuteranopia, and render a comparison
sheet next to the nearest-coloured icons before committing a change:
`python3 tools/closeness.py color <name> '#hex' ... --sheet <png>` does both (README, Editing).
Its "risk" (shape overlap x 20 / ΔE, the worse of normal and deuteranopia) only ranks; read the
ΔE and shape columns and look at the sheet. It weighs full deuteranopia, a worst case, as much
as normal vision.

## Letters
Chosen for distinctness first. See README "About the letters". Notably Hotel = Һ, Kilo = Ϟ,
Oscar = Θ, Quebec = Щ (no Q exists in Greek/Cyrillic), Sierra = ς, Victor = √. Don't "fix" these
to look more correct without asking. Before changing a letter, compare its shape (all letters in one
colour) against the whole set at 16 and 24 px, then check it against its colour neighbours:
`python3 tools/closeness.py letter <name> <char> ... --sheet <png>` does both.

## Workflow
- Source of truth: `art/<name>.svgfrag` + `icons.json`. `svg/` is generated **and committed**.
  `dist/` is generated and git-ignored.
- `./build.sh --full` regenerates svg/, dist/ (with `dist/taskbar-zoo-<VERSION>.zip`) and previews/. Steps
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
  and the font). Run them after changing build.py, closeness.py, art/ or icons.json: they also
  check that svg/ is up to date and that README's icon table matches icons.json.
- After any visual change: rebuild, then **look at** `previews/full-set-dark.png` (and a crop at
  16–32 px) before committing. Regenerating unchanged art should produce no git diff.
- Versions: `VERSION` holds the set's version; the zip's file name and README.txt carry it, the
  folder inside stays `taskbar-zoo/`. The first `CHANGELOG.md` entry must match (the tests
  check). `export`, `zip` and a refused or skipped zip remove old zips, so dist/ never holds an
  outdated one. Releasing is in README, Releasing; tag, push and publish only when the owner says so.
  Releases are full releases (pre-release only for -rc), immutable once published, and a ruleset
  keeps `v*` tags from being moved or deleted: a mistake in a release is fixed by a new version.
- Shell code blocks in README hold commands only, with no `#` comments: they get pasted into
  terminals, and zsh (the macOS default) passes a pasted `#` and the words after it as arguments
  unless `interactive_comments` is set. Explain commands in the text around the block instead.

## Privacy
The repo is public, so everything pushed, history included, must stay free of personal data.
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
