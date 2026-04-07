#!/usr/bin/env bash
set -euo pipefail

# Starts static client server in the background with nohup.
# Uses port 6003 by default and serves app/client/shell/dist_web.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"
ensure_runtime_dirs

if [[ -f "$CLIENT_PID_FILE" ]] && is_pid_running "$(cat "$CLIENT_PID_FILE" 2>/dev/null || true)"; then
  echo "Client is already running (PID: $(cat "$CLIENT_PID_FILE"))"
  echo "Log: $CLIENT_LOG_FILE"
  exit 0
fi

if [[ ! -f "$CLIENT_DIST_DIR/index.html" ]]; then
  echo "dist_web not found or incomplete: $CLIENT_DIST_DIR"
  echo "Build first from app/client: npm run build:prod"
  exit 1
fi

echo "Starting client static server on 127.0.0.1:$CLIENT_PORT ..."
nohup python3 -m http.server "$CLIENT_PORT" --bind 127.0.0.1 --directory "$CLIENT_DIST_DIR" > "$CLIENT_LOG_FILE" 2>&1 &
PID=$!
echo "$PID" > "$CLIENT_PID_FILE"

echo "Client started (PID: $PID)"
echo "PID file: $CLIENT_PID_FILE"
echo "Log: $CLIENT_LOG_FILE"
