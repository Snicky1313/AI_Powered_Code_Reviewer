#!/usr/bin/env bash
set -euo pipefail

# Launcher using uvicorn with reload (dev-friendly)
# Usage:
#   bash scripts/start_gateway_uvicorn.sh

# Get the project root directory (parent of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PORT="${API_GATEWAY_PORT:-8000}"

cd "$ROOT"
exec uvicorn --app-dir src ai_code_reviewer.main:app --host 0.0.0.0 --port "$PORT" --reload



