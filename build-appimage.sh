#!/bin/bash
# build-appimage.sh

set -e

APP_NAME="brepodder"
VERSION="0.1.0"

echo "Building PyInstaller executable..."
pyinstaller brepodder.spec

echo "Creating AppDir structure..."
rm -rf AppDir
mkdir -p AppDir/usr/bin

cp dist/${APP_NAME} AppDir/usr/bin/

# Create AppRun
cat > AppDir/AppRun << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin/:${PATH}"
exec "${HERE}/usr/bin/brepodder" "$@"
EOF
chmod +x AppDir/AppRun

# Create .desktop file
cat > AppDir/${APP_NAME}.desktop << EOF
[Desktop Entry]
Type=Application
Name=Brepodder
Comment=Podcast RSS feed aggregator
Exec=${APP_NAME}
Icon=${APP_NAME}
Categories=AudioVideo;Audio;
Terminal=false
EOF

# Create a simple icon if you don't have one
if [ ! -f icon.png ]; then
    echo "Creating placeholder icon..."
    convert -size 256x256 -gravity center -pointsize 72 \
        -fill white -background blue label:BR AppDir/${APP_NAME}.png
else
    cp icon.png AppDir/${APP_NAME}.png
fi

# Download appimagetool if not present
if [ ! -f appimagetool-x86_64.AppImage ]; then
    echo "Downloading appimagetool..."
    wget "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x appimagetool-x86_64.AppImage
fi

# Build AppImage
echo "Building AppImage..."
ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir ${APP_NAME}-${VERSION}-x86_64.AppImage

echo "Done! AppImage created: ${APP_NAME}-${VERSION}-x86_64.AppImage"
echo "Test it with: ./${APP_NAME}-${VERSION}-x86_64.AppImage"
