#!/bin/bash
# WiFi Voucher System - Ubuntu/Linux Installation Script
# Run as root: sudo bash install.sh

set -e

APP_NAME="wifi-voucher-system"
APP_DIR="/opt/${APP_NAME}"
SERVICE_NAME="${APP_NAME}"
USER_NAME="wifiadmin"
PORT=${PORT:-8000}

echo "=========================================="
echo "  WiFi Voucher System - Installer"
echo "=========================================="
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run as root (sudo)"
    exit 1
fi

# Update system
echo "[1/7] Updating system packages..."
apt-get update -qq

# Install Python and dependencies
echo "[2/7] Installing Python and dependencies..."
apt-get install -y -qq python3 python3-pip python3-venv sqlite3 curl

# Create user
echo "[3/7] Creating service user..."
id -u "$USER_NAME" &>/dev/null || useradd -r -s /bin/false "$USER_NAME"

# Create app directory
echo "[4/7] Setting up application directory..."
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/db"
mkdir -p /var/log/${APP_NAME}

# Install Python packages
echo "[5/7] Installing Python packages..."
pip3 install -q fastapi uvicorn sqlalchemy aiosqlite pydantic pydantic-settings python-multipart passlib python-jose httpx

# Copy application files
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[6/7] Copying application files..."
cp -r "$SCRIPT_DIR/api" "$APP_DIR/"
cp -r "$SCRIPT_DIR/db" "$APP_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/requirements.txt" "$APP_DIR/"

# Create environment file
cat > "$APP_DIR/.env" <<EOF
DATABASE_URL=sqlite+aiosqlite://${APP_DIR}/db/wifi_system.db
SECRET_KEY=$(openssl rand -hex 32)
API_KEY=$(openssl rand -hex 16)
APP_NAME=WiFi Voucher System
DEBUG=false
PORT=${PORT}
HOST=0.0.0.0
CORS_ORIGINS=*
EOF

# Set permissions
chown -R "$USER_NAME:$USER_NAME" "$APP_DIR"
chown -R "$USER_NAME:$USER_NAME" /var/log/${APP_NAME}
chmod 600 "$APP_DIR/.env"

# Create systemd service
echo "[7/7] Creating systemd service..."
cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=WiFi Voucher System
After=network.target

[Service]
Type=simple
User=${USER_NAME}
Group=${USER_NAME}
WorkingDirectory=${APP_DIR}
Environment=PYTHONPATH=${APP_DIR}
Environment=DATABASE_URL=sqlite+aiosqlite://${APP_DIR}/db/wifi_system.db
Environment=SECRET_KEY=$(openssl rand -hex 32)
Environment=API_KEY=$(openssl rand -hex 16)
Environment=DEBUG=false
Environment=PORT=${PORT}
Environment=HOST=0.0.0.0
ExecStart=/usr/bin/python3 -m uvicorn api.main:app --host 0.0.0.0 --port ${PORT}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

echo ""
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "Service:     ${SERVICE_NAME}"
echo "Directory:   ${APP_DIR}"
echo "Port:        ${PORT}"
echo "User:        ${USER_NAME}"
echo ""
echo "Commands:"
echo "  Start:     sudo systemctl start ${SERVICE_NAME}"
echo "  Stop:      sudo systemctl stop ${SERVICE_NAME}"
echo "  Status:    sudo systemctl status ${SERVICE_NAME}"
echo "  Logs:      sudo journalctl -u ${SERVICE_NAME} -f"
echo ""
echo "URLs:"
echo "  Admin:     http://YOUR_SERVER_IP:${PORT}"
echo "  API Docs:  http://YOUR_SERVER_IP:${PORT}/docs"
echo "  Health:    http://YOUR_SERVER_IP:${PORT}/health"
echo ""
echo "Default login: admin / admin123"
echo ""
echo "IMPORTANT: Change default password after first login!"
echo ""
