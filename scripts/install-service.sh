#!/bin/bash
# Install AirController as a systemd service

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Installing AirController systemd service...${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (sudo)$NC"
    exit 1
fi

# Get the actual user (even when run with sudo)
REAL_USER=${SUDO_USER:-$USER}
REAL_HOME=$(getent passwd $REAL_USER | cut -d: -f6)

# Paths
SERVICE_FILE="./scripts/aircontroller.service"
INSTALL_DIR="/opt/aircontroller"
SERVICE_DEST="/etc/systemd/system/aircontroller@.service"

echo -e "${YELLOW}Installing to $INSTALL_DIR${NC}"

# Create installation directory
mkdir -p $INSTALL_DIR

# Copy application files
cp -r ./AirController/*.py $INSTALL_DIR/
cp -r config/ $INSTALL_DIR/ 2>/dev/null || true

# Create log directory
mkdir -p /var/log/aircontroller
chown $REAL_USER:$REAL_USER /var/log/aircontroller

# Install service file
cp $SERVICE_FILE $SERVICE_DEST

# Reload systemd
systemctl daemon-reload

# Enable service for current user
systemctl enable aircontroller@$REAL_USER
systemctl start aircontroller@$REAL_USER

echo -e "${GREEN}✓ Service installed successfully!${NC}"
echo -e "${GREEN}✓ AirController is now running${NC}"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status aircontroller@$REAL_USER  # Check status"
echo "  sudo systemctl restart aircontroller@$REAL_USER # Restart service"
echo "  sudo journalctl -u aircontroller@$REAL_USER -f  # View logs"