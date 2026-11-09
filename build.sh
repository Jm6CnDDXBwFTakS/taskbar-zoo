#!/bin/sh
# Build PNG/ICO/ICNS from the SVGs, then dist/taskbar-zoo.zip and the previews.
# Pass --full to regenerate the SVGs from art/ first.
# The zip comes before the previews: it needs nothing beyond Python, so a missing preview font
# can't stop it.
set -e
cd "$(dirname "$0")"
if [ "$1" = "--full" ]; then python3 tools/build.py svg; fi
python3 tools/build.py export
python3 tools/build.py zip
python3 tools/build.py previews
