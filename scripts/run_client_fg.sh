#!/usr/bin/env bash
set -euo pipefail

# Runs static client server in foreground (useful for debugging).

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

if [[ ! -f "$CLIENT_DIST_DIR/index.html" ]]; then
  echo "dist_web not found or incomplete: $CLIENT_DIST_DIR"
  echo "Build first from app/client: npm run build:prod"
  exit 1
fi

python3 -m http.server "$CLIENT_PORT" --bind 127.0.0.1 --directory "$CLIENT_DIST_DIR"
