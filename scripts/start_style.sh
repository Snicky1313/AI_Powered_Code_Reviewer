#!/usr/bin/env bash
set -euo pipefail

# Simple launcher for the Style Analyzer (Flask on :5002)
# Usage:
#   bash scripts/start_style.sh

ROOT="/Users/mikew/Desktop/AI_Code_Reviewer-Current GIthub"

exec python "$ROOT/src/ai_code_reviewer/analyzers/staticA.py"


