# analyzers/llm_feedback.py
# Task 1.7 - LLM Feedback Service (Using Trussed API)
# Reproduces feedback from aggregator into human-like responses

import os
import json
import logging
from typing import Dict, Any
from flask import Flask, request, jsonify
import requests

# -----------------------------------------------------
# Flask + Logging Setup
# -----------------------------------------------------
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------------------------------
# Trussed API Configuration
# -----------------------------------------------------
API_URL = "https://fauengtrussed.fau.edu/provider/generic/chat/completions"
API_KEY = os.getenv("OPENAI_API_KEY")  # "WUs7HU5qGmJnmHsmGyXmEOTJnXfkPK7X1rqDgy6wbmWWc3uO" Delete this after we're done working on it
MODEL = "gpt-4o"

# -----------------------------------------------------
# Calling Trussed API
# -----------------------------------------------------
def get_llm_feedback(prompt: str) -> str:
    """
    Sends a text prompt to the Trussed GPT-4o endpoint and returns the model's reply.
    """
    if not API_KEY:
        raise ValueError("Missing OPENAI_API_KEY environment variable (Trussed key).")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are an expert software reviewer."},
            {"role": "user", "content": f"Provide human-readable feedback on the following code analysis report:\n{prompt}"}
        ],
        "max_tokens": 1500,
        "temperature": 0.5,
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"]
        return reply.strip()

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return f"Error: Unable to reach the LLM service — {e}"

    except (KeyError, json.JSONDecodeError) as e:
        logger.error(f"Malformed response from Trussed API: {e}")
        return "Error: Unexpected response format from the LLM."

# -----------------------------------------------------
# Flask route — used by Aggregator
# -----------------------------------------------------
@app.route("/generate_feedback", methods=["POST"])
def generate_feedback() -> Any:
    
    #Receives a 'combined_report' from the Aggregator,
    #sends it to the LLM, and returns structured feedback.
    
    try:
        data = request.get_json()
        combined_report = data.get("combined_report", {})
        logger.info("Received combined report for LLM feedback generation.")

        # Convert JSON to readable text
        prompt_text = json.dumps(combined_report, indent=2)
        feedback = get_llm_feedback(prompt_text)

        return jsonify({"llm_feedback": feedback}), 200

    except Exception as e:
        logger.error(f"Error generating feedback: {e}")
        return jsonify({"error": str(e)}), 500

# -----------------------------------------------------
# Run the Flask app
# -----------------------------------------------------
if __name__ == "__main__":
    logger.info("Starting LLM Feedback Service using Trussed API...")
    app.run(host="0.0.0.0", port=5003, debug=True)


