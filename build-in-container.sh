#!/bin/bash
# set -e

echo "=== runing build-in-container.sh ==="
# apt-get update
# apt-get install -y \
#     python3 \
#     python3-pip \
#     python3-dev \
#     wget \
#     file \
#     binutils \
#     patchelf

# echo "=== Upgrading pip ==="
# pip3 install --upgrade pip

# echo "=== Installing PyQt6 and dependencies from binary wheels ==="
# # Install PyQt6 from pre-built wheels (no compilation needed)
# pip3 install PyQt6 --only-binary :all:

# echo "=== Installing other Python dependencies ==="
# # Install your project dependencies
# cd /app
# if [ -f requirements.txt ]; then
#     pip3 install -r requirements.txt || true
# fi

# echo "=== Installing PyInstaller ==="
# pip3 install pyinstaller

echo "=== Building executable with PyInstaller ==="
pyinstaller brepodder.spec



echo "=== Creating AppDir structure ==="
rm -rf AppDir
mkdir -p AppDir/usr/bin
cp dist/brepodder AppDir/usr/bin/

cat > AppDir/AppRun << 'APPRUN'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin/:${PATH}"
exec "${HERE}/usr/bin/brepodder" "$@"
APPRUN
chmod +x AppDir/AppRun

cat > AppDir/brepodder.desktop << 'DESKTOP'
[Desktop Entry]
Type=Application
Name=Brepodder
Exec=brepodder
Icon=brepodder
Categories=AudioVideo;Audio;
Terminal=false
DESKTOP

echo '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><rect width="256" height="256" fill="#4285f4"/><text x="128" y="140" font-size="120" text-anchor="middle" fill="white">BR</text></svg>' > AppDir/brepodder.svg

echo "=== Downloading appimagetool ==="
wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

echo "=== Building AppImage ==="
ARCH=x86_64 ./appimagetool-x86_64.AppImage --appimage-extract-and-run AppDir /app/output/brepodder-0.1.0-x86_64.AppImage

echo "=== Checking GLIBC version requirement ==="
objdump -T /app/output/brepodder-0.1.0-x86_64.AppImage | grep GLIBC | sed 's/.*GLIBC_\([.0-9]*\).*/\1/g' | sort -Vu | tail -1 || echo "Could not determine GLIBC version"

echo ""
echo "=========================================="
echo "Build completed successfully!"
echo "=========================================="
