# backend.py  // Nancy
# Connects the UI to the Aggregator and then to the LLM Feedback Service

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

    # ----------------------------------------------------------
    # HANDLE SYNTAX ERRORS (stop early + return detailed message)
    # ----------------------------------------------------------
    if full_report.get("summary", {}).get("overall_status") == "STOPPED_DUE_TO_SYNTAX_ERRORS":

        syntax_findings = full_report.get("syntax", {}).get("findings", [])

        if syntax_findings:
            lines = []
            for f in syntax_findings:
                line = f.get("line") or f.get("location", {}).get("start", {}).get("line", "?")
                msg = f.get("message", "Unknown syntax error")
                snippet = f.get("snippet", "").strip()
                suggestion = f.get("suggestion", "")

                lines.append(f"Syntax Error on line {line}:\n{msg}")
                if snippet:
                    lines.append(f"→ {snippet}")
                if suggestion:
                    lines.append(f"Suggestion: {suggestion}")
                lines.append("")  # blank line for spacing

            detailed_message = (
                "\n".join(lines)
                + "\nPlease fix the syntax error(s) above before the AI reviewer can analyze "
                  "security, style, or performance."
            )
        else:
            detailed_message = (
                "Syntax errors were detected, but no details were provided. "
                "Please fix your code and try again."
            )

        return {
            "report": full_report,
            "llm_feedback": detailed_message
        }

    # ----------------------------------------------------------
    # NORMAL (NO SYNTAX ERRORS) — RUN LLM FEEDBACK PIPELINE
    # ----------------------------------------------------------
    formatted = format_report_with_line_numbers(full_report)
    runtime = full_report["summary"].get("performance_runtime_sec", "N/A")
    combined_text = f"{formatted}\n\n=== PERFORMANCE SUMMARY ===\nRuntime: {runtime}"

    llm_response = requests.post(
        "http://localhost:5003/generate_feedback",
        json={"combined_report": combined_text}
    )

    llm_text = llm_response.json().get("llm_feedback", "")

    return {
        "report": full_report,
        "llm_feedback": llm_text
    }
