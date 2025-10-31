#!/usr/bin/env bash
set -euo pipefail

# Simple launcher for the Style Analyzer (Flask on :5002)
# Usage:
#   bash scripts/start_style.sh

# Get the project root directory (parent of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec python "$ROOT/src/ai_code_reviewer/analyzers/staticA.py"



