#!/usr/bin/env bash
set -euo pipefail

# Stops client static server using PID file first, then falls back to pattern kill.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

stop_from_pid_file "$CLIENT_PID_FILE" "Client"

# Fallback for orphaned process without PID file.
pkill -f "http.server $CLIENT_PORT" 2>/dev/null || true

echo "Client stop complete."
