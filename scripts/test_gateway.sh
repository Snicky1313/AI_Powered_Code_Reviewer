#!/usr/bin/env bash
set -euo pipefail

# Simple test script for API Gateway (main.py)
# Make sure the gateway is running first: bash scripts/start_gateway.sh
# Usage:
#   bash scripts/test_gateway.sh

API_URL="${API_URL:-http://127.0.0.1:8000}"

echo "=== Testing API Gateway ==="
echo ""

echo "1. Root endpoint:"
curl -s "$API_URL/" | python -m json.tool
echo ""

echo "2. Health check:"
curl -s "$API_URL/health" | python -m json.tool
echo ""

echo "3. Submit code for analysis:"
curl -s -X POST "$API_URL/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "code": "def hello():\n    print(\"Hello World\")\n",
    "language": "python",
    "analysis_types": ["syntax", "style"],
    "include_llm_feedback": false
  }' | python -m json.tool
echo ""

echo "4. List all submissions:"
curl -s "$API_URL/submissions" | python -m json.tool
echo ""

echo "=== Tests complete ==="

