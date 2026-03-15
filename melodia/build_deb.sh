#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# build_deb.sh — Build the Melodia .deb package
#
# Requirements (install once):
#   sudo apt install build-essential devscripts debhelper dh-python \
#                    python3-all python3-setuptools python3-pip
#
# Usage:
#   chmod +x build_deb.sh
#   ./build_deb.sh
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail
cd "$(dirname "$0")"

PACKAGE="melodia"
VERSION="1.0.0"
DEB="${PACKAGE}_${VERSION}-1_all.deb"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Building $DEB"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Clean previous build artefacts
rm -rf build dist *.egg-info debian/melodia debian/.debhelper debian/files

# Build with dpkg-buildpackage (unsigned, no source package needed)
dpkg-buildpackage -b -us -uc -tc

echo ""
echo "✓ Done! Package built:"
ls -lh "../${DEB}" 2>/dev/null || ls -lh "${DEB}" 2>/dev/null || \
  find .. -maxdepth 1 -name '*.deb' -newer debian/changelog | xargs ls -lh

echo ""
echo "Install with:"
echo "  sudo dpkg -i ../${DEB}"
echo "  sudo apt-get install -f   # fix any missing dependencies"
