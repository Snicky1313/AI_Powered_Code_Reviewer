#!/usr/bin/env bash
set -euo pipefail

# Simple launcher for the API Gateway (FastAPI)
# Usage:
#   bash scripts/start_gateway.sh

# Get the project root directory (parent of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export PYTHONPATH="$ROOT/src:$ROOT"

# Optional: override API_GATEWAY_PORT, default 8000
export API_GATEWAY_PORT="${API_GATEWAY_PORT:-8000}"

exec python "$ROOT/src/ai_code_reviewer/main.py"



