#!/usr/bin/env bash
set -euo pipefail

# Shared paths and helpers for local VM process control.
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
RUN_DIR="$PROJECT_ROOT/run"
LOG_DIR="$PROJECT_ROOT/logs"

SERVER_PORT="${SERVER_PORT:-10002}"
CLIENT_PORT="${CLIENT_PORT:-6003}"

SERVER_PID_FILE="$RUN_DIR/edge-aistack-api-${SERVER_PORT}.pid"
CLIENT_PID_FILE="$RUN_DIR/edge-aistack-client-${CLIENT_PORT}.pid"

SERVER_LOG_FILE="$LOG_DIR/edge-aistack-api-${SERVER_PORT}.out"
CLIENT_LOG_FILE="$LOG_DIR/edge-aistack-client-${CLIENT_PORT}.out"

SERVER_DIR="$PROJECT_ROOT/app/server"
CLIENT_DIST_DIR="$PROJECT_ROOT/app/client/shell/dist_web"

ensure_runtime_dirs() {
  mkdir -p "$RUN_DIR" "$LOG_DIR"
}

is_pid_running() {
  local pid="$1"
  kill -0 "$pid" 2>/dev/null
}

stop_from_pid_file() {
  local pid_file="$1"
  local label="$2"

  if [[ ! -f "$pid_file" ]]; then
    echo "$label: PID file not found ($pid_file)"
    return 0
  fi

  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if [[ -z "$pid" ]]; then
    echo "$label: PID file is empty, removing stale file"
    rm -f "$pid_file"
    return 0
  fi

  if is_pid_running "$pid"; then
    echo "$label: stopping PID $pid"
    kill "$pid" || true
    sleep 1
    if is_pid_running "$pid"; then
      echo "$label: PID $pid still running, sending SIGKILL"
      kill -9 "$pid" || true
    fi
  else
    echo "$label: PID $pid is not running"
  fi

  rm -f "$pid_file"
}
