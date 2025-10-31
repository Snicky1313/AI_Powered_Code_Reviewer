#!/usr/bin/env bash
set -euo pipefail

# Submit a simple Python snippet to the API Gateway
# Usage:
#   bash scripts/submit_example.sh

URL="${API_URL:-http://127.0.0.1:8000/submit}"

curl -s -X POST "$URL" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user",
    "code": "import requests\ndef fetch_data(url):\n    data = requests.get(url)\n    print (data.status_code)\n    return data.text",
    "language": "python",
    "analysis_types": ["syntax", "style"],
    "include_llm_feedback": false
  }'



