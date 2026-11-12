# Changelog

What changed in each release of Taskbar Zoo. Versions follow [semantic versioning](https://semver.org):
for an icon set, the major number goes up when an existing icon changes in a way users would notice
(its name, letter, animal or colour, or where its files sit in the zip), the minor number for new
icons or formats, and the patch number for fixes that keep every icon looking the same. Before
1.0.0, any of these may still change in a minor release.

The newest entry's version must match the `VERSION` file (the tests check), and its text becomes
the GitHub release notes (README, Releasing).

## 0.11.0 (2026-11-12)

- Papa is now a penguin instead of a panda, in the same lime and with the same π. The panda's
  round head and round ears looked too much like Bravo's bear and Kilo's koala at 32 px and up;
  the penguin is the only upright full body in the set. At 16 and 24 px nothing changes, since
  those sizes show only the letter.
- Three colours are darker, so that pairs which looked alike to people with red-green colour
  blindness (deuteranopia) now differ in lightness:
  - Delta's deer is deep teal (`#1690a8`, was `#22bcc6`), apart from Uniform's pink unicorn.
  - Alfa's axolotl is deep blue (`#3577d8`, was `#4a9af0`), apart from Foxtrot's violet flamingo.
  - Charlie's crab is crimson (`#e83a5a`, was `#ff4f4f`), apart from Bravo's caramel bear.
- No other icon, letter, colour or file name changed.

## 0.10.0 (2026-11-09)

- Papa's panda is now lime (`#66ff75`) instead of mint green (`#59e0a0`). The mint sat between
  November's narwhal and Quebec's quetzal, the closest colours in the set, and its π looks like
  both of their letters at 16 px: a bar on legs like Щ upside down, and two uprights like N. Lime
  moves the panda well clear of both.
- No other icon, letter or file name changed.

## 0.9.0 (2026-11-09)

First release, for feedback before the set is fixed at 1.0.0.

- 26 icons, Alfa to Zulu: an animal on a charcoal tile with a Greek, Cyrillic or Latin letter
  badge, and a letter-only version for 16 and 24 px.
- Formats: `.ico` (16 to 256 px), `.icns` (16 to 1024 px), SVG, and PNG from 16 to 1024 px.
- `taskbar-zoo-0.9.0.zip` holds the whole set in one `taskbar-zoo/` folder, with `LICENSE` and a
  `README.txt` saying which file to use where.
