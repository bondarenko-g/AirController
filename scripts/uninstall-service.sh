#!/bin/bash
# Uninstall AirController systemd service

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (sudo)$NC"
    exit 1
fi

REAL_USER=${SUDO_USER:-$USER}
SERVICE_NAME="aircontroller@$REAL_USER"

echo -e "${RED}Stopping and removing AirController service...${NC}"

systemctl stop $SERVICE_NAME
systemctl disable $SERVICE_NAME
rm -f /etc/systemd/system/aircontroller@.service
systemctl daemon-reload

echo -e "${GREEN}✓ Service removed${NC}"