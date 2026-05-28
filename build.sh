#!/usr/bin/env bash
set -euo pipefail

echo "============================================"
echo " SEBI RA Automation - Unix Build Script"
echo "============================================"
echo

pip install "pyinstaller>=6.0"

echo
echo "Building executable..."
pyinstaller sebi_ra.spec --clean --noconfirm

echo
echo "Copying updater binary to output directory..."
if [ -f "dist/updater" ]; then
    cp "dist/updater" "dist/SEBI_RA_Automation/updater"
    chmod +x "dist/SEBI_RA_Automation/updater"
    echo "  updater copied."
else
    echo "WARNING: updater binary not found in dist/. Skipping copy."
fi

echo
echo "Creating release archive..."
VERSION=$(python3 -c "from core.version import __version__; print(__version__)")
case "$(uname -s)" in
    Darwin) PLATFORM="macOS" ;;
    *)      PLATFORM="Linux" ;;
esac
ZIP_NAME="SEBI_RA_Automation_v${VERSION}_${PLATFORM}"
DIST_DIR="dist/SEBI_RA_Automation"

if [ -d "$DIST_DIR" ]; then
    rm -f "dist/${ZIP_NAME}.zip"
    (cd dist && zip -r "${ZIP_NAME}.zip" "SEBI_RA_Automation/")
    echo "Release package created: dist/${ZIP_NAME}.zip"
else
    echo "WARNING: Could not find $DIST_DIR to archive."
fi

echo
echo "============================================"
echo " Build complete!"
echo " Output: dist/SEBI_RA_Automation/"
echo
echo " To run:"
echo "   ./dist/SEBI_RA_Automation/SEBI_RA_Automation"
echo "============================================"