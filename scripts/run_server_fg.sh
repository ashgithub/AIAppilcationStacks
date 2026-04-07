#!/usr/bin/env bash
set -euo pipefail

# Runs API server in foreground (useful for debugging).

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

cd "$SERVER_DIR"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$HOME/.cache/uv}"
uv run __main__.py --host 127.0.0.1 --port "$SERVER_PORT"
