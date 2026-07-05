#!/usr/bin/env bash
# setup.sh — Automated installer for the greed Telegram shop bot on Ubuntu 20.04 VPS
# Safe to run multiple times (idempotent).
set -euo pipefail

INSTALL_DIR="/opt/greed"
VENV="$INSTALL_DIR/venv"
SERVICE="greed"
REPO_URL="https://github.com/bitbybit91/greed.git"
BRANCH="copilot/add-setup-bots-script"

echo "=== Greed Bot Setup for Ubuntu 20.04 ==="
echo ""

# ── 1. System packages ────────────────────────────────────────────────────────
echo ">>> Updating system packages..."
apt-get update -y
apt-get upgrade -y
apt-get install -y python3 python3-pip python3-venv git screen sqlite3

# ── 2. Clone or update repo ───────────────────────────────────────────────────
if [ -d "$INSTALL_DIR/.git" ]; then
    echo ">>> Repository already exists, pulling latest changes..."
    cd "$INSTALL_DIR"
    git fetch --all
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
else
    echo ">>> Cloning repository to $INSTALL_DIR ..."
    git clone --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"

# ── 3. Python virtual environment ─────────────────────────────────────────────
echo ">>> Setting up Python virtual environment..."
python3 -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip
"$VENV/bin/pip" install -r requirements.txt coloredlogs

# ── 4. Configuration file ─────────────────────────────────────────────────────
CONFIG="$INSTALL_DIR/config/config.toml"
if [ ! -f "$CONFIG" ]; then
    echo ">>> Creating config file from template..."
    cp "$INSTALL_DIR/config/template_config.toml" "$CONFIG"
    echo ""
    read -rp "Enter your Telegram bot token (from @BotFather): " BOT_TOKEN
    sed -i "s|123456789:YOUR_TOKEN_GOES_HERE_______________|${BOT_TOKEN}|g" "$CONFIG"
    echo ""
    echo "Config created at $CONFIG"
    echo "Edit it to set your deposit addresses and other settings before the bot starts."
else
    echo ">>> Config file already exists at $CONFIG — skipping creation."
fi

# ── 5. Systemd service ────────────────────────────────────────────────────────
echo ">>> Installing systemd service..."
cat > /etc/systemd/system/${SERVICE}.service <<EOF
[Unit]
Description=Greed Telegram Shop Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
ExecStart=${VENV}/bin/python -OO ${INSTALL_DIR}/core.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE"
systemctl restart "$SERVICE"

# ── 6. Done ───────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║         ✅  Setup Complete!               ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Service commands:"
echo "  Status : systemctl status $SERVICE"
echo "  Logs   : journalctl -u $SERVICE -f"
echo "  Restart: systemctl restart $SERVICE"
echo "  Stop   : systemctl stop $SERVICE"
echo ""
echo "Edit config : nano $CONFIG"
echo "After editing config, restart: systemctl restart $SERVICE"
echo ""
echo "Send /start to your bot in Telegram to become the first owner/admin."
echo ""
