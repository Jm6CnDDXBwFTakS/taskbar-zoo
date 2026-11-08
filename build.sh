#!/bin/sh
# Build PNG/ICO/ICNS from the SVGs. Pass --full to regenerate the SVGs from art/ first.
set -e
cd "$(dirname "$0")"
if [ "$1" = "--full" ]; then python3 tools/build.py svg; fi
python3 tools/build.py export
python3 tools/build.py previews
