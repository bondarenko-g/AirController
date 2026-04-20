#!/bin/bash
# Install AirController as desktop autostart application

set -e

GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}Installing AirController autostart...${NC}"

# Get the directory where this script is run from
AIRCONTROLLER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Create autostart directory if it doesn't exist
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

# Create desktop entry
cat > "$AUTOSTART_DIR/aircontroller.desktop" << EOF
[Desktop Entry]
Type=Application
Name=AirController
Comment=Automatic stereo/mono switching for AirPods
Exec=/usr/bin/python3 $AIRCONTROLLER_DIR/main.py
Icon=audio-headset
Terminal=false
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

chmod +x "$AUTOSTART_DIR/aircontroller.desktop"

echo -e "${GREEN}✓ Autostart installed!${NC}"
echo "AirController will start when you login"