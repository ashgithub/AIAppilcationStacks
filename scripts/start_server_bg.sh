#!/usr/bin/env bash
set -euo pipefail

# Starts API server in the background with nohup.
# Uses port 10002 by default and writes PID/log files under project directories.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"
ensure_runtime_dirs

if [[ -f "$SERVER_PID_FILE" ]] && is_pid_running "$(cat "$SERVER_PID_FILE" 2>/dev/null || true)"; then
  echo "Server is already running (PID: $(cat "$SERVER_PID_FILE"))"
  echo "Log: $SERVER_LOG_FILE"
  exit 0
fi

if [[ ! -d "$SERVER_DIR" ]]; then
  echo "Server directory not found: $SERVER_DIR"
  exit 1
fi

echo "Starting API server on 127.0.0.1:$SERVER_PORT ..."
nohup bash -lc "export UV_CACHE_DIR=\"\$HOME/.cache/uv\"; cd \"$SERVER_DIR\" && uv run __main__.py --host 127.0.0.1 --port $SERVER_PORT" > "$SERVER_LOG_FILE" 2>&1 &
PID=$!
echo "$PID" > "$SERVER_PID_FILE"

echo "Server started (PID: $PID)"
echo "PID file: $SERVER_PID_FILE"
echo "Log: $SERVER_LOG_FILE"
