#!/bin/bash
set -e

echo "=== running build-appimage-opus.sh ==="

IMAGE_NAME="brepodder-builder"
CONTAINER_NAME="brepodder-build-$$"

echo "==> Building Docker image..."
docker build -f Dockerfile.appimage -t "$IMAGE_NAME" .

echo "==> Running PyInstaller build..."
docker run --rm \
    --name "$CONTAINER_NAME" \
    -v "$(pwd)/dist:/app/dist" \
    -v "$(pwd)/output:/app/output" \
    "$IMAGE_NAME"

echo "==> Build complete!"
echo "Output: dist/brepodder"

# Show file info
if [ -f "dist/brepodder" ]; then
    echo ""
    echo "==> Binary info:"
    file dist/brepodder
    ls -lh dist/brepodder
fi
