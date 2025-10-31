#!/usr/bin/env bash
set -euo pipefail

# Simple test script for Style Analyzer (staticA.py)
# Make sure the style analyzer is running first: bash scripts/start_style.sh
# Usage:
#   bash scripts/test_style.sh

API_URL="${STYLE_URL:-http://127.0.0.1:5002}"

echo "=== Testing Style Analyzer ==="
echo ""

echo "1. Health check:"
curl -s "$API_URL/health" | python -m json.tool
echo ""

echo "2. Test with bad code (has style violations):"
curl -s -X POST "$API_URL/style" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def add(a,b):\n\treturn  a+ b  \n",
    "user_id": "test",
    "submission_id": "test-1"
  }' | python -m json.tool
echo ""

echo "3. Test with good code (minimal violations):"
curl -s -X POST "$API_URL/style" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def add(a: int, b: int) -> int:\n    return a + b\n",
    "user_id": "test",
    "submission_id": "test-2"
  }' | python -m json.tool
echo ""

echo "=== Tests complete ==="

