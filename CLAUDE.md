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
Known near-pairs that were deliberately resolved: hippo is the only bright pink; the rhino is
terracotta (rose-clay clashed with the hippo); the flamingo is violet, not pink, for the same reason.
The lion's gold, bear's caramel and turtle's orange sit close together, so keep new warm colours away
from them. Render a comparison sheet next to the nearest-coloured icons before committing a change.

## Letters
Chosen for distinctness first. See README "About the letters". Notably Kilo = Ϟ, Oscar = Θ,
Quebec = Щ (no Q exists in Greek/Cyrillic), Victor = √. Don't "fix" these to look more correct
without asking.

## Workflow
- Source of truth: `art/<name>.svgfrag` + `icons.json`. `svg/` is generated **and committed**.
  `dist/` is generated and git-ignored.
- `./build.sh --full` regenerates svg/, dist/ and previews/. Steps can be limited:
  `python3 tools/build.py svg|export|previews|all [names…]`.
- Needs `rsvg-convert`, Pillow, fontTools and DejaVu Sans Bold (`ICON_FONT` env var to override).
  The fit step renders each animal with rsvg-convert to measure it, so it is required for `svg` too.
- After any visual change: rebuild, then **look at** `previews/full-set-dark.png` (and a crop at
  16–32 px) before committing. Regenerating unchanged art should produce no git diff.

## Privacy
The repo may be made public, so its whole history must stay free of personal data.
- **No personal data in any committed file or commit message**, even indirectly: no real names,
  user names, host names, home-folder paths (`/Users/…`, `C:\Users\…`) or personal email addresses.
- **No links to private pages**, such as Claude session links (`Claude-Session:` lines) in commit
  messages. `Co-Authored-By` lines are fine.
- **Commits use the identity in the repo's git config** (the GitHub no-reply address). Don't
  override it per commit.
- **Images and SVGs carry no metadata**: no author, software, date or path fields. If a tool starts
  adding them, strip them before committing.
- Rewriting history to remove something is a destructive step: ask first (see below).

## Working with the owner
- Show options as side-by-side preview images before changing the set, including nearby icons
  that might clash.
- Ask before deleting files or running destructive commands; explain where they run.
- Licence is still undecided (leaning split: artwork CC-BY-4.0, code MIT). Don't add one unasked.
