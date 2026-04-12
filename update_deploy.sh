#!/bin/bash
# Script to prepare a clean deployment folder excluding virtual environments and caches

DEPLOY_DIR="deploy/RA_Manager"

echo "Cleaning old deployment..."
rm -rf deploy

echo "Creating new deployment directory at '$DEPLOY_DIR'..."
mkdir -p "$DEPLOY_DIR"

echo "Copying application files..."
# Copy all necessary directories
cp -r core ui assets libs "$DEPLOY_DIR/" 2>/dev/null || true

# Copy top-level files
cp main.py launch.sh settings.json config.json icon.png "$DEPLOY_DIR/" 2>/dev/null || true

echo "Cleaning up __pycache__ directories from deployment..."
find "$DEPLOY_DIR" -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true

echo "Deployment preparation complete! 🚀"
echo "You can now copy the '$DEPLOY_DIR' folder directly to your SD card under the App/ directory."
