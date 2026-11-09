# Taskbar Zoo

26 distinct app icons, one per ICAO phonetic-alphabet name (Alfa, Bravo, Charlie …), for telling
apart several copies of the same app on a taskbar or dock — browser installs or profiles, editor
instances, VMs, terminals, and so on. Each icon has an animal on a shared charcoal tile, with its letter
in a hexagon badge, drawn in the animal colour's complement so it stands out on any taskbar.

![Full set](previews/full-set-dark.png)

## Download

Get `taskbar-zoo-<version>.zip` from the [latest release](../../releases/latest) (older versions
are on the [Releases](../../releases) page): every icon as `.ico` (Windows), `.icns` (macOS), SVG
and PNG, ready to use (see [Using the icons](#using-the-icons)). No build needed. What changed in
each version is in [CHANGELOG.md](CHANGELOG.md).

## Feedback

Releases before 1.0.0 are a test run before the set is fixed. If two icons are hard to tell
apart on your taskbar or dock, an animal doesn't read, or a format doesn't work on your system,
please [open an issue](../../issues) and say which icons, at what size, and on which OS. A
screenshot helps most.

## Telling them apart

The main design goal is that any two icons can be told apart at a glance, at every size from 16 px
up:

- **Two layers:** from 32 px up, each icon shows its animal plus a letter badge. At 16 and 24 px,
  where an animal would be a blur, the icon is the letter alone, in the animal's colour. The badge
  letter becomes readable from about 48 px; at 32 px the animal and its colour do the work.
- **Letters chosen by shape:** every letter was compared with every other at 16 and 24 px, all drawn
  in one colour so only shape counts, and letters in close pairs were replaced (see
  [About the letters](#about-the-letters)).
- **Colours chosen as the eye sees them:** colours were compared by perceived difference
  (CIEDE2000), also as seen with red-green colour blindness. The few colours that are still close
  belong to icons whose letters look nothing alike.
- **A heavy sans-serif font** (DejaVu Sans Bold), because thin strokes and serifs fade at taskbar
  size.

With 26 icons at 16 px, some pairs are inevitably closer than others, but the pairs closest in shape
all differ clearly in colour.

## The set

| Name | Letter | Animal | Colour |
|---|---|---|---|
| Alfa | α | Axolotl | `#4a9af0` |
| Bravo | β | Bear | `#c98049` |
| Charlie | Ч | Crab | `#ff4f4f` |
| Delta | Δ | Deer | `#22bcc6` |
| Echo | Э | Elephant | `#aab6c8` |
| Foxtrot | Ф | Flamingo | `#8a7cff` |
| Golf | Γ | Gecko | `#9d8fc0` |
| Hotel | Һ | Hippo | `#ff80aa` |
| India | I | Iguana | `#a6d63a` |
| Juliett | Ж | Jellyfish | `#cf6bff` |
| Kilo | Ϟ | Koala | `#8da7a3` |
| Lima | Л | Lion | `#f2b124` |
| Mike | μ | Moth | `#ffe04a` |
| November | N | Narwhal | `#7ff0d6` |
| Oscar | Θ | Owl | `#c9a26a` |
| Papa | π | Panda | `#66ff75` |
| Quebec | Щ | Quetzal | `#19c37d` |
| Romeo | R | Rhino | `#958b7f` |
| Sierra | ς | Shark | `#4fc0ff` |
| Tango | τ | Turtle | `#ff7b29` |
| Uniform | Ю | Unicorn | `#ff5fd0` |
| Victor | √ | Vampire bat | `#fddea9` |
| Whiskey | ω | Walrus | `#e8a882` |
| X-ray | X | X-ray fish | `#bfe8ff` |
| Yankee | ψ | Yak | `#c9568a` |
| Zulu | Z | Zebra | `#f4f4f4` |

## About the letters

Each name gets a letter that sounds or looks like its initial: Greek or Cyrillic where one fits,
a plain Latin letter where that is already distinct, and for Victor a symbol. Where the obvious
letter would look too much like another icon's letter at 16 px, distinctness won over accuracy.
Where a note turns down an alternative, it names what **in the current set** the alternative would
be confused with (another icon's letter, or for γ another icon's initial), so the reason can be
checked against the icons as they are now.

- **Greek where it fits:** α β Γ Δ μ π τ — mostly lowercase, with capitals where the lowercase
  form gets in the way: γ reads as a Latin *y*, which suggests Yankee, and δ is a round loop much
  like Θ, Э and β.
- **Sierra — ς:** the final sigma, the form σ takes at the end of a word. The other two forms clash:
  σ is almost the same blob as α at 16 px, and Σ is a zigzag like Z.
- **Yankee — ψ:** psi, for its *Y*-like fork rather than its sound. A plain Y would sit close to τ.
- **Whiskey — ω:** omega, for its *w*-like shape rather than its sound.
- **Cyrillic for Charlie, Echo, Foxtrot, Hotel, Juliett, Lima and Uniform:** Ч (*ch*), Э (*e*),
  Ф (*f*), Һ (*h*), Ж (*zh*), Л (*l*) and Ю (*yu*, as in the start of "Uniform").
  - Һ ("shha", used in Kazakh, Tatar and Bashkir) looks like a Latin h. Greek Η (eta) would look
    like N and Ч.
  - Л rather than Greek Λ, which is Δ without its base.
  - Э rather than Greek ε: against today's letters the two are equally distinct (ε comes closest
    to Z, Э to Θ), so Э stays as the letter already in use.
- **Kilo — Ϟ:** koppa, an archaic Greek *k*-type letter, in its later lightning-bolt form. Greek κ
  shares R's upright stroke with a leg, and X's diagonals.
- **Oscar — Θ:** theta, used for its shape: the bar inside keeps it from being a plain ring. Every
  O-like letter (O, Ö, Ω, Θ) comes closest to α at 16 px, and α is far away in colour.
- **Quebec — Щ:** neither alphabet has a Q, so this is purely a bold, distinctive shape (it's
  pronounced roughly *shch*). The historically "correct" letter, Ϙ (koppa, the ancestor of Latin
  Q), is the same letter as Kilo's Ϟ.
- **Victor — √:** a square-root sign, the most distinct shape in the set. A plain V would work, but
  it shares ψ's open fork, and √'s long tail keeps it further away. Nod to math class.
- **India, November, Romeo, X-ray, Zulu — I, N, R, X, Z:** plain Latin letters, used where they are
  already distinct. Greek ρ would look like μ, and Ξ (xi) like Z and Э.

## Repository layout

```
AGENTS.md         notes for AI coding assistants (CLAUDE.md just points Claude Code to it)
VERSION           the set's version (e.g. 0.10.0), used in the zip's name and README.txt
CHANGELOG.md      what changed in each release
icons.json        name → letter, animal, colour (optional: centre offset, display title like "X-ray")
art/*.svgfrag     the animal drawings (SVG snippets using colour tokens)
svg/              generated master SVGs — the files to use or convert
  <name>.svg                 full icon (animal + badge), used for 32 px and up
  <name>-small.svg           letter-only version, used for 16 and 24 px
tools/build.py    regenerates everything
tools/closeness.py  measures how close icons are in colour and letter shape (see Editing)
tests/            tests for build.py and closeness.py (need only Pillow)
build.sh          convenience wrapper
previews/         contact sheets of the whole set
dist/             (git-ignored) PNG / ICO / ICNS output, and taskbar-zoo-<version>.zip with all of it
```

The SVGs in `svg/` are self-contained: letters are stored as outlines, so they render identically
without any fonts installed.

## Building

Requirements:

- **export** (SVG → PNG/ICO/ICNS): `rsvg-convert` (librsvg) and Python 3 with Pillow
- **svg** (art → SVG, only needed after editing art or icons.json): also `fontTools` and the
  DejaVu Sans Bold font (set `ICON_FONT=/path/to/DejaVuSans-Bold.ttf` if it isn't found)
- **previews**: Pillow and DejaVu Sans (regular), looked for next to `ICON_FONT` and in the usual
  font folders

### Setup

`rsvg-convert` and the fonts come from the system. On Debian or Ubuntu (`python3-venv` provides
`python3 -m venv`):

```sh
sudo apt install librsvg2-bin fonts-dejavu-core python3-venv
```

On macOS (DejaVu Sans isn't in Homebrew's librsvg; get it from dejavu-fonts.github.io):

```sh
brew install librsvg
```

The Python packages (Pillow, fontTools) go in a virtual environment in `.venv/`, a folder with its
own Python and packages, so nothing is installed globally. `.venv/` is git-ignored. Create it once
(on Windows: `py -m venv .venv`, then `.venv\Scripts\pip install -r requirements.txt`):

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

The code blocks in this README hold only commands, no `#` comments, so they can be pasted into any
shell. zsh, the default on macOS, treats a pasted `#` as an ordinary word unless the
`interactive_comments` option is set, so a comment would turn into extra arguments.

### Build

Activate the virtual environment in each new shell, so `python3` means the one in `.venv/` (on
Windows: `.venv\Scripts\activate`; `deactivate` leaves it again). Then build: `./build.sh` turns
the SVGs into `dist/` (PNG 16–1024, ICO, ICNS), the zip and the previews.

```sh
. .venv/bin/activate
./build.sh
```

After editing `art/` or `icons.json`, run `./build.sh --full` instead: it regenerates `svg/` first.

Or step by step: `python3 tools/build.py svg|export|zip|previews|all [names…]`. Names limit `svg`
and `export`; `zip` and `previews` always cover the full set from `dist/`, so they need every icon
exported, and exported again after its SVGs change. Run on their own, they stop and say which icons
to export; within `all <names>` they are skipped with that message.

`dist/taskbar-zoo-<version>.zip` is the whole set in one file, ready to hand out: a `taskbar-zoo/`
folder with each icon's `.ico`, `.icns`, SVGs and PNGs, plus `LICENSE` and a `README.txt` saying
which file to use where. The version comes from the `VERSION` file and appears in the zip's name
and README.txt, but not in the folder inside: unpacking a newer zip over an older one keeps each
icon at the same path, so shortcuts pointing at it keep working. `export` and `zip` remove the
zips already in `dist/`, of any version, and so does a zip step that can't run, so a zip there
always matches the current files. The same files in `dist/` give a byte-identical zip on any OS.

`./build.sh` runs the zip and the previews even if the other fails: a bad `VERSION` stops only the
zip, a missing preview font only the previews.

On Windows, which has no `sh` or `python3`, run `python tools/build.py all` in place of
`./build.sh --full`.

### Tests

With the virtual environment active: `python3 -m unittest discover -s tests`. They need only
Pillow: small stand-ins replace rsvg-convert and the font. They also check that `svg/` is up to date
with `art/` and `icons.json`, that the table under "The set" matches `icons.json`, and on a Mac they
round-trip the `.icns` output through Apple's `iconutil`.

### Releasing

A release is a git tag plus a GitHub release with the zip attached:

1. Put the version in `VERSION` and add an entry for it at the top of `CHANGELOG.md`, headed like
   `## 0.10.0 (2026-11-09)` (UTC date); its introduction says which number to raise. The tests
   check the two match.
2. Run `./build.sh`, then the tests. A release builds from the committed SVGs, so it needs only
   rsvg-convert and Pillow (fontTools is for regenerating `svg/`).
3. Commit, then tag and publish with the GitHub CLI (`gh`), from the repository's top folder. The
   commands read the version from `VERSION`, so they need no editing. The release notes are the
   changelog entry, saved in `dist/` (which git ignores, so it can't be committed by accident):

```sh
v=$(cat VERSION)
awk -v v="$v" '/^## /{if(f)exit; if($2==v){f=1;next}} f' CHANGELOG.md | sed '1{/^$/d}' > dist/notes.md
test -s dist/notes.md || echo "CHANGELOG.md has no entry for $v: nothing will be tagged or published"
test -s "dist/taskbar-zoo-$v.zip" || echo "dist/taskbar-zoo-$v.zip is missing: run ./build.sh first"
test -s dist/notes.md && test -s "dist/taskbar-zoo-$v.zip" &&
  git tag -a "v$v" -m "Taskbar Zoo $v" &&
  git push origin main "v$v" &&
  gh release create "v$v" "dist/taskbar-zoo-$v.zip" --verify-tag --title "Taskbar Zoo $v" \
      --notes-file dist/notes.md
```

Line by line:

- `v=$(cat VERSION)` reads the version, e.g. 0.10.0. The other commands all use `$v`.
- `awk` copies this version's changelog entry without its heading: the lines from that heading up
  to the next `## `. `sed` drops the blank line after the heading.
- `test -s` means "the file exists and isn't empty". The two `test … || echo` lines only report a
  missing changelog entry or zip. The chain after them does the work: `&&` runs each step only if
  the one before it succeeded, so without notes and a zip nothing is tagged, and a failed tag or
  push stops it there. Checking first matters because a pushed `v*` tag is permanent (see below).
  If only the last step fails (say, the network drops), run the `gh release create` line again:
  the tag is already on GitHub, which is what `--verify-tag` wants.
- `git tag -a` makes an annotated tag, with its own date and message.
- `--verify-tag` stops if the tag isn't on GitHub yet, rather than creating one there. Add
  `--prerelease` only for release candidates (see below).

Releases are full releases, so the newest is "Latest": the repository's sidebar shows it, and
`…/releases/latest` leads to it. The 0.x number already says the set may still change. Mark only
release candidates (`1.0.0-rc.1`) as pre-releases.

Two things are one-way on this repository. Releases are immutable (Settings, General, Releases):
once published, the zip can't be replaced, so a fix goes out as a new version. And a ruleset
("Release tags are permanent") stops `v*` tags from being moved or deleted.

## Editing

- **Change a colour or letter:** first measure the candidates against the rest of the set, then
  edit `icons.json` and run `./build.sh --full`. For example, to try two colours for the panda or
  two letters for Victor:

  ```sh
  python3 tools/closeness.py color papa '#66ff75' '#33ffa7' --sheet /tmp/papa.png
  python3 tools/closeness.py letter victor √ V --sheet /tmp/victor.png
  ```

  `python3 tools/closeness.py report` lists the closest pairs in the set as it is. Each candidate is
  listed with its nearest icons by colour difference (CIEDE2000, also as seen
  with red-green colour blindness) and by letter-shape overlap at 16 and 24 px, safest first. The
  sheet draws them side by side at real pixel sizes, a second time as seen with colour blindness;
  look at it before deciding, since the numbers only rank. `color` and `letter` need what `svg`
  needs (fontTools and DejaVu Sans Bold); `report` needs only rsvg-convert and Pillow.
- **Redraw an animal:** edit `art/<name>.svgfrag`. Draw on a 512×512 canvas with these colour tokens:
  `MAIN` (icon colour, rendered as a gradient), `SHADE` (darker), `LIGHT` (lighter), `CREAM`, `DARK`.
  Exact size and position don't matter; each drawing is measured and auto-fitted to the tile. It
  only has to stay within 200 units of the canvas edge (the area the build measures).
  Side-profile animals face left, away from the badge.

## Using the icons

Each icon's files are in the zip's `taskbar-zoo/<name>/` folder, or after a build in `dist/<name>/`.

- **Linux:** in the app's `.desktop` file, set `Icon=` to the SVG or the 256/512 PNG.
- **Windows:** shortcut → Properties → Change Icon → choose the `.ico`. If a pinned taskbar icon keeps
  the app's original logo, unpin it, change the icon on the shortcut, then pin the shortcut again.
- **macOS:** Get Info on the app, then drag the `.icns` (or the 1024 PNG) onto the small icon at top left.

## Licence

MIT, for the code and the artwork alike: see [LICENSE](LICENSE). Using an icon on your own taskbar
or dock needs no credit; copies of the set should keep the licence file.

The letters in `svg/` are outlines from the DejaVu Sans Bold font, used under its licence (the
Bitstream Vera licence; DejaVu's changes are public domain).
