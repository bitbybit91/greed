#!/usr/bin/env bash
# Greed Multi-Bot Management Script
# Usage: ./manage-bots.sh {start|stop|restart|status|logs}

set -euo pipefail

SERVICE_NAME="greed-swap"

usage() {
    echo "Usage: $0 {start|stop|restart|status|logs}"
    echo ""
    echo "Commands:"
    echo "  start    - Start the greed bot service"
    echo "  stop     - Stop the greed bot service"
    echo "  restart  - Restart the greed bot service"
    echo "  status   - Show the current status of the service"
    echo "  logs     - Follow the service logs in real-time"
    echo ""
    echo "Examples:"
    echo "  $0 start       # Start all configured bots"
    echo "  $0 logs         # Tail logs (Ctrl+C to stop)"
    echo "  $0 status       # Check if service is running"
    exit 1
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "Warning: Some commands may require root privileges."
        echo "Run with: sudo $0 $1"
    fi
}

case "${1:-}" in
    start)
        check_root "start"
        echo "Starting ${SERVICE_NAME}..."
        systemctl start "${SERVICE_NAME}"
        echo "Service started. Check status with: $0 status"
        ;;
    stop)
        check_root "stop"
        echo "Stopping ${SERVICE_NAME}..."
        systemctl stop "${SERVICE_NAME}"
        echo "Service stopped."
        ;;
    restart)
        check_root "restart"
        echo "Restarting ${SERVICE_NAME}..."
        systemctl restart "${SERVICE_NAME}"
        echo "Service restarted. Check status with: $0 status"
        ;;
    status)
        echo "=== Service Status ==="
        systemctl status "${SERVICE_NAME}" --no-pager || true
        echo ""
        echo "=== Memory Usage ==="
        systemctl show "${SERVICE_NAME}" --property=MemoryCurrent --no-pager 2>/dev/null || true
        ;;
    logs)
        echo "Following logs for ${SERVICE_NAME} (Ctrl+C to stop)..."
        journalctl -u "${SERVICE_NAME}" -f --no-pager
        ;;
    *)
        usage
        ;;
esac
