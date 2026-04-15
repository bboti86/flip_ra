#!/bin/bash
# Script to prepare a clean deployment folder excluding virtual environments and caches

DEPLOY_DIR="deploy/RA_Manager"

# ANSI Color Codes
GREEN='\033[92m'
BLUE='\033[94m'
CYAN='\033[96m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${BOLD}${BLUE}Cleaning old deployment...${RESET}"
rm -rf deploy

echo -e "${BOLD}${BLUE}Creating new deployment directory at '${CYAN}$DEPLOY_DIR${BLUE}'...${RESET}"
mkdir -p "$DEPLOY_DIR"

echo -e "${BOLD}${BLUE}Copying application files...${RESET}"
# Copy all necessary directories
cp -r core ui assets libs "$DEPLOY_DIR/" 2>/dev/null || true

# Copy top-level files
cp main.py launch.sh settings.json config.json icon.png "$DEPLOY_DIR/" 2>/dev/null || true

echo -e "${BOLD}${BLUE}Cleaning up __pycache__ directories from deployment...${RESET}"
find "$DEPLOY_DIR" -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true

echo -e "${BOLD}${GREEN}Deployment preparation complete! 🚀${RESET}"
echo -e "${BLUE}You can now copy the '${CYAN}$DEPLOY_DIR${BLUE}' folder directly to your SD card under the App/ directory.${RESET}"
