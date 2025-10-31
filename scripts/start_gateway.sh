#!/usr/bin/env bash
set -euo pipefail

# Simple launcher for the API Gateway (FastAPI)
# Usage:
#   bash scripts/start_gateway.sh

ROOT="/Users/mikew/Desktop/AI_Code_Reviewer-Current GIthub"
export PYTHONPATH="$ROOT/src:$ROOT"

# Optional: override API_GATEWAY_PORT, default 8000
export API_GATEWAY_PORT="${API_GATEWAY_PORT:-8000}"

exec python "$ROOT/src/ai_code_reviewer/main.py"


