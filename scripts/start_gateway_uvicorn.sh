#!/usr/bin/env bash
set -euo pipefail

# Launcher using uvicorn with reload (dev-friendly)
# Usage:
#   bash scripts/start_gateway_uvicorn.sh

ROOT="/Users/mikew/Desktop/AI_Code_Reviewer-Current GIthub"
PORT="${API_GATEWAY_PORT:-8000}"

cd "$ROOT"
exec uvicorn --app-dir src ai_code_reviewer.main:app --host 0.0.0.0 --port "$PORT" --reload


