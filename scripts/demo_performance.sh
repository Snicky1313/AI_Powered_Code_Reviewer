#!/usr/bin/env bash
set -euo pipefail

# Simple launcher for Performance Profiler demo
# Usage:
#   bash scripts/demo_performance.sh

# Get the project root directory (parent of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export PYTHONPATH="$ROOT/src:$ROOT"

exec python "$ROOT/scripts/demo_performance.py"

