#!/bin/sh
# Build PNG/ICO/ICNS from the SVGs, then dist/taskbar-zoo-<VERSION>.zip and the previews.
# Pass --full to regenerate the SVGs from art/ first.
# The zip and the previews don't depend on each other, so both run even if one fails (a bad
# VERSION file stops only the zip, a missing preview font only the previews); the script then
# exits with the last failure's status. The zip comes first: it needs nothing beyond Python.
set -e
cd "$(dirname "$0")"
if [ "$1" = "--full" ]; then python3 tools/build.py svg; fi
python3 tools/build.py export
status=0
python3 tools/build.py zip || status=$?        # `|| status=$?` records a failure without set -e exiting
python3 tools/build.py previews || status=$?
exit $status
