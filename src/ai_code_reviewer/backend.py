# backend.py  // Nancy
# This is the middle module that connects the UI to the Backend Aggregator then LLM Feedback Service

from fastapi import FastAPI
from pydantic import BaseModel
import requests

from ai_code_reviewer.analyzers.aggregator import (
    run_all_analyzers,
    format_report_with_line_numbers
)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CodeInput(BaseModel):
    source_code: str

@app.post("/run-review")
def run_review(payload: CodeInput):
    code = payload.source_code

    # Run analyzers
    full_report = run_all_analyzers(code, filename="<ui_input>")

    # If syntax errors — return early
    if full_report.get("summary", {}).get("overall_status") == "STOPPED_DUE_TO_SYNTAX_ERRORS":
        return {
            "report": full_report,
            "llm_feedback": "Syntax errors detected. Please correct and try again."
        }

    # Format the analyzer report
    formatted = format_report_with_line_numbers(full_report)
    runtime = full_report["summary"].get("performance_runtime_sec", "N/A")
    combined_text = f"{formatted}\n\n=== PERFORMANCE SUMMARY ===\nRuntime: {runtime}"

    # Send formatted analyzer results to LLM Feedback Service
    llm_response = requests.post(
        "http://localhost:5003/generate_feedback",
        json={"combined_report": combined_text}
    )

    llm_text = llm_response.json().get("llm_feedback", "")

    return {
        "report": full_report,
        "llm_feedback": llm_text
    }
