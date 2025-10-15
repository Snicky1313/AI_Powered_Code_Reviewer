#!/bin/bash
# Quick start script for LLM Feedback Service (Task 1.7)

echo "========================================"
echo "  LLM Feedback Service - Task 1.7"
echo "========================================"
echo ""

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  WARNING: OPENAI_API_KEY environment variable is not set!"
    echo ""
    echo "Please set your OpenAI API key:"
    echo "  export OPENAI_API_KEY='your-api-key-here'"
    echo ""
    echo "Get your API key from: https://platform.openai.com/api-keys"
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Starting LLM Feedback Service..."
echo "Service will be available at: http://localhost:5003"
echo ""
echo "Press Ctrl+C to stop the service"
echo ""

# Start the service
PYTHONPATH=${PYTHONPATH:-src} python -m ai_code_reviewer.analyzers.llm_feedback

