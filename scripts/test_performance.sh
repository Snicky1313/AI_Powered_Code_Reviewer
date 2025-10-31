#!/usr/bin/env bash
set -euo pipefail

# Simple test script for Performance Profiler (performancePROF.py)
# Usage:
#   bash scripts/test_performance.sh

# Get the project root directory (parent of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export PYTHONPATH="$ROOT/src:$ROOT"

echo "=== Testing Performance Profiler ==="
echo ""

python - <<'PY'
from ai_code_reviewer.analyzers.performancePROF import PerformanceAnalyzer

analyzer = PerformanceAnalyzer(timeout_seconds=2.0)

print("1. Test with fast code:")
code_fast = "print('Hello World')"
result = analyzer.analyze(code_fast)
print(f"   Result: {result}")
print("")

print("2. Test with slow code (should timeout):")
code_slow = "import time\ntime.sleep(3)\nprint('Done')"
result = analyzer.analyze(code_slow)
print(f"   Result: {result}")
print("")

print("3. Test with infinite loop (will timeout):")
code_loop = "while True:\n    pass"
result = analyzer.analyze(code_loop)
print(f"   Result: {result}")
print("")

print("=== Tests complete ===")
PY

