#!/usr/bin/env bash
# Installs/updates greed systemd service files
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_DIR="/etc/systemd/system"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run as root (for example: sudo bash deploy/systemd/install.sh)"
  exit 1
fi

echo "Installing greed systemd service files..."

cp "${SCRIPT_DIR}/greed-swap.service" "${SYSTEMD_DIR}/greed-swap.service"
cp "${SCRIPT_DIR}/greed-swap-instance@.service" "${SYSTEMD_DIR}/greed-swap-instance@.service"

systemctl daemon-reload

echo "Done. To enable and start all services:"
echo "  systemctl enable --now greed-swap.service"
echo "  for i in \$(seq 1 10); do systemctl enable --now greed-swap-instance@\${i}.service; done"
