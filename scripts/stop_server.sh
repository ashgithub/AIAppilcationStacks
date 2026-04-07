#!/usr/bin/env bash
set -euo pipefail

# Stops API server using PID file first, then falls back to pattern kill.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

stop_from_pid_file "$SERVER_PID_FILE" "Server"

# Fallback for orphaned process without PID file.
pkill -f "__main__.py --host 127.0.0.1 --port $SERVER_PORT" 2>/dev/null || true

echo "Server stop complete."
